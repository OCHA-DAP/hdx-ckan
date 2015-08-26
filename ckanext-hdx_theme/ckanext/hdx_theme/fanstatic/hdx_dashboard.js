/* THIS IS A MODIFIED COPY OF THE CKAN CORE dashboard.js.
 * IT WAS MODIFIED TO WORK WITH BOOTSTRAP 3.
 *
 * NOTE: Mark all changes done for HDX with a comment
 */
this.ckan.module('dashboard', function ($, _) {
  return {
    button: null,
    popover: null,
    searchTimeout: null,

    /* Initialises the module setting up elements and event listeners.
     *
     * Returns nothing.
     */
    initialize: function () {
      $.proxyAll(this, /_on/);
      this.button = $('#followee-filter .btn').
        on('click', this._onShowFolloweeDropdown);
      var title = this.button.prop('title');
      this.button.popover({
          placement: 'bottom',
          title: 'Filter',
          html: true,
          content: $('#followee-popover').html()
        });
      this.button.prop('title', title);

      // Commented by HDX
      //this.popover = this.button.data('popover').tip().addClass('popover-followee');
    },

    /* Handles click event on the 'show me:' dropdown button
     *
     * Returns nothing.
     */
    _onShowFolloweeDropdown: function() {
      this.button.toggleClass('active');
      if (this.button.hasClass('active')) {

        // Modified by HDX
        //setTimeout(this._onInitSearch, 100);
        this.button.on('shown.bs.popover', this._onInitSearch)
      }
      return false;
    },

    /* Handles focusing on the input and making sure that the keyup
     * even is applied to the input
     *
     * Returns nothing.
     */
    _onInitSearch: function() {
      // Added by HDX
      this.popover = $('#followee-filter .popover');
      if ( !this.popover.hasClass('popover-followee'))
        this.popover.addClass('popover-followee');


      var input = $('input', this.popover);
      if (!input.hasClass('inited')) {
        input.
          on('keyup', this._onSearchKeyUp).
          addClass('inited');
      }
      input.focus();
    },

    /* Handles the keyup event
     *
     * Returns nothing.
     */
    _onSearchKeyUp: function() {
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(this._onSearchKeyUpTimeout, 300);
    },

    /* Handles the actual filtering of search results
     *
     * Returns nothing.
     */
    _onSearchKeyUpTimeout: function() {
      var input = $('input', this.popover);
      var q = input.val().toLowerCase();
      if (q) {
        $('li', this.popover).hide();
        $('li.everything, [data-search^="' + q + '"]', this.popover).show();
      } else {
        $('li', this.popover).show();
      }
    }
  };
});
