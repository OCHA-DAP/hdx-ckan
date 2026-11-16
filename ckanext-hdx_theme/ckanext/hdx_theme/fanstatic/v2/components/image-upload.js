(function () {
  'use strict';

  function init(root) {
    var attached  = root.querySelector('[data-image-upload-attached]');
    var web       = root.querySelector('[data-image-upload-web]');
    var blank     = root.querySelector('[data-image-upload-blank]');
    var thumb     = root.querySelector('[data-image-upload-thumb]');
    var name      = root.querySelector('[data-image-upload-name]');
    var url       = web ? web.querySelector('input') : root.querySelector('[data-image-upload-url]');
    var file      = root.querySelector('[data-image-upload-file]');
    var clear     = root.querySelector('[data-image-upload-clear]');
    var status    = root.querySelector('[data-image-upload-status]');
    var error     = root.querySelector('[data-image-upload-error]');
    var choose    = blank.querySelector('[data-image-upload-choose]');
    var replace   = attached.querySelector('[data-image-upload-choose]');
    var link      = root.querySelector('[data-image-upload-link]');
    var remove    = root.querySelector('[data-image-upload-remove]');
    var reset     = root.querySelector('[data-image-upload-reset]');
    var maxBytes  = Number(root.dataset.imageUploadMaxBytes) || 0;
    var width     = Number(root.dataset.imageUploadWidth) || 0;
    var objectUrl = null;
    var accepted  = null;

    function setState(state) {
      attached.hidden = state !== 'attached';
      if (web) web.hidden = state !== 'web';
      blank.hidden = state !== 'blank';
    }

    function notify() {
      root.dispatchEvent(new CustomEvent('image-upload:change', { bubbles: true }));
    }

    function toBlank() {
      url.value = '';
      file.value = '';
      accepted = null;
      clear.value = 'true';
      name.textContent = '';
      status.textContent = '';
      thumb.hidden = true;
      setState('blank');
      choose.focus();
    }

    function show(chosen, chosenUrl) {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = chosenUrl;
      accepted = chosen;
      thumb.src = objectUrl;
      thumb.hidden = false;
      name.textContent = chosen.name;
      status.textContent = chosen.name;
      if (clear) clear.value = '';
      setState('attached');
      (remove || replace).focus();
      notify();
    }

    function reject(chosenUrl) {
      URL.revokeObjectURL(chosenUrl);
      if (accepted) {
        var kept = new DataTransfer();
        kept.items.add(accepted);
        file.files = kept.files;
      } else {
        file.value = '';
      }
      error.textContent = root.dataset.imageUploadCheckMessage;
      status.textContent = root.dataset.imageUploadCheckMessage;
    }

    file.classList.add('sr-only');
    file.setAttribute('tabindex', '-1');
    if (remove) remove.hidden = false;
    if (reset) reset.hidden = false;

    thumb.addEventListener('error', function () { thumb.hidden = true; });
    if (thumb.hasAttribute('src') && thumb.complete && !thumb.naturalWidth) thumb.hidden = true;

    [choose, replace].forEach(function (button) {
      if (button) button.addEventListener('click', function () { file.click(); });
    });

    if (link) {
      link.addEventListener('click', function () {
        setState('web');
        url.focus();
      });
    }

    if (remove) remove.addEventListener('click', toBlank);
    if (reset) reset.addEventListener('click', toBlank);

    file.addEventListener('change', function () {
      var chosen = file.files && file.files[0];
      if (!chosen) return;
      var chosenUrl = URL.createObjectURL(chosen);
      if (!maxBytes && !width) {
        show(chosen, chosenUrl);
        return;
      }
      error.textContent = '';
      status.textContent = '';
      var probe = new Image();
      probe.addEventListener('load', function () {
        if ((maxBytes && chosen.size > maxBytes) || (width && probe.naturalWidth !== width)) {
          reject(chosenUrl);
        } else {
          show(chosen, chosenUrl);
        }
      });
      probe.addEventListener('error', function () { reject(chosenUrl); });
      probe.src = chosenUrl;
    });

    url.addEventListener('change', function () {
      if (url.value.trim()) notify();
    });

    setState(root.getAttribute('data-image-upload-state'));
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-image-upload]').forEach(init);
  });

  document.addEventListener('config-item:add', function (e) {
    e.target.querySelectorAll('[data-image-upload]').forEach(init);
  });
})();
