function closeCurrentWidget(self){
    $(self).parents(".popup").hide();
}

function spawnRecaptcha(id){
    var container = $(id);
    var init = container.attr("hdx-recaptcha");
    if (!init){
      container.attr("hdx-recaptcha", true);
      container.find(".hdx-recaptcha").each(function (idx, el) {
        var disabled = el.hasAttribute('disabled');
        grecaptcha.render(el);
        if(disabled) {
          el.setAttribute('disabled', true);
        }
      });
    }
}


function showContributorPopup(popupId, pkgTitle, pkgOwnerOrg, pkgId, overwritePopupTitle){
  spawnRecaptcha(popupId);
  //populate popup with hidden fields content
  pkgTitle = decodeURIComponent(pkgTitle);
  let form = $('#contact-contributor-form');
  form.find('input[type="hidden"][name="pkg_title"]').val(pkgTitle);
  form.find('input[type="hidden"][name="pkg_owner_org"]').val(pkgOwnerOrg);
  form.find('input[type="hidden"][name="pkg_id"]').val(pkgId);
  if (overwritePopupTitle) {
    form.find('.contact-popup-title').html(pkgTitle);

  }

  showOnboardingWidget(popupId)
}

function showOnboardingWidget(id, elid, val){
    if (id == "#signupPopup") {
        // we only want to send the analytics event for the sign-up widget
        hdxUtil.analytics.sendUserRegisteredEvent("start user register");
    }
    $(id).show();
    $(id).find("input[type!='button']:visible:first").focus();

    $(id).find('img.gif-auto-play').remove();
    $(id).find('img.gif').each(function(idx, element){
        var el = $(element);
        var src = el.attr("src");
        var clone = el.clone();
        $(el).addClass("d-none");
        clone.removeClass("d-none");
        clone.attr("src", "");
        clone.addClass("gif-auto-play");
        el.after(clone);
        setTimeout(function(){
            clone.attr("src", src);
        }, 0);
    });
    if(elid){
      $(elid).val(val);
    }
    function _triggerInputDataClass($this){
        if ($this.val() === "")
            $this.removeClass("input-content");
        else
            $this.addClass("input-content");
    }

    $(id).find('input[type="password"], input[type="number"], input[type="text"], textarea').each(
        function(idx, el){
            _triggerInputDataClass($(el));
        }
    );
    $(id).find('input[type="password"], input[type="number"], input[type="text"], textarea').change(
        function(){
            var $this = $(this);
            _triggerInputDataClass($this);
        }
    );
    $(id).find('input[type="password"], input[type="number"], input[type="text"], textarea').on("keyup",
        function(){
            var $this = $(this);
            _triggerInputDataClass($this);
        }
    );

    $(id).find('input[type="submit"]').on("click", function(){
        var result = precheckForm(id);
        return !result;
    });

    function precheckForm(id){
        var error = false;
        $(id).find("input.required, textarea.required, select.required").each(function(idx, el){
            var $el = $(el);
            if ($el.is(":visible") && ($el.val() === null || $el.val() === "")){
                $el.addClass("error");
                error = true;
            } else {
                $el.removeClass("error");
            }
        });
        return error;
    }

    return false;
}


requiredFieldsFormValidator = function () {
  var error = false;
  var $form = $(this).closest('form');
  var $submitButton = $form.find('[type="submit"]');
  $form.find('input, select, textarea').filter('[required]').each(function (idx, el) {
    if ((el.type === 'checkbox') ? !el.checked : (el.value === null || el.value === '' || el.value === '-1')) {
      error = true;
      return true;
    }
  });
  if (error) {
    $submitButton.attr('disabled', true);
  } else {
    $submitButton.removeAttr('disabled');
  }
};

$(
  function () {
    //  check for logout event
    var userLogout = $("#user-logout").text();
    if (userLogout && userLogout !== "") {
      showOnboardingWidget("#logoutPopup");
      return;
    }
  }
);
