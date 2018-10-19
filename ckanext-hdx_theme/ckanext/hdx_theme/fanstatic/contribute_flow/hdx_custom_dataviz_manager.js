"use strict";

ckan.module('hdx_custom_dataviz_manager', function($, _) {
    return {
        initialize: function () {
            var initializeAfterContributeGlobal = function (global) {
              this.contributeGlobal = global;

              var itemEl = this.el.find('.custom-viz-item');
              this.titleLabelTemplate = itemEl.find(this.options.title_label_selector).html();
              this.controlLabelTemplate = itemEl.find(this.options.control_label_selector).html();

              this.itemTemplate = itemEl.prop('outerHTML');
              this.el.html('');

              if (this.options.custom_viz_urls && this.options.custom_viz_urls.length) {
                var urls = this.options.custom_viz_urls;
                urls.forEach(function (url) {this.addNewItem(url)}.bind(this));
              }
              else {
                this.addNewItem();
              }
            }.bind(this);
            this.sandbox.subscribe('hdx-contribute-global-created', initializeAfterContributeGlobal);

            var manageValidationErrors = function(message) {
              var items = this.el.find('.controls');
              items.each(function(index, element){
                var wrapperEl = $(element);
                var errorEl = wrapperEl.find('.error-block');
                if (message.type === 'reset') {
                  wrapperEl.removeClass('error');
                  errorEl.html('');
                }
                else if (message.elementName === 'customviz' && message.index === index
                    && Object.keys(message.errorInfo).length) {

                  if (message.errorInfo.url && message.errorInfo.url.length) {
                    /** @type {[string]} */
                    var urlErrors = message.errorInfo.url;
                    wrapperEl.addClass('error');
                    for (var i=0; i<urlErrors.length; i++) {
                      var msg = urlErrors[i];
                      var existingText = errorEl.html().trim();
                      var newText = existingText ? existingText + ", " + msg : msg;
                      errorEl.html(newText);
                    }

                  }
                }

              });
            }.bind(this);
            this.sandbox.subscribe('hdx-form-validation', manageValidationErrors);


            // var moduleEl = this.el;
            this.newItemButton = this.el.parent().find('.add_custom_viz');
            this.newItemButton.click(function () {
              this.addNewItem();
            }.bind(this));

            Sortable.create(this.el[0], {
              handle: '.drag-handle',
              onUpdate: function () {
                this.afterChange();
              }.bind(this)
            });

            var moduleLog = this.moduleLog;

        },
        moduleLog: function(message) {
            console.log(message);
        },
        getNumberOfItems: function() {
          return this.el.children().length;
        },
        addNewItem: function (url) {
          this.addItem(this.newItem(this.getNumberOfItems() + 1, url));
        },
        addItem: function (item) {
          var htmlEl = $.parseHTML(item);
          var this_afterChange = this.afterChange.bind(this);
          $(htmlEl).find('.delete_custom_viz').click(function (){
            $(this).parents('.custom-viz-item').remove();
            this_afterChange();
          });
          $(htmlEl).find('.custom-viz-url').change(function (){
            this.afterChange();
          }.bind(this));
          this.el.append(htmlEl);
          this.afterChange();
        },
        newItem: function(index, url) {
          if (!url) {
            url = '';
          }
          var elem = this.itemTemplate.replace(/\$\{index\}/g, index);
          elem = elem.replace(/\$\{url\}/g, url);
          return elem;
        },
        afterChange: function() {
          var urls = [];
          var createListOfUrls = function (index, element) {
            var url = $(element).val();
            urls.push(url.trim());
          }.bind(this);
          this.el.find('.custom-viz-url').each(createListOfUrls);

          var setNewIndexOnItem = function (index, item) {
            item = $(item);
            index = index + 1;
            var title_label_text = this.titleLabelTemplate.replace(/\$\{index\}/g, index);
            var control_label_text = this.controlLabelTemplate.replace(/\$\{index\}/g, index);
            item.find(this.options.title_label_selector).html(title_label_text);
            item.find(this.options.control_label_selector).html(control_label_text);
          }.bind(this);

          this.el.find('.custom-viz-item').each(setNewIndexOnItem);


          this.moduleLog(urls);

          if (this.getNumberOfItems() >= this.options.max_number_of_items) {
            this.newItemButton.css('display', 'none');
          }
          else {
            this.newItemButton.css('display', 'block');
          }

          this.contributeGlobal.setCustomVizList(urls);
        },

        options: {
          custom_viz_urls: null,
          max_number_of_items: 5,
          title_label_selector: '.label-title-style',
          control_label_selector: '.control-label'

        }
    };
});
