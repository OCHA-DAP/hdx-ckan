(function () {
  'use strict';

  var FILTER_PARAMS = ['groups', 'organization', 'res_format', 'vocab_Topics'];

  // vocab_Topics is included here too (as well as in FILTER_PARAMS) because
  // nested HPC advanced-filter items share the vocab_Topics facet key.
  var ADVANCED_FILTER_PARAMS = [
    'ext_subnational', 'ext_geodata', 'ext_p_coded',
    'ext_tabular_data', 'ext_hdx_hapi',
    'cod_level', 'vocab_Topics'
  ];

  // ── URL helpers ─────────────────────────────────────────────────────────────
  // setNavParam lives in url-nav.js (loaded as a dependency).

  var setNavParam = window.hdxSetNavParam;

  function updateUrl(facet, value, checked) {
    var url    = new URL(window.location.href);
    var values = url.searchParams.getAll(facet);

    if (checked) {
      if (values.indexOf(value) === -1) {
        url.searchParams.append(facet, value);
      }
    } else {
      url.searchParams.delete(facet);
      values.filter(function (v) { return v !== value; }).forEach(function (v) {
        url.searchParams.append(facet, v);
      });
    }
    url.searchParams.delete('page');
    window.location.href = url.toString();
  }

  function clearFacet(facet) {
    var url = new URL(window.location.href);
    url.searchParams.delete(facet);
    url.searchParams.delete('page');
    window.location.href = url.toString();
  }

  function clearAdvancedFilters() {
    var url = new URL(window.location.href);
    ADVANCED_FILTER_PARAMS.forEach(function (param) { url.searchParams.delete(param); });
    url.searchParams.delete('page');
    window.location.href = url.toString();
  }

  function clearAllFilters() {
    var url = new URL(window.location.href);
    FILTER_PARAMS.forEach(function (param) { url.searchParams.delete(param); });
    ADVANCED_FILTER_PARAMS.forEach(function (param) { url.searchParams.delete(param); });
    url.searchParams.delete('page');
    window.location.href = url.toString();
  }

  // Dropdown open/close is handled by v2/components/dropdown.js (globally).

  // ── SearchFilters init ───────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', function () {

    // Set indeterminate state on parent group-toggle checkboxes
    document.querySelectorAll('[data-indeterminate]').forEach(function (input) {
      input.indeterminate = true;
    });

    // Delegated: regular checkbox change → URL update
    document.addEventListener('change', function (e) {
      var el = e.target;

      if (el.hasAttribute('data-filter-checkbox')) {
        updateUrl(el.getAttribute('data-facet'), el.value, el.checked);
        return;
      }

      // Group "select all" parent toggle
      if (el.hasAttribute('data-group-toggle')) {
        var group   = el.getAttribute('data-group');
        var checked = el.checked;
        var panel   = el.closest('.c-dropdown__panel');
        if (!panel) return;
        var children = panel.querySelectorAll('[data-filter-checkbox][data-facet="' + group + '"]');
        var groupUrl = new URL(window.location.href);
        groupUrl.searchParams.delete(group);
        if (checked) {
          children.forEach(function (child) {
            groupUrl.searchParams.append(group, child.value);
          });
        }
        groupUrl.searchParams.set('page', '1');
        window.location.href = groupUrl.toString();
        return;
      }

      if (el.hasAttribute('data-archived-toggle')) {
        var url = el.getAttribute('data-url');
        if (url) window.location.href = url;
      }
    });

    // ── Inline search bar: intercept Enter before list-header.js ─────────
    // list-header.js (loaded for both v1/v2) has a jQuery keydown handler on
    // #headerSearch that builds a v1-style URL — losing active filter params.
    // A capture-phase listener on the form parent fires before that handler.
    var searchForm = document.getElementById('dataset-filter-form');
    if (searchForm) {
      searchForm.addEventListener('keydown', function (e) {
        var input = e.target;
        if (input.name === 'q' && (e.key === 'Enter' || e.keyCode === 13)) {
          e.stopPropagation();
          e.preventDefault();
          setNavParam('q', input.value.trim());
        }

      }, true); // capture phase

      // Same interception for real form submits — the search-input submit
      // icon and the clear button (input-field.js) go through requestSubmit;
      // a native GET here would drop the URL-held facet params.
      searchForm.addEventListener('submit', function (e) {
        e.preventDefault();
        var input = searchForm.querySelector('input[name="q"]');
        setNavParam('q', input ? input.value.trim() : '');
      });
    }

    // Nav-item click (sort/page-size dropdowns) is handled by url-nav.js.
    // Dropdown open/close and outside-click-close are handled by dropdown.js.
    // This handler covers only search-specific click interactions.
    document.addEventListener('click', function (e) {

      // ── Clear facet / advanced filters ───────────────────────
      var clearBtn = e.target.closest && e.target.closest('[data-action="clear-filter"]');
      if (clearBtn) {
        var facet = clearBtn.getAttribute('data-facet');
        if (facet === 'advanced') {
          clearAdvancedFilters();
        } else {
          clearFacet(facet);
        }
        return;
      }

      /* ── Prior implementation (task 065, D5) — chip-based Advanced
         filters click handlers. Kept for reference / possible future
         reuse; superseded by the checkbox/change-based logic above,
         now that Advanced filters renders inside a dropdown panel again.

      // ── Advanced filters: group "select all" chip ─────────────
      var groupChip = e.target.closest && e.target.closest('button[data-group-toggle]');
      if (groupChip) {
        var group     = groupChip.getAttribute('data-group');
        var selectAll = !groupChip.classList.contains('c-selection-item--active');
        var wrapper   = groupChip.closest('.hdx-v2-advanced-filters__group');
        var groupUrl  = new URL(window.location.href);
        groupUrl.searchParams.delete(group);
        if (selectAll && wrapper) {
          wrapper.querySelectorAll('[data-facet="' + group + '"][data-value]').forEach(function (child) {
            groupUrl.searchParams.append(group, child.getAttribute('data-value'));
          });
        }
        groupUrl.searchParams.delete('page');
        window.location.href = groupUrl.toString();
        return;
      }

      // ── Advanced filters: flat / child chip ───────────────────
      var chip = e.target.closest && e.target.closest('button[data-filter-checkbox]');
      if (chip) {
        var chipChecked = !chip.classList.contains('c-selection-item--active');
        updateUrl(chip.getAttribute('data-facet'), chip.getAttribute('data-value'), chipChecked);
        return;
      }

      */

      // ── Applied filters: remove pill ──────────────────────────
      var pillBtn = e.target.closest && e.target.closest('[data-action="remove-pill"]');
      if (pillBtn) {
        var pillUrl = pillBtn.getAttribute('data-url');
        if (pillUrl) {
          window.location.href = pillUrl;
        } else {
          updateUrl(pillBtn.getAttribute('data-facet'), pillBtn.getAttribute('data-value'), false);
        }
        return;
      }

      // ── Applied filters: show more / show less ────────────────
      var toggleBtn = e.target.closest && e.target.closest('[data-action="toggle-pill-overflow"]');
      if (toggleBtn) {
        var list = document.querySelector('.hdx-v2-applied-filters__list');
        if (!list) return;
        var expanded = list.classList.toggle('hdx-v2-applied-filters__list--expanded');
        toggleBtn.classList.toggle('hdx-v2-applied-filters__toggle--expanded', expanded);
        var label = toggleBtn.querySelector('.c-text-button__label');
        if (label) label.textContent = expanded ? 'Show less' : 'Show more';
      }

    });

  });

  // ── Filter search (MiniSearch) ───────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', function () {
    if (typeof MiniSearch === 'undefined' || typeof toNormalForm === 'undefined') return;

    document.querySelectorAll('[data-filter-search]').forEach(function (wrapper) {
      var dd        = wrapper.closest('[data-filter-key]');
      var searchInput = wrapper.querySelector('input');
      if (!dd || !searchInput) return;

      var checkboxes = Array.from(dd.querySelectorAll('[data-filter-checkbox]'));
      if (checkboxes.length === 0) return;

      var ms = new MiniSearch({ fields: ['title'], storeFields: ['title'] });
      ms.addAll(checkboxes.map(function (cb, idx) {
        var li    = cb.closest('.c-list-item');
        var label = li ? li.querySelector('.c-list-item__label') : null;
        return { id: idx, title: toNormalForm(label ? label.textContent.trim() : '') };
      }));

      searchInput.addEventListener('input', function () {
        var value = toNormalForm(searchInput.value.trim());
        if (!value) {
          checkboxes.forEach(function (cb) {
            var li = cb.closest('.c-list-item');
            if (li) li.style.display = '';
          });
          return;
        }
        var hits   = ms.search(value, { prefix: true, combineWith: 'AND' });
        var hitIds = hits.map(function (r) { return parseInt(r.id); });
        checkboxes.forEach(function (cb, idx) {
          var li = cb.closest('.c-list-item');
          if (li) li.style.display = hitIds.indexOf(idx) !== -1 ? '' : 'none';
        });
      });
    });
  });

  // ── FilterOverlay init ───────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', function () {
    var overlay   = document.getElementById('hdx-filter-overlay');
    var filterBtn = document.querySelector('[data-module="filter-btn"]');

    if (!overlay) return;

    function openOverlay() {
      overlay.classList.add('hdx-v2-search-filter-overlay--open');
      document.body.style.overflow = 'hidden';
      if (filterBtn) filterBtn.setAttribute('aria-expanded', 'true');
      var firstFocusable = overlay.querySelector('button, [href], input');
      if (firstFocusable) firstFocusable.focus();
    }

    function closeOverlay() {
      overlay.classList.remove('hdx-v2-search-filter-overlay--open');
      document.body.style.overflow = '';
      if (filterBtn) {
        filterBtn.setAttribute('aria-expanded', 'false');
        filterBtn.focus();
      }
    }

    if (filterBtn) {
      filterBtn.addEventListener('click', openOverlay);
    }

    document.addEventListener('click', function (e) {
      if (!e.target.closest) return;

      if (e.target.closest('[data-action="close-overlay"]')) {
        closeOverlay();
        return;
      }
      if (e.target.closest('[data-action="show-results"]')) {
        closeOverlay();
        return;
      }
      if (e.target.closest('[data-action="clear-filters"]')) {
        e.preventDefault();
        clearAllFilters();
        return;
      }
    });

  });

  // ── Applied filters: pill row overflow detection ─────────────────────────────

  document.addEventListener('DOMContentLoaded', function () {
    var list   = document.querySelector('.hdx-v2-applied-filters__list');
    var toggle = document.querySelector('[data-action="toggle-pill-overflow"]');
    if (!list || !toggle) return;

    function checkOverflow() {
      var wasExpanded = list.classList.contains('hdx-v2-applied-filters__list--expanded');
      list.classList.remove('hdx-v2-applied-filters__list--expanded');
      var overflows = list.scrollHeight > list.clientHeight + 1;
      toggle.hidden = !overflows;
      if (wasExpanded && overflows) list.classList.add('hdx-v2-applied-filters__list--expanded');
    }

    checkOverflow();
    window.addEventListener('load', checkOverflow);

    var resizeTimer;
    window.addEventListener('resize', function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(checkOverflow, 150);
    });
  });

})();
