(function () {
  'use strict';

  function init(root) {
    var attached  = root.querySelector('[data-image-upload-attached]');
    var web       = root.querySelector('[data-image-upload-web]');
    var blank     = root.querySelector('[data-image-upload-blank]');
    var thumb     = root.querySelector('[data-image-upload-thumb]');
    var name      = root.querySelector('[data-image-upload-name]');
    var url       = web.querySelector('input');
    var file      = root.querySelector('[data-image-upload-file]');
    var clear     = root.querySelector('[data-image-upload-clear]');
    var status    = root.querySelector('[data-image-upload-status]');
    var choose    = root.querySelector('[data-image-upload-choose]');
    var link      = root.querySelector('[data-image-upload-link]');
    var remove    = root.querySelector('[data-image-upload-remove]');
    var reset     = root.querySelector('[data-image-upload-reset]');
    var objectUrl = null;

    function setState(state) {
      attached.hidden = state !== 'attached';
      web.hidden = state !== 'web';
      blank.hidden = state !== 'blank';
    }

    function notify() {
      root.dispatchEvent(new CustomEvent('image-upload:change', { bubbles: true }));
    }

    function toBlank() {
      url.value = '';
      file.value = '';
      clear.value = 'true';
      name.textContent = '';
      status.textContent = '';
      setState('blank');
      choose.focus();
    }

    file.classList.add('sr-only');
    file.setAttribute('tabindex', '-1');
    remove.hidden = false;
    reset.hidden = false;

    thumb.addEventListener('error', function () { thumb.hidden = true; });
    if (thumb.hasAttribute('src') && thumb.complete && !thumb.naturalWidth) thumb.hidden = true;

    choose.addEventListener('click', function () { file.click(); });

    link.addEventListener('click', function () {
      setState('web');
      url.focus();
    });

    remove.addEventListener('click', toBlank);
    reset.addEventListener('click', toBlank);

    file.addEventListener('change', function () {
      var chosen = file.files && file.files[0];
      if (!chosen) return;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = URL.createObjectURL(chosen);
      thumb.src = objectUrl;
      thumb.hidden = false;
      name.textContent = chosen.name;
      status.textContent = chosen.name;
      clear.value = '';
      setState('attached');
      remove.focus();
      notify();
    });

    url.addEventListener('change', function () {
      if (url.value.trim()) notify();
    });

    setState(root.getAttribute('data-image-upload-state'));
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-image-upload]').forEach(init);
  });
})();
