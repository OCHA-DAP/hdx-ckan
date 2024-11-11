$(document).ready(function() {
  function onTestTwoStep() {
    let userName = $("#hidden-user-name").val();
    let body = {
      mfa: $("#field-mfa").val()
    };
    let mfaTestForm = $("#form-mfa-test");
    const msgContainer = $('#test-two-step-result');
    msgContainer.html('');
    msgContainer.removeClass('alert-success');
    msgContainer.removeClass('alert-danger');

    $.ajax({
      url: `/user/configure_mfa/${userName}`,
      type: 'POST',
      headers: hdxUtil.net.getCsrfTokenAsObject(),
      data: mfaTestForm.serialize(),
      success: function (response) {
        const result = JSON.parse(response);
        if (result.success == true) {
          msgContainer.html('Code is valid, two-step verification is configured correctly!');
          msgContainer.addClass('alert-success');
          msgContainer.show();
          // Saving and reloading/redirecting is now possible
          $('#submit-two-step-btn').show();
          $('#disabled-submit-two-step-btn').hide();
          window.onbeforeunload = null;
        } else {
          msgContainer.html('Code is invalid, please check code and try again!');
          msgContainer.addClass('alert-danger');
          msgContainer.show();
        }
      },
      error: function () {
        msgContainer.html('Error while attempting test!');
        msgContainer.addClass('alert-danger');
      }
    });
  }

  function toggleTwoStep(on = false) {
    let $tsvPopup = $('#tsvPopup');
    if (on) {
      $('#new-two-step-actions').css('display', 'flex');
      // disable popup closing mechanisms
      $tsvPopup.unbind('click');
      $tsvPopup.click((ev) => {ev.preventDefault();})
      $tsvPopup.find('i.close').hide();
      //confirm if closing/reloading tab
      window.onbeforeunload = () => {
        // this message is no longer shown in recent browsers due to security reason.
        return "Please finish setting up your two-step verification. Failing to verify it might lock you out of your account! Are you sure you want to leave?"
      }

      let userName = $("#hidden-user-name").val();
      $.get(`/user/configure_mfa/${userName}/new`)
        .done((response) => {
          const result = JSON.parse(response);
          if (result.success == true){
            $('#totp-secret').html(result.totp_secret);
            $('#totp-uri').val(result.totp_challenger_uri);
            new QRious({
                size: 250,
                element: $('#qr-code-container')[0],
                value: result.totp_challenger_uri
            })

            $('#two-step-turn-on-container').hide();
            $('#two-step-turn-off-container').show();
          }
        })
        .fail(() => {
          alert('Error!');
        });
    } else {
      window.onbeforeunload = null;
      $tsvPopup.find('i.close').show();
      let userName = $("#hidden-user-name").val();
      $.get(`/user/configure_mfa/${userName}/delete`)
        .done((response) => {
          const result = JSON.parse(response);
          if (result.success == true){
            $('#two-step-turn-on-container').show();
            $('#two-step-turn-off-container').hide();
          }
        })
        .fail(() => {
          alert('Error!');
        });
    }
  }

  $("#form-mfa-test").on('submit', (e) => { e.preventDefault(); return false; });
  $('#test-two-step-btn').on('click', onTestTwoStep);
  $('#two-step-turn-off').on('click', () => toggleTwoStep(false));
  $('#two-step-turn-on, #two-step-regenerate').on('click', () => toggleTwoStep(true));

  if (window.location.href.indexOf("show_totp") !== -1) {
    showOnboardingWidget('#tsvPopup');
  }

  $('#submit-two-step-btn').on('click', () => {
    let url = window.location.href.split('?')[0]
    location.assign(url);
  })
  $('#cancel-two-step-btn').on('click', () => { toggleTwoStep(false); location.reload(); })

});
