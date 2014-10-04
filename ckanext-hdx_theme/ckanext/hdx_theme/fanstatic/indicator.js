$(document).ready(function() {
  $("#showOptions").on("click", function (){
    const showOptionsText = 'Select countries';
    const hideOptionsText = 'Hide select countries';
    if ($(this).text() == showOptionsText)
      $(this).text(hideOptionsText);
    else
      $(this).text(showOptionsText);

    $('#optionsContent').toggleClass('hidden');
    $('#graphContent').toggleClass('col-xs-12 col-xs-9');

    return false;
  });

  $("#optionDropDown").find("li > a").on("click", function (){
    var value = $(this).attr("val");
    var container = $("#" + value);
    container.parent().find("ul").hide();
    container.show();
    $("#location-dd").find("span").text($(this).text());
  })
});