(function() {
  /**
   * Initialise a Google Picker
   */
  var FilePicker = window.FilePicker = function(options) {
    // Config
    this.apiKey = options.apiKey;
    this.clientId = options.clientId;
    this.scope = options.scope;

    // Events
    this.onSelect = options.onSelect;

    // Load the APIs
    gapi.load('auth', {'callback': this._authApiLoaded.bind(this)});
    gapi.load('picker', {'callback': this._pickerApiLoaded.bind(this)});
  };

  FilePicker.prototype = {
    open: function() {
      // Public method to open the picker.

      // Check if the user has already authenticated
      var token = gapi.auth.getToken();
      if (token) {
        this._showPicker();
      } else {
        // The user has not yet authenticated with Google. We need to do the
        // authentication before displaying the picker.
        this._doAuth(false, function() { this._showPicker(); }.bind(this));
      }
    },

    _showPicker: function() {
     // Show the file picker once authentication has been done.
      var accessToken = gapi.auth.getToken().access_token;
      this.picker = new google.picker.PickerBuilder()
        .addView(google.picker.ViewId.DOCS)
        .setDeveloperKey(this.apiKey)
        .setOAuthToken(accessToken)
        .setCallback(this._pickerCallback.bind(this))
        .build()
        .setVisible(true);
    },

    _pickerCallback: function(data) {
      if (data[google.picker.Response.ACTION] == google.picker.Action.PICKED) {
        var doc = data[google.picker.Response.DOCUMENTS][0];
        var url = doc[google.picker.Document.URL];
        var filename = doc[google.picker.Document.NAME];
        this.onSelect(url, filename);
      }
    },

    _pickerApiLoaded: function() {
      // Called when the Google Drive file picker API has finished loading.
      // console.log('picker api loaded');
    },

    _authApiLoaded: function() {
      // Called when the Google Drive API has finished loading.
      this._doAuth(true);
    },

    _doAuth: function(immediate, callback) {
      // Authenticate with Google Drive via the Google JavaScript API.
      gapi.auth.authorize({
        client_id: this.clientId,
        scope: this.scope,
        immediate: immediate
      }, callback);
    }
  };
}());
