(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    window.hdxV2.wireReveal(
      document.getElementById('field-in-dataviz-gallery'),
      document.getElementById('dataviz-gallery-section'),
      {values: ['true']}
    );
  });
})();
