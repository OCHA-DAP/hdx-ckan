/*
 * v2/search-autocomplete.js
 *
 * Global search autocomplete for the HDX v2 header and homepage hero.
 * Reuses feature_index, MiniSearch, and normalize.js from search-scripts bundle.
 *
 * Behaviour by breakpoint:
 *   XL (≥ 80rem) — inline dropdown panel below the input
 *   MD/SM (< 80rem) — fullscreen overlay (#hdx-search-autocomplete-overlay)
 *
 * Triggers for the overlay:
 *   • SM: search icon button ([data-action="open-search-overlay"])
 *   • MD: focus on any navbar c-autocomplete input
 *   • MD/SM: focus on homepage hero c-autocomplete input
 */

(function () {
  'use strict';

  var MAX_RESULTS   = 5;
  var MAX_QUERY_LEN = 200;
  var BP_XL         = '(min-width: 80rem)';

  // ── Index (built once) ───────────────────────────────────────────────

  var searchIndex = null;

  function buildIndex() {
    if (typeof feature_index === 'undefined' || typeof MiniSearch === 'undefined') return null;

    var idx = new MiniSearch({
      fields:       ['title', 'title_nf', 'extra_terms', 'event', 'url'],
      storeFields:  ['title', 'url', 'type']
    });

    for (var i = 0; i < feature_index.length; i++) {
      var fi   = feature_index[i];
      fi.id    = i;
      fi.title_nf = typeof toNormalForm !== 'undefined' ? toNormalForm(fi.title) : fi.title;
      fi.event = fi.type === 'event' ? (fi.extra_terms || '') : '';
    }
    idx.addAll(feature_index);
    return idx;
  }

  function performSearch(query) {
    if (!searchIndex) return { results: [], termList: [] };

    var trimmed = query.trim().slice(0, MAX_QUERY_LEN);
    var normalized = typeof toNormalForm !== 'undefined' ? toNormalForm(trimmed) : trimmed;
    var termList = normalized.split(/\s+/).filter(function (w) { return w.length; });

    var modifiedQ = termList.join(' ');
    if (!modifiedQ) return { results: [], termList: [] };

    var hits = searchIndex.search(modifiedQ, {
      prefix: true,
      boost:  { title: 10, event: 1000 }
    });

    return { results: hits.slice(0, MAX_RESULTS), termList: termList };
  }

  // ── DOM helpers ──────────────────────────────────────────────────────

  function sanitize(str) {
    if (typeof hdxUtil !== 'undefined' && hdxUtil.text && hdxUtil.text.sanitize) {
      return hdxUtil.text.sanitize(str);
    }
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function processTitle(title, termList) {
    if (!termList || !termList.length) return title;
    var terms = termList.map(function (t) { return String(t).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); });
    var re = new RegExp(terms.join('|'), 'gi');
    return title.replace(re, '<strong>$&</strong>');
  }

  function getTypeLabel(type) {
    if (type === 'organisation') return 'Organisation';
    if (type === 'location')     return 'Location';
    if (type === 'event')        return 'Crisis';
    return type ? type.charAt(0).toUpperCase() + type.slice(1) : '';
  }

  function renderResults(container, hits, termList) {
    container.innerHTML = '';

    if (!hits.length) {
      var msg = document.createElement('div');
      msg.className   = 'c-autocomplete__no-results';
      msg.textContent = 'No results found';
      container.appendChild(msg);
      return;
    }

    hits.forEach(function (hit) {
      var item  = feature_index[hit.id];
      var title = sanitize(item.title);

      var row = document.createElement('div');
      row.className = 'c-autocomplete__result-row';
      row.setAttribute('role',          'option');
      row.setAttribute('aria-selected', 'false');
      row.setAttribute('tabindex',      '-1');
      row.setAttribute('data-href',     item.url);
      row.setAttribute('data-type',     item.type);

      // Mirror the text-link snippet output (style=tertiary, size=m)
      var linkWrap = document.createElement('div');
      linkWrap.className = 'c-autocomplete__result-link';

      var a = document.createElement('a');
      a.className = 'c-text-link c-text-link--tertiary c-text-link--size-m c-autocomplete__result-label';
      a.href      = item.url;
      a.title     = item.title;
      a.innerHTML = processTitle(title, termList);
      linkWrap.appendChild(a);

      var badge = document.createElement('span');
      badge.className   = 'c-autocomplete__result-count';
      badge.textContent = getTypeLabel(item.type);

      row.appendChild(linkWrap);
      row.appendChild(badge);
      container.appendChild(row);
    });
  }

  function setFilledState(searchInputEl, hasValue) {
    if (!searchInputEl) return;
    searchInputEl.classList.toggle('c-search-input--filled', !!hasValue);
  }

  // ── Analytics + navigation ───────────────────────────────────────────

  function navigateToResult(row, searchTerm) {
    var href = row.getAttribute('data-href');
    var type = row.getAttribute('data-type');
    if (!href) return;

    var source =
      (row.closest && row.closest('[data-hdx-v2-search-autocomplete]') &&
        row.closest('[data-hdx-v2-search-autocomplete]').getAttribute('data-search-source')) ||
      (ovSourceInput && ovSourceInput.value) ||
      '';

    if (source) {
      try {
        var u = new URL(href, window.location.origin);
        u.searchParams.set('ext_search_source', source);
        href = u.toString();
      } catch (err) {
        // Ignore URL parse errors
      }
    }

    var follow = function () { window.location.href = href; };
    if (searchTerm && type && typeof hdxUtil !== 'undefined' && hdxUtil.analytics) {
      hdxUtil.analytics.sendTopBarSearchEvents(searchTerm, type).then(follow, follow);
    } else {
      follow();
    }
  }

  // ── Keyboard navigation (shared) ─────────────────────────────────────

  function handleKeyNav(e, resultsContainer, inputEl, onClose) {
    var rows    = Array.from(resultsContainer.querySelectorAll('.c-autocomplete__result-row'));
    var current = rows.findIndex(function (r) { return r.getAttribute('aria-selected') === 'true'; });

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        var next = (current + 1 < rows.length) ? current + 1 : 0;
        activateRow(rows, next);
        break;

      case 'ArrowUp':
        e.preventDefault();
        if (current <= 0) {
          activateRow(rows, -1);
          if (inputEl) inputEl.focus();
        } else {
          activateRow(rows, current - 1);
        }
        break;

      case 'Enter':
        if (current >= 0 && rows[current]) {
          e.preventDefault();
          navigateToResult(rows[current], inputEl ? inputEl.value : '');
        }
        break;

      case 'Escape':
        e.preventDefault();
        if (onClose) onClose();
        if (inputEl) inputEl.focus();
        break;
    }
  }

  function activateRow(rows, index) {
    rows.forEach(function (r, i) {
      r.setAttribute('aria-selected', i === index ? 'true' : 'false');
    });
    if (index >= 0 && rows[index]) rows[index].focus();
  }

  // ── Overlay ──────────────────────────────────────────────────────────

  var ov            = null;
  var ovInput       = null;
  var ovSearchInput = null;  // .c-search-input wrapper around ovInput
  var ovResults     = null;
  var ovSourceInput = null;  // hidden ext_search_source <input>
  var ovTrigger     = null;

  function initOverlay() {
    ov = document.getElementById('hdx-search-autocomplete-overlay');
    if (!ov) return;

    ovInput       = ov.querySelector('#hdx-search-overlay-input');
    ovSearchInput = ovInput && ovInput.closest('.c-search-input');
    ovResults     = ov.querySelector('.hdx-v2-search-filter-overlay__results');
    ovSourceInput = ov.querySelector('input[name="ext_search_source"]');

    if (ovInput) {
      ovInput.addEventListener('input', function () {
        setFilledState(ovSearchInput, ovInput.value);
        updateOverlayClearBtn();
        runOverlaySearch(ovInput.value);
      });

      ovInput.addEventListener('keydown', function (e) {
        handleKeyNav(e, ovResults, ovInput, closeOverlay);
      });

      // Clear button inside the overlay's search input
      var ovClearBtn = ovSearchInput && ovSearchInput.querySelector('.c-search-input__clear');
      if (ovClearBtn) {
        ovClearBtn.addEventListener('click', function () {
          clearOverlayInput();
          ovInput.focus();
        });
      }
    }

    // Delegated clicks inside the overlay
    ov.addEventListener('click', function (e) {
      if (e.target.closest('[data-action="close-search-overlay"]')) {
        closeOverlay();
        return;
      }

      if (e.target.closest('[data-action="clear-search-overlay"]')) {
        clearOverlayInput();
        if (ovInput) ovInput.focus();
        return;
      }

      var row = e.target.closest('.c-autocomplete__result-row[data-href]');
      if (row) {
        e.preventDefault();
        e.stopPropagation();
        navigateToResult(row, ovInput ? ovInput.value : '');
      }
    });

    // Escape key (document-level, so it also catches when a row has focus)
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' &&
          ov.classList.contains('hdx-v2-search-filter-overlay--open')) {
        closeOverlay();
      }
    });
  }

  function openOverlay(triggerEl, prefill, searchSource) {
    if (!ov) return;
    ovTrigger = triggerEl || null;

    // Update search source for form submission
    if (ovSourceInput && searchSource) {
      ovSourceInput.value = searchSource;
    }

    ov.classList.add('hdx-v2-search-filter-overlay--open');
    document.body.style.overflow = 'hidden';

    if (ovTrigger) ovTrigger.setAttribute('aria-expanded', 'true');

    if (ovInput) {
      ovInput.value = prefill || '';
      setFilledState(ovSearchInput, ovInput.value);
      updateOverlayClearBtn();
      // Small timeout so the overlay is visible before focusing (avoids scroll jump)
      setTimeout(function () { ovInput.focus(); }, 50);
      if (ovInput.value) runOverlaySearch(ovInput.value);
    }
  }

  function closeOverlay() {
    if (!ov) return;
    ov.classList.remove('hdx-v2-search-filter-overlay--open');
    document.body.style.overflow = '';

    if (ovTrigger) {
      ovTrigger.setAttribute('aria-expanded', 'false');
      ovTrigger.focus();
      ovTrigger = null;
    }
    clearOverlayInput();
  }

  function clearOverlayInput() {
    if (ovInput)   ovInput.value = '';
    if (ovResults) ovResults.innerHTML = '';
    setFilledState(ovSearchInput, false);
    updateOverlayClearBtn();
  }

  function runOverlaySearch(value) {
    if (!ovResults) return;
    var trimmed = value.trim();
    if (!trimmed) {
      ovResults.innerHTML = '';
      return;
    }
    var res = performSearch(trimmed);
    renderResults(ovResults, res.results, res.termList);
  }

  function updateOverlayClearBtn() {
    var clearBtn = ov && ov.querySelector('[data-action="clear-search-overlay"]');
    if (!clearBtn) return;
    clearBtn.disabled = !(ovInput && ovInput.value.trim().length > 0);
  }

  // ── Inline autocomplete (XL only) ────────────────────────────────────

  function initInlineAutocomplete(el) {
    var input       = el.querySelector('.c-search-input input');
    var panel       = el.querySelector('.c-autocomplete__panel');
    var results     = el.querySelector('.c-autocomplete__results');
    var clearBtn    = el.querySelector('.c-search-input__clear');
    var searchInput = input && input.closest('.c-search-input');

    if (!input || !panel || !results) return;

    function openPanel() {
      panel.removeAttribute('hidden');
      el.setAttribute('aria-expanded', 'true');
    }

    function closePanel() {
      panel.setAttribute('hidden', '');
      el.setAttribute('aria-expanded', 'false');
      results.querySelectorAll('[aria-selected="true"]').forEach(function (r) {
        r.setAttribute('aria-selected', 'false');
      });
    }

    function runSearch(value) {
      var trimmed = value.trim();
      if (!trimmed) { closePanel(); return; }
      var res = performSearch(trimmed);
      renderResults(results, res.results, res.termList);
      openPanel();
    }

    input.addEventListener('input', function () {
      setFilledState(searchInput, input.value);
      runSearch(input.value);
    });

    input.addEventListener('focus', function () {
      if (input.value.trim()) runSearch(input.value);
    });

    input.addEventListener('keydown', function (e) {
      handleKeyNav(e, results, input, closePanel);
    });

    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        input.value = '';
        setFilledState(searchInput, false);
        closePanel();
        input.focus();
      });
    }

    // Close on click outside
    document.addEventListener('click', function (e) {
      if (!el.contains(e.target)) closePanel();
    });

    // Mousedown guard — prevents blur firing before click registers on result rows
    var pendingMousedown = false;
    panel.addEventListener('mousedown', function () { pendingMousedown = true; });
    document.addEventListener('mouseup', function () { pendingMousedown = false; });
    input.addEventListener('blur', function () {
      if (!pendingMousedown) closePanel();
    });

    results.addEventListener('mousedown', function (e) {
      var row = e.target.closest('.c-autocomplete__result-row[data-href]');
      if (row) {
        e.preventDefault();
        navigateToResult(row, input.value);
      }
    });

    // Set initial filled state if input has a server-provided value
    setFilledState(searchInput, input.value);
  }

  // ── Overlay-redirect mode (MD/SM non-XL) ─────────────────────────────

  function initOverlayRedirect(el) {
    var input       = el.querySelector('.c-search-input input');
    var searchInput = input && input.closest('.c-search-input');
    if (!input) return;

    var searchSource = el.getAttribute('data-search-source') || 'main-nav';

    // Mousedown prevents focus flicker; also handles touch
    searchInput && searchInput.addEventListener('mousedown', function (e) {
      e.preventDefault();  // prevent focus on the underlying input
      openOverlay(input, input.value, searchSource);
    });

    // Keyboard Tab → focus; redirect to overlay
    input.addEventListener('focus', function () {
      if (!ov || !ov.classList.contains('hdx-v2-search-filter-overlay--open')) {
        input.blur();
        openOverlay(input, input.value, searchSource);
      }
    });
  }

  // ── Main init ─────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', function () {
    searchIndex = buildIndex();

    initOverlay();

    var xl = window.matchMedia(BP_XL);

    // SM search icon → open overlay
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-action="open-search-overlay"]');
      if (btn) openOverlay(btn, '', 'main-nav');
    });

    // Init each c-autocomplete
    document.querySelectorAll('[data-hdx-v2-search-autocomplete]').forEach(function (el) {
      if (xl.matches) {
        initInlineAutocomplete(el);
      } else {
        initOverlayRedirect(el);
      }
    });

    // On breakpoint change close any open state
    // (full re-init not needed; behaviors degrade gracefully on resize)
    xl.addEventListener('change', function () {
      closeOverlay();
      document.querySelectorAll('.c-autocomplete__panel').forEach(function (p) {
        p.setAttribute('hidden', '');
      });
      document.querySelectorAll('[data-hdx-v2-search-autocomplete]').forEach(function (el) {
        el.setAttribute('aria-expanded', 'false');
      });
    });
  });

})();
