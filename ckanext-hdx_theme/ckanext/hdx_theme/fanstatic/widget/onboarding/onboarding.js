function closeCurrentWidget(self){
    $(self).parents(".popup").hide();
}

function showOnboardingWidget(id){
    $(id).show();
    $(id).find("input[type!='button']:visible:first").focus();

    $(id).find('img.gif-auto-play').remove();
    $(id).find('img.gif').each(function(idx, element){
        var el = $(element);
        var src = el.attr("src");
        var clone = el.clone();
        $(el).addClass("hide");
        clone.removeClass("hide");
        clone.attr("src", "");
        clone.addClass("gif-auto-play");
        el.after(clone);
        setTimeout(function(){
            clone.attr("src", src);
        }, 0);
    });

    function _triggerInputDataClass($this){
        if ($this.val() === "")
            $this.removeClass("input-content");
        else
            $this.addClass("input-content");
    }

    $(id).find('input[type="password"], input[type="text"], textarea').each(
        function(idx, el){
            _triggerInputDataClass($(el));
        }
    );
    $(id).find('input[type="password"], input[type="text"], textarea').change(
        function(){
            var $this = $(this);
            _triggerInputDataClass($this);
        }
    );
    $(id).find('input[type="password"], input[type="text"], textarea').on("keyup",
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

$(document).ready(function(){
    //check cookies
    var loginCookie = $.cookie("hdx_login");
    if (loginCookie){
        var data = JSON.parse(loginCookie);
        //console.log(data);

        $('#username-form-field, #login-photo-default').hide();
        $('#field-login').val(data.login);
        $('#user-display-name').text(data.display_name);
        if (data.email)
            $('#user-display-email').text(data.email);
        $('#login-photo-gravatar-img').attr("src", "//gravatar.com/avatar/"+ data.email_hash +"?s=95&d=identicon");
        $('#username-static, #login-photo-gravatar').show();
    }

    //check for first login
    var firstLogin = $("#first-login").text();
    if (firstLogin && firstLogin != ""){
        showOnboardingWidget("#registeredPopup");
        return;
    }

    //check for logout event
    var userLogout = $("#user-logout").text();
    if (userLogout && userLogout != ""){
        showOnboardingWidget("#logoutPopup");
        return;
    }
    //check for login error
    var loginError = $("#login-error").text();
    if (loginError && loginError != ""){
        var errMsg = $("#loginPopup").find(".error-message");
        errMsg.text(loginError);
        $("#field-login").addClass("error");
        $("#field-password").addClass("error");
        errMsg.show();

    }
    var userLogin = $("#user-login").text();
    if (userLogin && userLogin != ""){
        showOnboardingWidget("#loginPopup");
        return;
    }

    var userRegister = $("#user-register").text();
    if (userRegister && userRegister != ""){
        showOnboardingWidget('#signupPopup');
        return;
    }


});