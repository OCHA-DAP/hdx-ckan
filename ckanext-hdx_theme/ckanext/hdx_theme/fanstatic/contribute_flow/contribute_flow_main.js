"use strict";

ckan.module('contribute_flow_main', function($, _) {
	return {
		initialize : function() {
            var sandbox = this.sandbox;
            var formId = this.options.form_id;
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
                            formDataArray.push({'name':'id', 'value': datasetId});
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
                    var formSelector = "#" + formId;
                    var modifiedFormDataArray = [
                        {
                            'name':'save',
                            'value': save_mode
                        }
                    ];
                    var formDataArray = $("#create_dataset_form").serializeArray();
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
                  contributeGlobal.saveDatasetForm();
                  e.preventDefault();
              }
            );
        },
        options: {
            form_id: 'create_dataset_form',
            request_url: '/contribute/new',
            dataset_id: null
        }

	};
});
