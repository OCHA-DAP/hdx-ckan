"use strict";

ckan.module('contribute_flow_main', function($, _) {
	return {
		initialize : function() {
            var moduleLog = this.moduleLog;
            var sandbox = this.sandbox;
            var formBodyId = this.options.form_body_id;
            var dataset_id = this.options.dataset_id;
            var validateUrl = this.options.validate_url;
            var requestUrl = window.location.pathname;
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
                            var resourceDataArray = this.generateResourcePostData();
                            formDataArray = formDataArray.concat(resourceDataArray);
                            formDataArray.push({'name': 'id', 'value': datasetId});

                            $.post(validateUrl, formDataArray,
                                function (data, status, xhr) {
                                    data.error_summary = data.error_summary ? data.error_summary : {};
                                    if (!resourceDataArray || resourceDataArray.length == 0) {
                                        data.error_summary['Resources'] = 'Please add at least 1 resource to the dataset';
                                    }
                                    contributeGlobal.updateValidationUi(data, status, xhr);
                                    deferred.resolve(contributeGlobal.validateSucceeded(data, status));
                                    moduleLog('Validation finished');
                                }
                            );

                        }.bind(this)
                    );


                    return deferred.promise();
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
                                    formDataArray.push({'name': 'id', 'value': datasetId});

                                    analyticsPromise = {};
                                }
                                else{ // Saving a new dataset
                                    formDataArray = contributeGlobal.getFormValues('new-dataset-json');

                                     /* Send analytics tracking events */
                                    analyticsPromise = hdxUtil.analytics.sendDatasetCreationEvent();
                                }
                                contributeGlobal.controlUserWaitingWidget(true, 'Saving dataset form...');

                                $.when(analyticsPromise).done(function () {
                                    $.post(requestUrl, formDataArray,
                                        function (data, status, xhr) {
                                            contributeGlobal.updateInnerState(data, status);
                                            deferred.resolve(data, status, xhr);
                                        }
                                    );
                                });
                            }
                        }
                    );

                    return deferred.promise();
                },
                'getFormValues': function(save_mode) {
                    var formSelector = "#" + formBodyId;
                    var modifiedFormDataArray = [
                        {
                            'name':'save',
                            'value': save_mode
                        }
                    ];
                    var formDataArray = $(formSelector).find(':input').serializeArray();
                    for (var i=0; i<formDataArray.length; i++) {
                        var item = formDataArray[i];
                        if (item.value) {
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
                    var resetMessage = {type: 'reset'};
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
                                    errorInfo: errorList[i]
                                };
                                sandbox.publish('hdx-form-validation', message);
                            }
                        }
                        contributeGlobal.controlUserWaitingWidget(false);
                    }
                },
                'afterBodyFormSave': function (data, status, xhr) {
                    // Even if there are no errors we need to update the validation UI (hide previous errors)
                    contributeGlobal.updateValidationUi(data, status, xhr);

                    if ( contributeGlobal.validateSucceeded(data, status) ) {
                        if (!contributeGlobal.resourceSaveReadyDeferred) {
                            contributeGlobal.resourceSaveReadyDeferred = new $.Deferred();
                        }
                        contributeGlobal.resourceSaveReadyDeferred.resolve(data.data.id);
                        contributeGlobal.resourceSaveReadyDeferred = null;
                    }
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
                'browseToDataset': function() {
                    /**
                     *
                     */
                    if ( this._datasetName ) {
                        var promise = this.getDatasetIdPromise();
                        window.top.location.href = '/dataset/' + this._datasetName;
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
                    'newValue': privateVal == 'false' ? 'public' : 'private'
                }
            );

            privateRadioEls.change(
                function (event) {
                    if ($(this).prop('checked')){
                        var message = {
                            'type': 'private_changed',
                            'newValue': $(this).val() == 'false' ? 'public' : 'private'
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
            'validate_url': '/contribute/validate',
            dataset_id: null
        }

	};
});
