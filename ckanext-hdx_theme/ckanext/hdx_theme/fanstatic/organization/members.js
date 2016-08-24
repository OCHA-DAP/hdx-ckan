$(document).ready(function(){
  $('#add_member_tabs a').click(function (e) {
    e.preventDefault();
    $(this).tab('show');
  });

  $(".approval-actions .action-approve a").click(function(){
    var role = $(this).attr('data-role');
    var memberId = $(this).attr('data-member-id');
    $.ajax({
      method: "POST",
      url: "/action/approve",
      data: {
        "member": memberId,
        "role": role,
        "approve": true
      },
      dataType: "json"
    })
      .done(function(){
        $(this).parents('.approval-actions').find('.approved-message .approved-role').text(role);
        $(this).parents('.approval-request').toggleClass('request-approved');
      })
      .fail(function(){
        alert("Your request failed!")
      });
  });

  $(".approval-actions .action-decline").click(function(){
    var memberId = $(this).attr('data-member-id');
    $.ajax({
      method: "POST",
      url: "/action/decline",
      data: {
        "member": memberId,
        "reject": true
      },
      dataType: "json"
    })
      .done(function(){
        $(this).parents('.approval-actions').find('.approved-message').text("Membership request declined!");
        $(this).parents('.approval-request').toggleClass('request-approved');
      })
      .fail(function(){
        alert("Your request failed!")
      });

    return false;
  });

});