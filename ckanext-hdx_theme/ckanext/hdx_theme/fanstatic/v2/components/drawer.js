(function () {
  'use strict';

  // Exported to window so notification platform scripts can call it directly.
  // Depends on window.hdxV2.getFocusable (v2/utils.js).
  window.hdxV2Drawer = function hdxV2Drawer(drawerId) {
    var $drawer    = $('#' + drawerId);
    var $container = $drawer.find('.c-drawer__container');
    var lastFocus;

    function getFocusable() {
      return window.hdxV2.getFocusable($container.get(0));
    }

    function open() {
      if ($drawer.hasClass('is-open')) return;
      lastFocus = document.activeElement;
      $drawer.addClass('is-open').attr('aria-hidden', 'false');
      $('body').addClass('is-drawer-open');
      var focusable = getFocusable();
      if (focusable.length) {
        focusable[0].focus();
      } else {
        $container.focus();
      }
    }

    function close() {
      if (!$drawer.hasClass('is-open')) return;
      $drawer.removeClass('is-open').attr('aria-hidden', 'true');
      $('body').removeClass('is-drawer-open');
      $drawer.get(0).dispatchEvent(new CustomEvent('drawer:close'));
      if (lastFocus) lastFocus.focus();
    }

    // ESC key + Tab focus trap
    $(document).off('keydown.drawer-' + drawerId);
    $(document).on('keydown.drawer-' + drawerId, function (e) {
      if (!$drawer.hasClass('is-open')) return;

      if (e.key === 'Escape') {
        close();
        return;
      }

      if (e.key === 'Tab') {
        var focusable = getFocusable();
        if (!focusable.length) return;
        var first = focusable[0];
        var last  = focusable[focusable.length - 1];
        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    });

    // Any element with [data-drawer-close] (overlay, header X, Cancel buttons, etc.)
    $drawer.off('click', '[data-drawer-close]');
    $drawer.on('click', '[data-drawer-close]', function () {
      close();
    });

    return { open: open, close: close };
  };

})();
