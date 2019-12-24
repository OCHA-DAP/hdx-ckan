function _updateLoadingMessage(message) {
  $('#loadingScreen .spinner-message').html(message);
}

function _showLoading() {
  $("#loadingScreen").show();
  _updateLoadingMessage("Sending, please wait ...");
}

function _updateQuarantine(resource, flag) {
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

function _getPackageResourceList(elementId) {
  return JSON.parse($(elementId).html());
}

function _getPackageResourceIdList(elementId) {
  return _getPackageResourceList(elementId).map((resource) => resource.id);
}


function updateQAComplete(package, flag) {
  _showLoading();
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

function _runPIICheck(resource) {
  let body = {
    "resourceId": `${resource}`
  };
  let promise = new Promise((resolve, reject) => {
    $.post('/api/action/qa_pii_run', body)
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

function runPIICheck(resource) {
  _updateLoadingMessage("Launching PII check, please wait ...");
  _showLoading();
  _runPIICheck(resource)
    .then(
      (resolve) => {
        _updateLoadingMessage("PII check launched! Reloading page ...");
      },
      (error) => {
        alert("Error, PII check couldn't be launched!");
        $("#loadingScreen").hide();
      }
    )
    .finally(() => {
      location.reload();
    });
}

function updateQuarantine(resource, flag) {
  _showLoading();
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

function updateQuarantineList(resourceListId, flag) {
  _showLoading();
  let resources = _getPackageResourceIdList(resourceListId);
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

function bulkUpdateQAComplete(flag) {
  const packages = $(".dataset-heading").toArray().reduce((accumulator, item) => {
    if ($(item).find("input[type='checkbox']").is(':checked')) {
      let packageId = $(item).find(".package-resources").attr('data-package-id');
      if (packageId) {
        accumulator.push(packageId)
      }
    }
    return accumulator;
  }, []);

  _showLoading();
  let packagesPromise = packages.reduce((currentPromise, package) => {
    return currentPromise
      .then(() => {
        _updateLoadingMessage(`Updating package with id [${package}], please wait ...`);
        return _updateQAComplete(package, flag);
      })
  }, Promise.resolve([]));

  packagesPromise
    .then(values => {
      _updateLoadingMessage("QA status successfully updated for all packages! Reloading page ...");
    })
    .catch(errors => {
      alert("Error, QA status not updated for at least one package!");
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
