/**
 * focus-trap.js — shared focus-trap utility (RF-01)
 *
 * Exposes window.FocusTrap for use in navbar.js (offcanvas).
 *
 * Usage:
 *   var trap = new FocusTrap(panelElement, triggerElement);
 *   trap.activate();   // moves focus inside, traps Tab/Shift+Tab
 *   trap.deactivate(); // releases trap, returns focus to trigger
 */
(function () {
  'use strict';

  var FOCUSABLE = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ].join(', ');

  function getFocusable(el) {
    return Array.from(el.querySelectorAll(FOCUSABLE)).filter(function (node) {
      return !node.closest('[hidden]') && !node.closest('[aria-hidden="true"]');
    });
  }

  function FocusTrap(element, triggerElement) {
    this.element        = element;
    this.triggerElement = triggerElement;
    this._handler       = null;
  }

  FocusTrap.prototype.activate = function () {
    var el   = this.element;
    var list = getFocusable(el);
    if (list.length) list[0].focus();

    this._handler = function (e) {
      if (e.key !== 'Tab') return;
      var current = getFocusable(el);
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
  };

  FocusTrap.prototype.deactivate = function () {
    if (this._handler) {
      document.removeEventListener('keydown', this._handler);
      this._handler = null;
    }
    if (this.triggerElement) this.triggerElement.focus();
  };

  window.FocusTrap = FocusTrap;
}());
