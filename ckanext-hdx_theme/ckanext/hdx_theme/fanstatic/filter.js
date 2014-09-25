$(document).ready(function(){
  $('#filter_dropdown').on('change','select', function(){
      window.location = $(this).val();
  });

  $("#search_filter_btn").click(function() {
      if ($("#search_filter_btn span").text() === '+') {
        return $("#search_bar_content").slideDown(300, function() {
          return $("#search_filter_btn span").text('-');
        });
      } else {
        return $("#search_bar_content").slideUp(300, function() {
          return $("#search_filter_btn span").text('+');
        });
      }
    });
});
