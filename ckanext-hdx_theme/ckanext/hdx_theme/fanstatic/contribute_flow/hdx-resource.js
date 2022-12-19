$(function(){

    /*
        A Backbone module for work with CKAN Package Resources for the HDX
        Contribute Flow.

        TODO:
        - Handle server validation errors on create/update of resources
    */

    // CONSTANTS
    var URLS = {
        'guessFormat': '/api/action/hdx_guess_format_from_extension?q='
    };
    var WARNINGS = {
        'archive': 'Please indicate the primary format of the data files inside your compressed file.'
    };
    var ARCHIVE_EXTENSIONS = ['zip', '7z', 'tar', 'rar'];

    // MODELS

    var Resource = Backbone.Model.extend({

        // A model for CKAN resources. Most of the stuff here is to align
        // Backbone verbs with the CKAN api endpoints.
        fileAttribute: 'upload',

        methodToURL: {
            'create': '/api/action/resource_create',
            'read': '/api/action/resource_show?id=',
            'patch': '/api/action/resource_patch?id=',
            'update': '/api/action/resource_update?id=',
            'delete': '/api/action/resource_delete'
        },

        sync: function(method, model, options) {
            // console.log('syncing resource with method: ' + method);
            options = options || {};
            options.emulateHTTP = true;

            options.url = model.methodToURL[method.toLowerCase()];

            if (_.contains(['read', 'update', 'patch'], method)) {
                options.url += model.id;
            } else if (method == 'delete') {
                options.data = JSON.stringify({
                    id: model.id,
                    batch_mode: 'DONT_GROUP'
                });
            }
            return Backbone.sync.apply(this, arguments);
        },

        parse: function(data) {
            // Check whether the data has a 'package_id' key to determine if we've
            // been passed an object directly. Otherwise, we may have the results
            // of a resource_show, in which case the data is the value of the
            // 'result' key.
            var ret;
            if (_.has(data, 'package_id')) {
                ret = data;
            } else if (_.has(data, 'result')) {
                ret = data.result;
            }
            return ret;
        },

        hashResource: function() {
            var newUpload = this.get('upload') ? 'true' : 'false';
            var dpe = this.get('dataset_preview_enabled') === '1' || this.get('dataset_preview_enabled') === 'True' ? 'True' : 'False';
            var microdata = this.get('microdata') ? 'true' : 'false';
            var properties = [
                this.get('name'), this.get('format'), this.get('url'),
                this.get('description'), this.get('url_type'), this.get('resource_type'),
                dpe,
                newUpload,
                microdata
            ];

            var hashCode = hdxUtil.compute.strListHash(properties);

            console.log('Hash code for ' + this.get('name') + ' is ' + hashCode);
            return hashCode;

        },

        initialize: function() {
            this.set('originalHash', this.hashResource());
            this.set('batch_mode', 'DONT_GROUP');

            // this.on('progress', function (percentage) {
            //     var position = this.get('position') + 1;
            //     console.log('Percentage is ' + percentage + ' for ' + position)
            // })
        }

    });

    var PackageResources = Backbone.Collection.extend({
        // A collection of resources for a package.
        model: Resource,
        comparator: 'position',
        removedModels: [],  // An array for models set to be removed during next sync.
        orderChanged: false,  // A flag to determine whether the collection order has changed.

        initialize: function(models, options) {
            this.package_id = options.package_id;

            sandbox.subscribe('hdx-form-validation', function (message) {
                if (message.elementName == 'error_block' && 'Resources' in message.errorBlock
                    && $.type(message.errorBlock.Resources)!='string' ) {
                    $.each(message.errorBlock.Resources, function(k, o) {
                        var resource_index = k.split(" ").pop();
                        var resource_field_errors = o;
                        this.at(resource_index).view.display_errors(resource_field_errors);
                    }.bind(this));
                }
            }.bind(this));

            sandbox.subscribe('hdx-resource-information', function (message) {
                if (message.type == 'dataset_preview_resource_change' && message.newValue!=null) {
                    var resIdx = Number(message.newValue);
                    var modelsList = this.models;
                    for(var i=0; i<modelsList.length; i++){
                        // modelsList[i].attributes['dataset_preview_enabled'] = '0';
                        modelsList[i].set('dataset_preview_enabled', '0');
                    }
                    if(!isNaN(resIdx)){
                        modelsList[resIdx].set('dataset_preview_enabled', '1');
                    }

                }
            }.bind(this));
        },

        url: function() {
            return '/api/action/package_show_edit?id=' + this.package_id;
        },

        parse: function(data) {
            return data.result.resources;
        },

        saveAll: function(pkg_id) {
            var deferred = new $.Deferred();
            var index = 0;
            var resources = this;

            var saveResources = function () {
                /**
                 * We need to save the resources sequentially to avoid
                 * race conditions on the server side
                 */
                this.trigger('upload event', 'Saving resource ' + (index+1) +  '...');
                var model = resources.models[index];
                model.set('package_id', pkg_id);
                //if ( model.get('resource_type') == 'file.upload' && !model.get('upload')){
                //    model.set('upload', '');
                //}
                if("fs_check_info" in model.attributes){
                  delete model.attributes['fs_check_info'];
                }
                var promise;
                if ( model.get('originalHash') != model.hashResource() ){
                    promise = model.save();
                }
                else {
                    promise = $.Deferred().resolve().promise();
                }
                if (index + 1 < resources.length) {
                    index++;
                    promise.then(saveResources);
                } else {
                    promise.then(function(){
                        deferred.resolve();
                    });
                }
            }.bind(this);

            if (resources.length)
                saveResources();
            else
                deferred.resolve();

            return deferred.promise();
        },

        destroyRemovedModels: function() {
            // Sequentially destroy all models on the server that are in the
            // removedModels array, i.e. marked for deletion.

            var deferred = new $.Deferred();
            var index = 0;
            var resources = this;

            this.trigger('upload event', 'Almost done...');

            var destroyResources = function() {
                var model = resources.removedModels[index];
                var promise = model.destroy();
                // `destroy` returns `false` for unpersisted models. Set
                // `promise` to an immediately resolved promise.
                if (promise === false) promise = $.when();
                if (index + 1 < resources.removedModels.length) {
                    index++;
                    promise.then(destroyResources);
                } else {
                    promise.then(function() {
                        deferred.resolve();
                    });
                }
            };

            if (resources.removedModels.length)
                destroyResources();
            else
                deferred.resolve();

            return deferred.promise();
        },

        resourceReorder: function() {
            // If the models in this collection have been reordered, update
            // them on the server.
            if (this.orderChanged && this.package_id) {
                // pluck the resource ids from the models
                var resource_ids = this.pluck("id");

                url = '/api/action/package_resource_reorder';
                options = {
                    url: url,
                    type: 'POST',
                    data: JSON.stringify({
                        id: this.package_id,
                        order: resource_ids,
                        batch_mode: 'DONT_GROUP'
                    }),
                    success: function(model, response, options) {
                        this.orderChanged = false;  // reset flag
                    }.bind(this),
                    error: function(response) {
                        console.log('Error: could not reorder resources:');
                        console.log(response.responseJSON.error);
                    }.bind(this)
                };
                return (this.sync || Backbone.sync).call(this, null, this, options);
            }
            // Return a resolved promise if we don't need to change the order.
            return $.when();
        }

    });


    // VIEWS

    var PackageResourcesListView = Backbone.View.extend({
        el: '#resource-list',

        events: {
            'sort-updated': 'onSortOrderChange'
        },

        initialize: function(options) {
            this.contribute_global = options.contribute_global;
            this.resource_list = this.$('.resources');
            // Fetch the collection if we have a package_id and no models.
            if (this.collection.package_id !== null && this.collection.length === 0){
                this.collection.fetch({
                success: function(){
                    // console.log('Fetched the collection.');
                }.bind(this),
                error: function(e){
                    console.log('Cannot render: ' + e);
                }.bind(this)});
            } else if (this.collection.length > 0) {
                this.render();
                this.updateTotal();
            }
            this.listenTo(this.collection, 'sync add remove reset change', this.generateDatasetPreviewOptions);
            this.listenTo(this.collection, 'sync add remove reset', this.render);
            this.listenTo(this.collection, 'add remove reset', this.updateTotal);
            this.listenTo(this.collection, 'remove', this.onSortOrderChange);
            this.listenTo(this.collection, 'upload event', this.showUserWaitingMessage);

            // Initialize drag n drop sorting
            Sortable.create(this.resource_list[0], {
                animation: 250,
                ghostClass: "drag-drop-ghost",
                handle: ".drag-handle",
                scroll: true,
                onUpdate: function (e){
                    this.$el.trigger('sort-updated');
                }.bind(this),
                onStart: function(e){
                    console.log("Drag Area Disable");
                    this.$el.find(".drag-drop-component").trigger("drag-area-disable");
                }.bind(this),
                onEnd: function(e){
                    console.log("Drag Area Enable");
                    this.$el.find(".drag-drop-component").trigger("drag-area-enable");
                }.bind(this)
            });
        },

        render: function() {
            this.resource_list.empty();
            this.collection.each(function(resource) {
                this.addOne(resource);
            }, this);
            return this;
        },

        generateDatasetPreviewOptions: function(options) {
            if(options.changed && !options.changed.dataset_preview_enabled){
                this.contribute_global.generateDatasetPreviewOptions(this.collection);
            }
        },

        addOne: function(resource) {
            var view = new ResourceItemView({model: resource});
            this.listenTo(view, 'upload progress', this.showUserWaitingMessage);
            this.resource_list.append(view.render().el);
        },

        updateTotal: function() {
            var total_text = this.collection.length == 1 ? "1 Resource" : this.collection.length + " Resources";
            this.$('.resources_total').text(total_text);
        },

        showUserWaitingMessage: function(msg) {
          this.contribute_global.controlUserWaitingWidget(true, msg);
          console.log('User waiting msg: ' + msg);
        },

        onSortOrderChange: function(e) {
            // Sort order may be changed either by drag n drop reordering, or
            // by removing a resource.
            var has_changed = false;
            this.collection.each(function(resource, i) {
                var new_pos = resource.view.$el.index();
                if (resource.get('position') != new_pos) {
                    has_changed = true;
                    resource.set({position: new_pos});
                }
            });
            if (has_changed) {
                this.collection.orderChanged = true;
                this.collection.sort();
                this.render();
            }
        }
    });

    function defaultGoogleDriveOptions() {
        return {
            apiKey: 'AIzaSyDI2YqaXNwndxy6UEisT-5fUeJ2FMtz0VY',
            clientId: '378410536565-mvin02sm8rbr0f8rq9q9injarh93ego4.apps.googleusercontent.com',
            scope: 'https://www.googleapis.com/auth/drive.readonly',
        };
    }

    var ResourceItemView = Backbone.View.extend({
        // A template view for each Resource.
        tagName: 'div',
        className: 'drag-drop-component source-file',
        template: _.template($('#resource-item-tmpl').html()),

        // prevFileExtension: null,

        events: {
            'click .update_resource': 'onUpdateBtn',
            'click .delete_resource': 'onDeleteBtn',
            //'change .resource_file_field': 'onFileChange',
            'change input[type=radio].resource-source': 'onSourceChange',
            'change input[type=checkbox][name=pii]': 'onPiiChange',
            'change input[type=checkbox][name=microdata]': 'onMicrodataChange',
            'change .source-file-fields .form-control': 'onFieldEdit',
            'click .dropbox a': 'onDropboxBtn',
            'click .googledrive a': 'onGoogleDriveBtn'
        },

        initialize: function() {
            this.model.view = this;
            this.listenTo(this.model, 'progress', function(fraction){
                var idx = this.model.get('position') + 1;
                var percentage = Math.floor(fraction * 100);
                this.trigger('upload progress', 'Saving resource ' + idx +  ': ' + percentage + '%');
            });

            var dragGhost, dragParent;

            // Initially users should be able to drag and drop files
            this.dragAreaEnabled = true;

            this.el.addEventListener("dragstart", function(e) {
                dragGhost = document.createElement("div");
                $(dragGhost).addClass("hdx-form");
                $(dragGhost).removeClass("drag-drop-ghost");
                $(dragGhost).css("width", $(e.target).parent().width());
                $(dragGhost).css("position","absolute");
                $(dragGhost).css("top","0");
                $(dragGhost).css("left","0");
                dragGhost.appendChild(e.target.cloneNode(true));

                var p = $(e.target).offset();
                var x = e.pageX - p.left;
                var y = e.pageY - p.top;
                dragParent = e.target;
                dragParent.appendChild(dragGhost);
                e.dataTransfer.setDragImage(dragGhost, x, y);
                e.dataTransfer.ghostImage = dragGhost;
            }, false);

            this.el.addEventListener("dragend", function(e) {
                console.log("Removing ghost!");
                //dragParent.removeChild(dragGhost);
            }, false);

            //this.listenTo(this.model, "change", this.render);
            this.listenTo(this.model, "destroy", this.remove);
            this.$el.on("drag-area-disable", function(){
                this.dragAreaEnabled = false;
            }.bind(this));
            this.$el.on("drag-area-enable", function(){
                this.dragAreaEnabled = true;
            }.bind(this));

            this.googlepicker = this.initGooglePicker();

            if (!this.model.id) {
                this._guessFormat();
            }
        },

        initGooglePicker: function() {
            var options = defaultGoogleDriveOptions();
            options.onSelect = this.cloudFileURLSelected.bind(this);
            var picker = new FilePicker(options);
            return picker;
        },

        _convertToBoolean: function (value) {
          if (value === "True")
            return true;
          if (value === "False")
            return false;
          return value;
        },

        render: function () {
            var template_data = _.clone(this.model.attributes);
            template_data.template_position = this.model.collection.indexOf(this.model);
            template_data.lower_case_format = template_data.format ? template_data.format.toLowerCase() : null;
            template_data.pii = this._convertToBoolean(this.model.get('pii'));
            template_data.microdata = this._convertToBoolean(this.model.get('microdata'));
            var html = this.template(template_data);
            this.$el.html(html);

            /* Initializing CKAN js modules inside this VIEW */
            this.$el.find('[data-module]').each(
                function (i, el) {
                    //console.log("Initializing ckan module for " + $(el).prop('outerHTML'));
                    ckan.module.initializeElement(el);
                }
            );
            this._setUpDragAndDrop();

            var modelUrlType = this.model.get('url_type');
            var modelResourceType = this.model.get('resource_type');
            if (modelUrlType || modelResourceType) {
                if (modelUrlType == 'upload' || modelResourceType == 'file.upload')
                    this._setUpForSourceType('source-file-selected');
                else
                    this._setUpForSourceType('source-url');
            } else {
                this._setUpForSourceType('source-file');
            }

            if (template_data.pii && template_data.pii === 'true') {
              this.$el.addClass('orange');
            }

            this._showFormatWarningIfNeeded();

            return this;
        },

        display_errors: function(field_errors) {
            _.each(field_errors, function(error_text, field_name) {
                var error_block = this.$("[name='" + field_name + "'] ~ .error-block");
                error_block.html(error_text);
                if (error_text) {
                    var parent_el = this.$("[name='" + field_name + "']").parent('.controls');
                    parent_el.addClass('error');
                    parent_el.closest('.source-file').addClass('error');
                }
            }.bind(this));

            //this._setUpForSourceType('source-url');
        },

        onSourceChange: function(e){
            var sourceClass = "source-" + e.target.value;
            var changedType = sourceClass === "source-url" ? "api" : "upload";
            var currentUrlType =  this.model.get('url_type');

            if ( currentUrlType && currentUrlType != changedType ) {
                this.model.unset('upload', {silent: true});
                this.model.unset('url_type', {silent: true});
                this.model.unset('resource_type', {silent: true});
                this.model.set('url', '');
            }
            this._setUpForSourceType(sourceClass);
        },
        _updatePiiCount: function(value){
          let terms = $("#terms-of-service-label");
          let count = parseInt(terms.attr("piiCount"));
          if (!count) {
            count = 0;
          }
          count = Math.max(0, count + value);
          terms.attr("piiCount", count);
          if (count > 0) {
            terms.addClass('disabled');
            terms.find('input[type="checkbox"]').prop("disabled", true);
            terms.find('input[type="checkbox"]').prop("checked", false).change();
          } else {
            terms.removeClass('disabled');
            terms.find('input[type="checkbox"]').prop("disabled", false);
          }
        },

        onPiiChange: function (e) {
          const value = e.target.checked;
          this.model.set('pii', value);
          this._updatePiiCount(value ? 1 : -1);
          $(e.target).closest('.controls').find('.item-description').toggle(value);
          $(e.target).closest('.drag-drop-component').toggleClass("orange", value);
        },

        onMicrodataChange: function (e) {
          const value = e.target.checked;
          this.model.set('microdata', value);
          $(e.target).closest('.controls').find('.item-description').toggle(value);
        },

        onUpdateBtn: function(e) {
            this.updateResource();
        },

        onDeleteBtn: function(e){
            this.deleteResource();
        },

        onDropboxBtn: function(e) {
            this.createDropboxChooser();
            e.preventDefault();
        },

        onGoogleDriveBtn: function(e) {
            this.createGoogleDrivePicker();
            e.preventDefault();
        },

        onFieldEdit: function(e) {
          var modifiedFieldName = e.target.name;
          this.model.set(modifiedFieldName, e.target.value);

            if (modifiedFieldName === 'name' || modifiedFieldName === 'url') {
                this._guessFormat();
                this._showFormatWarningIfNeeded();
            }
            if (modifiedFieldName === 'format') {
              this._showFormatWarningIfNeeded();
            }

        },
        //onFileChange: function(e) {
        //    this._onFileChange($(e.currentTarget).val(), this.$('.resource_file_field')[0].files[0]);
        //},

        _onFileChange: function(file){
            // If a file has been selected, set up interface with file path.
            this.model.set('format', '');
            this._setUpWithPath(file.name, true, null, false, file);
            this._setUpForSourceType("source-file-selected");
            this.render();
            this._guessFormat();
        },

        onFormatGetsFocus: function(e){
            console.log('initializing autocomplete for format');
            if ( !this.hasOwnProperty('formatInitialized') || !this.formatInitialized ){
                ckan.module.initializeElement(e.currentTarget);
                this.formatInitialized = true;
            }
        },


        updateResource: function() {
            // Update the Resource from this view's form fields.

            var update_form_array = this.$el.find(':input').serializeArray();

            // Serialize in the correct JSON format.
            var form_data = {format: 'txt'};
            _.map(update_form_array, function(x){form_data[x.name] = x.value;});

            this.model.set('upload', this.$('.resource_file_field')[0].files[0]);
            this.model.save(form_data, {
                wait: true,
                success: function(model, response, options) {
                    // console.log('successfully updated model');
                }.bind(this),
                error: function(model, response, options) {
                    // ::TODO:: Handle validation errors returned by server here.
                    console.log('Could not update the resource');
                    console.log(response.responseJSON.error);
                }.bind(this)
            });
        },

        deleteResource: function(){
            // Remove model from collection and push it to the removedModels
            // array. These will be destroyed if the dataset update is
            // submitted.
            var collection = this.model.collection;
            collection.removedModels.push(collection.remove(this.model));
        },

        createDropboxChooser: function() {
            options = {
                success: function(files) {
                    var file = files[0];
                    this.cloudFileURLSelected(file.link, file.name);
                }.bind(this),
                linkType: "preview"
            };
            Dropbox.choose(options);
        },

        createGoogleDrivePicker: function() {
            this.googlepicker.open();
        },

        cloudFileURLSelected: function(url, filename) {
            this._setUpWithPath(url, false, filename);
            this._setUpForSourceType("source-url");
            // focus on first text field
            this.$('input:text')[0].focus();
            this.render();
        },

        _setUpDragAndDrop: function(){
            var widget = this.$el.find(".drag-drop-area"),
                mask = widget.find(".drop-here-mask"),
                browseButton = this.$el.find(".browse-button input[type='file']");

            var handleFiles = function(files){
                if (files.length !== 1){
                    alert("Please choose only one file!");
                    return;
                }
                this._onFileChange(files[0]);
            }.bind(this);

            widget
                .on('drag dragstart dragend dragover dragenter dragleave drop', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                })
                .on('dragover dragenter', function(e) {
                    if (this.dragAreaEnabled){
                        mask.show();
                        widget.addClass("drop-incoming");
                    }
                }.bind(this));
            mask
                .on('dragend dragleave', function(e) {
                    if (this.dragAreaEnabled){
                        mask.hide();
                        widget.removeClass('drop-incoming');
                    }
                }.bind(this))
                .on('drop', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    widget.removeClass('drop-incoming');
                    handleFiles(e.originalEvent.dataTransfer.files);
                });
            browseButton.on('change', function(e){
                handleFiles(this.files);
            });

        },

        _setUpForSourceType: function(source_class) {
            // Set up interface for the source type based on source_class.
            var source_classes = ['source-url', 'source-file', 'source-file-selected'];

            if (source_class === "source-url"){
                // switch resource-source radio to URL input
                this.$('input:radio.resource-source[value=url]').prop('checked', true);
                this.model.unset('upload', {silent: true});

                // change the model
                this.model.set('url_type', 'api');
                this.model.set('resource_type', 'api');
                this.model.set('upload', null);

            }

            $.each(source_classes, function(i, v){
                this.$el.removeClass(v);
            }.bind(this));
            this.$el.addClass(source_class);
        },

        _setUpWithPath: function(path, use_short_url, filename, is_url, file) {
            // Set up interface for the given path. Either a url, or filepath.
            // If use_short_url is true, populate the model's `url` with the
            // filename rather than the full url (used for file uploads). Use
            // `filename` as the model name if passed.

            is_url = typeof is_url !== 'undefined' ? is_url : true;
            var resource_type = is_url ? 'api' : 'file.upload';
            var url_type = is_url ? 'api' : 'upload';

            var name = filename || path.split('\\').pop().split('/').pop();
            var url = use_short_url ? name : path;
            if (file)
                this.model.set('upload', file);
            this.model.set('url_type', url_type);
            this.model.set('resource_type', resource_type);
            this.model.set('url', url);
            //if (!this.model.get('name')) {
            //    this.model.set('name', name);
            //}
            this.model.set('name', name);
        },
        _showFormatWarningIfNeeded: function () {

            var extension = this._computeExtension();

            var isArchive = ARCHIVE_EXTENSIONS.indexOf(extension) >= 0;
            // var wasArchive = ARCHIVE_EXTENSIONS.indexOf(this.prevFileExtension) >= 0;

            if (isArchive && !this.model.get('format') ) {
                this.display_errors({'format': WARNINGS.archive});
            }
            else if (this.model.get('format') || !isArchive) {
                this.display_errors({'format': ''});
            }
            // this.prevFileExtension = extension;
        },
        _guessFormat: function() {
            var onSuccessSetFormat = function(data) {
                if (data.success === true && data.result) {
                    this.model.set('format', data.result);
                    this.render();
                }
            }.bind(this);
            var extension = this._computeExtension();
            $.get(URLS.guessFormat + extension, onSuccessSetFormat);
        },
        _computeExtension: function() {
            var __getExtension = function(url) {
                var extension = null;
                if (url) {
                    try {
                        var urlObj = new URL(url, 'https://data.humdata.org');
                        var lastIndex = urlObj.pathname.lastIndexOf('.');
                        if (lastIndex > 0 && lastIndex+1 < urlObj.pathname.length) {
                            extension = urlObj.pathname.substring(lastIndex+1).toLowerCase();
                        }
                    } catch (error) {
                        console.log(error);
                    }
                }
                return extension;
            }

            var extension = __getExtension(this.model.get('name')) || __getExtension(this.model.get('url'));

            return extension;
        }
    });

    var ResourceWidgetView = Backbone.View.extend({

        // The main app to kick things off, and manage the create widget.

        el: '#resource-widget',

        events: {
            'click .add_new_resource': 'onCreateBtn'
        },

        resourceDefaults: function () {
            return {
                //id: 'new',
                /* Internally the position will start from 0 like in CKAN. In template it is +1 */
                position: this.resourceCollection.length,
                url: '',
                format: '',
                pii: false,
                microdata: false,
                description: ''
            };
        },
        initialize: function(options) {
            var sandbox = options.sandbox;
            var data = options.data;
            this.resourceListView = undefined;

            // Listen for the hdx-contribute-global-created notification...
            sandbox.subscribe('hdx-contribute-global-created', function (global) {
                // ... when ready, get the contribute_global object.
                this.contribute_global = global;

                this.contribute_global.getDatasetIdPromise().then(
                    function(package_id){
                        this.resourceCollection = new PackageResources(data, {package_id: package_id});

                        ///* Have at least one empty resource in the form for a new dataset */
                        //if (this.resourceCollection.length == 0) {
                        //    this.resourceCollection.add(new Resource(this.resourceDefaults()));
                        //}

                        this.resourceListView = new PackageResourcesListView({
                            collection: this.resourceCollection,
                            contribute_global: this.contribute_global
                        });

                        this.contribute_global.setResourceModelList(this.resourceCollection);
                        this.contribute_global.generateDatasetPreviewOptions(this.resourceCollection);
                        this.contribute_global.controlUserWaitingWidget(false);
                    }.bind(this)
                );

                global.getResourceSaveStartPromise()
                    .then(function(){
                        return this.contribute_global.getDatasetIdPromise();
                    }.bind(this))
                    .then(function(package_id){
                      if (this.contribute_global.isRequestedData()){
                        return true;
                      }
                      else {
                        return this.resourceCollection.saveAll(package_id)
                        .then(function(){
                            return this.resourceCollection.destroyRemovedModels();
                        }.bind(this))
                        .then(function(){
                            return this.resourceCollection.resourceReorder();
                        }.bind(this));
                      }
                    }.bind(this))
                    .then(function(){
                        console.log('Browsing away ');
                        this.contribute_global.finishContributeFlow();
                    }.bind(this),
                    function (error){
                        console.error("error while uploading resources");
                    });


            }.bind(this));
        },

        onCreateBtn: function(e) {
            var data = this.resourceDefaults();
            var newResourceModel = new Resource(data);
            this.resourceCollection.unshift(newResourceModel);
            this.resourceListView.onSortOrderChange();
        },
        onFileViaDragAndDrop: function(file){
            var data = this.resourceDefaults();
            var newResourceModel = new Resource(data);
            newResourceModel.set("upload", file);
            newResourceModel.set("url_type", "upload");
            newResourceModel.set('resource_type', "file.upload");
            newResourceModel.set("name", file.name);
            newResourceModel.set("url", file.name);
            this.resourceCollection.add(newResourceModel);
        },
        onURLViaDragAndDrop: function(url, name){
            var data = this.resourceDefaults();
            var newResourceModel = new Resource(data);
            newResourceModel.set("url_type", "api");
            newResourceModel.set('resource_type', "api");
            newResourceModel.set("name", name);
            newResourceModel.set("url", url);
            this.resourceCollection.add(newResourceModel);
        }
    });

    var AppView = Backbone.View.extend({
        el: '#create-dataset-app',
        events: {
            'click .contribute-splash .google-drive': 'onGoogleDriveBtn',
            'click .contribute-splash .dropbox': 'onDropboxBtn',
            'click .contribute-splash .apis-urls': 'onApisURLsBtn'
        },
        initialize: function(options){
            this.googlepicker = this.initGooglePicker();
            this.resourceWidget = new ResourceWidgetView({sandbox: sandbox, data: initial_resource_data});

            /* Make sure that the close X is gray. Could be white if there was an edit action before. */
            $(".content i.close", window.top.document).removeClass("white");

            var isAdvancedUpload = function() {
                var div = document.createElement('div');
                return (('draggable' in div) || ('ondragstart' in div && 'ondrop' in div)) && 'FormData' in window && 'FileReader' in window;
            }();

            if (!isAdvancedUpload){
                //TODO: remove the drag&drop functionality + texts
                alert("Drag & drop is not supported in your browser!");
            }

            sandbox.subscribe('hdx-contribute-global-created', function (global) {
                // ... when ready, get the contribute_global object.
                this.contribute_global = global;

                this.contribute_global.getDatasetIdPromise().then(
                    function(package_id){
                        if (package_id != null){
                            this.goToStep2();
                        }
                    }.bind(this));
            }.bind(this));

            sandbox.subscribe('hdx-form-validation', function (message) {
              // ... when ready, get the contribute_global object.
              // this.contribute_global = global;
              //
              // this.contribute_global.getDatasetIdPromise().then(
              //     function(package_id){
              //         if (package_id != null){
              //             this.goToStep2();
              //         }
              //     }.bind(this));
              $('#dataset-is-public-description').toggle(message.type === 'private_changed' && message.newValue === 'public');
              if (message.type === 'private_changed' && message.newValue === 'requestdata') {
                // this.contribute_global.resourceModelList.models = [];
                this._prepareFormForMetadataOnly({isEdit: true}, true);
                var isMetadataOnly = $('input[name=_is_requestdata_type][value=true]');
                // if (isMetadataOnly.length === 1) {
                if(isMetadataOnly.length === 1 || this.contribute_global!=null && !this.contribute_global._datasetId){
                  var req_type_notification = $('#requestdata_type_notification');
                  req_type_notification.addClass('hdx-invisible-element');
                }
              }
              else{
                if(message.data!=null && message.data.data!=null && message.data.data.is_requestdata_type==='True'){
                  this._prepareFormForMetadataOnly({isEdit: true}, true);
                }
                else {
                  this._prepareFormForMetadataOnly({isEdit: true}, false);
                }
              }
            }.bind(this));

            var widget = $(".contribute-splash .drop-here.full-dataset-box"),
                mask = widget.find(".drop-here-mask"),
                browseButton = $(".contribute-splash .browse-button input[type='file']");

            var handleFiles = function(files){
                this.goToStep2();
                for (var i = 0; i < files.length; i++){
                    var file = files[i];
                    this.resourceWidget.onFileViaDragAndDrop(file);
                }
            }.bind(this);

            var handleDropEvent = function(e){
                console.log("4");
                e.preventDefault();
                e.stopPropagation();
                widget.removeClass('drop-incoming');
                handleFiles(e.originalEvent.dataTransfer.files);
            };

            widget
                .on('drag dragstart dragend dragover dragenter dragleave drop', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                })
                .on('dragover dragenter', function(e) {
                    mask.show();
                    widget.addClass("drop-incoming");
                })
                .on('drop', handleDropEvent);
            mask
                .on('dragend dragleave', function(e) {
                    mask.hide();
                    widget.removeClass('drop-incoming');
                })
                .on('drop', handleDropEvent);
            browseButton.on('change', function(e){
                handleFiles(this.files);
            });

            var addMetadataBtn = $('.contribute-splash .add-metadata-btn');

            addMetadataBtn.on('click', function() {
                this.goToStep2();
                var formSectionPrivacy = $('.form-privacy-section');
                var privacyPublicRadioBtn = formSectionPrivacy.find('input[type=radio][value=requestdata]');
                privacyPublicRadioBtn.click();
                this._prepareFormForMetadataOnly({isEdit: false}, true);
                var req_type_notification = $('#requestdata_type_notification');
                req_type_notification.addClass('hdx-invisible-element');

            }.bind(this));

            var isMetadataOnly = $('input[name=_is_requestdata_type][value=true]');

            // For already created datasets, if they are metadata-only adapt
            // the form
            if (isMetadataOnly.length === 1) {
                this._prepareFormForMetadataOnly({isEdit: true}, true);
                var req_type_notification = $('#requestdata_type_notification');
                req_type_notification.addClass('hdx-invisible-element');
            }
        },
        initGooglePicker: function() {
            var options = defaultGoogleDriveOptions();
            options.onSelect = this.cloudFileURLSelected.bind(this);
            options.multiselect = true;
            var picker = new FilePicker(options);
            return picker;
        },
        cloudFileURLSelected: function(url, filename) {
            this.goToStep2();
            this.resourceWidget.onURLViaDragAndDrop(url, filename);
        },
        onGoogleDriveBtn: function(e) {
            this.googlepicker.open();
            e.preventDefault();
        },
        onDropboxBtn: function(e) {
            options = {
                success: function(files) {
                    for (var i = 0; i < files.length; i++){
                        var file = files[i];
                        this.resourceWidget.onURLViaDragAndDrop(file.link, file.name);
                    }
                    this.goToStep2();
                }.bind(this),
                multiselect: true,
                linkType: "direct"
            };
            Dropbox.choose(options);
            e.preventDefault();
        },
        onApisURLsBtn: function(e){
            this.goToStep2();
            this.resourceWidget.onURLViaDragAndDrop("", "");
            e.preventDefault();
        },
        goToStep2: function () {
            $(".content i.close", window.top.document).addClass("white");
            $(".create-step1").hide();
            $(".create-step2").show();
        },
        _prepareFormForMetadataOnly: function(data, is_req_dataset) {
            var formSectionResources = $('.form-resources-section');
            var formSectionPrivacy = $('.form-privacy-section');
            var privacyPublicRadioBtn = formSectionPrivacy.find('input[type=radio][value=false]');
            var selectMethodology = $('#field_methodology');
            var methodologySelectModule = $('.methodology-select');
            var currentlySelectedMethodology = methodologySelectModule.find('.select2-chosen');
            var formBody = $('#contribute-flow-form-body');
            var selectUpdateFrequency = $('#field_data_update_frequency');
            var updateFrequencySelectModule = $('.update-frequency-select');
            var currentlySelectedUpdateFrequency = updateFrequencySelectModule.find('.select2-chosen');
            var selectTagsModule = $('.tags-select');
            var licenseField = $('.special-license');
            var selectFieldNames = $('.field-names-select');
            var selectFileTypes = $('.file-types-select');
            var selectNumOfRows = $('.num-of-rows-select');
            var isEdit = data.isEdit;
            var req_type_notification = $('#requestdata_type_notification');


            // // We set the type so that the right schema is used in the backend
            // formBody.append('<input type="hidden" name="is_requestdata_type" value="true" />');


            if(is_req_dataset) {
              // Resources are not required for metadata-only datasets
              formSectionResources.hide();
              // Hides the horizontal line
              formSectionResources.next().hide();
              // Hides the horizontal line
              formSectionResources.next().hide();

              // hide dataset preview
              $('#_dataset_preview').hide();

              // For some reason, when editing a dataset, the class wasn't
              // applied, that's why the timeout is needed.
              setTimeout(function () {

                // Methodology and Update frequency fields are not required in a
                // metadata-only dataset
                methodologySelectModule.removeClass('required');
                updateFrequencySelectModule.removeClass('required');

                selectTagsModule.addClass('required');
              }, 500);

              // License is not required as well
              licenseField.hide();

              // These are already created fields in the DOM, but they are
              // initially hidden, and are only shown for metadata-only datasets
              selectFieldNames.show();
              selectFileTypes.show();
              selectNumOfRows.show();
              req_type_notification.removeClass('hdx-invisible-element');
            }
            else{
              // Resources are not required for metadata-only datasets
              formSectionResources.show();
              // Hides the horizontal line
              formSectionResources.next().show();
              // Hides the horizontal line
              formSectionResources.next().show();

              // hide dataset preview
              $('#_dataset_preview').show();

              // For some reason, when editing a dataset, the class wasn't
              // applied, that's why the timeout is needed.
              // setTimeout(function () {
              //
              //   // Methodology and Update frequency fields are not required in a
              //   // metadata-only dataset
              //   methodologySelectModule.removeClass('required');
              //   updateFrequencySelectModule.removeClass('required');
              //
              //   selectTagsModule.addClass('required');
              // }, 500);

              // License is not required as well
              licenseField.show();

              // These are already created fields in the DOM, but they are
              // initially hidden, and are only shown for metadata-only datasets
              selectFieldNames.hide();
              selectFileTypes.hide();
              selectNumOfRows.hide();
              req_type_notification.addClass('hdx-invisible-element');
            }


        }
    });

    var sandbox = ckan.sandbox();
    var initial_resource_data = null;
    if ($('#resource-list-json').length > 0) {
        initial_resource_data = JSON.parse($('#resource-list-json').html());
    }
    this.app = new AppView({sandbox: sandbox, data: initial_resource_data});

}());
