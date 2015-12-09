"use strict";

ckan.module('contribute_flow_main', function($, _) {
	return {
		initialize : function() {
            var formId = this.options.form_id;
            var contributeGlobal = {
                'getDatasetIdPromise': function() {
                    var deferred = new $.Deferred();
                    if ( !this.hasOwnProperty('_datasetId')) {
                        var promise = $.post('/contribute/new', this.getFormValues());
                        $.when(promise).done(function(data, status, xhr) {
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
                    else {
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
            form_id: 'create_dataset_form'
        }

	};
});