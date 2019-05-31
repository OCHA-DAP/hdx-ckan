$(document).ready(function() {
  var actionsMenuTimer;
  $(".base-actions-menu .hide-text").hover(
    function (e) {
      actionsMenuTimer = setTimeout(function () {
        $(e.currentTarget).toggleClass("hovering", true);
      }, 350);
    },
    function (e) {
      if (actionsMenuTimer) {
        clearTimeout(actionsMenuTimer);
        actionsMenuTimer = undefined;
      }
      $(e.currentTarget).toggleClass("hovering", false);
    }
  );
});
