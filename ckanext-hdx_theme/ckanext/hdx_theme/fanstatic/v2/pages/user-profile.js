// ============================================================
// user-profile.js — v2 Profile and Password (task 079)
// Two-step verification drawer of templates/user/edit_user_form.html:
// - Turn on / Generate → POST …/new, draw the QR (QRious), start the setup
// - Test → POST the code; a pass enables Save
// - Save → reload without the query string or fragment
// - Cancel / Turn off → POST …/delete, reload
// - Closing the drawer mid-setup: Cancel before a passed test, Save after
// - ?show_totp opens the drawer on load
// ============================================================
(function () {
  'use strict';

  var DRAWER_ID = 'two-step-drawer';
  var LEAVE_WARNING = 'Please finish setting up your two-step verification. Failing to verify it might lock you out of your account! Are you sure you want to leave?';
  var VALID = 'Code is valid, two-step verification is configured correctly!';
  var INVALID = 'Code is invalid, please check code and try again!';
  var TEST_ERROR = 'Error while attempting test!';
  var ERROR = 'Error!';

  function succeeded(resp) {
    if (!resp || resp.success !== true) throw new Error('failed');
    return resp;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var drawerEl = document.getElementById(DRAWER_ID);
    var root = drawerEl && drawerEl.querySelector('[data-two-step]');
    if (!root) return;

    var part = function (name) { return root.querySelector('[data-two-step-' + name + ']'); };
    var errorAlert = part('error');
    var resultAlert = part('result');
    var testForm = part('test');
    var saveButton = part('save');
    var setup = null;

    function leave(navigate) {
      setup = null;
      window.onbeforeunload = null;
      navigate();
    }

    function reload() {
      leave(function () { window.location.reload(); });
    }

    function save() {
      leave(function () { window.location.assign(window.location.href.split(/[?#]/)[0]); });
    }

    function turnOff(reloadOnError) {
      errorAlert.hidden = true;
      window.hdxV2.post(root.getAttribute('data-two-step-delete-url'))
        .then(succeeded)
        .then(reload)
        .catch(function () {
          if (reloadOnError) {
            reload();
          } else {
            window.hdxV2.showAlert(errorAlert, ERROR);
          }
        });
    }

    function startSetup() {
      errorAlert.hidden = true;
      window.hdxV2.post(root.getAttribute('data-two-step-new-url'))
        .then(succeeded)
        .then(function (resp) {
          part('secret').textContent = resp.totp_secret;
          part('setup').querySelector('.c-copy-button').setAttribute('data-copy-value', resp.totp_secret);
          new window.QRious({ size: 250, element: part('qr'), value: resp.totp_challenger_uri });
          part('state').hidden = true;
          part('setup').hidden = false;
          part('actions').hidden = false;
          testForm.hidden = false;
          resultAlert.hidden = true;
          window.hdxV2.setDisabled(saveButton, true);
          setup = 'untested';
          window.onbeforeunload = function () { return LEAVE_WARNING; };
        })
        .catch(function () { window.hdxV2.showAlert(errorAlert, ERROR); });
    }

    testForm.addEventListener('submit', function (e) {
      e.preventDefault();
      resultAlert.hidden = true;
      window.hdxV2.post(root.getAttribute('data-two-step-test-url'), new URLSearchParams(new FormData(testForm)))
        .then(function (resp) {
          if (!resp || resp.success !== true) {
            window.hdxV2.showAlert(resultAlert, INVALID, 'error');
            return;
          }
          window.hdxV2.showAlert(resultAlert, VALID, 'success');
          if (setup) {
            setup = 'tested';
            window.hdxV2.setDisabled(saveButton, false);
            window.onbeforeunload = null;
          }
        })
        .catch(function () { window.hdxV2.showAlert(resultAlert, TEST_ERROR, 'error'); });
    });

    root.addEventListener('click', function (e) {
      if (e.target.closest('[data-two-step-new]')) startSetup();
      else if (e.target.closest('[data-two-step-off], [data-two-step-cancel]')) turnOff(false);
      else if (e.target.closest('[data-two-step-save]')) save();
    });

    drawerEl.addEventListener('drawer:close', function () {
      if (setup === 'tested') save();
      else if (setup === 'untested') turnOff(true);
    });

    if (new URLSearchParams(window.location.search).has('show_totp')) {
      window.hdxV2Drawer(DRAWER_ID).open();
    }
  });

})();
