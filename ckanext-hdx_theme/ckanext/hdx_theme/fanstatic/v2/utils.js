(function () {
  'use strict';

  // Shared v2 utilities — loaded first in the v2-components-scripts bundle
  // so all component JS can reference window.hdxV2.*.

  window.hdxV2 = window.hdxV2 || {};

  var rootStyle = null;

  // Returns the raw (trimmed) computed value of a CSS custom property.
  window.hdxV2.token = function token(name) {
    if (!rootStyle) rootStyle = getComputedStyle(document.documentElement);
    return rootStyle.getPropertyValue(name).trim();
  };

  // Converts a design token to a plain px number. Rem-based tokens are
  // scaled by the actual computed root font-size (not a hardcoded 16),
  // so it stays correct under browser text-size/zoom settings.
  window.hdxV2.tokenPx = function tokenPx(name) {
    var raw = window.hdxV2.token(name);
    var value = parseFloat(raw);
    if (isNaN(value)) return 0;
    if (raw.indexOf('rem') !== -1) {
      var rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
      return value * rootFontSize;
    }
    return value;
  };

  // Selector for all natively focusable elements.
  // For focus-trap implementations.
  var FOCUSABLE = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    'iframe:not([tabindex="-1"])',
    '[tabindex]:not([tabindex="-1"])'
  ].join(', ');

  // Returns an array of visible focusable elements within `container` (DOM node).
  window.hdxV2.getFocusable = function getFocusable(container) {
    return Array.from(container.querySelectorAll(FOCUSABLE)).filter(function (el) {
      return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    });
  };

  // Keeps a same-origin iframe's height matched to its content, for content
  // that loads/grows asynchronously (e.g. an async fetch inside the iframe).
  // Polls indefinitely on `load` rather than stopping after one recheck, so
  // late height growth is still caught. options: minHeight, padding,
  // interval (ms), onError(iframe) — all optional.
  window.hdxV2.initRecalibratingIframe = function initRecalibratingIframe(iframe, options) {
    options = options || {};
    var minHeight = options.minHeight || 400;
    var padding = options.padding != null ? options.padding : 30;
    var interval = options.interval || 200;
    var onError = options.onError;
    var intervalId;

    function getSameOriginBody() {
      try {
        return iframe.contentWindow.document.body || null;
      } catch (e) {
        return null;
      }
    }

    function recalibrate() {
      var body = getSameOriginBody();
      if (!body) return;
      var height = Math.max(body.scrollHeight, minHeight);
      iframe.style.height = (height + padding) + 'px';
    }

    function onLoad() {
      recalibrate();
      clearInterval(intervalId);
      if (getSameOriginBody()) {
        intervalId = setInterval(recalibrate, interval);
      }
    }

    iframe.addEventListener('load', onLoad);
    if (onError) {
      iframe.addEventListener('error', function () { onError(iframe); });
    }

    // Same-origin content that already finished loading before this ran
    // (fast/cached iframe) would otherwise miss the 'load' event above.
    if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {
      onLoad();
    }

    // Firefox caches iframes — force it to fetch fresh content.
    if (/#$/.test(iframe.src)) {
      iframe.src = iframe.src.slice(0, -1);
    } else {
      iframe.src = iframe.src + '#';
    }
  };

  // Active traps, most recent last. Only the most recent one acts, so
  // stacked traps never fight over focus.
  var activeTraps = [];

  // Traps Tab/Shift+Tab focus inside `element`, and returns focus to
  // `triggerElement` on deactivate. Promoted here once a second consumer needed it (task 070 A6).
  window.hdxV2.FocusTrap = function FocusTrap(element, triggerElement) {
    this.element        = element;
    this.triggerElement = triggerElement;
    this._handler       = null;
    this._focusHandler  = null;
  };

  window.hdxV2.FocusTrap.prototype.activate = function () {
    var self = this;
    var el   = this.element;
    this._release();
    activeTraps.push(this);

    var list = window.hdxV2.getFocusable(el);
    if (list.length) list[0].focus();

    this._handler = function (e) {
      if (e.key !== 'Tab' || activeTraps[activeTraps.length - 1] !== self) return;
      var current = window.hdxV2.getFocusable(el);
      if (!current.length) { e.preventDefault(); return; }
      var first = current[0];
      var last  = current[current.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    };
    document.addEventListener('keydown', this._handler);

    // Tab keydowns inside a cross-origin iframe never reach this document,
    // so the handler above can't stop focus leaving through one. Pull it
    // back if it lands outside the trap anyway.
    this._focusHandler = function (e) {
      if (activeTraps[activeTraps.length - 1] !== self || el.contains(e.target) || e.target.tagName === 'IFRAME') return;
      var current = window.hdxV2.getFocusable(el);
      (current[0] || el).focus();
    };
    document.addEventListener('focusin', this._focusHandler);
  };

  window.hdxV2.FocusTrap.prototype._release = function () {
    var index = activeTraps.indexOf(this);
    if (index !== -1) activeTraps.splice(index, 1);
    if (this._handler) {
      document.removeEventListener('keydown', this._handler);
      this._handler = null;
    }
    if (this._focusHandler) {
      document.removeEventListener('focusin', this._focusHandler);
      this._focusHandler = null;
    }
  };

  window.hdxV2.FocusTrap.prototype.deactivate = function () {
    this._release();
    if (this.triggerElement) this.triggerElement.focus();
  };

  // Currently a no-op pending task 069's follow-up — uncomment the
  // matchMedia check to re-enable prefers-reduced-motion support
  // everywhere this helper is called.
  window.hdxV2.prefersReducedMotion = function prefersReducedMotion() {
    // return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    return false;
  };

  // Sets an element's disabled state as button.html renders it: is-disabled +
  // aria-disabled, plus [disabled] on form controls or tabindex="-1" on links.
  window.hdxV2.setDisabled = function setDisabled(el, disabled) {
    el.classList.toggle('is-disabled', disabled);
    if (disabled) {
      el.setAttribute('aria-disabled', 'true');
    } else {
      el.removeAttribute('aria-disabled');
    }
    if ('disabled' in el) {
      el.disabled = disabled;
    } else if (disabled) {
      el.setAttribute('tabindex', '-1');
    } else {
      el.removeAttribute('tabindex');
    }
  };

  // Shows a hidden c-alert (templates/v2/components/alert.html) with `text`.
  // The optional `variant` (success | warning | info | error) swaps the
  // c-alert--* class and the role as alert.html sets them.
  window.hdxV2.showAlert = function showAlert(alertEl, text, variant) {
    if (variant) {
      ['success', 'warning', 'info', 'error'].forEach(function (v) {
        alertEl.classList.toggle('c-alert--' + v, v === variant);
      });
      alertEl.setAttribute('role', variant === 'success' || variant === 'info' ? 'status' : 'alert');
    }
    alertEl.querySelector('.c-alert__message').textContent = text;
    alertEl.hidden = false;
  };

  var FIELD_BLOCKS = ['c-search-input', 'c-checkbox', 'c-dropdown', 'c-image-upload'];

  function linkError(controls, errorEl, on) {
    controls.forEach(function (control) {
      var ids = (control.getAttribute('aria-describedby') || '').split(' ').filter(Boolean);
      if (errorEl) {
        ids = ids.filter(function (id) { return id !== errorEl.id; });
        if (on && errorEl.textContent) ids.push(errorEl.id);
      }
      if (ids.length) {
        control.setAttribute('aria-describedby', ids.join(' '));
      } else {
        control.removeAttribute('aria-describedby');
      }
      if (on) {
        control.setAttribute('aria-invalid', 'true');
      } else {
        control.removeAttribute('aria-invalid');
      }
    });
  }

  function errorSlot(block, wrapper, input, create) {
    var errorEl;
    if (block === 'c-dropdown') {
      errorEl = wrapper.nextElementSibling;
      if (!errorEl || !errorEl.classList.contains('c-dropdown__error')) errorEl = null;
    } else if (block === 'c-image-upload') {
      errorEl = wrapper.querySelector('.c-image-upload__error');
    } else {
      errorEl = wrapper.parentElement && wrapper.parentElement.querySelector('.' + block + '__error');
    }
    if (!errorEl && create && (block === 'c-dropdown' || block === 'c-image-upload')) {
      errorEl = document.createElement('span');
      errorEl.className = block + '__error';
      if (block === 'c-dropdown') {
        wrapper.insertAdjacentElement('afterend', errorEl);
      } else {
        wrapper.appendChild(errorEl);
      }
    }
    if (errorEl && !errorEl.id && input.id) errorEl.id = input.id + '-error';
    return errorEl;
  }

  function setRadioGroupError(input, message, on) {
    var scope  = input.form || document;
    var radios = Array.from(scope.querySelectorAll('input[type="radio"]')).filter(function (radio) {
      return radio.name === input.name;
    });
    var errorEl = null;
    radios.forEach(function (radio) {
      var label = radio.closest('.c-radio');
      if (!label) return;
      label.classList.toggle('c-radio--error', on);
      var next = label.nextElementSibling;
      if (next && next.classList.contains('c-radio__error')) errorEl = next;
    });
    if (errorEl) {
      if (!errorEl.id && input.id) errorEl.id = input.id + '-error';
      errorEl.textContent = message || '';
    }
    linkError(radios, errorEl, on);
  }

  // Sets the error text of a text-field.html, checkbox.html, select.html,
  // radio.html group or image-upload.html control, toggles its --error
  // modifier (on when there is a message or `invalid` is true) and syncs
  // aria-invalid / aria-describedby. A slug-preview.html field is revealed.
  window.hdxV2.setFieldError = function setFieldError(input, message, invalid) {
    var on = !!(message || invalid);
    if (input.type === 'radio') {
      setRadioGroupError(input, message, on);
      return;
    }
    var wrapper = input.closest('.c-search-input, .c-checkbox, .c-dropdown, .c-image-upload');
    if (!wrapper) return;
    var block = FIELD_BLOCKS.filter(function (name) { return wrapper.classList.contains(name); })[0];
    var errorEl = errorSlot(block, wrapper, input, !!message);
    wrapper.classList.toggle(block + '--error', on);
    if (errorEl) errorEl.textContent = message || '';
    var controls = [input];
    var selection = block === 'c-dropdown' && wrapper.querySelector('.select2-selection');
    if (selection) controls.push(selection);
    linkError(controls, errorEl, on);
    if (on && input.closest('[data-slug-preview]')) input.dispatchEvent(new Event('invalid'));
  };

  // Shows `target` while `select`'s lower-cased value is in options.values.
  // options: hiddenClass (else the hidden attribute), requiredInputs (required
  // only while shown), clearOnHide (empties the target's inputs when hidden).
  window.hdxV2.wireReveal = function wireReveal(select, target, options) {
    if (!select || !target) return;
    var requiredInputs = (options.requiredInputs || []).filter(Boolean);

    var sync = function () {
      var shown = options.values.indexOf((select.value || '').toLowerCase()) !== -1;

      if (options.hiddenClass) {
        target.classList.toggle(options.hiddenClass, !shown);
      } else {
        target.hidden = !shown;
      }
      requiredInputs.forEach(function (input) {
        if (shown) {
          input.setAttribute('required', 'required');
        } else {
          input.removeAttribute('required');
        }
      });
      if (!shown && options.clearOnHide) {
        target.querySelectorAll('input, textarea').forEach(function (input) {
          input.value = '';
        });
      }
    };

    select.addEventListener('change', sync);
    sync();
  };

  // POSTs `body` to `url` with the CSRF header and resolves with the parsed JSON response.
  // A plain-object `body` is sent as JSON.
  window.hdxV2.post = function post(url, body) {
    var headers = window.hdxUtil.net.getCsrfTokenAsObject();
    if (Object.prototype.toString.call(body) === '[object Object]') {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(body);
    }
    return fetch(url, {
      method: 'POST',
      headers: headers,
      body: body
    }).then(function (r) { return r.json(); });
  };

})();
