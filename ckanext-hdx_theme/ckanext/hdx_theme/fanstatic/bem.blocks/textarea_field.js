$(document).ready(function () {

  $('.textarea-field__character-count').each(function () {
    var $characterCountElement = $(this);
    var $textareaElement = $characterCountElement.parent().find('textarea');
    $characterCountElement.text('0 characters');
    $textareaElement.on('keyup change input', function () {
      var textLength = $(this).val().length;
      var textCharacters = textLength !== 1 ? ' characters' : ' character';
      $characterCountElement.text(textLength.toString() + textCharacters);
    });
  });

});
