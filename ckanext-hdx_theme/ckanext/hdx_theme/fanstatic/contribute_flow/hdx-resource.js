$(function(){

    /*
        A Backbone module for work with CKAN Package Resources for the HDX
        Contribute Flow.

        TODO:
        - Format select form widget for resource update
        - Handle server validation errors on create/update of resources
        - File browse upload
        - upload_type selector: url vs file browse
        - decide what user action submits create/update requests (button
          click?, change events?)

    */

    // MODELS

    var Resource = Backbone.Model.extend({

        // A model for CKAN resoruces. Most of the stuff here to get line
        // Backbone verbs with the CKAN api endpoints.

        fileAttribute: 'upload',

        defaults: {
            'action_btn_label': 'Update',
            'action_btn_class': 'update_resource'
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

        initialize: function(options) {
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
            this.collection.fetch({
                success: function(){
                    this.render();
                }.bind(this),
                error: function(e){
                    console.log('Cannot render: ' + e);
                }.bind(this)});
            this.listenTo(this.collection, 'sync', this.render);
        },

        render: function() {
            var $list = this.$el.empty();
            this.collection.each(function(model) {
                var item = new ResourceItemView({model: model});
                $list.append(item.render().$el);
            }, this);
            return this;
        },
    });

    var ResourceItemView = Backbone.View.extend({

        // A template view for each Resource.

        template: _.template($('#resource-item-tmpl').html()),

        events: {
            'click .update_resource': 'onUpdateBtn',
            'change .resource_file_field': 'onFileChange'
        },

        render: function() {
            var html = this.template(this.model.toJSON());
            this.$el.html(html);
            return this;
        },

        onUpdateBtn: function(e) {
            this.updateResource();
        },

        onFileChange: function(e) {
            // If a file has been selected, populate the url and file name
            // fields.
            var file_name = $(e.currentTarget).val().split(/^C:\\fakepath\\/).pop();
            if (file_name) {
                this.$('.resource_url_field').val(file_name);
            }
            if (!this.$('.resource_name_field').val()) {
                this.$('.resource_name_field').val(file_name);
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

        createResource: function(package_id, collection) {
            // Add a new Resource to the collection arg with data from this
            // view's form fields.

            // Get the serialised create form.
            var create_form_array = this.$(':input').serializeArray();
            // Serialize in the correct JSON format.
            var form_data = {package_id: package_id, format: 'txt'};
            _.map(create_form_array, function(x){form_data[x.name] = x.value;});

            var resource = new Resource(form_data);
            resource.set('upload', this.$('.resource_file_field')[0].files[0]);
            resource.save(form_data, {
                wait: true,
                success: function(model, response, options) {
                    // console.log('successfully saved model');
                    this.$(':input').val('');
                    collection.add(resource);
                }.bind(this),
                error: function(model, response, options) {
                    // ::TODO:: Handle validation errors returned by server here.
                    console.log('Could not create the resource');
                    console.log(response.responseJSON.error);
                }.bind(this)
            });
        }
    });

    var AppView = Backbone.View.extend({

        // The main app to kick things off, and manage the create widget.

        el: '#resource-app',

        events: {
            'click .create_resource': 'onCreateBtn',
        },

        initialize: function(options) {
            var sandbox = options.sandbox;
            this.create_el = this.$('#resource-create');
            this.datasetId = undefined;
            this.resourceListView = undefined;
            // Listen for the hdx-contribute-global-created notification...
            sandbox.subscribe('hdx-contribute-global-created', function (global) {
                // ... when ready, get the contribute_global object.
                this.contribute_global = global;
            }.bind(this));
            this._setUpCreateResourceEl();
        },

        onCreateBtn: function(e) {
            // Get the dataset ID from the global object.
            $.when(this.contribute_global.getDatasetIdPromise()).done(function(id){
                if (this.datasetId === undefined) this.datasetId = id;
                if (this.resourceListView === undefined) this._setUp(id);
                this.resourceCreateView.createResource(this.datasetId, this.resourceListView.collection);
            }.bind(this));
        },

        _setUpCreateResourceEl: function() {
            var data = {
                id: 'new',
                position: 'new',
                url: '',
                format: '',
                description: '',
                action_btn_label: 'Create',
                action_btn_class: 'create_resource'
            };
            var newResourceModel = new Resource(data);
            this.resourceCreateView = new ResourceItemView({model: newResourceModel});
            // this.resourceCreateView.el = this.create_el;
            this.create_el.append(this.resourceCreateView.render().$el);
        },

        _setUp: function(package_id) {
            var resources = new PackageResources({package_id: package_id});
            this.resourceListView = new PackageResourcesListView({collection: resources});
        }
    });

    var sandbox = ckan.sandbox();
    this.app = new AppView({sandbox: sandbox});
}());
