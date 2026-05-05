(function () {
  'use strict';

  var activePanel = null;

  // ── Offcanvas helpers ────────────────────────────────────────

  function getOffcanvas() {
    return document.getElementById('hdx-offcanvas');
  }

  function getHamburger() {
    return document.querySelector('[data-hdx-panel="offcanvas"]');
  }

  function getBackdrop() {
    return document.querySelector('[data-hdx-close="offcanvas"]');
  }

  function openOffcanvas() {
    var el = getOffcanvas();
    var btn = getHamburger();
    var backdrop = getBackdrop();
    if (!el) return;
    el.classList.add('is-open');
    el.setAttribute('aria-hidden', 'false');
    if (btn) {
      btn.setAttribute('aria-expanded', 'true');
      btn.setAttribute('aria-label', btn.getAttribute('aria-label-close') || 'Close menu');
      btn.classList.add('is-open');
    }
    if (backdrop) backdrop.hidden = false;
    document.body.style.overflow = 'hidden';
  }

  function closeOffcanvas() {
    var el = getOffcanvas();
    var btn = getHamburger();
    var backdrop = getBackdrop();
    if (!el) return;
    el.classList.remove('is-open');
    el.setAttribute('aria-hidden', 'true');
    if (btn) {
      btn.setAttribute('aria-expanded', 'false');
      btn.classList.remove('is-open');
    }
    if (backdrop) backdrop.hidden = true;
    document.body.style.overflow = '';
    // Return to primary level
    var primary = el.querySelector('.hdx-offcanvas__primary');
    var levels = el.querySelectorAll('.hdx-offcanvas__level');
    if (primary) primary.hidden = false;
    levels.forEach(function (lvl) { lvl.hidden = true; });
  }

  function getPanelEl(name) {
    return document.getElementById('hdx-panel-' + name);
  }

  function getTrigger(name) {
    return document.querySelector('[data-hdx-panel="' + name + '"]');
  }

  function closePanel(name) {
    var el = getPanelEl(name);
    var trigger = getTrigger(name);
    if (el) el.hidden = true;
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
    if (activePanel === name) activePanel = null;
  }

  function showPanel(name) {
    var el = getPanelEl(name);
    var trigger = getTrigger(name);
    if (!el) return;
    if (activePanel && activePanel !== name) closePanel(activePanel);
    el.hidden = false;
    if (trigger) trigger.setAttribute('aria-expanded', 'true');
    activePanel = name;
  }

  // Rule 1 & 2: panel toggle, close button, outside click
  document.addEventListener('click', function (e) {
    // Offcanvas close (backdrop or data-hdx-close="offcanvas")
    var closeBtn = e.target.closest('[data-hdx-close]');
    if (closeBtn) {
      var closeName = closeBtn.getAttribute('data-hdx-close');
      if (closeName === 'offcanvas') { closeOffcanvas(); return; }
      closePanel(closeName);
      return;
    }

    // Offcanvas open (hamburger)
    var trigger = e.target.closest('[data-hdx-panel]');
    if (trigger) {
      var panelName = trigger.getAttribute('data-hdx-panel');
      if (panelName === 'offcanvas') {
        var offcanvas = getOffcanvas();
        if (offcanvas && offcanvas.classList.contains('is-open')) {
          closeOffcanvas();
        } else {
          openOffcanvas();
        }
        return;
      }
      var el = getPanelEl(panelName);
      if (!el) return;
      if (!el.hidden) {
        closePanel(panelName);
      } else {
        showPanel(panelName);
      }
      return;
    }

    // Offcanvas second-level: user row
    var levelTrigger = e.target.closest('[data-hdx-offcanvas-level]');
    if (levelTrigger) {
      var levelId = 'hdx-offcanvas-level-' + levelTrigger.getAttribute('data-hdx-offcanvas-level');
      var offcanvasEl = getOffcanvas();
      if (!offcanvasEl) return;
      var primary = offcanvasEl.querySelector('.hdx-offcanvas__primary');
      var levelEl = document.getElementById(levelId);
      if (primary) primary.hidden = true;
      if (levelEl) levelEl.hidden = false;
      return;
    }

    // Offcanvas back button
    var backBtn = e.target.closest('[data-hdx-offcanvas-back]');
    if (backBtn) {
      var offcanvasEl2 = getOffcanvas();
      if (!offcanvasEl2) return;
      var primary2 = offcanvasEl2.querySelector('.hdx-offcanvas__primary');
      var openLevel = offcanvasEl2.querySelector('.hdx-offcanvas__level:not([hidden])');
      if (openLevel) openLevel.hidden = true;
      if (primary2) primary2.hidden = false;
      return;
    }

    // Products inline toggle
    var expandBtn = e.target.closest('.hdx-offcanvas__nav-item--expandable');
    if (expandBtn) {
      var expanded = expandBtn.getAttribute('aria-expanded') === 'true';
      var subnavId = expandBtn.getAttribute('aria-controls');
      var subnav = subnavId ? document.getElementById(subnavId) : null;
      expandBtn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
      if (subnav) subnav.hidden = expanded;
      return;
    }

    if (activePanel) {
      var panelEl = getPanelEl(activePanel);
      var triggerEl = getTrigger(activePanel);
      var isOutside =
        (!panelEl || !panelEl.contains(e.target)) &&
        (!triggerEl || !triggerEl.contains(e.target));
      if (isOutside) closePanel(activePanel);
    }
  });

  // Rule 2: ESC closes panels and offcanvas
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      if (activePanel) closePanel(activePanel);
      var offcanvas = getOffcanvas();
      if (offcanvas && offcanvas.classList.contains('is-open')) closeOffcanvas();
    }
  });

  // Rule 3: user menu section collapse
  document.addEventListener('click', function (e) {
    var toggle = e.target.closest('.hdx-user-menu__section-toggle');
    if (!toggle) return;
    var expanded = toggle.getAttribute('aria-expanded') === 'true';
    var itemsEl = document.getElementById(toggle.getAttribute('aria-controls'));
    toggle.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    if (itemsEl) itemsEl.hidden = expanded;
  });

}());
