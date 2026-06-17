(function () {
  'use strict';

  // ── Map init ─────────────────────────────────────────────────────────────
  var countDatasets = prepareCount();
  prepareMap(countDatasets, false);

  // ── Smooth scroll (delegates to shared anchor-links utility) ─────────────
  document.addEventListener('click', function (e) {
    var anchor = e.target.closest('a[href^="#"]');
    if (!anchor) return;
    var href = anchor.getAttribute('href');
    if (!href || href === '#') return;
    var target = document.getElementById(href.slice(1));
    if (!target) return;
    e.preventDefault();
    if (window.hdxSmoothScrollTo) {
      window.hdxSmoothScrollTo(target);
    } else {
      target.scrollIntoView({ block: 'start' });
    }
  });

  // ── HRP filter toggle ────────────────────────────────────────────────────
  var hrpToggle = document.getElementById('hrp-filter');
  if (hrpToggle) {
    hrpToggle.addEventListener('change', function () {
      applyFilters();
    });
  }

  // ── Sort buttons ─────────────────────────────────────────────────────────
  var sortBtns = document.querySelectorAll('[data-sort]');
  var currentSort = 'az';

  sortBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      currentSort = btn.dataset.sort;
      sortBtns.forEach(function (b) { b.classList.remove('is-active'); });
      btn.classList.add('is-active');
      applyFilters();
    });
  });

  // ── Combined filter + sort ────────────────────────────────────────────────
  function applyFilters() {
    var showHrpOnly = hrpToggle && hrpToggle.checked;
    var sections = document.querySelector('.hdx-v2-all-locations-sections');
    if (!sections) return;

    var sectionEls = Array.from(sections.querySelectorAll('.hdx-v2-all-locations-section'));

    // Sort sections by letter
    sectionEls.sort(function (a, b) {
      var la = a.dataset.letter || '';
      var lb = b.dataset.letter || '';
      return currentSort === 'za' ? lb.localeCompare(la) : la.localeCompare(lb);
    });

    sectionEls.forEach(function (section) {
      var grid = section.querySelector('.hdx-v2-all-locations-grid');
      if (grid) {
        var items = Array.from(grid.querySelectorAll('.c-selection-item'));

        // Sort items within section
        items.sort(function (a, b) {
          var ka = (a.dataset.sortKey || '').toLowerCase();
          var kb = (b.dataset.sortKey || '').toLowerCase();
          return currentSort === 'za' ? kb.localeCompare(ka) : ka.localeCompare(kb);
        });

        // Apply HRP filter visibility + reorder
        items.forEach(function (item) {
          var isHrp = item.dataset.isHrp === 'true';
          item.style.display = showHrpOnly && !isHrp ? 'none' : '';
          grid.appendChild(item);
        });
      }

      // Hide section if no visible items
      var anyVisible = grid && Array.from(
        grid.querySelectorAll('.c-selection-item')
      ).some(function (el) { return el.style.display !== 'none'; });

      section.style.display = anyVisible ? '' : 'none';
      sections.appendChild(section);
    });

    updateAnchorStates();
  }

  // ── Sync anchor disabled state with filtered sections ────────────────────
  function updateAnchorStates() {
    document.querySelectorAll('.hdx-v2-all-locations-sidebar .c-letter-anchor').forEach(function (anchor) {
      var href = anchor.getAttribute('href') || '';
      var id = href.replace('#', '');
      var section = id ? document.getElementById(id) : null;
      var visible = section && section.style.display !== 'none';

      anchor.classList.toggle('is-disabled', !visible);

      if (!visible) {
        anchor.classList.remove('is-active');
        anchor.setAttribute('aria-disabled', 'true');
        anchor.setAttribute('tabindex', '-1');
      } else {
        anchor.removeAttribute('aria-disabled');
        anchor.removeAttribute('tabindex');
      }
    });
  }

  // ── IntersectionObserver: active anchor on scroll (XL sidebar) ──────────
  var sidebar = document.querySelector('.hdx-v2-all-locations-sidebar');
  if (sidebar && 'IntersectionObserver' in window) {
    var sectionEls = document.querySelectorAll('.hdx-v2-all-locations-section');
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var letter = entry.target.dataset.letter;
        if (!letter) return;
        sidebar.querySelectorAll('.c-letter-anchor').forEach(function (a) {
          var isMatch = (a.getAttribute('href') || '') === '#loc-letter-' + letter;
          a.classList.toggle('is-active', isMatch);
        });
      });
    }, { rootMargin: '-20% 0px -70% 0px', threshold: 0 });

    sectionEls.forEach(function (el) { observer.observe(el); });
  }

})();
