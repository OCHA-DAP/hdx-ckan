'use strict';

/* hdx-modal-form based / copied on modal-form.js from requestdata module.
 * Adding analytics.
 *
 * This JavaScript module creates a modal and responds to actions
 *
 */

ckan.module('hdx-modal-form', function($) {
    var api = {
        get: function(action, params, api_ver = 3) {
            var base_url = ckan.sandbox().client.endpoint;
            params = $.param(params);
            var url = base_url + '/api/' + api_ver + '/action/' + action + '?' + params;
            return $.getJSON(url);
        },
        post: function(action, data, api_ver = 3) {
            var base_url = ckan.sandbox().client.endpoint;
            var url = base_url + '/api/' + api_ver + '/action/' + action;
            return $.post(url, JSON.stringify(data), "json");
        }
    };

    return {
        initialize: function() {
            $.proxyAll(this, /_on/);

            this.el.on('click', this._onClick);
        },
        // Whether or not the rendered snippet has already been received from CKAN.
        _snippetReceived: false,
        _onClick: function(event) {
            var is_current_user_a_maintainer = this.options.is_current_user_a_maintainer
            var dialogResult = true

            if (is_current_user_a_maintainer === 'True') {
                var dialogResult = window.confirm('Request own dataset\n\nWARNING: You are a maintainer of the dataset you are requesting. Do you wish to continue making this request?')
            }

            if (dialogResult) {
                var base_url = ckan.sandbox().client.endpoint;

                if (!this.options.is_logged_in) {
                    if(this.options.is_hdx == 'True'){
                        showOnboardingWidget('#loginPopup');
                        return;
                     }
                  location.href = base_url + this.options.redirect_url
                  return;
                }
                var payload = {
                    message_content: this.options.message_content,
                    package_name: this.options.post_data.package_name,
                    package_title: this.options.post_data.package_title,
                    maintainers: JSON.stringify(this.options.post_data.maintainers),
                    requested_by: this.options.post_data.requested_by,
                    sender_id: this.options.post_data.sender_id
                }
                if (!this._snippetReceived) {
                    this.sandbox.client.getTemplate(this.options.template_file, payload, this._onReceiveSnippet);
                    this._snippetReceived = true;
                } else if (this.modal) {
                    this.modal.modal('show');
                }

                var success_msg = document.querySelector('#request-success-container');

                if (success_msg) {
                    success_msg.parentElement.removeChild(success_msg);
                }
            }
        },
        _onReceiveSnippet: function(html) {
            this.sandbox.body.append(this.createModal(html));
            this.modal.modal('show');

            var backdrop = $('.modal-backdrop');

            if (backdrop) {
                backdrop.on('click', this._onCancel);
            }
        },
        createModal: function(html) {
            if (!this.modal) {
                var element = this.modal = jQuery(html);
                element.on('click', '.btn-primary', this._onSubmit);
                element.on('click', '.btn-cancel', this._onCancel);
                element.modal({
                    show: false
                });
                this.modalFormError = this.modal.find('.alert-error')
            }
            return this.modal;
        },
        _onSubmit: function(event) {
            var base_url = ckan.sandbox().client.endpoint;
            var url = base_url + this.options.submit_action || '';
            var data = this.options.post_data || '';
            var form = this.modal.find('form')
            var formElements = $(form[0].elements)
            var submit = true
            var formData = new FormData();

            // Clear form errors before submitting the form.
            this._clearFormErrors(form)

            for (var item in data) {
              formData.append(item, data[item])
            }

            // Add field data to payload data
            $.each(formElements, function(i, element) {
                var value = element.value.trim()

                if (element.required && value === '') {
                    var hasError = element.parentElement.querySelector('.error-block')

                    if (!hasError) {
                        this._showInputError(element, 'Missing value')
                    }

                    submit = false
                } else {
                    if (element.type == 'file') {
                       if (element.files.length > 0) {
                             formData.append(element.name, element.files[0], element.value)

                             // If a file has been attached, than move the request to archive
                            // and mark it that data has been shared

                             formData.append('state', 'archive')
                             formData.append('data_shared', true)
                      }
                    } else {
                      formData.append(element.name, element.value)
                    }
                }
            }.bind(this))

            if (submit) {
              $.ajax({
                url: url,
                data: formData,
                processData: false,
                contentType: false,
                type: 'POST'
              })
                .done(function(data) {
                    data = JSON.parse(data)
                    if (data.error && data.error.fields) {
                        for(var key in data.error.fields){
                            this._showFormError(data.error.fields[key]);
                        }
                    } else if (data.success) {
                        this._showSuccessMsg(data.message);

                        if (this.options.disable_action_buttons) {
                          this._disableActionButtons();
                        }
                        var analyticsPromise = true;
                        if (this.options.submit_action === '/request_data') {
                            analyticsPromise = hdxUtil.analytics.sendMessagingEvent('dataset', 'data request',
                                null, null, true, this.options.analytics);
                        }
                        $.when(analyticsPromise).then(function(result){
                                if (this.options.refresh_on_success) {
                                    location.reload();
                                }
                                console.log('Analytics sent');
                        }.bind(this));

                    }
                }.bind(this))
                .error(function(error) {
                    this._showFormError(error.statusText)
                }.bind(this))
            }
        },
        _onCancel: function(event) {
            this._snippetReceived = false;
            this._clearFormErrors()
            this._resetModalForm();
        },
        _showInputError: function(element, message) {
            var div = document.createElement('div');
            div.className = 'error-block';
            div.textContent = message;

            element.parentElement.appendChild(div);
        },
        _clearFormErrors: function() {
            var errors = this.modal.find('.error-block')

            $.each(errors, function(i, error) {
                error.parentElement.removeChild(error)
            })

            this.modalFormError.addClass('hide')
            this.modalFormError.text('')
        },
        _showFormError: function(message) {
            this.modalFormError.removeClass('hide')
            this.modalFormError.text(message)
        },
        _showSuccessMsg: function(msg) {
            var div = document.createElement('div');
            div.className = "alert alert-success alert-dismissable fade in";
            div.id = 'request-success-container'
            div.textContent = msg;
            div.style.marginTop = '25px';
            var currentDiv = $('.requested-data-message')

            if (currentDiv.length > 1) {
                currentDiv = this.el.next('.requested-data-message');
            }
            currentDiv.css('display', 'block');
            currentDiv.append(div)
            this._resetModalForm();
        },
        _resetModalForm: function(){
            this.modal.modal('hide');
            // Clear form fields
            this.modal.find('form')[0].reset();
        },
        _disableActionButtons: function() {
            this.el.attr('disabled', 'disabled');
            this.el.siblings('.btn').attr('disabled', 'disabled');
        }
    };
});
