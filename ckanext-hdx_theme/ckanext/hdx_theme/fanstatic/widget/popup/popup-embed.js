$(document).ready(function(){
    $(".embed-link").on("click", function(){
       $(this).select();
    });
    $(".popup").each(function(){
        var popup = $(this);
        var config = popup.find(".config").first();
        var frameSize = $(".frame-size");
        frameSize.on("change", function(){
            var valueString = $(this).find("option:selected").first().val();
            var value = JSON.parse(valueString);
            var url = $.trim(config.find(".embed-url").text());
            var url_param = $.trim(config.find(".embed-param").text());

            var result = '<iframe frameborder="0" ' +
                         ' width="' + value.width + 'px" height="'+ value.height +'px"' +
                         'src="'+ url +'?'+ url_param +'"></iframe>';
            popup.find(".embed-link").attr("value", result);
            popup.find(".preview-container").html(result);
        });

        var embedTriggerId = $.trim(config.find(".embed-trigger").text());
        $("#"+embedTriggerId).on("click", function(){
            frameSize.change();
            popup.show();
        });
    });


});