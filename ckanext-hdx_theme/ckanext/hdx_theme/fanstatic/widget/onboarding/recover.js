$(document).ready(function(){
    const $recoverForm = $('#recover-form');

    $recoverForm.on("submit", function () {
        $this = $(this);
        $.post("/user/reset", $this.serialize(), function (result_data) {
            var result = JSON.parse(result_data);
            if (result.success) {
                closeCurrentWidget($this); showOnboardingWidget('#recoverSuccessPopup');
            } else {
                var errMsg = $("#recoverPopup").find(".error-message");
                errMsg.text(result.error.message);
                $("#field-recover-id").addClass("error");
                errMsg.show();
            }
        });

        return false;
    });

    $recoverForm.find('input, select, textarea').filter('[required]').on('input change', requiredFieldsFormValidator);
});
