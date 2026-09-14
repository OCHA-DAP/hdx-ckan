(function () {
  'use strict';

  // Resets the filter-search input inside a closed panel.
  function resetSearch(panel) {
    var si = panel && panel.querySelector('[data-filter-search] input');
    if (si && si.value) { si.value = ''; si.dispatchEvent(new Event('input')); }
  }

  // Close a single dropdown. Pass returnFocus=true when triggered by keyboard.
  function closeDropdown(dd, returnFocus) {
    if (!dd) return;
    var panel   = dd.querySelector('.c-dropdown__panel');
    var trigger = dd.querySelector('.c-dropdown__trigger');
    dd.classList.remove('is-open');
    if (panel) { panel.hidden = true; resetSearch(panel); }
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
    if (returnFocus && trigger) trigger.focus();
  }

  // Closes all open dropdowns except `except` (pass null to close all).
  function closeAll(except) {
    document.querySelectorAll('.c-dropdown.is-open').forEach(function (dd) {
      if (dd === except) return;
      closeDropdown(dd, false);
    });
  }

  // Open a dropdown. Pass moveFocus=true when triggered by keyboard.
  function openDropdown(dd, moveFocus) {
    if (!dd) return;
    var panel   = dd.querySelector('.c-dropdown__panel');
    var trigger = dd.querySelector('.c-dropdown__trigger');
    closeAll(dd);
    dd.classList.add('is-open');
    if (panel) panel.hidden = false;
    if (trigger) trigger.setAttribute('aria-expanded', 'true');
    // For navigate panels (role="menu"), always move focus to first menuitem.
    // For checklist panels, only move focus on keyboard open.
    if (panel && moveFocus) {
      var isMenu = panel.getAttribute('role') === 'menu';
      var target = isMenu
        ? panel.querySelector('[role="menuitem"]')
        : window.hdxV2.getFocusable(panel)[0];
      if (target) {
        requestAnimationFrame(function () { target.focus(); });
      }
    }
  }

  document.addEventListener('DOMContentLoaded', function () {

    // ── Toggle open/close on trigger click ───────────────────
    document.addEventListener('click', function (e) {
      var trigger = e.target.closest && e.target.closest('.c-dropdown__trigger');
      if (!trigger) return;
      var dd     = trigger.closest('.c-dropdown');
      var isOpen = dd && dd.classList.contains('is-open');
      if (!dd) return;
      if (isOpen) { closeDropdown(dd, false); } else { openDropdown(dd, false); }
    });

    // ── Enter / Space on trigger — keyboard activation (V-04) ─
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      var trigger = e.target.closest && e.target.closest('.c-dropdown__trigger');
      if (!trigger) return;
      e.preventDefault();
      var dd     = trigger.closest('.c-dropdown');
      var isOpen = dd && dd.classList.contains('is-open');
      if (!dd) return;
      if (isOpen) { closeDropdown(dd, true); } else { openDropdown(dd, true); }
    });

    // ── Escape — close open dropdown and return focus (V-04, V-06) ──
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      var dd = document.querySelector('.c-dropdown.is-open');
      if (dd) closeDropdown(dd, true);
    });

    // ── Arrow keys — navigate menu items (V-04) ──────────────
    document.addEventListener('keydown', function (e) {
      var key = e.key;
      if (key !== 'ArrowDown' && key !== 'ArrowUp' && key !== 'Home' && key !== 'End') return;

      // Find the open navigate panel (role="menu") that contains focus,
      // or that belongs to the focused trigger.
      var panel = null;
      var inPanel = e.target.closest && e.target.closest('.c-dropdown__panel[role="menu"]');
      if (inPanel) {
        panel = inPanel;
      } else {
        var tr = e.target.closest && e.target.closest('.c-dropdown__trigger');
        if (tr) {
          var dd2 = tr.closest('.c-dropdown');
          var p2  = dd2 && dd2.querySelector('.c-dropdown__panel[role="menu"]');
          if (p2 && !p2.hidden) panel = p2;
        }
      }
      if (!panel) return;
      e.preventDefault();

      var items   = Array.from(panel.querySelectorAll('[role="menuitem"]'));
      if (!items.length) return;
      var current = items.indexOf(document.activeElement);

      if      (key === 'ArrowDown') current = current < items.length - 1 ? current + 1 : 0;
      else if (key === 'ArrowUp')   current = current > 0 ? current - 1 : items.length - 1;
      else if (key === 'Home')      current = 0;
      else if (key === 'End')       current = items.length - 1;

      items[current].focus();
    });

    // ── Enter / Space on menuitem → activate (V-04) ──────────
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      var item = e.target.closest && e.target.closest('[role="menuitem"]');
      if (!item) return;
      e.preventDefault();
      item.click(); // triggers the existing data-nav-value click handler below
    });

    // ── Navigate item click → URL navigation ─────────────────
    // Items inside [data-nav-key] are handled by search.js (setNavParam).
    // All other navigate items navigate directly to the URL in data-nav-value.
    document.addEventListener('click', function (e) {
      var item = e.target.closest && e.target.closest('[data-nav-value]');
      if (!item) return;
      if (item.closest('[data-nav-key]')) return;
      var url = item.getAttribute('data-nav-value');
      if (url) window.location.href = url;
    });

    // ── Outside click → close all open dropdowns ─────────────
    document.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('.c-dropdown')) return;
      closeAll(null);
    });

  });
})();
