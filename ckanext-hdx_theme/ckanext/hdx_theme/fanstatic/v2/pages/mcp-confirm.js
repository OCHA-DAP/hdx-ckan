/*
 * MCP connect confirmation page (user/mcp_confirm.html).
 * Submits the form only once: Scalekit may reject a second POST for the same login request,
 * and the browser would show that error.
 */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('mcp-confirm-form');
    if (!form) return;

    var submitButton = document.getElementById('mcp-confirm-submit');
    var submitted = false;

    form.addEventListener('submit', function (e) {
      if (submitted) {
        e.preventDefault();
        return;
      }
      submitted = true;
      submitButton.disabled = true;
    });

    // Back after a failed sign-in can restore this page from the browser's back/forward cache,
    // button still disabled. Re-enable it so the user can try again.
    window.addEventListener('pageshow', function (e) {
      if (e.persisted) {
        submitted = false;
        submitButton.disabled = false;
      }
    });
  });
})();
