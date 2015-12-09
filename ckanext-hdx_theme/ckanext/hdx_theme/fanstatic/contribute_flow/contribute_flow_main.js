"use strict";

ckan.module('contribute_flow_main', function($, _) {
	return {
		initialize : function() {
            var formId = this.options.form_id;
            var dataset_id = this.options.dataset_id;
            var contributeGlobal = {
                'getDatasetIdPromise': function() {
                    var deferred = new $.Deferred();

                    if ( !this.hasOwnProperty('_datasetId')) { // This is the first time that we look for the ID

                        if ( dataset_id ) { // If we're in "edit" mode the ID was injected in options
                            this._datasetId = dataset_id;
                            deferred.resolve(this._datasetId);
                        }
                        else {  // We're in the "new" mode and we need to create the initial dataseet
                            var promise = $.post('/contribute/new', this.getFormValues());
                            $.when(promise).done(function (data, status, xhr) {
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
                'getFormValues': function() {
                    var formSelector = "#" + formId;
                    var modifiedFormDataArray = [
                        {
                            'name':'save',
                            'value': 'generate-dataset-id-json'
                        }
                    ];
                    var formDataArray = $("#create_dataset_form").serializeArray();
                    for (var i=0; i<formDataArray.length; i++) {
                        var item = formDataArray[i];
                        if (item.value) {
                            modifiedFormDataArray.push(item);
                        }
                    }
                    return $.param(modifiedFormDataArray);
                }
            };
            window.hdxContributeGlobal = contributeGlobal;

        },
        options: {
            form_id: 'create_dataset_form',
            dataset_id: null
        }

	};
});