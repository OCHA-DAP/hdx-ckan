"use strict";

ckan.module('hdx_tag_recommender', function ($, _) {
  return {
    initialize: function () {
      jQuery.proxyAll(this, /_on/);
      this.apiEndpoint = '/api/action/hdx_recommend_tags';
      this.datasetTitle = null;
      this.datasetOrgName = null;
      this.tagWrapperEl = $(this.options.recommended_tag_wrapper_selector);
      this.tagContainerEl = this.tagWrapperEl.find('span');
      this.tagInputEl = $(this.options.tag_input_selector);

      this.debouncedFetchRecommendedTags = hdxUtil.eventUtil.debouncer(this.fetchRecommendedTags, 1000);

      this.recommendedTags = null;
      this.currentTags = null;

      this.sandbox.subscribe(this.options.form_change_channel, this._onMessageReceived);
    },
    _onRecommendedTagClicked: function(e) {
      var tag = $(e.target).text();
      var currentTagsString = this.tagInputEl.val();
      if (!currentTagsString || currentTagsString.indexOf(tag) < 0) {
        var newTagsString = currentTagsString ? currentTagsString + ',' + tag : tag;
        this.tagInputEl.val(newTagsString);
        this.tagInputEl.trigger('change');
        hdxUtil.analytics.sendLinkClickEvent({
          destinationUrl: '#',
          linkType: 'dataset recommended tag'
        });
      }
    },
    /**
     *
     * @param {string} message.srcElement the 'name' attribute of the element that was changed
     * @param {string} message.newValue the new value of the element that was changed
     * @private
     */
    _onMessageReceived: function (message) {
      if (message.srcElement === 'title') {
        this.datasetTitle = message.newValue;
        this.debouncedFetchRecommendedTags();
      } else if (message.srcElement === 'owner_org') {
        this.datasetOrgName = message.newValue;
        this.debouncedFetchRecommendedTags();
      } else if (message.srcElement === 'tag_string') {
        var tags = message.newValue.split(',');
        this.currentTags = tags.map(function(tag){return tag.trim()});
        this.renderRecommendedTags();
      }
    },
    fetchRecommendedTags: function () {
      if (this.datasetTitle && this.datasetTitle.length > 3) {
        // alert(this.datasetTitle + " - " + this.datasetOrgName);

        var encodedTitle = encodeURIComponent(this.datasetTitle);
        var url = this.apiEndpoint + '?title=' + encodedTitle;
        if (this.datasetOrgName && this.datasetOrgName.length > 2) {
          var encodedOrg = encodeURIComponent(this.datasetOrgName);
          url += '&organization=' + encodedOrg;
        }
        $.getJSON(url, function (result) {
          if (result.success) {
            this.recommendedTags = result.result.map(function(tag){return tag.name});
            this.renderRecommendedTags();
          }
        }.bind(this));
      } else {
        this.recommendedTags = null;
        this.renderRecommendedTags();
      }
    },
    renderRecommendedTags: function() {
      var htmlCode = '';
      if (this.recommendedTags) {
        var unusedRecommendedTags = this.recommendedTags.filter(function(tag){
          if (this.currentTags && this.currentTags.indexOf(tag) >= 0) {
            return false;
          }
          return true;
        }.bind(this));
        for (var i=0; i < unusedRecommendedTags.length; i++) {
          var tag = unusedRecommendedTags[i];
          var linkHtmlCode = '<a class="recommended-tag" href="javascript:void(0)">' + tag + '</a>';
          if (htmlCode && htmlCode.length > 0) {
            htmlCode += ', ' + linkHtmlCode;
          } else {
            htmlCode = linkHtmlCode
          }
        }
      }
      this.tagContainerEl.html(htmlCode);
      if (htmlCode.length > 0) {
        this.tagWrapperEl.show();
      } else {
        this.tagWrapperEl.hide();
      }
      $('.recommended-tag').click(this._onRecommendedTagClicked);
    },
    options: {
      tag_input_selector: null,
      recommended_tag_wrapper_selector: null,
      form_change_channel: 'hdx-dataset-form-change'
    }
  }
});
