# Datastore lifecycle management

## Requirements

### 1. Push uploaded (or URL-only) resources to the datastore

When a dataset is updated and one or more resources have a new file uploaded, each uploaded resource should be submitted to `datapusher_plus` for ingestion into the CKAN datastore, **provided both conditions are met**:

- **Supported format** — the resource's format is listed in `ckan.datapusher.formats` (or the fallback `ckanext.datapusher_plus.formats` config key).
- **HDX allowlist** — the dataset or its owning organisation is present in the HDX datastore allowlist, as determined by the `hdx_is_package_allowed_for_datastore` action.

The same eligibility logic also applies when a **brand-new, URL-only resource** (no uploaded file at all, e.g. a link to a remote CSV) is created via `resource_create()`: it must reach the same submission logic, even though it was never "uploaded" in the file sense. See [Implementation](#implementation) below for how the two cases (upload vs. URL-only creation) each reach `_manage_datastore_for_uploads()`.


### 2. Remove the datastore when a resource is no longer eligible

When a dataset is updated and one or more resources have a new file uploaded, any resource that **currently has a datastore table** but no longer meets the eligibility criteria above must have its datastore table deleted. This covers two scenarios:

- **Format changed to an unsupported type** — e.g. the resource was a CSV (supported) and was re-uploaded as a PDF (not supported).
- **Dataset removed from the HDX allowlist** — the external allowlist may change between uploads; a resource that was allowed previously may no longer be allowed at the time of the next upload.

Only resources that had a file uploaded during the current update are evaluated. New resources (no prior existence) are excluded from cleanup.

---

## Implementation

`_manage_datastore_for_uploads()` is invoked from **two distinct call paths**, both of which populate `context[FILE_WAS_UPLOADED]` before calling it — the function itself is agnostic to which path called it:

1. **`package_update()`** (`ckanext-hdx_package/ckanext/hdx_package/actions/update.py`) — **after** `model.repo.commit()` and the subsequent `package_show` call, so the saved resource format reflects the committed database state before any decision is made. This covers genuine file uploads/re-uploads: existing resources are flagged with their real id before validation, new resources (including ones created via `resource_create()`'s underlying `package_revise` → `package_update` call, when a real `upload` payload is present) are flagged with their real id after `model.Session.flush()`.
2. **`resource_create()`** (`ckanext-hdx_package/ckanext/hdx_package/actions/create.py`) — for **URL-only** new resources specifically (no `upload` payload at all). `package_update()`'s upload-based flagging never considers these (it only flags resources with a truthy `upload`), so `resource_create()` constructs its own single-resource `context[FILE_WAS_UPLOADED]` set — `{FILE_WAS_UPLOADED: {resource['id']}}` — right after the resource is created (its real id and the full package dict are already known at that point) and calls `_manage_datastore_for_uploads()` directly, **outside** of any `package_update()` call. This only runs when the resource was **not** a genuine upload (`was_real_upload` is `False`, captured before `data_dict` is mutated), so a genuine upload created via `resource_create()` is never evaluated twice — it's already fully handled by path 1 above.

### `_manage_datastore_for_uploads(context, package_dict)`

Iterates over resource ids in `context[FILE_WAS_UPLOADED]` (populated by whichever of the two call paths above invoked it). Eligibility is computed once per resource and the resource goes down exactly one path — submit or delete, never both:

1. Returns immediately if `FILE_WAS_UPLOADED` is absent from context.
2. Reads and normalises supported formats once via `_normalize_supported_formats`: `ckan.datapusher.formats` → fallback `ckanext.datapusher_plus.formats`.
3. Calls `hdx_is_package_allowed_for_datastore` **once per package**. If it raises, logs the exception and returns immediately without submitting or deleting (fail open).
4. For each uploaded resource id:
   - Computes `eligible`: format is in supported formats **and** package is in the allowlist **and** `url_type != "datapusher"`.
   - If **eligible** → calls `datapusher_plus._submit_to_datapusher()`. Any existing datastore table is replaced by the DP+ job itself.
   - If **not eligible** → calls `_datastore_table_exists()` to check whether a real table exists. If it does, calls `datastore_delete` with `force=True`. The delete is wrapped in `try/except` so a cleanup failure never aborts the dataset update.

### `_datastore_table_exists(resource_id)`

Calls `datastore_search` with `limit=0` to verify whether a datastore table actually exists for the resource. Returns `True` if the search succeeds, `False` if it raises `ObjectNotFound`. This is used instead of the `datastore_active` metadata field, which can be out of sync with reality (e.g. if the form submission set it to `False` before the delete was triggered).

### `_normalize_supported_formats(config_value)`

Normalises the formats config value to a lowercase set, handling both list-typed config values and legacy space/comma-separated strings.

### Config keys

| Key | Purpose |
|---|---|
| `ckan.datapusher.formats` | Primary list of formats eligible for datastore ingestion |
| `ckanext.datapusher_plus.formats` | Fallback (used when primary key is absent) |

### Related actions

| Action | Defined in | Purpose |
|---|---|---|
| `hdx_is_package_allowed_for_datastore` | `ckanext-hdx_package/ckanext/hdx_package/actions/get.py` | Returns `True` if the dataset or its org is in the HDX datastore allowlist |
| `datastore_delete` | `ckanext/datastore/logic/action.py` | Drops the datastore table and sets `datastore_active = False` |

---

## Tests

Unit tests for `_manage_datastore_for_uploads` live in
`ckanext-hdx_package/ckanext/hdx_package/tests/test_actions/test_package_update.py`
(class `TestManageDatastoreForUploads`). The function is called directly with a crafted context and package dict; `_get_action`, `tk`, and `plugins.PluginImplementations` are patched with `unittest.mock`.

| Test | Scenario | Expected |
|---|---|---|
| `test_submit_when_eligible` | CSV, `datastore_active=True`, allowlist=True | `_submit_to_datapusher` **called**, `datastore_delete` **not** called |
| `test_delete_when_format_not_supported` | PDF, datastore table exists, allowlist=True | `datastore_delete` **called**, `_submit_to_datapusher` **not** called |
| `test_delete_when_not_hdx_allowed` | CSV, datastore table exists, allowlist=False | `datastore_delete` **called**, `_submit_to_datapusher` **not** called |
| `test_no_action_when_ineligible_and_no_datastore_table` | PDF, no datastore table, allowlist=True | neither called |
| `test_no_action_for_unmatched_id` | `FILE_WAS_UPLOADED` contains an id with no matching resource in `package_dict` (stale/unknown id) | neither called |
| `test_skip_on_allowlist_exception` | allowlist lookup raises | returns early; neither called |
| `test_submit_when_formats_config_is_string` | CSV, string config `'csv xls xlsx tsv'`, allowlist=True | `_submit_to_datapusher` **called**, `datastore_delete` **not** called |

Regression tests for the `resource_create()` call path (path 2 above) live in the same file, class `TestHDXPackageUpdate`, and exercise the real `resource_create()` action end-to-end (DB-backed):

| Test | Scenario | Expected |
|---|---|---|
| `test_resource_create_url_only_reaches_manage_datastore` | New resource, no `upload` payload (URL-only) | `_manage_datastore_for_uploads` **called once**, with `context[FILE_WAS_UPLOADED] == {new_resource_id}` |
| `test_resource_create_real_upload_does_not_double_submit` | New resource with a genuine `upload` payload | `resource_create()`'s own explicit call to `_manage_datastore_for_uploads` **not** called (already handled by `package_update()`'s internal call) |

