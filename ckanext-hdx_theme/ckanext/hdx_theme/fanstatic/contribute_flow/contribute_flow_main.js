(function () {
  "use strict";

  ckan.module('contribute_flow_main', function($, _) {
    return {
		    initialize : function() {
            var moduleLog = this.moduleLog;
            var sandbox = this.sandbox;
            var formBodyId = this.options.form_body_id;
            var dataset_id = this.options.dataset_id;
            var validateUrl = this.options.validate_url;
            var hxlPreviewApi = this.options.hxl_preview_api;
            var requestUrl = window.location.pathname;
            var isNewDataset = null; // Whether we're editing or creating a new dataset
            // var managePrivateField = this.managePrivateField;
            // var __this = this;
            var contributeGlobal = {
                'getDatasetIdPromise': function() {
                    var deferred = new $.Deferred();

                    if ( !this.hasOwnProperty('_datasetId')) { // This is the first time that we look for the ID

                        if ( dataset_id ) { // If we're in "edit" mode the ID was injected in options
                            this._datasetId = dataset_id;
                            deferred.resolve(this._datasetId);
                        }
                        else {  // We're in the "new" mode
                            deferred.resolve(null);
                            //var formDataArray = this.getFormValues('generate-dataset-id-json');
                            //var promise = $.post(requestUrl, $.param(formDataArray));
                            //$.when(promise).done(
                            //    function (data, status, xhr) {
                            //        contributeGlobal.updateValidationUi(data, status, xhr);
                            //        if (data.data && data.data.id) {
                            //            contributeGlobal._datasetId = data.data.id;
                            //            deferred.resolve(data.data.id);
                            //        }
                            //        else {
                            //            deferred.resolve(null);
                            //        }
                            //    }
                            //);
                        }
                    }
                    else { // We already have the dataset ID
                        deferred.resolve(this._datasetId);
                    }
                    return deferred.promise();
                },
                'validate': function() {
                    var deferred = new $.Deferred();

                    this.getDatasetIdPromise().done(
                        function (datasetId) {
                            var formDataArray = this.getFormValues('validate-json');
                            var resourceDataArray;
                            if(!this.isRequestedData()){
                              resourceDataArray = this.generateResourcePostData();
                              formDataArray = formDataArray.concat(resourceDataArray);
                              var customVizArray = this.generateCustomVizPostData();
                              formDataArray = formDataArray.concat(customVizArray);
                            }

                            formDataArray.push({'name': 'id', 'value': datasetId});

                            $.post(validateUrl, formDataArray,
                                function (data, status, xhr) {
                                    data.error_summary = data.error_summary ? data.error_summary : {};

                                    // Resources are not required for metadata-only datasets
                                    if (!data.data.is_requestdata_type && (!resourceDataArray || resourceDataArray.length === 0)) {
                                        data.error_summary['resource-list'] = 'Please add at least 1 resource to the dataset';

                                    }

                                    // Tags are required for metadata-only datasets
                                    if (data.data.is_requestdata_type && data.data.tag_string.length === 0) {
                                        data.errors.tag_string = ['Missing value'];
                                    }

                                    contributeGlobal.updateValidationUi(data, status, xhr);
                                    // contributeGlobal._managePrivateField();
                                    deferred.resolve(contributeGlobal.validateSucceeded(data, status));
                                    moduleLog('Validation finished');

                                }
                            ).fail(contributeGlobal.recoverFromServerError);

                        }.bind(this)
                    );


                    return deferred.promise();
                },
                '_managePrivateField': function () {
                  // var sandbox = this.sandbox;
                  var privateVal = null;
                  var privateEl = null;
                  var privateRadioEls = $("input[name='private']");
                  for (var i = 0; i < privateRadioEls.length; i++) {
                    var radioEl = $(privateRadioEls[i]);
                    if (radioEl.prop('checked')) {
                      privateVal = radioEl.val();
                    }
                    if (radioEl.val() == "true") {
                      privateEl = radioEl;
                    }
                  }
                  if (privateVal == null) {
                    privateVal = "false";
                    // If no checkbox is selected assume it's a private dataset
                    // this is logic is reflected in the contribute controller as well
                    privateEl.prop('checked', true);
                  }
                  sandbox.publish('hdx-form-validation', {
                      'type': 'private_changed',
                      'newValue': privateVal //privateVal == 'false' ? 'public' : 'private'
                    }
                  );
                },
                'saveDatasetForm': function() {
                    this.controlUserWaitingWidget(true, "Validating...");
                    var validatePromise = this.validate();
                    var datasetIdPromise = this.getDatasetIdPromise();
                    var deferred = new $.Deferred();
                    $.when(validatePromise, datasetIdPromise).done(
                        function(validateSucceeded, datasetId){
                            moduleLog('In saveDatasetForm() function. Got validateSucceeded: ' +
                                validateSucceeded + ' and datasetId:' + datasetId);
                            if (validateSucceeded) {
                                var analyticsPromise;
                                var formDataArray;
                                if (datasetId) { // updating existing dataset
                                    formDataArray = contributeGlobal.getFormValues('update-dataset-json');
                                    var special = $("#confirm-resource-freshness").find(':input').serializeArray();
                                    formDataArray = formDataArray.concat(special);

                                    formDataArray.push({'name': 'id', 'value': datasetId});

                                    analyticsPromise = {};
                                    isNewDataset = false;

                                }
                                else{ // Saving a new dataset
                                    formDataArray = contributeGlobal.getFormValues('new-dataset-json');

                                     /* Send analytics tracking events */
                                    analyticsPromise = hdxUtil.analytics.sendDatasetCreationEvent(formDataArray);
                                    isNewDataset = true;
                                }
                                formDataArray.push({'name': 'batch_mode', 'value': 'DONT_GROUP'});

                                var customVizArray = contributeGlobal.generateCustomVizPostData();
                                formDataArray = formDataArray.concat(customVizArray);

                                contributeGlobal.controlUserWaitingWidget(true, 'Saving dataset form...');

                                $.when(analyticsPromise).done(function () {
                                    $.post(requestUrl, formDataArray,
                                        function (data, status, xhr) {
                                            contributeGlobal.updateInnerState(data, status);
                                            deferred.resolve(data, status, xhr);
                                        }
                                    ).fail(contributeGlobal.recoverFromServerError);
                                });
                            }
                        }
                    );

                    return deferred.promise();
                },
                'isRequestedData': function() {
                    var formDataArray = this.getFormValues('validate-json');
                    var isRequestedData = false;
                    for (var i=0; i<formDataArray.length; i++) {
                      var item = formDataArray[i];
                      if (item.name==='private' && item.value === 'requestdata') {
                        isRequestedData = true;
                        break;
                      }
                    }
                    return isRequestedData;
                },
                'getFormValues': function(save_mode) {
                    // var formSelector = "#" + formBodyId;
                    var formSelector = ".contribute-form-container-items";
                    var modifiedFormDataArray = [
                        {
                            'name':'save',
                            'value': save_mode
                        }
                    ];
                    var formDataArray = $(formSelector).find(':input').serializeArray();

                    /**
                     * We're generating the custom viz POST data in generateCustomVizPostData(). So this input field is
                     * not needed anymore
                     */
                    var toSkip = ['custom_viz_url'];
                    for (var i=0; i<formDataArray.length; i++) {
                        var item = formDataArray[i];
                        if (item.value && toSkip.indexOf(item.name) === -1) {
                            modifiedFormDataArray.push(item);
                        }
                    }


                    return modifiedFormDataArray;
                },
                'updateInnerState': function (data, status) {
                    if ( this.validateSucceeded(data, status)) {
                        if ( !this.hasOwnProperty('_datasetId') && data.data && data.data.id) {
                            this._datasetId = data.data.id;
                        }
                        if ( data.data && data.data.name ) {
                            this._datasetName = data.data.name;
                        }
                    }
                },
                'updateValidationUi': function (data, status, xhr) {
                    var resetMessage = {type: 'reset', data: data};
                    sandbox.publish('hdx-form-validation', resetMessage);
                    if (data.error_summary && Object.keys(data.error_summary).length > 0) {
                        var sumMessage = {
                            'type': 'new_summary',
                            'elementName': 'error_block',
                            'errorBlock': data.error_summary
                        };
                        sandbox.publish('hdx-form-validation', sumMessage);
                        contributeGlobal.controlUserWaitingWidget(false);
                    }
                    if (data.errors && Object.keys(data.errors).length > 0) {
                        for (var key in data.errors) {
                            var errorList = data.errors[key];
                            for (var i = 0; i < errorList.length; i++) {
                                var message = {
                                    type: 'new',
                                    elementName: key,
                                    errorInfo: errorList[i],
                                    index: i
                                };
                                sandbox.publish('hdx-form-validation', message);
                            }
                        }
                        contributeGlobal.controlUserWaitingWidget(false);
                    }
                    var privateVal = null;
                    var privateEl = null;
                    var privateRadioEls = $("input[name='private']");
                    for (var i = 0; i < privateRadioEls.length; i++) {
                      var radioEl = $(privateRadioEls[i]);
                      if (radioEl.prop('checked')) {
                        privateVal = radioEl.val();
                      }
                      if (radioEl.val() == "true") {
                        privateEl = radioEl;
                      }
                    }
                    if (privateVal == null) {
                      privateVal = "false";
                      // If no checkbox is selected assume it's a private dataset
                      // this is logic is reflected in the contribute controller as well
                      privateEl.prop('checked', true);
                    }
                    sandbox.publish('hdx-form-validation', {
                        'type': 'private_changed',
                        'newValue': privateVal //privateVal == 'false' ? 'public' : 'private'
                      }
                    );
                },
                'datasetWaitToValidateAndSave': function(data, status) {
                  if (contributeGlobal.validateSucceeded(data, status)) {
                    if (!contributeGlobal.resourceSaveReadyDeferred) {
                      contributeGlobal.resourceSaveReadyDeferred = new $.Deferred();
                    }
                    contributeGlobal.resourceSaveReadyDeferred.resolve(data.data.id);
                    contributeGlobal.resourceSaveReadyDeferred = null;
                  }
                },
                'displayPrivateDatasetInfoPopup': function (data) {
                  // Check if we need to display the info about private datasets
                  let deferred = new $.Deferred();
                  const STORAGE_KEY = "/contribute:hidePrivateDatasetInfo";
                  let hideInfo = window.localStorage.getItem(STORAGE_KEY);

                  if (data.data.private && !hideInfo) {
                    $('#privateDatasetInfoPopup, #privateDatasetInfoPopup .close, #privateDatasetInfoPopup .btn-primary').click(function(ev) {
                      let { deferred, STORAGE_KEY } = this;
                      if ($('#privateDatasetInfoPopup input[name="hide-message"]').is(':checked')) {
                        window.localStorage.setItem(STORAGE_KEY, 'true');
                      }
                      $('#privateDatasetInfoPopup').hide();
                      deferred.resolve();
                    }.bind({deferred: deferred, STORAGE_KEY: STORAGE_KEY}));
                    $('#privateDatasetInfoPopup').show();
                  } else {
                    deferred.resolve();
                  }
                  return deferred.promise();
                },
                'displayContributeDatasetReviewPopup': function (data) {
                  // display the dataset contribute review info
                  let deferred = new $.Deferred();
                  const STORAGE_KEY = "/contribute:hideContributeDatasetReviewInfo";
                  let hideInfo = window.localStorage.getItem(STORAGE_KEY);

                  if (!hideInfo) {
                    $('#contributeDatasetReviewPopup, #contributeDatasetReviewPopup .close, #contributeDatasetReviewPopup .btn-primary').click(function(ev) {
                      let { deferred, STORAGE_KEY } = this;
                      if ($('#contributeDatasetReviewPopup input[name="hide-message"]').is(':checked')) {
                        window.localStorage.setItem(STORAGE_KEY, 'true');
                      }
                      $('#contributeDatasetReviewPopup').hide();
                      deferred.resolve()
                    }.bind({deferred: deferred, STORAGE_KEY: STORAGE_KEY}));
                    $('#contributeDatasetReviewPopup').show();
                  } else {
                    deferred.resolve();
                  }
                  return deferred.promise();
                },
                'afterBodyFormSave': function (data, status, xhr) {
                  // Even if there are no errors we need to update the validation UI (hide previous errors)
                  contributeGlobal.updateValidationUi(data, status, xhr);

                  let deferred = new $.Deferred();
                  const callbackContext = {contributeGlobal: contributeGlobal, data: data, status: status};
                  deferred.promise()
                    .then(function () {
                      let { contributeGlobal, data } = this;
                      return contributeGlobal.displayPrivateDatasetInfoPopup(data);
                    }.bind(callbackContext))
                    //DISABLED functionality for now
                    // .then(function () {
                    //   let { contributeGlobal, data } = this;+
                    //   return contributeGlobal.displayContributeDatasetReviewPopup(data)
                    // }.bind(callbackContext))
                    .then(function () {
                      let { contributeGlobal, data, status } = this;
                      contributeGlobal.datasetWaitToValidateAndSave(data, status);
                    }.bind(callbackContext));
                  deferred.resolve();
                },
                'resourceSaveReadyDeferred': null,
                'getResourceSaveStartPromise':  function() {
                    /**
                     * returns a promise which gets fulfilled when the body of the form
                     * is saved successfully.
                     * NOTE: If saving the resources fails you'll need to
                     * get another promise !
                     *
                     */
                    moduleLog('getResourceSaveStartPromise called');
                    if (!this.resourceSaveReadyDeferred) {
                        this.resourceSaveReadyDeferred = new $.Deferred();
                    }
                    return this.resourceSaveReadyDeferred.promise();
                },
                'browseToDataset': function(data, status, xhr) {
                    /**
                     *
                     */
                    if ( this._datasetName ) {
                        // var promise = this.getDatasetIdPromise();

                        // var fragment = '';
                        // if (data.result && data.result.length > 0) {
                        //     fragment = '#hxlEditMode';
                        // }
                        // var currentUrl = window.top.location.href;
                        var newUrl = '/dataset/' + this._datasetName;
                        //window.top.location.href = newUrl + fragment;
                        window.top.location.href = newUrl;

                        // If we're just adding the fragment (#hash) to the current url the page will not reload
                        // by itself. When we're editing a dataset the current url and the new url are the same.
                        // if (currentUrl && currentUrl.indexOf(newUrl)>0  && fragment) {
                        //     window.top.location.reload();
                        // }
                    }
                    else {
                        moduleLog.log('Cannot browse to dataset because name is missing');
                    }
                },
                'validateSucceeded': function(data, status) {
                    var validated = status == 'success' &&
                        (!data.errors || Object.keys(data.errors).length == 0) &&
                        (!data.error_summary || Object.keys(data.error_summary).length == 0);
                    return validated;
                },
                'setResourceModelList': function (resourceModelList) {
                    this.resourceModelList = resourceModelList;
                },
                /**
                *
                * @param {[string]} customVizList
                */
                'setCustomVizList': function (customVizUrls) {
                  this.customVizUrls = customVizUrls;
                },
                'generateCustomVizPostData': function() {
                  var customVizList = [];
                  if (this.customVizUrls) {

                    /**
                     * If we only have one empty custom viz then don't send it to the server
                     * because it's the one that is being shown automatically
                     */
                    if (this.customVizUrls.length >= 2 || this.customVizUrls[0]) {
                      for (var i = 0; i < this.customVizUrls.length; i++) {
                        customVizList.push({
                          name: 'customviz__' + i + '__url',
                          value: this.customVizUrls[i].trim()
                        });
                        // customVizList.push({
                        //   name: 'customviz__' + i + '__name',
                        //   value: 'CV TITLE ' + i
                        // });
                      }
                    }
                  }
                  return customVizList;
                },
                'generateDatasetPreviewOptions': function (resourceModelList) {
                    var newOptions = resourceModelList.models;
                    $("#field_dataset_preview_value").find("option").remove();
                    var selectOptions = $('#field_dataset_preview_value').prop('options');
                    selectOptions[0] = new Option('Default (first resource with preview)', 'first_resource');
                    var i = 'first_resource';
                    $.each(newOptions, function(index, value) {
                        var resName = value.get('name') ? value.get('name') : 'Resource '+(index+1);
                        if (value.get('dataset_preview_enabled') === true){
                            selectOptions[selectOptions.length] = new Option(resName, index+'', true, true);
                            i = index+'';
                        }
                        else {
                            selectOptions[selectOptions.length] = new Option(resName, index+'');
                        }
                    });
                    $("#field_dataset_preview_value").val(i).trigger('change');


                },
                'generateResourcePostData': function() {
                    var resourceModelList = this.resourceModelList.models;

                    var result = [];
                    for (var i=0; i<resourceModelList.length; i++) {
                        for (var key in resourceModelList[i].attributes) {
                            var postKey = 'resources__' + i + '__' + key;
                            result.push(
                                {
                                    'name': postKey,
                                    'value': resourceModelList[i].get(key)
                                }
                            );
                        }
                    }
                    return result;
                },
                /**
                 * @param {boolean} show - show or hide the widget
                 * @param {string} message - message to be shown
                 */
                'controlUserWaitingWidget':  function(show, message) {
                    sandbox.publish('hdx-user-waiting', {'show': show, 'message': message});
                },
                /**
                 *
                 * @returns {Promise}
                 */
                'callHxlPreviewGenerator': function(){
                    // Since this is called after the dataset is saved we surely have a _datasetId
                    // hxlPreviewApi, [{name: 'id', value: this._datasetId}], null, 'application/json'
                    return $.ajax({
                        url: hxlPreviewApi,
                        type: 'POST',
                        data: JSON.stringify({'id': this._datasetId}),
                        contentType: 'application/json',
                        dataType: 'json'
                    });
                },
                'finishContributeFlow': function() {

                    if(!this.isRequestedData()){
                      var callback = this.browseToDataset.bind(this);
                      this.callHxlPreviewGenerator().then(callback, callback);
                    }
                    else{
                      this.browseToDataset();
                    }

                },
                'recoverFromServerError': function() {
                    contributeGlobal.controlUserWaitingWidget(false);
                    const errMsg = 'A connection or server error occurred. Please try again in a few moments or contact HDX support.';
                    const errorSummary = {
                      'server_or_connection_error': errMsg
                    };
                    contributeGlobal.updateValidationUi({'error_summary': errorSummary});
                    //alert(errMsg);
                }
            };
            window.hdxContributeGlobal = contributeGlobal;
            sandbox.publish('hdx-contribute-global-created', contributeGlobal);

            // Submit the form via Ajax
            $("#" + this.options.form_id).submit(
              function(e) {
                  var promise = contributeGlobal.saveDatasetForm();
                  promise.done(contributeGlobal.afterBodyFormSave);
                  e.preventDefault();
              }
            );

            // Initialize private/public logic
            this.managePrivateField();

            //initialize organisation change, triggering autocomplete changes
            this.manageAutocompleteOrgBinding();

            this.manageDatasetPreviewSelect();
        },
        manageAutocompleteOrgBinding: function(){
            var selectMaintainer = $('#field_maintainer');
            var selectOrganisation = $('#field_owner_org');

            selectOrganisation.on("change", function(e){
                var value = e.val;
                // console.log(selectMaintainer);
                var attrValue = "org=" + value;
                selectMaintainer.attr('data-module-extra-params', attrValue);
                ckan.module.initializeElement(selectMaintainer[0]);
            });
        },
        manageDatasetPreviewSelect: function(){
		    var sandbox = this.sandbox;
            var selectOptions = $('#field_dataset_preview_value');
            selectOptions.on("change", function(e){
                sandbox.publish('hdx-resource-information', {
                    'type': 'dataset_preview_resource_change',
                    'newValue': e.val
                    }
                );
            });

        },
        managePrivateField: function() {
            var sandbox = this.sandbox;
            var privateVal = null;
            var privateEl = null;
            var privateRadioEls = $("input[name='private']");
            for (var i=0; i<privateRadioEls.length; i++) {
                var radioEl = $(privateRadioEls[i]);
                if (radioEl.prop('checked')) {
                    privateVal = radioEl.val();
                }
                if (radioEl.val() == "true") {
                    privateEl = radioEl;
                }
            }
            if (privateVal == null) {
                privateVal = "false";
                // If no checkbox is selected assume it's a private dataset
                // this is logic is reflected in the contribute controller as well
                privateEl.prop('checked', true);
            }
            sandbox.publish('hdx-form-validation', {
                    'type': 'private_changed',
                    'newValue': privateVal //privateVal == 'false' ? 'public' : 'private'
                }
            );

            privateRadioEls.change(
                function (event) {
                    if ($(this).prop('checked')){
                        var message = {
                            'type': 'private_changed',
                            'newValue': $(this).val() //$(this).val() == 'false' ? 'public' : 'private'
                        };
                        sandbox.publish('hdx-form-validation', message);
                    }
                }
            );
        },
        moduleLog: function (message) {
            //console.log(message);
        },
        options: {
            form_id: 'create_dataset_form',
            form_body_id: 'contribute-flow-form-body',
            validate_url: '/contribute/validate',
            hxl_preview_api: '/api/action/package_hxl_update',
            dataset_id: null
        }

    };
  });
}());
