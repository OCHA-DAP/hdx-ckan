$(function(){

    /*
        A Backbone module for work with CKAN Package Resources for the HDX
        Contribute Flow.

        TODO:
        - Handle server validation errors on create/update of resources
        - decide what user action submits create/update requests (button
          click?, change events?)
    */

    // MODELS

    var Resource = Backbone.Model.extend({

        // A model for CKAN resources. Most of the stuff here is to align
        // Backbone verbs with the CKAN api endpoints.
        fileAttribute: 'upload',

        defaults: {
            //'action_btn_label': 'Update',
            //'action_btn_class': 'update_resource'
        },

        methodToURL: {
            'create': '/api/action/resource_create',
            'read': '/api/action/resource_show?id=',
            'patch': '/api/action/resource_patch?id=',
            'update': '/api/action/resource_update?id=',
            'delete': '/api/action/resource_delete'
        },

        sync: function(method, model, options) {
            options = options || {};
            options.emulateHTTP = true;

            options.url = model.methodToURL[method.toLowerCase()];

            if (_.contains(['read', 'update', 'patch'], method)) {
                options.url += model.id;
            } else if (method == 'delete') {
                options.data = JSON.stringify({id: model.id});
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
        }
    });

    var PackageResources = Backbone.Collection.extend({
        // A collection of resources for a package.
        model: Resource,

        initialize: function(models, options) {
            this.package_id = options.package_id;
        },

        url: function() {
            return '/api/action/package_show?id=' + this.package_id;
        },

        parse: function(data) {
            return data.result.resources;
        }
    });


    // VIEWS

    var PackageResourcesListView = Backbone.View.extend({
        el: '#resource-list',

        initialize: function() {
            if (this.collection.package_id != null){
                this.collection.fetch({
                success: function(){
                    this.render();
                }.bind(this),
                error: function(e){
                    console.log('Cannot render: ' + e);
                }.bind(this)});
            }
            this.items = [];
            this.listenTo(this.collection, 'sync', this.render);
            this.listenTo(this.collection, 'add', this.addOne);
        },

        render: function() {
            this.$el.empty();
            this.collection.each(function(resource) {
                this.addOne(resource);
            }, this);
            return this;
        },

        addOne: function(resource){
            // console.log(resource);
            var view = new ResourceItemView({model: resource});
            this.$el.append(view.render().el);
        }
    });

    var ResourceItemView = Backbone.View.extend({
        // A template view for each Resource.
        tagName: 'div',
        className: 'drag-drop-component source-file',
        template: _.template($('#resource-item-tmpl').html()),

        events: {
            'click .update_resource': 'onUpdateBtn',
            'click .delete_resource': 'onDeleteBtn',
            'change .resource_file_field': 'onFileChange',
            'change input[type=radio].resource-source': 'onSourceChange',
            'change .source-file-fields .form-control': 'onFieldEdit',
            'click .dropbox a': 'onDropboxBtn',
            'click .googledrive a': 'onGoogleDriveBtn'
        },

        initialize: function() {
            this.model.view = this;
            this.listenTo(this.model, "change", this.render);
            this.listenTo(this.model, "destroy", this.remove);

            this.googlepicker = this.initGooglePicker();
        },

        initGooglePicker: function() {
            var picker = new FilePicker({
                apiKey: 'AIzaSyDI2YqaXNwndxy6UEisT-5fUeJ2FMtz0VY',
                clientId: '378410536565-mvin02sm8rbr0f8rq9q9injarh93ego4.apps.googleusercontent.com',
                scope: 'https://www.googleapis.com/auth/drive.readonly',
                onSelect: this.cloudFileURLSelected.bind(this)
            });
            return picker;
        },

        render: function() {
            var html = this.template(this.model.attributes);
            this.$el.html(html);
            return this;
        },

        onSourceChange: function(e){
            this._setUpForSourceType("source-" + e.target.value);
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
            this.model.set(e.target.name, e.target.value);
        },

        onFileChange: function(e) {
            // If a file has been selected, set up interface with file path.
            this._setUpWithPath($(e.currentTarget).val(), true);
            this._setUpForSourceType("source-file-selected");
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

        createResource: function(package_id, collection) {
            // Add a new Resource to the collection arg with data from this
            // view's form fields.

            // Get the serialised create form.
            var create_form_array = this.$(':input').serializeArray();
            // Serialize in the correct JSON format.
            var form_data = {package_id: package_id, format: 'txt'};
            _.map(create_form_array, function(x){form_data[x.name] = x.value;});

            var deferred = new $.Deferred();

            var resource = new Resource(form_data);
            resource.set('upload', this.$('.resource_file_field')[0].files[0]);
            resource.save(form_data, {
                wait: true,
                success: function(model, response, options) {
                    // console.log('successfully saved model');
                    this.$(':input').val('');
                    //collection.add(resource);
                    if (response.success){
                        deferred.resolve(response.result.id);
                    } else {
                        deffered.reject(response.result);
                    }
                }.bind(this),
                error: function(model, response, options) {
                    // ::TODO:: Handle validation errors returned by server here.
                    console.log('Could not create the resource');
                    console.log(response.responseJSON.error);
                }.bind(this)
            });

            return deferred;
        },

        deleteResource: function(){
            this.remove();
            //check if resource was created and then
            if (this.model.id)
               this.model.destroy();
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
            this._setUpForSourceType("source-file-selected");
            // switch resource-source radio to URL input
            this.$('input:radio.resource-source[value=url]').prop('checked', true);
        },

        _setUpForSourceType: function(source_class) {
            // Set up interface for the source type based on source_class.
            var source_classes = ['source-url', 'source-file', 'source-file-selected'];
            $.each(source_classes, function(i, v){
                this.$el.removeClass(v);
            }.bind(this));
            this.$el.addClass(source_class);
        },

        _setUpWithPath: function(path, use_short_url, filename) {
            // Set up interface for the given path. Either a url, or filepath.
            // If use_short_url is true, populate the model's `url` with the
            // filename rather than the full url (used for file uploads). Use
            // `filename` as the model name if passed.
            var name = filename || path.split('\\').pop().split('/').pop();
            var url = use_short_url ? name : path;
            this.model.set('url', url);
            if (!this.model.get('name')) {
                this.model.set('name', name);
            }
        }
    });

    var AppView = Backbone.View.extend({

        // The main app to kick things off, and manage the create widget.

        el: '#resource-app',

        events: {
            'click .add_new_resource': 'onCreateBtn'
        },

        initialize: function(options) {
            var sandbox = options.sandbox;
            this.resourceListView = undefined;
            var package_id = null; //TODO: on edit we should have the package id
            var resources = new PackageResources(null, {package_id: package_id});
            this.resources = resources;
            this.resourceListView = new PackageResourcesListView({collection: resources});

            // Listen for the hdx-contribute-global-created notification...
            sandbox.subscribe('hdx-contribute-global-created', function (global) {
                // ... when ready, get the contribute_global object.
                this.contribute_global = global;
                this.contribute_global.setResourceModelList(this.resources);

                global.getResourceSaveStartPromise()
                    .then(function(){
                        return this.contribute_global.getDatasetIdPromise();
                    }.bind(this))
                    .then(function(package_id){
                        var promiseList = [];
                        this.resources.each(function(model){
                            model.set('package_id', package_id);
                            //console.log(JSON.stringify(model));
                            var promise = model.view.createResource(package_id);
                            promiseList.push(promise);
                        });
                        return $.when.apply($, promiseList);
                    }.bind(this))
                    .then(function(){
                        // debugger;
                        this.contribute_global.browseToDataset();
                    }.bind(this),
                    function (error){
                        console.error("error while uploading resources");
                    });
            }.bind(this));
            //this._setUpCreateResourceEl();
        },

        onCreateBtn: function(e) {
            var data = {
                //id: 'new',
                position: this.resources.length + 1,
                url: '',
                format: '',
                description: '',
                //action_btn_label: 'Upload',
                //action_btn_class: 'create_resource'
            };
            var newResourceModel = new Resource(data);
            this.resources.add(newResourceModel);

            // console.log(this.resources);
        }
    });

    var sandbox = ckan.sandbox();
    this.app = new AppView({sandbox: sandbox});
}());
