function floatingLogo() {
  var window_top = $(window).scrollTop();
  var floatingLogoAnchor = $('#floatingLogoAnchor');
  var floatingLogo = $('#floatingLogo');
  var div_top = floatingLogoAnchor.offset().top - 45;
  if (window_top > div_top) {
    floatingLogo.css("display", "block");
  } else {
    floatingLogo.css("display", "none");
  }
}
$(document).ready(function(){
    $(window).scroll(floatingLogo);
    floatingLogo();
});