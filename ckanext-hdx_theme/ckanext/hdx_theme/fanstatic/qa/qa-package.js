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
    $.post('/api/action/hdx_qa_resource_patch', body)
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

function _updateBrokenLink(resource, flag) {
  let body = {
    "id": `${resource}`,
    "broken_link": `${flag}`,
  };
  let promise = new Promise((resolve, reject) => {
    $.post('/api/action/hdx_mark_broken_link_in_resource', body)
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
    $.post('/api/action/hdx_mark_qa_completed', body)
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

function _updateAllResourcesKeyValue(package,key,value) {
  let body = {
    "id": `${package}`,
    "key": key,
    "value": value,
  };
  let promise = new Promise((resolve, reject) => {
    $.post('/api/action/hdx_qa_package_revise_resource', body)
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

function updateQASelection(cb) {
  $(".dataset-heading").find("input[type='checkbox']").prop('checked', cb.checked);
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
    });
}

function updateAllResourcesPIISensitive(package) {
  _showLoading();
  _updateAllResourcesKeyValue(package,'pii_is_sensitive','False')
    .then(() => {
        _updateLoadingMessage("QA PII is sensitive status successfully updated! Reloading page ...");
    })
    .catch(() => {
        alert("Error, QA PII is sensitive status not updated!");
        $("#loadingScreen").hide();
    })
    .finally(() => {
      location.reload();
    });
}

function updateAllResourcesQuarantine(package,value) {
  _showLoading();
  _updateAllResourcesKeyValue(package,'in_quarantine',value)
    .then(() => {
        _updateLoadingMessage("QA quarantine status successfully updated! Reloading page ...");
    })
    .catch(() => {
        alert("Error, QA quarantine status not updated!");
        $("#loadingScreen").hide();
    })
    .finally(() => {
      location.reload();
    });
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
        let extraMsg = '';
        if( error && error.responseJSON){
          extraMsg = JSON.stringify(error.responseJSON.error.message);
        }
        alert("Error, PII check couldn't be launched!!  " + extraMsg);
        $("#loadingScreen").hide();
      }
    )
    .finally(() => {
      location.reload();
    });
}

function viewPIIResults(url) {
  $.get(`${url}?noredirect=true`)
    .done((result)=> {
      console.log(result);
      const visWidgetId = '#qa-results-visualisation';
      const visUrl = 'https://ocha-dap.github.io/dlp-output-viz/';
      const dataUrl = encodeURIComponent(result);
      $(visWidgetId+"-iframe").attr('src', `${visUrl}?dataUrl=${dataUrl}`);
      showOnboardingWidget(visWidgetId);
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
        alert("Error, quarantine status not updated! " + extraMsg);
        $("#loadingScreen").hide();
      }
    )
    .finally(() => {
      location.reload();
    });
}

function updateBrokenLink(resource, flag) {
  _showLoading();
  _updateBrokenLink(resource, flag)
    .then(
      (resolve) => {
        _updateLoadingMessage("Broken link status successfully updated! Reloading page...");
      },
      (error) => {
        alert("Error, broken link status not updated! " + extraMsg);
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

function qaPackageDetailsSelect(target) {
  $('.qa-package-details').hide();
  $('.qa-package-item.open').removeClass('open');
  $(target).addClass('open');
  let index = $(target).attr('data-index');
  window.location.hash = `qa-pkg-idx-${index}`;
  $(`#qa-package-details-${index}`).show();
}

function _updateResourceConfirmState(resource, flag, score, piiReportId) {
  let body = {
    "id": `${resource}`,
    "pii_is_sensitive": flag,
  };

  let promise = new Promise((resolve, reject) => {
    const mixpanelPromise = hdxUtil.analytics.sendQADashboardEvent(resource,flag,score,piiReportId);
    const patchPromise = $.post('/api/action/hdx_qa_resource_patch', body);
    mixpanelPromise.then((mixpanelResults) => {
      patchPromise
        .done((result) => {
          if (result.success) {
            resolve(result);
          } else {
            reject(result);
          }
        })
        .fail((result) => {
          reject(result);
        });
    });
  });
  return promise;
}

function _awsLogUpdate(resourceId, filename, key, value, dlpRun) {
  // if(dlpRun === 'False' || dlpRun==='false'){
  //   return ;
  // }
  let body = {
    "resourceId": resourceId,
    "filename": filename,
    "key": key,
    "value": value,
    "dlpRun": dlpRun
  };

  let promise = new Promise((resolve, reject) => {
    const logUpdatePromise = $.post('/api/action/hdx_aws_log_update', body);
    logUpdatePromise
        .done((result) => {
          if (result.success) {
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

function confirmPIIState(el, resourceId, score, piiReportId, dlpRun) {
  $(el).parents(".modal").modal("hide");
  let sensitive = $(el).parents(".modal-content").find("input[name='pii-confirm']:checked").val();
  // console.log('Confirm: ' + resourceId + " " + sensitive + " " + piiReportId);
  _showLoading();
  const logUpdatePromise = _awsLogUpdate(resourceId, piiReportId, "pii_is_sensitive", sensitive, dlpRun);
  const resourceConfirmStatePromise = _updateResourceConfirmState(resourceId, sensitive, score, piiReportId);

  $.when(logUpdatePromise, resourceConfirmStatePromise)
    .then(
      (resolve) => {
        _updateLoadingMessage("PII State successfully confirmed! Reloading page ...");
        // location.reload();
      },
      (error) => {
        let extraMsg = '';
        if( error && error.responseJSON){
          extraMsg = JSON.stringify(error.responseJSON.error.message);
        }
        alert("Error, PII state not updated! " + extraMsg);
        $("#loadingScreen").hide();
      }
    )
    .always(() => {
      location.reload();
    });
  // location.reload();
}

$(document).ready(() => {
  $(".qa-package-item").on("click", (ev) => qaPackageDetailsSelect(ev.currentTarget));
  let hash = window.location.hash ? window.location.hash.substr(1):null;
  let pkgIdx = (hash && hash.startsWith('qa-pkg-idx-')) ? hash.substr(11) : 1;
  const target = `.qa-package-item[data-index=${pkgIdx}]`;
  qaPackageDetailsSelect(target);
  if (pkgIdx > 1) {
    $(target)[0].scrollIntoView();
  }
});
