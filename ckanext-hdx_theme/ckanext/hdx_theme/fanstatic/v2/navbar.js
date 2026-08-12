(function () {
  'use strict';

  var activePanel     = null;
  var offcanvasTrap   = null;
  var hamburgerOpenLabel = null;
  var LEVEL_TRANSITION_MS = 300;

  // ── Offcanvas helpers ────────────────────────────────────────

  function getOffcanvas() {
    return document.getElementById('hdx-v2-offcanvas');
  }

  function getHamburger() {
    return document.querySelector('[data-hdx-v2-panel="offcanvas"]');
  }

  function getBackdrop() {
    return document.querySelector('[data-hdx-v2-close="offcanvas"]');
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
    // Trap focus inside the offcanvas panel (V-02 / C-04)
    offcanvasTrap = new window.hdxV2.FocusTrap(el, btn);
    offcanvasTrap.activate();
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
      // Restore the "Open menu" label (V-02: return focus + label on close)
      if (hamburgerOpenLabel) btn.setAttribute('aria-label', hamburgerOpenLabel);
      btn.classList.remove('is-open');
    }
    if (backdrop) backdrop.hidden = true;
    document.body.style.overflow = '';
    // Return to primary level
    var primary = el.querySelector('.hdx-v2-offcanvas__primary');
    var levels = el.querySelectorAll('.hdx-v2-offcanvas__level');
    if (primary) primary.hidden = false;
    levels.forEach(function (lvl) {
      lvl.classList.remove('is-open');
      lvl.hidden = true;
    });
    // Release focus trap and return focus to hamburger (V-02)
    if (offcanvasTrap) {
      offcanvasTrap.deactivate();
      offcanvasTrap = null;
    }
  }

  function openOffcanvasLevel(levelEl) {
    if (!levelEl) return;
    levelEl.hidden = false;
    void levelEl.offsetWidth;
    levelEl.classList.add('is-open');
  }

  function closeOffcanvasLevel(levelEl) {
    if (!levelEl) return;
    levelEl.classList.remove('is-open');
    var done = false;
    var onTransitionEnd = function (e) {
      if (e.target === levelEl && e.propertyName === 'visibility') finish();
    };
    var finish = function () {
      if (done) return;
      done = true;
      levelEl.hidden = true;
      levelEl.removeEventListener('transitionend', onTransitionEnd);
    };
    levelEl.addEventListener('transitionend', onTransitionEnd);
    setTimeout(finish, LEVEL_TRANSITION_MS);
  }

  function getPanelEl(name) {
    return document.getElementById('hdx-v2-panel-' + name);
  }

  function getTrigger(name) {
    return document.querySelector('[data-hdx-v2-panel="' + name + '"]');
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

    if (name === 'notifications' && trigger && typeof hdxUtil !== 'undefined' && hdxUtil.analytics) {
      hdxUtil.analytics.sendNotificationInteractionEvent({
        type: 'header icon',
        count: parseInt(trigger.getAttribute('data-notification-count'), 10) || 0
      });
    }
  }

  // Rule 1 & 2: panel toggle, close button, outside click
  document.addEventListener('click', function (e) {
    // Offcanvas close (backdrop or data-hdx-v2-close="offcanvas")
    var closeBtn = e.target.closest('[data-hdx-v2-close]');
    if (closeBtn) {
      var closeName = closeBtn.getAttribute('data-hdx-v2-close');
      if (closeName === 'offcanvas') { closeOffcanvas(); return; }
      closePanel(closeName);
      return;
    }

    // Offcanvas open (hamburger)
    var trigger = e.target.closest('[data-hdx-v2-panel]');
    if (trigger) {
      var panelName = trigger.getAttribute('data-hdx-v2-panel');
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
    var levelTrigger = e.target.closest('[data-hdx-v2-offcanvas-level]');
    if (levelTrigger) {
      var levelId = 'hdx-v2-offcanvas-level-' + levelTrigger.getAttribute('data-hdx-v2-offcanvas-level');
      var offcanvasEl = getOffcanvas();
      if (!offcanvasEl) return;
      var primary = offcanvasEl.querySelector('.hdx-v2-offcanvas__primary');
      var levelEl = document.getElementById(levelId);
      if (primary) primary.hidden = true;
      openOffcanvasLevel(levelEl);
      return;
    }

    // Offcanvas back button
    var backBtn = e.target.closest('[data-hdx-v2-offcanvas-back]');
    if (backBtn) {
      var offcanvasEl2 = getOffcanvas();
      if (!offcanvasEl2) return;
      var primary2 = offcanvasEl2.querySelector('.hdx-v2-offcanvas__primary');
      var openLevel = offcanvasEl2.querySelector('.hdx-v2-offcanvas__level.is-open');
      closeOffcanvasLevel(openLevel);
      if (primary2) primary2.hidden = false;
      return;
    }

    // Products inline toggle
    var expandBtn = e.target.closest('.hdx-v2-offcanvas__nav-item--expandable');
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
    var toggle = e.target.closest('.hdx-v2-user-menu__section-toggle');
    if (!toggle) return;
    var expanded = toggle.getAttribute('aria-expanded') === 'true';
    var itemsEl = document.getElementById(toggle.getAttribute('aria-controls'));
    toggle.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    if (itemsEl) itemsEl.hidden = expanded;
  });

  // Capture the translated "Open menu" label once the DOM is ready so
  // closeOffcanvas() can restore it (V-02 — aria-label must round-trip).
  document.addEventListener('DOMContentLoaded', function () {
    var btn = getHamburger();
    if (btn) hamburgerOpenLabel = btn.getAttribute('aria-label');
  });

}());
