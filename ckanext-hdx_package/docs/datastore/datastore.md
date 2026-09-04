# Datastore lifecycle management

## Requirements

### 1. Push uploaded (or URL-only) resources to the datastore

When a dataset is updated and one or more resources are new or have a new file uploaded, each such resource should be submitted to `datapusher_plus` for ingestion into the CKAN datastore, **provided both conditions are met**:

- **Supported format** — the resource's format is listed in `ckan.datapusher.formats` (or the fallback `ckanext.datapusher_plus.formats` config key).
- **HDX allowlist** — the dataset or its owning organisation is present in the HDX datastore allowlist, as determined by the `hdx_is_package_allowed_for_datastore` action.

The same eligibility logic applies uniformly to **brand-new resources regardless of how they were added** — a genuine file upload, or a URL-only resource (no uploaded file at all, e.g. a link to a remote CSV) — and regardless of the call path: `resource_create()`, a direct `package_revise(update__resources__extend=[...])` call, or any other caller of `package_update()`. See [Implementation](#implementation) below.

### 2. Remove the datastore when a resource is no longer eligible

When a dataset is updated and one or more resources have a new file uploaded, any resource that **currently has a datastore table** but no longer meets the eligibility criteria above must have its datastore table deleted. This covers two scenarios:

- **Format changed to an unsupported type** — e.g. the resource was a CSV (supported) and was re-uploaded as a PDF (not supported).
- **Dataset removed from the HDX allowlist** — the external allowlist may change between uploads; a resource that was allowed previously may no longer be allowed at the time of the next upload.

Only resources that had a file uploaded during the current update are evaluated. New resources (no prior existence) are excluded from cleanup.

### 3. Never act on non-committed or rolled-back data, and never break the calling action

- If the caller sets `context['defer_commit']`, `package_update()` doesn't commit the transaction itself — datastore management must not run in that case either, since DataPusher+ is a separate process/worker that could otherwise be told to ingest (or delete) a resource whose row isn't actually persisted yet, or one that's later rolled back by the deferring caller. It's the deferring caller's responsibility to trigger datastore management themselves after their own commit, if needed.
- A transient failure inside datastore management (e.g. a DataPusher+/network hiccup) must never make an otherwise-successful, already-committed `package_update()` call fail for the caller — that would surface as a spurious error on an action that actually succeeded, inviting client retries that can create duplicate resources.

---

## Implementation

`_manage_datastore_for_uploads()` is invoked from a **single call path**: inside `package_update()` (`ckanext-hdx_package/ckanext/hdx_package/actions/update.py`), **after** `model.repo.commit()` and the subsequent `package_show` call, so the saved resource format reflects the committed database state before any decision is made. This one call path covers every way a resource can reach `package_update()`, including via `resource_create()`'s underlying `package_revise` → `package_update` call, or a direct `package_revise(update__resources__extend=[...])` call — there is no separate/duplicate call path in `create.py`.

`package_update()`'s own flagging loop populates `context[FILE_WAS_UPLOADED]` with the real id of every resource that should be evaluated:

- **Existing resources with a real upload/re-upload** are flagged with their real id before validation (needed so validators like `hdx_reset_on_file_upload` can read the flag during validation).
- **Existing resources whose `url` changed** (e.g. a link-type resource edited directly through the form/API, with no `upload`/`clear_upload` key at all) are likewise flagged before validation. This mirrors what CKAN core's `resource_dict_save()` itself checks to set `obj.url_changed = True`, replacing reliance on the `IResourceUrlChange` hook (`DatapusherPlusPlugin.notify()`, now an intentional no-op — see rationale in `update.py`). The comparison tolerates CKAN's own scheme-less-vs-`http://` synthesis (`model_dictize.resource_dictize()`) without masking a genuine `http -> https` scheme change (see `test_package_update_existing_resource_url_change_reaches_manage_datastore` and `test_package_update_http_to_https_url_change_reaches_manage_datastore`).
- **Existing resources whose `last_modified` changed** (e.g. a harvester/`package_revise` call bumping `last_modified` for content at a stable remote URL, to signal "re-fetch me") are likewise flagged before validation, mirroring the same `resource_dict_save()` check (`'last_modified' in changed and not new`) (see `test_package_update_stable_url_last_modified_change_reaches_manage_datastore`).
- **Every brand-new resource** — whether it has a genuine `upload` payload or is URL-only (no `upload` key at all) — is flagged with its real id after `model.Session.flush()`, once that id is known. Format/allowlist eligibility is still fully decided inside `_manage_datastore_for_uploads()` itself, so it's safe to flag every new resource unconditionally here.
- A caller-supplied resource id that reuses a **deleted resource from a different package** is still treated as existing for this flagging (via a targeted global id lookup), matching CKAN core's unfiltered `resource_dict_save()` lookup (see `test_package_update_cross_package_deleted_resource_id_flagged_pre_validation`).

Two safety mechanisms wrap the call itself:

- **`defer_commit` gate**: the call is skipped entirely (and logged) when `context.get('defer_commit')` is truthy, since the enclosing transaction hasn't actually been committed (or may still be rolled back) at that point.
- **Fail-open `try/except`**: any exception raised by `_manage_datastore_for_uploads()` (e.g. an unguarded exception from `DatapusherPlusPlugin._submit_to_datapusher()`, such as its allowlist lookup or `task_status_show` call) is caught and logged, never allowed to propagate out of `package_update()`.

### `_manage_datastore_for_uploads(context, package_dict)`

Iterates over resource ids in `context[FILE_WAS_UPLOADED]`. Eligibility is computed once per resource and the resource goes down exactly one path — submit or delete, never both:

1. Returns immediately if `FILE_WAS_UPLOADED` is absent from context.
2. Reads and normalises supported formats once via `_normalize_supported_formats`: `ckan.datapusher.formats` → fallback `ckanext.datapusher_plus.formats`.
3. Calls `hdx_is_package_allowed_for_datastore` **once per package** as a precheck. If it raises, logs the exception and returns immediately without submitting or deleting (fail open).
4. For each uploaded resource id:
   - Computes `eligible`: format is in supported formats **and** package is in the allowlist (per the precheck above) **and** `url_type != "datapusher"`.
   - If **eligible** → calls `datapusher_plus._submit_to_datapusher()`, which — in the pinned `datapusher-plus` dependency (`src/datapusher-plus/ckanext/datapusher_plus/plugin.py`) — calls `hdx_is_package_allowed_for_datastore` **again**, per resource, before actually submitting. So an eligible package/resource pair triggers **two** allowlist lookups in total for that resource: one package-level precheck here, plus one more inside the plugin per submitted resource. Any existing datastore table is replaced by the DP+ job itself.
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

Regression tests exercising `package_update()`'s real flagging/call logic end-to-end (DB-backed) live in the same file, class `TestHDXPackageUpdate`:

| Test | Scenario | Expected |
|---|---|---|
| `test_resource_create_url_only_reaches_manage_datastore` | New resource created via `resource_create()`, no `upload` payload (URL-only) | `_manage_datastore_for_uploads` **called once**, with the new resource's id in `context[FILE_WAS_UPLOADED]` |
| `test_package_revise_direct_url_only_new_resource_reaches_manage_datastore` | New URL-only resource added via a **direct** `package_revise(update__resources__extend=[...])` call, no `resource_create()` involved | `_manage_datastore_for_uploads` **called once**, with the new resource's id in `context[FILE_WAS_UPLOADED]` |
| `test_package_update_defer_commit_skips_datastore_management` | `package_update()` called with `context['defer_commit'] = True` | `_manage_datastore_for_uploads` **not** called |
| `test_package_update_datastore_management_failure_does_not_propagate` | `_manage_datastore_for_uploads` raises an exception | `package_update()` still returns successfully (exception is caught and logged) |
