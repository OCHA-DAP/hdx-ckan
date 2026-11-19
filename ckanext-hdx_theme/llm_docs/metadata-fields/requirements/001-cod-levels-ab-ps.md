# 001 — COD levels: replace Standard / Enhanced with COD-AB / COD-PS

Jira: [HDX-11735](https://humanitarian.atlassian.net/browse/HDX-11735), bundled with the label bug
[HDX-11726](https://humanitarian.atlassian.net/browse/HDX-11726).
Parent initiative: DSHDX-1151 / HDXCLEAN-120 (COD-AB clean-up).
Dataset → level mapping: `cod_level_mapping.csv` from the ticket (314 rows), kept next to the
migration script in `tmp/cod_level_migration/` (gitignored, not committed).

---

## Scope

Included:
- `cod_level` allowed values become `cod-ab`, `cod-ps`, `not-cod`. `cod-standard`, `cod-enhanced` and
  `cod-candidate` are removed and rejected by validation.
- One-off migration script (datasets + crisis pages), run manually right after the deploy.
- COD sub-categories in the Advanced filters: **COD Admin Boundaries** (`cod-ab`) and
  **COD Population Stats** (`cod-ps`).
- A `COD` label on the v2 dataset card and the v2 dataset page header for both levels (HDX-11726).
- COD documentation link constant → `https://docs.humdata.org/about/cod`.
- `page_group_list` input checks (the script depends on it): 409 for a missing `id`, 404 for an
  unknown page, instead of a 500.

Out of scope:
- Info icons / "Learn more" links in the v2 Advanced filters (HDX-11734) — deferred.
- Redesign of v1 / light templates; they only need to keep working.

---

## 1. Audit — current implementation

### Data model (`ckanext-hdx_package`)

| Piece | Where | Behaviour |
|---|---|---|
| Allowed values | `helpers/constants.py` — `COD_ENHANCED`, `COD_STANDARD`, `COD_CANDIDATE`, `COD_NOT`, `COD_VALUES_MAP` | Ordered map: `title`, `is_cod`, `explanation`, computed `index` (sort order in the filter) |
| Doc link | `helpers/constants.py` — `COD_GROUP_EXPLANATION_LINK` | ArcGIS storymap URL |
| Create/update schema | `plugin.py` — `cod_level` | `hdx_delete_unless_authorized_to_update_cod` (needs the `hdx_cod_update` permission) → `hdx_keep_prev_value_if_empty` → `hdx_in_cod_values` → extra |
| List validation | `plugin.py` — `hdx_in_cod_values` = `vd.hdx_value_in_list_wrapper(COD_VALUES_MAP.keys(), False)` | Existing generic validator ("Value not in allowed list"), reused as is — only the map's keys change |
| Show schema | `plugin.py` | `convert_from_extras`, `ignore_missing` — no validation on read |
| Analytics | `helpers/analytics.py` — `is_cod()` | `'true'` only for `cod-enhanced` / `cod-standard`; feeds Mixpanel `isCod` / "is cod" and the page header's `cod_dataset` flag |
| Resource grouping | `helpers/resource_grouping.py` — `set_show_groupings_flag()`, called by `views/dataset.py` on every dataset page view | `COD_VALUES_MAP.get(cod_level).get('is_cod')` — **raises `AttributeError` on a value not in the map → dataset page 500** |
| Edit UI | none | `cod_level` is set only via the API |

### Search / facets (`ckanext-hdx_search`)

- `plugin.py` registers the facet `{!ex=cod_level,batch}cod_level` ("CODs").
- `controller_logic/search_logic.py` — `__create_featured_cod_facet_category()` keeps only values with
  `is_cod` in `COD_VALUES_MAP`, takes `display_name` / `explanation` from the map, sorts by `index`,
  builds the parent "CODs" row and sets `explanation_link`. Otherwise value-agnostic.

### Display (`ckanext-hdx_theme`)

| Template | Finding |
|---|---|
| `search/snippets/package_item_v2.html` | Badge `COD` only when `cod_level == 'cod'` (a value that never exists → **no badge for standard CODs**, HDX-11726); `cod-enhanced` → `COD+` (type `cod_plus`) |
| `v2/components/dataset-card.html` | `cod` / `cod_plus` types → `c-label` `color='dark'`, `size='xs'`, text from the item |
| `package/hdx_read.html` → `v2/components/page-header.html` | `cod_dataset=(analytics_is_cod == 'true')`; header renders `c-label` text **`COD+` hardcoded** (`color='grey'`, `size='s'`) → every COD shows "COD+" (HDX-11726) |
| `search/snippets/package_icons_cod.html` (v1 card) | `COD`, with a `+` suffix for `cod-enhanced` — shows plain `COD` after the migration |
| `search/snippets/package_search_facets.html` | v1 filter, still rendered by the light pages (`/m/search`, `/m/dataset`, `/m/event/<id>`, light org/location pages). The **only** place that shows each item's `explanation` (`[?]` tooltip) and the `explanation_link` ("[Learn more]") |
| `v2/search-filters.html`, `search/snippets/package_list.html`, `v2/pages/search.js`, `google-analytics.js` | Value-agnostic (read names from the facet data) |

### Crisis pages (`ckanext-hdx_pages`)

Sections store a `data_url`; `helpers/helper.py` turns its query params into an `fq`. Production check
(public `page_list`, 2026-11-18) — 11 active pages, 2 use `cod_level`:

| Page | Type / status | `data_url` | Effect if not updated |
|---|---|---|---|
| `cod` | event / **ongoing** | `/dataset?cod_level=cod-standard&cod_level=cod-enhanced` | **Dataset list becomes empty** |
| `turkiye-syria-earthquakes` | event / archived | `/search?q=… OR cod_level:cod-standard OR cod_level:cod-enhanced …&groups=tur&groups=syr&ext_archived=0` | COD datasets drop out of the OR'ed `q` |

API: `page_show` (public), `page_group_list` (public, returns group ids), `page_update` (needs the
manage-crisis permission). `page_update` **replaces the whole page**:
- groups and tags are deleted and re-created from the request — `page_show` does not return groups,
  so they must come from `page_group_list`, or the page loses its locations;
- `extras` is stored as sent, but `page_show` returns it parsed — it must be sent back as a JSON string;
- `sections` is a JSON string in both directions.

`page_group_list` (`actions/get.py`) has no input checks: it reads `data_dict['id']` directly
(`KeyError` when `id` is missing, e.g. when `name` is passed) and
`PageGroupAssociation.get_group_ids_for_page()` (`model.py`) dereferences the result of
`Page.get_by_id()` without a `None` check (`AttributeError` for an unknown page). Both surface as
HTTP 500 — reproduced on production with no params, `?name=cod` and an unknown `id`. With a valid
`id` (page UUID or name) it returns the stored location names (`["syr", "tur"]`).

### Production data vs CSV (2026-11-18)

| Check | Result |
|---|---|
| COD datasets in production (public) | 314 — `cod-enhanced` 222, `cod-standard` 92; no `cod-candidate` |
| CSV rows | 314 — `cod-ab` 165, `cod-ps` 149 |
| Names | Identical sets |
| `cod_level_current` vs production | One difference: `cod-ab-bhr` is `cod-enhanced` in production, `cod-standard` in the CSV — irrelevant, the script uses `cod_level_new` only |
| Name prefix vs new level | All match except `global-pcodes` → `cod-ab` (tagged "administrative boundaries-divisions", so consistent) |

Private datasets are not visible to the public check; the script's final check covers them.

### Tests

`tests/test_dataset_special_fields/test_cod.py`, `tests/test_helpers/test_resource_grouping.py`.

---

## 2. Target

```
Advanced filters                      Dataset card            Dataset page header
☐ CODs (314)                          [COD]  dark, xs         [COD]  grey, s
   ☐ COD Admin Boundaries (165)       (both levels)           (both levels)
   ☐ COD Population Stats (149)
```

---

## 3. Approach

### 3.1 Code (one release)

1. **Constants** (`hdx_package/helpers/constants.py`)
   - Add `COD_AB = 'cod-ab'`, `COD_PS = 'cod-ps'`; keep `COD_NOT`; remove `COD_STANDARD`,
     `COD_ENHANCED`, `COD_CANDIDATE`.
   - `COD_VALUES_MAP`: `not-cod` (`is_cod` False), `cod-ab` → "COD Admin Boundaries", `cod-ps` →
     "COD Population Stats" (`is_cod` True, no `explanation`).
   - `COD_GROUP_EXPLANATION_LINK` → `https://docs.humdata.org/about/cod`.
2. **Validation**: no code change — `hdx_in_cod_values` already reuses `hdx_value_in_list_wrapper`
   over `COD_VALUES_MAP.keys()`, so the old values are rejected.
3. **Is-COD check**: `is_cod_level(cod_level)` in `constants.py`, next to `COD_VALUES_MAP` (reads its
   `is_cod`, `False` for any value not in the map), used by `analytics.is_cod()`,
   `set_show_groupings_flag()` and the new template helper `h.hdx_is_cod(pkg_dict)` (`helpers.py`,
   registered by the `hdx_package` plugin).
4. **Resource grouping** `set_show_groupings_flag()`: `COD_VALUES_MAP.get(cod_level, {})`, so a value
   missing from the map can't 500 the dataset page (needed between deploy and migration).
5. **Labels** (HDX-11726)
   - `package_item_v2.html`: one `cod` badge with text `COD` for any COD level (via the helper);
     removes the `'cod'` / `'cod-enhanced'` comparisons.
   - `page-header.html`: label text `COD+` → `COD`. The `cod_dataset` param and `hdx_read.html` stay
     as they are.
   - `package_icons_cod.html` (v1): unchanged — its `+` suffix check simply stops matching.
6. **`page_group_list`** (`ckanext-hdx_pages/actions/get.py`), same pattern as `page_show` in that
   file: missing `id` → `logic.ValidationError({'id': _('Missing value')})` (409); `Page.get_by_id()`
   returns `None` → `NotFound` (404); otherwise pass `page.id` to `get_group_ids_for_page()`. Return
   value and behaviour for valid input unchanged; no auth function added (still public).
7. **Tests**: update `test_cod.py` (new values accepted, old ones rejected, permission rule kept) and
   `test_resource_grouping.py`; add tests for the COD facet category (names, order, counts); in
   `ckanext-hdx_pages/tests/test_api.py`, `page_group_list` with a missing `id`
   (ValidationError) and an unknown page (NotFound).

### 3.2 Release sequence

```
deploy (accepts only cod-ab / cod-ps / not-cod)
        │   window — keep it as short as possible:
        │   - dataset pages still render (3.1 step 4)
        │   - COD filter shows no sub-categories, no COD badges
        │   - updates to COD datasets fail validation (old value kept, then rejected)
        │   - the `cod` crisis page lists no datasets
        ▼
run the migration script immediately (datasets, then crisis pages, then checks)
```

Notifications: not affected — they fire only for resource/data changes; this is a metadata change.

### 3.3 Migration script

One-off, run manually, **not committed**: `tmp/cod_level_migration/migrate_cod_levels.py` (`tmp/` is
gitignored). Python + `requests` against the CKAN action API.

- Inputs: `--url` (site), API token from an env var, `--csv` (default: `cod_level_mapping.csv` next
  to the script),
  `--apply` (default is a dry run that only prints the planned changes).
- Token: a sysadmin (has both `hdx_cod_update` — without it `hdx_delete_unless_authorized_to_update_cod`
  silently drops the field — and the manage-crisis permission for `page_update`).
- **Datasets**: for each row, `package_patch(id=name, cod_level=cod_level_new)`; skip rows already at
  the new value (safe to re-run); log and continue on errors; summary of ok / skipped / failed.
- **Crisis pages**: for `cod` and `turkiye-syria-earthquakes` (found by scanning `page_list` for
  `cod_level` in a section's `data_url`): `page_show` + `page_group_list`, replace `cod-standard` →
  `cod-ab` and `cod-enhanced` → `cod-ps` in the `data_url`s (both pages use both old values, so each
  ends up filtering on both new ones), then `page_update` with every field sent back: `name`, `title`,
  `description`, `type`, `state`, `status`, `sections` (string), `extras` (JSON string), `groups` (ids),
  `tags` (names). Dry run prints the before/after `data_url`s.
- **Final checks**: `package_search` with `include_private=True` for
  `cod_level:(cod-standard OR cod-enhanced OR cod-candidate)` → expect 0, otherwise **list the
  datasets found (flag only, no change)**; facet counts for `cod-ab` / `cod-ps` → expect 165 / 149;
  no page `data_url` contains an old value.
- Test run against a local / staging instance before production.

---

## 4. Decisions taken

| # | Question | Decision |
|---|---|---|
| D1 | Where do these requirements live? | New `llm_docs/metadata-fields/` category, not the redesign |
| D2 | Filter shape | Keep the "CODs" parent with sub-categories |
| D3 | Sub-category names | `cod-ab` → "COD Admin Boundaries", `cod-ps` → "COD Population Stats" |
| D4 | `cod-candidate` | Dropped |
| D5 | Badge | Text `COD` for both levels, in today's `COD+` style (card: dark `xs`; page header: grey `s`) |
| D6 | Info icons in filters (HDX-11734) | Not now |
| D7 | Notifications during migration | None expected — metadata-only change |
| D8 | Old values after migration | Rejected, through the existing `hdx_value_in_list_wrapper` validator |
| D9 | Release | Deploy the version that accepts only the new values, then run the migration immediately |
| D10 | Migration script | In this repo, not committed, run once manually |
| D11 | Crisis pages | Updated by the same script through `page_show` / `page_group_list` / `page_update` |
| D12 | External scripts writing old values | Team already notified |
| D13 | Explanations for COD-AB / COD-PS | None — they only render on the light (`/m/...`) pages, which are no longer used |
| D14 | Datasets on an old value that are not in the CSV (e.g. private) | The script's final check lists them; no automatic change |
| D15 | Location of the CSV | `tmp/cod_level_migration/`, next to the script, not committed |
| D16 | Make `page_show` return the page's groups so the script needs no `page_group_list` call | No, not in this task (`page_show` runs on every crisis page view and in several internal callers; groups alone wouldn't make `page_show` → `page_update` a clean round trip because of the `extras` format) |
| D17 | `page_group_list` 500s on a missing `id` / unknown page | Fixed in this task: 409 / 404, as `page_show` |

---

## 5. Files affected

| File | Change |
|---|---|
| `ckanext-hdx_package/.../helpers/constants.py` | `COD_AB`, `COD_PS` replace `COD_STANDARD`, `COD_ENHANCED`, `COD_CANDIDATE`; new `COD_VALUES_MAP` entries (no explanations); `is_cod_level()`; `DOCUMENTATION_LINKS['COD']` → `COD_GROUP_EXPLANATION_LINK` |
| `ckanext-hdx_package/.../helpers/analytics.py` | `is_cod()` uses `is_cod_level()` |
| `ckanext-hdx_package/.../helpers/resource_grouping.py` | `set_show_groupings_flag()` uses `is_cod_level()` (no crash on unknown values) |
| `ckanext-hdx_package/.../helpers/helpers.py`, `plugin.py` | New template helper `hdx_is_cod` |
| `ckanext-hdx_theme/.../templates/search/snippets/package_item_v2.html` | `COD` badge for any COD level via `h.hdx_is_cod` |
| `ckanext-hdx_theme/.../templates/v2/components/page-header.html` | Label text `COD+` → `COD` (+ param doc) |
| `ckanext-hdx_pages/.../actions/get.py` | `page_group_list`: 409 missing `id`, 404 unknown page |
| `ckanext-hdx_package/.../tests/test_dataset_special_fields/test_cod.py` | New values, permission rule, old values rejected |
| `ckanext-hdx_package/.../tests/test_helpers/test_resource_grouping.py` | Real values instead of mocking `COD_VALUES_MAP`; unknown/old value → no grouping, no exception |
| `ckanext-hdx_search/.../tests/test_cod_facet_category.py` (new) | COD filter group: children names, order, counts, old values dropped, doc link |
| `ckanext-hdx_pages/.../tests/test_api.py` | `page_group_list` by name, missing `id`, `name` instead of `id`, unknown page |
| `tmp/cod_level_migration/migrate_cod_levels.py` + `cod_level_mapping.csv` | One-off migration (not committed) |

No search-page render cost change: the card swaps two string comparisons for one dict lookup per
dataset; no new queries.

---

## 6. Verification

- [ ] Test suites (`hdx_package` COD + grouping, `hdx_search`
      `test_cod_facet_category.py`, `hdx_pages` `test_api.py`) pass in the CKAN test environment.
- [ ] Local / staging: a dataset patched to `cod-ab` / `cod-ps` shows `COD` on its search card and
      dataset page header; a dataset still on an old value renders its page without error.
- [ ] Advanced filters show "CODs" with "COD Admin Boundaries" / "COD Population Stats"; selecting
      them filters correctly and the applied-filter pills use those names.
- [ ] Mixpanel dataset events report "is cod" true for both levels.
- [ ] Migration script dry run, then `--apply` on staging; checks section reports no problems.
- [ ] Production: deploy, run the script with `--apply` immediately, checks report no problems,
      `/event/cod` lists the same datasets as before the migration.
