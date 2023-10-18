(function () {
  /**
   * Initialise a Google Picker
   */
  var FilePicker = window.FilePicker = function (options) {
    // Config
    this.apiKey = options.apiKey;
    this.clientId = options.clientId;
    this.scope = options.scope;
    this.appId = options.appId;
    this.multiselect = options.multiselect || false;
    this.tokenClient = null;
    this.accessToken = null;
    // Events
    this.onSelect = options.onSelect;

    // Load the Google API Loader script
    this._loadApi();
  };

  FilePicker.prototype = {
    open: function () {
      // Public method to open the picker.
      // Request an access token
      this.tokenClient.callback = async (response) => {
        if (response.error !== undefined) {
          throw (response);
        }
        this.accessToken = response.access_token;
        await this._showPicker();
      };

      if (this.accessToken === null) {
        // Prompt the user to select a Google Account and ask for consent to share their data
        // when establishing a new session.
        this.tokenClient.requestAccessToken({prompt: 'consent'});
      } else {
        // Skip the display of the account chooser and consent dialog for an existing session.
        this.tokenClient.requestAccessToken({prompt: ''});
      }
    },

    /**
     *  Create and render a Picker object.
     */
    _showPicker: function () {
      // Show the file picker once authentication has been done.
      const view = new google.picker.View(google.picker.ViewId.DOCS);
      const picker = new google.picker.PickerBuilder()
        .addView(view)
        .setDeveloperKey(this.apiKey)
        .setOAuthToken(this.accessToken)
        .setAppId(this.appId)
        .addView(new google.picker.DocsUploadView())
        .setCallback(this._pickerCallback.bind(this));
      if (this.multiselect) {
        picker.enableFeature(google.picker.Feature.MULTISELECT_ENABLED);
      }
      picker
        .build()
        .setVisible(true);

    },

    /**
     * File details of the user's selection.
     * @param {object} data - Containers the user selection from the picker
     */
    _pickerCallback: async function (data) {
      if (data.action === google.picker.Action.PICKED) {
        if (this.multiselect) {
          for (var i = 0; i < data[google.picker.Response.DOCUMENTS].length; i++) {
            var doc = data[google.picker.Response.DOCUMENTS][i];
            var url = doc[google.picker.Document.URL];
            var filename = doc[google.picker.Document.NAME];
            this.onSelect(url, filename);
          }
        } else {
          var doc = data[google.picker.Response.DOCUMENTS][0];
          var url = doc[google.picker.Document.URL];
          var filename = doc[google.picker.Document.NAME];
          this.onSelect(url, filename);
        }
      }
    },

    _loadApi: function () {
      const apiScript = document.createElement('script');
      apiScript.src = 'https://apis.google.com/js/api.js';
      apiScript.async = true;
      apiScript.defer = true;
      apiScript.onload = this._onApiLoad.bind(this);

      document.head.appendChild(apiScript);
    },

    /**
     * Callback after api.js is loaded.
     */
    _onApiLoad: function () {
      gapi.load('client:picker', this._initializePicker.bind(this));
    },

    /**
     * Callback after the API client is loaded. Loads the
     * discovery doc to initialize the API.
     */
    _initializePicker: async function () {
      await gapi.client.load('https://www.googleapis.com/discovery/v1/apis/drive/v3/rest');
      this._initGoogleSignIn();
    },

    /**
     * Callback after Google Identity Services are loaded.
     */
    _initGoogleSignIn: function () {
      // Initialize Google Sign-In.
      this.tokenClient = google.accounts.oauth2.initTokenClient({
        client_id: this.clientId,
        scope: this.scope,
        callback: '',
      });
    }
  };
}());
