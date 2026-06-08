# Datastore lifecycle management

## Requirements

### 1. Push uploaded resources to the datastore

When a dataset is updated and one or more resources have a new file uploaded, each uploaded resource should be submitted to `datapusher_plus` for ingestion into the CKAN datastore, **provided both conditions are met**:

- **Supported format** — the resource's format is listed in `ckan.datapusher.formats` (or the fallback `ckanext.datapusher_plus.formats` config key).
- **HDX allowlist** — the dataset or its owning organisation is present in the HDX datastore allowlist, as determined by the `hdx_is_package_allowed_for_datastore` action.

### 2. Remove the datastore when a resource is no longer eligible

When a dataset is updated and one or more resources have a new file uploaded, any resource that **currently has an active datastore** (`datastore_active = True`) but no longer meets the eligibility criteria above must have its datastore table deleted. This covers two scenarios:

- **Format changed to an unsupported type** — e.g. the resource was a CSV (supported) and was re-uploaded as a PDF (not supported).
- **Dataset removed from the HDX allowlist** — the external allowlist may change between uploads; a resource that was allowed previously may no longer be allowed at the time of the next upload.

Only resources that had a file uploaded during the current update are evaluated. New resources (no prior existence) are excluded from cleanup.

---

## Implementation

Both operations are performed in `package_update()` in
`ckanext-hdx_package/ckanext/hdx_package/actions/update.py`, **after** `model.repo.commit()` and the subsequent `package_show` call. This ensures `datastore_active` and the saved resource format reflect the committed database state before any decision is made.

### `_submit_uploads_to_datapusher_plus(context, package_dict)`

Iterates over resource ids in `context[FILE_WAS_UPLOADED]` (set by `flag_if_file_uploaded()` earlier in the update). For each id (excluding `'NEW'`), locates the resource dict in `package_dict['resources']` and calls `datapusher_plus._submit_to_datapusher()`. The eligibility check (format + allowlist) is handled inside the datapusher_plus plugin.

### `_delete_datastore_if_no_longer_eligible(context, package_dict)`

Mirrors the eligibility logic from `_submit_to_datapusher` on the hdx-ckan side to identify resources whose datastore should be removed:

1. Returns immediately if `FILE_WAS_UPLOADED` is absent from context.
2. Reads supported formats once: `ckan.datapusher.formats` → fallback `ckanext.datapusher_plus.formats`.
3. Calls `hdx_is_package_allowed_for_datastore` **once per package**.
4. For each uploaded resource id (skipping `'NEW'`):
   - Skips if `datastore_active` is falsy — nothing to clean up.
   - If format is **not** in supported formats **or** package is **not** in the allowlist → calls `datastore_delete` with `force=True`.
   - The delete is wrapped in `try/except` so a cleanup failure never aborts the dataset update.

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

Unit tests for `_delete_datastore_if_no_longer_eligible` live in
`ckanext-hdx_package/ckanext/hdx_package/tests/test_actions/test_package_update.py`
(class `TestDatastoreCleanup`). The function is called directly with a crafted context and package dict; `_get_action` and `hdx_is_package_allowed_for_datastore` are patched with `unittest.mock.patch`.

| Test | Scenario | Expected |
|---|---|---|
| `test_no_delete_when_format_supported_and_allowed` | CSV, `datastore_active=True`, allowlist=True | `datastore_delete` **not** called |
| `test_delete_when_format_not_supported` | PDF, `datastore_active=True`, allowlist=True | `datastore_delete` called |
| `test_delete_when_not_hdx_allowed` | CSV, `datastore_active=True`, allowlist=False | `datastore_delete` called |
| `test_no_delete_when_datastore_not_active` | PDF, `datastore_active=False` | `datastore_delete` **not** called |
| `test_no_delete_for_new_resource` | `FILE_WAS_UPLOADED = {'NEW'}` | `datastore_delete` **not** called |
