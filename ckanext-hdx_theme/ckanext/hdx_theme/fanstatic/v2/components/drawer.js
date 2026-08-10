(function () {
  'use strict';

  // Exported to window so notification platform scripts can call it directly.
  // Depends on window.hdxV2.getFocusable / window.hdxV2.FocusTrap (v2/utils.js).
  //
  // Called fresh on every trigger click (inline onclick="hdxV2Drawer(id).open()"),
  // so every listener bound here is stored on the drawer element and removed
  // before being re-added — repeat calls never stack duplicate listeners.
  window.hdxV2Drawer = function hdxV2Drawer(drawerId) {
    var drawer = document.getElementById(drawerId);
    if (!drawer) return { open: function () {}, close: function () {} };

    var container = drawer.querySelector('.c-drawer__container');
    var trap      = new window.hdxV2.FocusTrap(container, null);

    function open() {
      if (drawer.classList.contains('is-open')) return;
      trap.triggerElement = document.activeElement;
      drawer.classList.add('is-open');
      drawer.setAttribute('aria-hidden', 'false');
      document.body.classList.add('is-drawer-open');

      trap.activate();
      if (!container.contains(document.activeElement)) container.focus();

      if (drawer._hdxV2Esc) document.removeEventListener('keydown', drawer._hdxV2Esc);
      drawer._hdxV2Esc = function (e) {
        if (e.key === 'Escape') close();
      };
      document.addEventListener('keydown', drawer._hdxV2Esc);
    }

    function close() {
      if (!drawer.classList.contains('is-open')) return;
      drawer.classList.remove('is-open');
      drawer.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('is-drawer-open');
      drawer.dispatchEvent(new CustomEvent('drawer:close'));
      trap.deactivate();

      if (drawer._hdxV2Esc) {
        document.removeEventListener('keydown', drawer._hdxV2Esc);
        drawer._hdxV2Esc = null;
      }
    }

    // Any element with [data-drawer-close] (overlay, header X, Cancel buttons, etc.)
    if (drawer._hdxV2CloseClick) drawer.removeEventListener('click', drawer._hdxV2CloseClick);
    drawer._hdxV2CloseClick = function (e) {
      if (e.target.closest('[data-drawer-close]')) close();
    };
    drawer.addEventListener('click', drawer._hdxV2CloseClick);

    return { open: open, close: close };
  };

})();
