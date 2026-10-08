// ============================================================
// hdx-connect.js — v2 HDX Connect Requests dashboard (task 074)
// - Reply / Decline → fill + open the drawers of
//   templates/v2/hdx-connect-drawers.html, POST FormData, reload
// - Yes / No ("Did you share the data?") → POST, reload
// ============================================================
(function () {
  'use strict';

  var DRAWER_IDS = {
    reply: 'hdx-connect-reply-drawer',
    decline: 'hdx-connect-decline-drawer'
  };
  var SEND_ERROR = 'There was an error sending your message. Please try again.';
  var SHARED_ERROR = 'There was an error updating the request. Please try again.';

  function post(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: window.hdxUtil.net.getCsrfTokenAsObject(),
      body: body
    }).then(function (r) { return r.json(); });
  }

  function errorText(resp, fallback) {
    var error = resp && resp.error;
    var messages = [];
    if (error) {
      var fields = error.fields || {};
      Object.keys(fields).forEach(function (key) {
        messages = messages.concat(fields[key]);
      });
      if (error.message_content) messages = messages.concat(error.message_content);
    }
    return messages.length ? messages.join(' ') : fallback;
  }

  function validate(form) {
    var fields = form.querySelectorAll('textarea, input:not([type="hidden"])');
    var valid = Array.prototype.every.call(fields, function (field) {
      return field.value.trim() !== '';
    });
    window.hdxV2.setDisabled(form.querySelector('[data-hdx-connect-submit]'), !valid);
  }

  function openDrawer(trigger) {
    var drawerId = DRAWER_IDS[trigger.getAttribute('data-hdx-connect-action')];
    var drawer = document.getElementById(drawerId);
    var form = drawer && drawer.querySelector('[data-hdx-connect-form]');
    if (!form) return;
    var data = JSON.parse(trigger.getAttribute('data-hdx-connect-request'));
    Object.keys(data).forEach(function (key) {
      var input = form.querySelector('input[type="hidden"][name="' + key + '"]');
      if (input) input.value = data[key];
    });
    form.querySelectorAll('[data-hdx-connect-summary]').forEach(function (el) {
      el.textContent = data[el.getAttribute('data-hdx-connect-summary')] || '';
    });
    validate(form);
    window.hdxV2Drawer(drawerId).open();
  }

  function submitForm(form) {
    var alertEl = form.querySelector('[data-hdx-connect-error]');
    alertEl.hidden = true;
    window.hdxV2.setDisabled(form.querySelector('[data-hdx-connect-submit]'), true);
    post(form.getAttribute('action'), new FormData(form))
      .then(function (resp) {
        if (resp && resp.success) {
          window.location.reload();
          return;
        }
        window.hdxV2.showAlert(alertEl, errorText(resp, SEND_ERROR));
        validate(form);
      })
      .catch(function () {
        window.hdxV2.showAlert(alertEl, SEND_ERROR);
        validate(form);
      });
  }

  function markShared(button) {
    var item = button.closest('.c-request-item');
    var buttons = item.querySelectorAll('[data-hdx-connect-shared]');
    var url = button.closest('[data-hdx-connect-shared-url]').getAttribute('data-hdx-connect-shared-url');
    var alertEl = document.querySelector('[data-hdx-connect-shared-error]');
    var data = JSON.parse(button.getAttribute('data-hdx-connect-request'));
    var body = new URLSearchParams({
      id: data.id,
      package_id: data.package_id,
      state: 'archive',
      data_shared: button.getAttribute('data-hdx-connect-shared')
    });

    function fail(text) {
      item.after(alertEl);
      window.hdxV2.showAlert(alertEl, text);
      buttons.forEach(function (b) { window.hdxV2.setDisabled(b, false); });
    }

    alertEl.hidden = true;
    buttons.forEach(function (b) { window.hdxV2.setDisabled(b, true); });
    post(url, body)
      .then(function (resp) {
        if (resp && resp.success) {
          window.location.reload();
          return;
        }
        fail(errorText(resp, SHARED_ERROR));
      })
      .catch(function () { fail(SHARED_ERROR); });
  }

  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var trigger = e.target.closest('[data-hdx-connect-action]');
    if (trigger) {
      openDrawer(trigger);
      return;
    }
    var submit = e.target.closest('[data-hdx-connect-submit]');
    if (submit && !submit.disabled) {
      submitForm(submit.closest('[data-hdx-connect-form]'));
      return;
    }
    var shared = e.target.closest('[data-hdx-connect-shared]');
    if (shared && !shared.disabled) markShared(shared);
  });

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-hdx-connect-form]').forEach(function (form) {
      form.addEventListener('submit', function (e) { e.preventDefault(); });
      form.addEventListener('input', function () { validate(form); });
      form.closest('.c-drawer').addEventListener('drawer:close', function () {
        form.reset();
        form.querySelector('[data-hdx-connect-error]').hidden = true;
        validate(form);
      });
    });
  });

})();
