$(document).ready(function() {
  $("#showOptions").on("click", function (){
    const showOptionsText = 'Show options';
    const hideOptionsText = 'Hide options';
    if ($(this).text == showOptionsText)
      $(this).text(hideOptionsText);
    else
      $(this).text(showOptionsText);

    $('#optionsContent').toggleClass('hidden');
    $('#graphContent').toggleClass('col-xs-12 col-xs-9');

    return false;
  })
});