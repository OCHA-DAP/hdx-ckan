"use strict";

ckan.module('contribute_flow_main', function($, _) {
	return {
		initialize : function() {
            var sandbox = this.sandbox;
            var formId = this.options.form_id;
            var formBodyId = this.options.form_body_id;
            var dataset_id = this.options.dataset_id;
            var request_url = this.options.request_url;
            var contributeGlobal = {
                'getDatasetIdPromise': function() {
                    var deferred = new $.Deferred();

                    if ( !this.hasOwnProperty('_datasetId')) { // This is the first time that we look for the ID

                        if ( dataset_id ) { // If we're in "edit" mode the ID was injected in options
                            this._datasetId = dataset_id;
                            deferred.resolve(this._datasetId);
                        }
                        else {  // We're in the "new" mode and we need to create the initial dataseet
                            var formDataArray = this.getFormValues('generate-dataset-id-json');
                            var promise = $.post(request_url, $.param(formDataArray));
                            $.when(promise).done(
                                function (data, status, xhr) {
                                    if (data.data && data.data.id) {
                                        contributeGlobal._datasetId = data.data.id;
                                        deferred.resolve(data.data.id);
                                    }
                                    else {
                                        deferred.resolve(null);
                                    }
                                }
                            );
                        }
                    }
                    else { // We already have the dataset ID
                        deferred.resolve(this._datasetId);
                    }
                    return deferred.promise();
                },
                'saveDatasetForm': function() {
                    var formDataArray = this.getFormValues('update-dataset-json');
                    var datasetIdPromise = this.getDatasetIdPromise();
                    var deferred = new $.Deferred();
                    $.when(datasetIdPromise).done(
                        function(datasetId){
                            if (datasetId) {
                                formDataArray.push({'name': 'id', 'value': datasetId});
                            }
                            $.post(request_url, formDataArray,
                                function(data, status, xhr) {
                                    deferred.resolve(data, status, xhr);
                                }
                            );
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
                }
            };
            window.hdxContributeGlobal = contributeGlobal;
            sandbox.publish('hdx-contribute-global-created', window.hdxContributeGlobal);

            // Submit the form via Ajax
            $("#" + formId).submit(
              function(e) {
                  var promise = contributeGlobal.saveDatasetForm();
                  promise.done(
                      function(data, status, xhr) {
                          var resetMessage = { type:'reset' };
                          sandbox.publish('hdx-form-validation', resetMessage);
                          if (data.error_summary){
                              var sumMessage = {
                                  'type': 'new_summary',
                                  'elementName': 'error_block',
                                  'errorBlock': data.error_summary
                              };
                              sandbox.publish('hdx-form-validation', sumMessage);
                          }
                          if (data.errors) {
                              for (var key in data.errors ) {
                                  var errorList = data.errors[key];
                                  for (var i=0; i<errorList.length; i++) {
                                      var message = {
                                          type: 'new',
                                          elementName: key,
                                          errorInfo: errorList[i]
                                      };
                                      sandbox.publish('hdx-form-validation', message);
                                  }
                              }
                          }
                          else {
                              //Form submitted succesfully, go to some URL
                          }
                      }
                  );
                  e.preventDefault();
              }
            );
        },
        options: {
            form_id: 'create_dataset_form',
            form_body_id: 'contribute-flow-form-body',
            request_url: '/contribute/new',
            dataset_id: null
        }

	};
});
