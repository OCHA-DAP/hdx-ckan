/* Image Upload
 *
 */
this.ckan.module('hdx-image-upload', function($, _) {
  return {
    /* options object can be extended using data-module-* attributes */
    options: {
      is_url: true,
      is_upload: false,
      field_upload: 'image_upload',
      field_url: 'image_url',
      field_clear: 'clear_upload',
      upload_label: '',
      i18n: {
        upload: _('Upload'),
        url: _('Link'),
        remove: _('Remove'),
        upload_label: _('Image'),
        upload_tooltip: _('Upload a file on your computer'),
        url_tooltip: _('Link to a URL on the internet (you can also link to an API)'),
        remove_tooltip: _('Reset this')
      },
      template: [
        ''
      ].join("\n")
    },

    state: {
      attached: 1,
      blank: 2,
      web: 3
    },

    /* Initialises the module setting up elements and event listeners.
     *
     * Returns nothing.
     */
    initialize: function () {
      $.proxyAll(this, /_on/);
      var options = this.options;

      // firstly setup the fields
      var field_upload = 'input[name="' + options.field_upload + '"]';
      var field_url = 'input[name="' + options.field_url + '"]';
      var field_clear = 'input[name="' + options.field_clear + '"]';

      this.input = $(field_upload, this.el);
      this.field_url = $(field_url, this.el).parents('.mb-3');
      this.field_image = this.input.parents('.mb-3');

      // Is there a clear checkbox on the form already?
      var checkbox = $(field_clear, this.el);
      if (checkbox.length > 0) {
        options.is_upload = true;
        checkbox.parent().remove();
      }

      // Adds the hidden clear input to the form
      this.field_clear = $('<input type="hidden" name="'+options.field_clear+'">')
        .appendTo(this.el);

      // Button to set the field to be a URL
      this.button_url = $('<a href="javascript:;" class="btn btn-sm"><i class="fa fa-globe"></i> '+this.i18n('url')+'</a>')
        .prop('title', this.i18n('url_tooltip'))
        .on('click', this._onFromWeb)
        .insertAfter(this.input);

      // Button to attach local file to the form
      this.button_upload = $('<a href="javascript:;" class="btn btn-sm"><i class="fa fa-cloud"></i> '+this.i18n('upload')+'</a>')
        .insertAfter(this.input);

      // Button to reset the form back to the first from when there is a image uploaded
      this.button_remove = $('<a href="javascript:;" class="btn btn-sm btn-danger ms-0" />')
        .text(this.i18n('remove'))
        .on('click', this._onRemove)
        .insertAfter(this.button_upload);

      // Button for resetting the form when there is a URL set
      $('<a href="javascript:;" class="input-group-text btn-remove-url"><i class="fa fa-close"></i></a>')
        .prop('title', this.i18n('remove_tooltip'))
        .on('click', this._onRemove)
        .insertBefore($('input', this.field_url));
      $('input', this.field_url).parent().addClass('input-group');

      // Update the main label
      $('label[for="field-'+options.field_upload+'"]').text(options.upload_label || this.i18n('upload_label'));

      // Setup the file input
      this.input
        .on('mouseover', this._onInputMouseOver)
        .on('mouseout', this._onInputMouseOut)
        .on('change', this._onInputChange)
        .prop('title', this.i18n('upload_tooltip'))
        .css('width', this.button_upload.outerWidth());

      // Fields storage. Used in this.changeState
      this.fields = $('<i />')
        .add(this.button_remove)
        .add(this.button_upload)
        .add(this.button_url)
        .add(this.input)
        .add(this.field_url)
        .add(this.field_image);

      // Setup the initial state
      if (options.is_url) {
        this.changeState(this.state.web);
      } else if (options.is_upload) {
        this.changeState(this.state.attached);
      } else {
        this.changeState(this.state.blank);
      }

    },

    /* Method to change the display state of the image fields
     *
     * state - Pseudo constant for passing the state we should be in now
     *
     * Examples
     *
     *   this.changeState(this.state.web); // Sets the state in URL mode
     *
     * Returns nothing.
     */
    changeState: function(state) {
      this.fields.hide();
      if (state == this.state.blank) {
        this.button_upload
          .add(this.field_image)
          .add(this.button_url)
          .add(this.input)
          .show();
      } else if (state == this.state.attached) {
        this.button_remove
          .add(this.field_image)
          .show();
      } else if (state == this.state.web) {
        this.field_url
          .show();
      }
    },

    /* Event listener for when someone sets the field to URL mode
     *
     * Returns nothing.
     */
    _onFromWeb: function() {
      this.changeState(this.state.web);
      $('input', this.field_url).focus();
      if (this.options.is_upload) {
        this.field_clear.val('true');
      }
    },

    /* Event listener for resetting the field back to the blank state
     *
     * Returns nothing.
     */
    _onRemove: function() {
      this.changeState(this.state.blank);
      $('input', this.field_url).val('');
      this.field_clear.val('true');
    },

    /* Event listener for when someone chooses a file to upload
     *
     * Returns nothing.
     */
    _onInputChange: function() {
      var id = this.input[0].id;
      this.file_name = $('#'+id).val();
      this.field_clear.val('');
      this.changeState(this.state.attached);
    },

    /* Event listener for when a user mouseovers the hidden file input
     *
     * Returns nothing.
     */
    _onInputMouseOver: function() {
      this.button_upload.addClass('hover');
    },

    /* Event listener for when a user mouseouts the hidden file input
     *
     * Returns nothing.
     */
    _onInputMouseOut: function() {
      this.button_upload.removeClass('hover');
    }

  }
});
