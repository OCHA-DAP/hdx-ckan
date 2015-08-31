$(document).ready(function(){
    $(".list-header-showall a").on("click", function(){
        var $this = $(this);
        var value = $this.text();
        window.location.href = replaceParam("limit", value);
    });

    $("#headerSearch").on("keyup", function(event){
        if (event.keyCode == '13'){
            var $this = $(this);
            var value = $this.val();
            window.location.href = replaceParam("q", value);
            event.preventDefault();
        }
    });

});