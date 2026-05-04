(function () {
  'use strict';

  var activePanel = null;

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
    var closeBtn = e.target.closest('[data-hdx-close]');
    if (closeBtn) {
      var closeName = closeBtn.getAttribute('data-hdx-close');
      if (closeName !== 'offcanvas') closePanel(closeName);
      return;
    }

    var trigger = e.target.closest('[data-hdx-panel]');
    if (trigger) {
      var panelName = trigger.getAttribute('data-hdx-panel');
      if (panelName === 'offcanvas') return; // task 019
      var el = getPanelEl(panelName);
      if (!el) return;
      if (!el.hidden) {
        closePanel(panelName);
      } else {
        showPanel(panelName);
      }
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

  // Rule 2: ESC
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && activePanel) closePanel(activePanel);
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
