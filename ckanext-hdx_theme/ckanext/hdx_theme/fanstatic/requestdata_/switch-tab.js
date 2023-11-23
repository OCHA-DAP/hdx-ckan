$(document).ready(function () {
  $('#switch-to-metadata-tab').on('click', function () {
    var metadataTab = document.querySelector('#link-metadata-tab');
    var tab = new bootstrap.Tab(metadataTab);
    tab.show();
    return false;
  });
});
