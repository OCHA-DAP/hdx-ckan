$(document).ready(function(){
    //select 2 everywhere
    $(".hdx-form").find("select").select2({
        allowClear: true
    });

    var hoverDropdowns = document.querySelectorAll('.dropdown.dropdown-on-hover');
    hoverDropdowns.forEach(function(dropdown) {
        var dropdownMenu = dropdown.querySelector('.dropdown-menu');
        var timeoutId;
        dropdown.addEventListener('mouseenter', function() {
            if (dropdownMenu) {
                clearTimeout(timeoutId); // Clear any existing timeout
                dropdownMenu.classList.add('show');
            }
        });
        dropdown.addEventListener('mouseleave', function() {
            // Set a short delay before removing the 'show' class
            timeoutId = setTimeout(function() {
                if (dropdownMenu) {
                    dropdownMenu.classList.remove('show');
                }
            }, 200);
        });
    });

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

    function checkFromLoginPage() {
        var fromLoginPageElement = document.getElementById('from-login');
        if (fromLoginPageElement && fromLoginPageElement.getAttribute('data-value') === 'true') {
          hdxUtil.net.removeOnboardingFlowData();
        }
    }

    // initCookiePopup();


    // showDataUseSurveyPopup();

    checkFromLoginPage();
});
