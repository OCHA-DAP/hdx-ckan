$(document).ready(function(){
    //select 2 everywhere
    $(".hdx-form").find("select").select2({
        allowClear: true
    });

    $(".dropdown.dropdown-on-hover").hover(
        function(){ $(this).addClass('open') },
        function(){ $(this).removeClass('open') }
    );

    function showSurveyPopup(){
      var SURVEY_COOKIE = "hdx-cookie-consent";
      var cookie = $.cookie(SURVEY_COOKIE);
      if (!cookie) {
        $("#surveyPopup a.btn-primary").click(function (e) {
          window.open("https://www.surveymonkey.com/r/FWXQ6W2", "_blank");
          $("#surveyPopup").hide();
          $.cookie(SURVEY_COOKIE, true, {
            expires: 200 //days
          });
        });
        $.cookie(SURVEY_COOKIE, true, {
          expires: 2 //days
        });
        $("#surveyPopup").show();
      }
    }

    function initCookiePopup(){
        var consent = $.cookie("hdx-cookie-consent");
        if (!consent) {
            $(".allow-cookies-container .allow-cookies-continue").click(function () {
               $.cookie("hdx-cookie-consent", true);
               $(".allow-cookies-container").hide();
            });
            $(".allow-cookies-container").show();
        }
    }

    // initCookiePopup();


    showSurveyPopup();
});
