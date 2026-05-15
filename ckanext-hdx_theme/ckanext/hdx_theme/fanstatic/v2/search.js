(function () {
  'use strict';

  var FILTER_PARAMS = ['groups', 'organization', 'res_format', 'vocab_Topics'];

  var ADVANCED_FILTER_PARAMS = [
    'ext_subnational', 'ext_geodata', 'ext_p_coded',
    'ext_tabular_data', 'ext_hdx_hapi',
    'cod_level'
  ];


  // ── URL helpers ─────────────────────────────────────────────────────────────

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
    url.searchParams.set('page', '1');
    window.location.href = url.toString();
  }

  function clearFacet(facet) {
    var url = new URL(window.location.href);
    url.searchParams.delete(facet);
    url.searchParams.set('page', '1');
    window.location.href = url.toString();
  }

  function clearAdvancedFilters() {
    var url = new URL(window.location.href);
    ADVANCED_FILTER_PARAMS.forEach(function (param) { url.searchParams.delete(param); });
    url.searchParams.set('page', '1');
    window.location.href = url.toString();
  }

  function clearAllFilters() {
    var url = new URL(window.location.href);
    FILTER_PARAMS.forEach(function (param) { url.searchParams.delete(param); });
    ADVANCED_FILTER_PARAMS.forEach(function (param) { url.searchParams.delete(param); });
    url.searchParams.set('page', '1');
    window.location.href = url.toString();
  }

  // ── Mixpanel helper ──────────────────────────────────────────────────────────

  function track(event, props) {
    try {
      if (window.mixpanel && typeof window.mixpanel.track === 'function') {
        window.mixpanel.track(event, props);
      }
    } catch (ex) {}
  }

  // ── Dropdown open/close ──────────────────────────────────────────────────────

  function closeAllDropdowns(except) {
    document.querySelectorAll('[data-filter-key].c-dropdown--open').forEach(function (dd) {
      if (dd === except) return;
      dd.classList.remove('c-dropdown--open');
      var t = dd.querySelector('.c-dropdown__trigger');
      var p = dd.querySelector('.c-dropdown__panel');
      if (t) t.setAttribute('aria-expanded', 'false');
      if (p) p.hidden = true;
      var searchWrapper = dd.querySelector('[data-filter-search]');
      if (searchWrapper) {
        var si = searchWrapper.querySelector('input');
        if (si && si.value) { si.value = ''; si.dispatchEvent(new Event('input')); }
      }
    });
  }

  // ── SearchFilters init ───────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', function () {

    // Set indeterminate state on parent group-toggle checkboxes
    document.querySelectorAll('[data-indeterminate]').forEach(function (input) {
      input.indeterminate = true;
    });

    // Delegated: regular checkbox change → URL update
    document.addEventListener('change', function (e) {
      var cb = e.target;

      if (cb.hasAttribute('data-filter-checkbox')) {
        var facet   = cb.getAttribute('data-facet');
        var value   = cb.value;
        var checked = cb.checked;
        updateUrl(facet, value, checked);
        // track('filter_applied', { facet: facet, value: value, checked: checked });
        return;
      }

      // Group "select all" parent toggle
      if (cb.hasAttribute('data-group-toggle')) {
        var group   = cb.getAttribute('data-group');
        var checked = cb.checked;
        var panel   = cb.closest('.c-dropdown__panel');
        if (!panel) return;
        var children = panel.querySelectorAll('[data-filter-checkbox][data-facet="' + group + '"]');
        var url = new URL(window.location.href);
        url.searchParams.delete(group);
        if (checked) {
          children.forEach(function (child) {
            url.searchParams.append(group, child.value);
          });
        }
        url.searchParams.set('page', '1');
        // track('filter_applied', { facet: group, value: 'ALL', checked: checked });
        window.location.href = url.toString();
      }
    });

    // Delegated: click dispatcher
    document.addEventListener('click', function (e) {

      // ── Dropdown trigger toggle ───────────────────────────────
      var trigger = e.target.closest && e.target.closest('[data-filter-key] .c-dropdown__trigger');
      if (trigger) {
        var dd     = trigger.closest('[data-filter-key]');
        var isOpen = dd.classList.contains('c-dropdown--open');
        closeAllDropdowns(dd);
        dd.classList.toggle('c-dropdown--open', !isOpen);
        trigger.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
        var panel = dd.querySelector('.c-dropdown__panel');
        if (panel) panel.hidden = isOpen;
        e.stopPropagation();
        return;
      }

      // ── Outside click → close all ─────────────────────────────
      if (!e.target.closest || !e.target.closest('[data-filter-key]')) {
        closeAllDropdowns(null);
      }

      // ── Clear single facet ────────────────────────────────────
      var clearBtn = e.target.closest && e.target.closest('[data-action="clear-filter"]');
      if (clearBtn) {
        var facet = clearBtn.getAttribute('data-facet');
        clearFacet(facet);
        // track('filter_cleared', { scope: 'single', facet: facet });
        return;
      }

      // ── Clear advanced filters (ext_* + cod_level) ────────────
      var clearAdvBtn = e.target.closest && e.target.closest('[data-action="clear-advanced"]');
      if (clearAdvBtn) {
        clearAdvancedFilters();
        // track('filter_cleared', { scope: 'advanced' });
        return;
      }

    });

  });

  // ── Filter search (MiniSearch) ───────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', function () {
    if (typeof MiniSearch === 'undefined' || typeof toNormalForm === 'undefined') return;

    document.querySelectorAll('[data-filter-search]').forEach(function (wrapper) {
      var key       = wrapper.getAttribute('data-filter-search');
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
        // track('filter_cleared', { scope: 'all' });
        clearAllFilters();
        return;
      }
    });

  });

})();
