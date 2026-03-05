$(document).on('click', '.facet[data-filter-url]', function (e) {
  if ($(e.target).closest('a').length) return;

  e.preventDefault();
  e.stopPropagation();

  var url = $(this).data('filter-url');
  if (url) window.location.href = url;
});

$(document).on('click', '.facet-option-explanation', function (e) {
  e.preventDefault();
  e.stopPropagation();
});

$(document).on('click', '.parent-facet', function (e) {
  if (this.disabled) return;

  e.preventDefault();
  e.stopPropagation();

  var url = $(this).closest('.facet[data-filter-url]').data('filter-url');
  if (url) window.location.href = url;
});
