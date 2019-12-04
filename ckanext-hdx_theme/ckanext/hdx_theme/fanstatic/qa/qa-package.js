

function _updateQuarantine(resource, flag) {
  let body = {
    "id": `${resource}`,
    "in_quarantine": flag,
  };
  let promise = new Promise((resolve, reject) => {
    $.post(
      '/api/action/resource_patch', body,
      (result) => {
        if (result.success){
          resolve(result);
        } else {
          reject(result);
        }
      });
  });
  return promise;
}

function updateQuarantine(resource, flag) {
  _updateQuarantine(resource, flag)
    .then(
      (resolve) => {
        alert("Quarantine status successfully updated!");
      },
      (error) => {
        alert("Error, quarantine status not updated!");
      }
    )
    .finally(() => {
      location.reload();
    });
}

function updateQuarantineList(resources, flag) {
  const promises = resources.map(resource => {
    _updateQuarantine(resource, flag);
    console.log(`Resource ${resource}`);
  });
  Promise.all(promises)
    .then(values => {
      alert("Quarantine status successfully updated for all resources!");
    })
    .catch(errors => {
      alert("Error, quarantine status not updated for at least one resource!");
    })
    .finally(() => {
      location.reload();
    });
}

$(document).ready(() => {
  $(".qa-package-item").on("click", (ev) => {
    $('.qa-package-details').hide();
    $('.qa-package-item.open').removeClass('open');
    $(ev.currentTarget).addClass('open');
    let index = $(ev.currentTarget).attr('data-index');
    $(`#qa-package-details-${index}`).show();
  });
});
