$(document).ready(function(){
  $('#add_member_tabs a').click(function (e) {
    e.preventDefault();
    $(this).tab('show');
  });
});