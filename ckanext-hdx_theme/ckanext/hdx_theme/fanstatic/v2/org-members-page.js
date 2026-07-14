// ============================================================
// org-members-page.js — v2 Organization page, Members tab (task 059)
// - Change-role dropdowns → hidden form POST to member_new
// - Pending-approval Approve/Decline → AJAX member_request_process
//   (keeps the v1 analytics contract: sendMemberAddRejectEvent)
// - Group-message drawer: topic preselect, invisible reCAPTCHA,
//   AJAX POST to /membership/contact_members
// - Invite tags-autocomplete on /util/user/hdx_autocomplete (Q10)
// ============================================================
(function () {
  'use strict';

  var EMAIL_RE = /\S+@\S+\.\S+/;

  function csrfHeaders() {
    try {
      return window.hdxUtil && window.hdxUtil.net.getCsrfTokenAsObject();
    } catch (e) {
      return {};
    }
  }

  // ── Change role — one-click role dropdown ──────────────────
  document.addEventListener('click', function (e) {
    var item = e.target.closest && e.target.closest('[data-role-value]');
    if (!item) return;
    if (item.getAttribute('aria-disabled') === 'true') { e.preventDefault(); return; }
    var wrapper = item.closest('[data-change-role-user]');
    var form = document.getElementById('hdx-change-role-form');
    if (!wrapper || !form) return;
    form.querySelector('input[name="username"]').value = wrapper.getAttribute('data-change-role-user');
    form.querySelector('input[name="role"]').value = item.getAttribute('data-role-value');
    form.submit();
  });

  // ── Pending approval — Approve / Decline AJAX ──────────────
  function processRequest(payload, onDone) {
    fetch('/api/action/member_request_process', {
      method: 'POST',
      headers: Object.assign({ 'Content-Type': 'application/json' }, csrfHeaders()),
      body: JSON.stringify(payload)
    })
      .then(function (r) { if (!r.ok) throw new Error('request failed'); return r.json(); })
      .then(onDone)
      .catch(function () { window.alert('Your request failed!'); });
  }

  function resolveRequestUI(requestId, messageText, roleText) {
    var actions = document.querySelector('[data-request-id="' + requestId + '"]');
    var message = document.querySelector('[data-request-message="' + requestId + '"]');
    if (actions) actions.hidden = true;
    if (!message) return;
    if (messageText !== null) message.textContent = messageText;
    var roleSpan = message.querySelector('.hdx-v2-org-members__request-role');
    if (roleText !== null && roleSpan) roleSpan.textContent = roleText;
    message.hidden = false;
  }

  document.addEventListener('click', function (e) {
    var item = e.target.closest && e.target.closest('[data-approve-role]');
    if (!item) return;
    var wrapper = item.closest('[data-approve-request]');
    if (!wrapper) return;
    var requestId = wrapper.getAttribute('data-approve-request');
    var role = item.getAttribute('data-approve-role');
    processRequest({ member: requestId, role: role, approve: true }, function () {
      resolveRequestUI(requestId, null, role);
      if (window.hdxUtil) window.hdxUtil.analytics.sendMemberAddRejectEvent('by request', false);
    });
  });

  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('[data-decline-request]');
    if (!btn) return;
    var requestId = btn.getAttribute('data-decline-request');
    processRequest({ member: requestId, reject: true }, function () {
      resolveRequestUI(requestId, 'Membership request declined!', null);
      if (window.hdxUtil) window.hdxUtil.analytics.sendMemberAddRejectEvent('by request', true);
    });
  });

  // ── Group message drawer ───────────────────────────────────
  var recaptchaWidgetId = null;

  function gmForm() { return document.getElementById('group-message-form'); }
  function gmSubmitBtn() { return document.getElementById('group-message-submit'); }

  function gmValidate() {
    var form = gmForm();
    var btn = gmSubmitBtn();
    if (!form || !btn) return;
    var topic = form.querySelector('[name="topic"]');
    var msg = form.querySelector('[name="msg"]');
    var valid = topic && topic.value && msg && msg.value.trim();
    btn.disabled = !valid;
    btn.classList.toggle('is-disabled', !valid);
  }

  function gmShowError(text) {
    var form = gmForm();
    var alertEl = form && form.querySelector('.c-drawer-form__alert');
    if (!alertEl) return;
    alertEl.textContent = text || 'There was an error sending your message. Please try again.';
    alertEl.hidden = false;
  }

  // Renders the invisible reCAPTCHA into its dedicated container (between the
  // form fields and the buttons). Returns true when the widget is available.
  function gmEnsureRecaptcha() {
    var container = document.getElementById('group-message-recaptcha');
    if (!container) return false;
    if (recaptchaWidgetId !== null) return true;
    if (window.grecaptcha && window.grecaptcha.render) {
      recaptchaWidgetId = window.grecaptcha.render(container, {
        sitekey: container.getAttribute('data-sitekey'),
        size: 'invisible',
        badge: 'inline',
        callback: window.hdxGroupMessageSubmit
      });
      return true;
    }
    return false;
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('#group-message-submit');
    if (!btn || btn.disabled) return;
    if (gmEnsureRecaptcha()) {
      window.grecaptcha.execute(recaptchaWidgetId);
    } else {
      // recaptcha script unavailable — submit anyway, server validates
      window.hdxGroupMessageSubmit('');
    }
  });

  // data-callback target for the invisible reCAPTCHA on the submit button
  window.hdxGroupMessageSubmit = function (token) {
    var form = gmForm();
    if (!form) return;
    var alertEl = form.querySelector('.c-drawer-form__alert');
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
        if (resp && resp.success) {
          var success = document.getElementById('group-message-success');
          if (success) success.hidden = false;
          var msg = form.querySelector('[name="msg"]');
          if (msg) msg.value = '';
          gmValidate();
          if (recaptchaWidgetId !== null) window.grecaptcha.reset(recaptchaWidgetId);
        } else {
          gmShowError(resp && resp.error && resp.error.message);
          if (recaptchaWidgetId !== null) window.grecaptcha.reset(recaptchaWidgetId);
        }
      })
      .catch(function () {
        gmShowError(null);
        if (recaptchaWidgetId !== null) window.grecaptcha.reset(recaptchaWidgetId);
      });
  };

  document.addEventListener('click', function (e) {
    var trigger = e.target.closest && e.target.closest('[data-gm-topic]');
    if (!trigger) return;
    var topicSelect = document.getElementById('group-message-topic');
    var topic = trigger.getAttribute('data-gm-topic');
    if (topicSelect && topicSelect.querySelector('option[value="' + topic + '"]')) {
      topicSelect.value = topic;
    }
    var success = document.getElementById('group-message-success');
    if (success) success.hidden = true;
    if (window.hdxV2Drawer) window.hdxV2Drawer('group-message-drawer').open();
    gmEnsureRecaptcha();
    gmValidate();
  });

  document.addEventListener('DOMContentLoaded', function () {
    var form = gmForm();
    if (form) {
      form.addEventListener('submit', function (e) { e.preventDefault(); });
      form.addEventListener('input', gmValidate);
      form.addEventListener('change', gmValidate);
    }
    initInviteTags();
  });

  // ── Invite tags-autocomplete (Q10) ─────────────────────────
  // Chips input on top of /util/user/hdx_autocomplete: pick existing
  // users from suggestions; free-typed tokens must be emails (v1
  // "only-email-as-tags"); comma/Enter tokenize; the joined values
  // POST through the hidden "emails" field to bulk_member_new.
  function initInviteTags() {
    var root = document.querySelector('[data-invite-tags]');
    if (!root) return;

    var box = root.querySelector('.hdx-v2-invite-tags__box');
    var input = root.querySelector('.hdx-v2-invite-tags__input');
    var hidden = root.querySelector('input[name="emails"]');
    var panel = root.querySelector('.hdx-v2-invite-tags__panel');
    var source = root.getAttribute('data-invite-source') || '/util/user/hdx_autocomplete';
    var form = root.closest('form');

    var tags = [];          // {value, label, existing}
    var suggestions = [];   // current fetch results
    var activeIndex = -1;
    var debounceTimer = null;

    function syncHidden() {
      hidden.value = tags.map(function (t) { return t.value; }).join(',');
    }

    function renderTags() {
      box.querySelectorAll('.hdx-v2-invite-tags__chip').forEach(function (el) { el.remove(); });
      tags.forEach(function (tag, i) {
        var chip = document.createElement('span');
        chip.className = 'hdx-v2-invite-tags__chip' + (tag.existing ? ' hdx-v2-invite-tags__chip--user' : '');
        chip.appendChild(document.createTextNode(tag.label));
        var remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'hdx-v2-invite-tags__chip-remove';
        remove.setAttribute('aria-label', 'Remove ' + tag.label);
        remove.textContent = '×';
        remove.addEventListener('click', function () {
          tags.splice(i, 1);
          renderTags();
          syncHidden();
        });
        chip.appendChild(remove);
        box.insertBefore(chip, input);
      });
      syncHidden();
    }

    function hasTag(value) {
      return tags.some(function (t) { return t.value === value; });
    }

    function addTag(value, label, existing) {
      if (!value || hasTag(value)) return;
      tags.push({ value: value, label: label || value, existing: !!existing });
      renderTags();
    }

    function closePanel() {
      panel.hidden = true;
      panel.textContent = '';
      suggestions = [];
      activeIndex = -1;
    }

    function renderSuggestions(items) {
      panel.textContent = '';
      suggestions = items;
      activeIndex = -1;
      if (!items.length) { panel.hidden = true; return; }
      items.forEach(function (user, i) {
        var row = document.createElement('div');
        row.className = 'c-list-item c-list-item--type-list c-list-item--size-sm';
        row.setAttribute('role', 'option');
        row.textContent = (user.fullname || user.name) + ' (' + user.name + ')';
        row.addEventListener('mousedown', function (e) {
          // mousedown so the input doesn't blur before we handle the pick
          e.preventDefault();
          addTag(user.name, user.fullname || user.name, true);
          input.value = '';
          closePanel();
        });
        row.addEventListener('mouseenter', function () { setActive(i); });
        panel.appendChild(row);
      });
      panel.hidden = false;
    }

    function setActive(index) {
      activeIndex = index;
      panel.querySelectorAll('[role="option"]').forEach(function (el, i) {
        el.classList.toggle('is-active', i === index);
      });
    }

    function fetchSuggestions(term) {
      fetch(source + '?q=' + encodeURIComponent(term))
        .then(function (r) { return r.json(); })
        .then(function (users) {
          if (input.value.trim() !== term) return;   // stale response
          renderSuggestions((users || []).filter(function (u) { return !hasTag(u.name); }));
        })
        .catch(closePanel);
    }

    // Free-typed tokens are accepted only when they look like an email
    // (v1 only-email-as-tags). Returns true when consumed.
    function tokenizeInput() {
      var raw = input.value.trim().replace(/,$/, '').trim();
      if (!raw) return true;
      var consumedAll = true;
      raw.split(',').forEach(function (part) {
        var token = part.trim();
        if (!token) return;
        if (EMAIL_RE.test(token)) { addTag(token, token, false); }
        else { consumedAll = false; }
      });
      if (consumedAll) input.value = '';
      return consumedAll;
    }

    box.addEventListener('click', function () { input.focus(); });

    input.addEventListener('input', function () {
      var term = input.value.trim();
      if (debounceTimer) clearTimeout(debounceTimer);
      if (!term || term.indexOf(',') !== -1) {
        if (term.indexOf(',') !== -1) tokenizeInput();   // pasted comma list
        closePanel();
        return;
      }
      debounceTimer = setTimeout(function () { fetchSuggestions(term); }, 300);
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' && !panel.hidden) {
        e.preventDefault();
        setActive(activeIndex < suggestions.length - 1 ? activeIndex + 1 : 0);
      } else if (e.key === 'ArrowUp' && !panel.hidden) {
        e.preventDefault();
        setActive(activeIndex > 0 ? activeIndex - 1 : suggestions.length - 1);
      } else if (e.key === 'Enter' || e.key === ',') {
        e.preventDefault();
        if (!panel.hidden && activeIndex >= 0 && suggestions[activeIndex]) {
          var user = suggestions[activeIndex];
          addTag(user.name, user.fullname || user.name, true);
          input.value = '';
        } else {
          tokenizeInput();
        }
        closePanel();
      } else if (e.key === 'Escape') {
        closePanel();
      } else if (e.key === 'Backspace' && !input.value && tags.length) {
        tags.pop();
        renderTags();
      }
    });

    document.addEventListener('click', function (e) {
      if (!root.contains(e.target)) closePanel();
    });

    if (form) {
      form.addEventListener('submit', function () {
        tokenizeInput();   // pick up a leftover typed email
        syncHidden();
      });
    }
  }
})();
