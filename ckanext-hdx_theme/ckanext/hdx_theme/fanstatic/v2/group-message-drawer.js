// ============================================================
// group-message-drawer.js — shared "Group message" c-drawer form
// Renders from templates/v2/group-message-drawer.html,
// used on the dataset/org page header (page-header.html — triggers
// #contact-members, #group-message-org-action) and the org Members
// tab (organization/members.html — per-role [data-gm-topic] triggers,
// drawer id 'group-message-drawer'). Any number of instances can
// coexist on the same page; each is scoped by its own recaptcha
// widget id.
// ============================================================
(function () {
  'use strict';

  function csrfHeaders() {
    try {
      return window.hdxUtil && window.hdxUtil.net.getCsrfTokenAsObject();
    } catch (e) {
      return {};
    }
  }

  var recaptchaWidgets = {};

  function formIn(drawer) {
    return drawer && drawer.querySelector('[data-group-message-form]');
  }

  function validate(drawer) {
    var form = formIn(drawer);
    if (!form) return;
    var submitBtn = form.querySelector('[data-group-message-submit]');
    var topic = form.querySelector('[name="topic"]');
    var msg = form.querySelector('[name="msg"]');
    var valid = topic && topic.value && msg && msg.value.trim();
    if (submitBtn) {
      submitBtn.disabled = !valid;
      submitBtn.classList.toggle('is-disabled', !valid);
    }
  }

  function showError(drawer, text) {
    var form = formIn(drawer);
    var alertEl = form && form.querySelector('.c-form-alert');
    if (!alertEl) return;
    alertEl.textContent = text || 'There was an error sending your message. Please try again.';
    alertEl.hidden = false;
  }

  // Renders the invisible reCAPTCHA into its dedicated container (between
  // the form fields and the buttons). Returns true when available.
  function ensureRecaptcha(drawer) {
    var form = formIn(drawer);
    var container = form && form.querySelector('[data-group-message-recaptcha]');
    if (!container) return false;
    if (recaptchaWidgets[drawer.id] !== undefined) return true;
    if (window.grecaptcha && window.grecaptcha.render) {
      recaptchaWidgets[drawer.id] = window.grecaptcha.render(container, {
        sitekey: container.getAttribute('data-sitekey'),
        size: 'invisible',
        badge: 'inline',
        callback: function (token) { submitForm(drawer, token); }
      });
      return true;
    }
    return false;
  }

  function submitForm(drawer, token) {
    var form = formIn(drawer);
    if (!form) return;
    var alertEl = form.querySelector('.c-form-alert');
    if (alertEl) alertEl.hidden = true;
    var topic = form.querySelector('[name="topic"]');
    if (window.hdxUtil) {
      // v1 parity: fired on submit (google-analytics.js sendMessagingEvent)
      window.hdxUtil.analytics.sendMessagingEvent('dataset', 'group message', null, topic && topic.value, true);
    }
    var data = new URLSearchParams(new FormData(form));
    if (token) data.set('g-recaptcha-response', token);
    fetch('/membership/contact_members', {
      method: 'POST',
      headers: csrfHeaders(),
      body: data
    })
      .then(function (r) { return r.json(); })
      .then(function (resp) {
        var widgetId = recaptchaWidgets[drawer.id];
        if (resp && resp.success) {
          var success = form.querySelector('[data-group-message-success]');
          if (success) success.hidden = false;
          var msg = form.querySelector('[name="msg"]');
          if (msg) msg.value = '';
          validate(drawer);
          if (widgetId !== undefined) window.grecaptcha.reset(widgetId);
        } else {
          showError(drawer, resp && resp.error && resp.error.message);
          if (widgetId !== undefined) window.grecaptcha.reset(widgetId);
        }
      })
      .catch(function () {
        showError(drawer, null);
        var widgetId = recaptchaWidgets[drawer.id];
        if (widgetId !== undefined) window.grecaptcha.reset(widgetId);
      });
  }

  // Submit button click → recaptcha execute (falls back to a direct
  // submit if the recaptcha script failed to load — server validates).
  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('[data-group-message-submit]');
    if (!btn || btn.disabled) return;
    var drawer = btn.closest('.c-drawer');
    if (!drawer) return;
    if (ensureRecaptcha(drawer)) {
      window.grecaptcha.execute(recaptchaWidgets[drawer.id]);
    } else {
      submitForm(drawer, '');
    }
  });

  // Generic open triggers — page-header buttons (dataset org-card +
  // org header_actions), no topic preselect.
  document.addEventListener('click', function (e) {
    var trigger = e.target.closest && e.target.closest('#contact-members, #group-message-org-action');
    if (!trigger) return;
    if (window.hdxV2Drawer) window.hdxV2Drawer('gm-header-drawer').open();
  });

  // Per-role preselect trigger (org Members tab) — pre-fills the topic
  // select on the page's 'group-message-drawer' instance.
  document.addEventListener('click', function (e) {
    var trigger = e.target.closest && e.target.closest('[data-gm-topic]');
    if (!trigger) return;
    var drawer = document.getElementById('group-message-drawer');
    var form = formIn(drawer);
    if (!form) return;
    var topicSelect = form.querySelector('[name="topic"]');
    var topic = trigger.getAttribute('data-gm-topic');
    if (topicSelect && topicSelect.querySelector('option[value="' + topic + '"]')) {
      topicSelect.value = topic;
    }
    var success = form.querySelector('[data-group-message-success]');
    if (success) success.hidden = true;
    if (window.hdxV2Drawer) window.hdxV2Drawer('group-message-drawer').open();
    ensureRecaptcha(drawer);
    validate(drawer);
  });

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-group-message-form]').forEach(function (form) {
      var drawer = form.closest('.c-drawer');
      form.addEventListener('submit', function (e) { e.preventDefault(); });
      form.addEventListener('input', function () { validate(drawer); });
      form.addEventListener('change', function () { validate(drawer); });
    });
  });

})();
