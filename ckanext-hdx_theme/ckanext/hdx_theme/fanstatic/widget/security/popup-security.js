$(document).ready(function() {
  function onTestTwoStep() {
    let userName = $("#hidden-user-name").val();
    let body = {
      mfa: $("#field-mfa").val()
    };
    const msgContainer = $('#test-two-step-result');
    msgContainer.html('');
    msgContainer.removeClass('alert-success');
    msgContainer.removeClass('alert-danger');

    $.post(`/user/configure_mfa/${userName}`, body)
      .done((response) => {
        const result = JSON.parse(response);
        if (result.success == true){
          msgContainer.html('Code is valid, two-step verification is configured correctly!');
          msgContainer.addClass('alert-success');
          msgContainer.show();
        } else {
          msgContainer.html('Code is invalid, please check code and try again!');
          msgContainer.addClass('alert-danger');
          msgContainer.show();
        }
      })
      .fail((result) => {
        msgContainer.html('Error while attempting test!');
        msgContainer.addClass('alert-danger');
      });
  }

  function toggleTwoStep(on = false) {
    if (on) {
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

  $('#test-two-step-btn').on('click', onTestTwoStep);
  $('#two-step-turn-off').on('click', () => toggleTwoStep(false));
  $('#two-step-turn-on, #two-step-regenerate').on('click', () => toggleTwoStep(true));

  if (window.location.href.indexOf("show_totp") !== -1) {
    showOnboardingWidget('#tsvPopup');
  }
});
