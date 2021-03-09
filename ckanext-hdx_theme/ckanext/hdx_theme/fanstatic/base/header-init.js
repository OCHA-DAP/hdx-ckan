$(document).ready(function(){
    //select 2 everywhere
    $(".hdx-form").find("select").select2({
        allowClear: true
    });

    $(".dropdown.dropdown-on-hover").hover(
        function(){ $(this).addClass('open') },
        function(){ $(this).removeClass('open') }
    );

    $(".dropdown .collapsible-submenu-item").click((ev) => {
      let container = $(ev.currentTarget).siblings(".dropdown-submenu");
      let icon = $(ev.currentTarget).find("i");
      let classes = icon.prop("classList");
      let toggle = classes.contains('humanitarianicons-Down');
      classes.forEach(c => icon.removeClass(c));
      icon.addClass((toggle ? 'humanitarianicons-Up' : 'humanitarianicons-Down'));
      container.collapse((toggle ? 'hide':'show'));
      console.log("click fired");
      ev.stopPropagation();
      return true;
    });

    // function showDataUseSurveyPopup() {
    //   var SURVEY_COOKIE = "hdx-data-usesurvey-popup";
    //   var cookie = $.cookie(SURVEY_COOKIE);
    //   // if (!cookie) {
    //     $("#dataUseSurveyPopup a.btn-primary").click(function (e) {
    //       hdxUtil.analytics.sendSurveyEvent('confirm popup');
    //       var pkg_id = $("#dataUseSurveryPkgId").text();
    //       var org_id = $("#dataUseSurveryOrgId").text();
    //       window.open(pkg_id + org_id, "_blank");
    //       $("#dataUseSurveyPopup").hide();
    //       var date = new Date();
    //       date.setTime(date.getTime() + 1000);
    //       $.cookie(SURVEY_COOKIE, true, {
    //         expires: date.setTime(date) //days
    //       });
    //     });
    //     var date = new Date();
    //     date.setTime(date.getTime() + 1000);
    //     $.cookie(SURVEY_COOKIE, true, {
    //       expires: date //days
    //     });
    //     hdxUtil.analytics.sendSurveyEvent('show popup');
    //     $("#dataUseSurveyPopup").show();
    //   // }
    // }

    function showSurveyPopup(){
      var SURVEY_COOKIE = "hdx-survey-popup";
      var cookie = $.cookie(SURVEY_COOKIE);
      if (!cookie) {
        $("#surveyPopup a.btn-primary").click(function (e) {
          hdxUtil.analytics.sendSurveyEvent('confirm popup');
          window.open("https://www.surveymonkey.com/r/FWXQ6W2", "_blank");
          $("#surveyPopup").hide();
          $.cookie(SURVEY_COOKIE, true, {
            expires: 200 //days
          });
        });
        $.cookie(SURVEY_COOKIE, true, {
          expires: 2 //days
        });
        hdxUtil.analytics.sendSurveyEvent('show popup');
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


    // showDataUseSurveyPopup();
});
