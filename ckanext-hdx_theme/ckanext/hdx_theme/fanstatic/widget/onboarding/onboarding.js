function closeCurrentWidget(self){
    $(self).parents(".popup").hide();
}

function showOnboardingWidget(id){
    $(id).show();
    $(id).find("input:first").focus();

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

    return false;
}