function showFaqWidget(id) {
    $(id).show();



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
    $('#topics-selector').select2();

    $('#faq-send-message-form').on('submit', function(){
        $this = $(this);
        $iframe = $($(".g-recaptcha").find("iframe:first"));
        $iframe.css("border", "");
        $.post('/faq/contact_us', $this.serialize(), function(result_data){
            var result = JSON.parse(result_data);
            if (result.success){
                closeCurrentWidget($this); showFaqWidget('#faqDonePopup');
            }
            else {
                if (result.error.message == "Captcha is not valid"){
                    $iframe.css("border", "1px solid red");
                } else {
                    alert("Can't send your request: " + result.error.message);
                }
            }
        });
        return false;
    });

});