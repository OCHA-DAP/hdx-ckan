// old-design-banner.js — dismiss handling for the v1 old-design banner
// Renders from templates/snippets/old_design_banner.html
(function () {
  'use strict';

  var STORAGE_KEY = '/site:hideOldDesignBanner';

  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('[data-old-design-banner-close]');
    if (!btn) return;
    var banner = document.getElementById('hdx-old-design-banner');
    window.localStorage.setItem(STORAGE_KEY, 'true');
    if (banner) banner.style.display = 'none';
  });

})();
