"use strict";

ckan.module('hdx_show_more_lines', function ($, _) {
  return {
    options: {
      lines: 2,
      more_text: "... More",
      less_text: "Less",
      bg_color: "#ffffff"
    },

    initialize: function () {
      this.originalStyle = this.el.attr("style") || "";
      this.update();

      // Re-check on resize
      let timer;
      $(window).on("resize", () => {
        clearTimeout(timer);
        timer = setTimeout(() => this.update(), 150);
      });
    },

    update: function () {
      this.removeClamp();

      const el = this.el[0];
      const lineHeight = this.getLineHeight();
      const maxHeight = this.options.lines * lineHeight;

      // If content fits, do nothing
      if (el.scrollHeight <= maxHeight + 1) return;

      // Apply the Clamp
      this.applyClamp(maxHeight, lineHeight);
    },

    applyClamp: function (maxHeight, lineHeight) {
      this.el.css({
        display: "-webkit-box",
        "-webkit-line-clamp": this.options.lines,
        "-webkit-box-orient": "vertical",
        overflow: "hidden",
        position: "relative",
        maxHeight: maxHeight + "px"
      });

      // Add “More” button
      const $btn = $(`<a href="#" class="read-more-btn">${this.options.more_text}</a>`);

      $btn.css({
        position: "absolute",
        bottom: "0",
        right: "0",
        background: this.options.bg_color,
        paddingLeft: "4px",
        lineHeight: lineHeight + "px"
      });

      $btn.on("click", (e) => {
        e.preventDefault();
        this.expand();
      });

      this.el.append($btn);
    },

    expand: function () {
      this.el.attr("style", this.originalStyle); // restore original
      this.el.find(".read-more-btn").remove();

      const $less = $(`<a href="#" class="read-less-btn">${this.options.less_text}</a>`);

      $less.on("click", (e) => {
        e.preventDefault();
        this.update();
      });

      this.el.append($less);
    },

    removeClamp: function () {
      this.el.attr("style", this.originalStyle);
      this.el.find(".read-more-btn, .read-less-btn").remove();
    },

    getLineHeight: function () {
      const lh = parseFloat(this.el.css("line-height"));
      return isNaN(lh)
        ? parseFloat(this.el.css("font-size")) * 1.2
        : lh;
    }
  };
});
