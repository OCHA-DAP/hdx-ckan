$(document).ready(function () {
  const $performResetForm = $('#perform-reset-form');

  $performResetForm.find('input, select, textarea').filter('[required]').on('input change', requiredFieldsFormValidator);
});
