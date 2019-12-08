function _updateLoadingMessage(message) {
  $('#loadingScreen .spinner-message').html(message);
}

function _showLoading() {
  $("#loadingScreen").show();
  _updateLoadingMessage("Sending, please wait ...");
}

function _updateQuarantine(resource, flag) {
  _showLoading();
  let body = {
    "id": `${resource}`,
    "in_quarantine": flag,
  };
  let promise = new Promise((resolve, reject) => {
    $.post('/api/action/resource_patch', body)
      .done((result) => {
        if (result.success){
          resolve(result);
        } else {
          reject(result);
        }
      })
      .fail((result) => {
        reject(result);
      });
  });
  return promise;
}

function _updateQAComplete(package, flag) {
  _showLoading();
  let body = {
    "id": `${package}`,
    "qa_completed": flag,
  };
  let promise = new Promise((resolve, reject) => {
    $.post('/api/action/package_patch', body)
      .done((result) => {
        if (result.success){
          resolve(result);
        } else {
          reject(result);
        }
      })
      .fail((result) => {
        reject(result);
      });
  });
  return promise;
}

function updateQAComplete(package, flag) {
  _updateQAComplete(package, flag)
    .then(() => {
        _updateLoadingMessage("QA Complete status successfully updated! Reloading page ...");
    })
    .catch(() => {
        alert("Error, QA Complete status not updated!");
        $("#loadingScreen").hide();
    })
    .finally(() => {
      location.reload();
    })
}

function updateQuarantine(resource, flag) {
  _updateQuarantine(resource, flag)
    .then(
      (resolve) => {
        _updateLoadingMessage("Quarantine status successfully updated! Reloading page ...");
      },
      (error) => {
        alert("Error, quarantine status not updated!");
        $("#loadingScreen").hide();
      }
    )
    .finally(() => {
      location.reload();
    });
}

function updateQuarantineList(resources, flag) {
  let resourcesPromise = resources.reduce((currentPromise, resource) => {
    return currentPromise
      .then(() => {
        _updateLoadingMessage(`Updating resource with id [${resource}], please wait ...`);
        return _updateQuarantine(resource, flag);
      })
  }, Promise.resolve([]));

  resourcesPromise
    .then(values => {
      _updateLoadingMessage("Quarantine status successfully updated for all resources! Reloading page ...");
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
