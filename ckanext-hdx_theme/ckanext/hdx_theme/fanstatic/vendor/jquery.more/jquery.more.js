/* http://keith-wood.name/more.html
   Text truncation and show more for jQuery v2.0.1.
   Written by Keith Wood (kwood{at}iinet.com.au) May 2010.
   Available under the MIT (https://github.com/jquery/jquery/blob/master/LICENSE.txt) license. 
   Please attribute the author if you use it. */

(function($) { // Hide scope, no $ conflict

	var pluginName = 'more';

	/** Create the more plugin.
		<p>Sets an element to hide/show additional text.</p>
		<p>Expects HTML like:</p>
		<pre>&lt;p>...&lt;/p></pre>
		<p>Provide inline configuration like:</p>
		<pre>&lt;p data-more="name: 'value'">...&lt;/p></pre>
	 	@module More
		@augments JQPlugin
		@example $(selector).more()
 $(selector).more({length: 200, toggle: false}) */
	$.JQPlugin.createPlugin({
	
		/** The name of the plugin. */
		name: pluginName,

		/** More/less change callback.
			Triggered when the more/less button is clicked.
			@callback changeCallback
			@param expanding {boolean} True if expanding the text, false if collapsing. */
			
		/** Default settings for the plugin.
			@property [length=100] {number} Truncation length.
			@property [leeway=5] {number} Overrun allowed without truncation.
			@property [wordBreak=false] {boolean} True to break between words, false to break anywhere.
			@property [ignoreTags=['br','hr','img']] {string[]} Non-terminated tags to ignore.
			@property [toggle=true] {boolean} True to toggle, false to display and exit.
			@property [ellipsisText='...'] {string} Display text for ellipsis.
			@property [moreText='Show more'] {string} Display text for more link.
			@property [lessText='Show less'] {string} Display text for less link.
			@property [andNext=''] {string} Selector for any following tags to include in the collapse.
			@property [onChange=null] {changeCallback} Callback function when expanded/collapsed.
			@example onChange: function(expanding) {
 	console.log('Showing ' + (expanding ? 'more' : 'less'));
 } */
		defaultOptions: {
			length: 100,
			leeway: 5,
			wordBreak: false,
			ignoreTags: ['br', 'hr', 'img'],
			toggle: true,
			ellipsisText: '...',
			moreText: 'More',
			lessText: 'Less',
			andNext: '',
			onChange: null
		},

		_ellipsisClass: pluginName + '-ellipsis', // The ellipsis marker class
		_linkClass: pluginName + '-link', // The link marker class
		_hiddenClass: pluginName + '-hidden', // The text hidden marker class
		
		_tagName: /^<(\w+).*>$/, // Extract a tag name

		_instSettings: function(elem, options) {
			return {html: elem.html()};
		},
		
		_optionsChanged: function(elem, inst, options) {
			var self = this;
			$.extend(inst.options, options);
			this._preDestroy(elem, inst); // Reset
			var html = '';
			if (elem.text().length > inst.options.length + inst.options.leeway) { // If text is longer
				var matches = elem.html().match(/(<[^>]+>)|([^<]+)/g); // Extract text and tags
				var i = 0;
				var pos = 0;
				var tags = [];
				for (; i < matches.length; i++) {
					if (matches[i][0] === '<') { // A tag
						if (matches[i][1] === '/' || matches[i][matches[i].length - 2] === '/') {
							tags.pop(); // Closing
						}
						else if ($.inArray(matches[i].toLowerCase().replace(this._tagName, '$1'),
								inst.options.ignoreTags) === -1) {
							tags.push(matches[i]); // Opening
						}
					}
					else if (pos + matches[i].length > inst.options.length) { // Found truncation point
						break;
					}
					else { // Count text
						pos += matches[i].length;
					}
				}
				pos = inst.options.length - pos; // Split point
				if (inst.options.wordBreak) { // Move back to start of word
					var matched = matches[i].substring(0, pos + 1).replace('\n', ' ').match(/^.*\W/m);
					pos = (matched ? matched[0].length - 1 : pos);
				}
				var closeTags = function(tags) { // Close any opened tags
					var html = '';
					for (var i = tags.length - 1; i >= 0; i--) {
						html += '</' + tags[i].replace(self._tagName, '$1') + '>';
					}
					return html;
				};
				// Generate new content
				html = matches.slice(0, i).join('') + matches[i].substring(0, pos) + closeTags(tags) +
					'<span class="' + this._ellipsisClass + '">' + inst.options.ellipsisText + '</span>' +
					'<span class="' + this._hiddenClass + '">' + tags.join('') + 
					matches[i].substring(pos) + closeTags(tags) + matches.slice(i + 1).join('') + '</span>';
			}
			else if (options.andNext && elem.nextAll(options.andNext).length) {
				html = elem.html();
			}
			if (html) {
				html += '<a href="#" class="' + this._linkClass + '">' + inst.options.moreText + '</a>';
				elem.html(html).find('a.' + this._linkClass).click(function(event) {
					var link = $(this);
					var expanding = link.html() === inst.options.moreText;
					link.html(expanding ? inst.options.lessText : inst.options.moreText).
						siblings('span.' + self._ellipsisClass + ',span.' + self._hiddenClass).toggle();
					if (options.andNext) {
						link.parent().nextAll(options.andNext).toggle();
					}
					if (!inst.options.toggle) { // Once only
						link.remove();
					}
					if ($.isFunction(inst.options.onChange)) { // Callback
						inst.options.onChange.apply(elem, [expanding]);
					}
					event.stopPropagation();
					return false;
				});
				if (options.andNext) {
					elem.nextAll(options.andNext).hide();
				}
			}
		},

		_preDestroy: function(elem, inst) {
			elem.html(inst.html);
			if (inst.options.andNext) {
				elem.nextAll(inst.options.andNext).show();
			}
		}
	});

})(jQuery);
