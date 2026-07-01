(function () {
    'use strict';

    // ── Generic infinite-loop carousel ────────────────────────────────────────
    // Usage: window.hdxCarousel.init(config)
    //
    // config {object}
    //   containerSelector  {string}  Outer wrapper element (clips overflow at SM/MD).
    //   slideSelector      {string}  Individual slide items (direct children of inner).
    //   prevBtnSelector    {string}  Previous arrow button selector (within container).
    //   nextBtnSelector    {string}  Next arrow button selector (within container).
    //   mediaQuery         {string}  Above this MQ the carousel is inactive (static flex).
    //   dotsSelector       {string}  Optional dot nav container selector. default: null
    //
    // DOM contract: container's FIRST CHILD must be the scrolling inner element
    // that wraps the slides. Arrow buttons and dots are siblings of that inner.
    //
    // Called by the host page from within DOMContentLoaded. Carousel state is
    // closed over per-instance so multiple carousels can co-exist on one page.

    function initCarousel(config) {
        var cSel    = config.containerSelector;
        var sSel    = config.slideSelector;
        var prevSel = config.prevBtnSelector;
        var nextSel = config.nextBtnSelector;
        var mqStr   = config.mediaQuery;
        var dotsSel = config.dotsSelector || null;

        var mql   = window.matchMedia ? window.matchMedia(mqStr) : null;
        var idx   = 1;     // current track position (1 = first real slide)
        var slot  = 0;     // slot width in px (slide + margin-right)
        var n     = 0;     // number of real slides
        var busy  = false; // animation lock
        var ready = false; // initialised flag

        function getInner() {
            var c = document.querySelector(cSel);
            return c ? c.firstElementChild : null;
        }

        // ── Breakpoint change listener ─────────────────────────────────────────
        if (mql) {
            mql.addEventListener('change', function (e) {
                var inner = getInner();
                if (!inner) return;
                if (e.matches) {
                    inner.style.left = '0px';      // XL: reset for static flex row
                } else if (!ready) {
                    setup();                       // SM/MD first time
                } else {
                    idx = 1;                       // SM/MD return: show slide 1
                    inner.style.left = -slot + 'px';
                    setDot(1);
                }
            });
        }

        // ── Initialise ────────────────────────────────────────────────────────
        function setup() {
            var c = document.querySelector(cSel);
            if (!c || ready)          return;
            if (mql && mql.matches)   return;  // XL: static flex, no carousel needed

            var inner  = c.firstElementChild;
            var slides = Array.from(inner.querySelectorAll(':scope > ' + sSel));
            n = slides.length;
            if (!n) return;
            ready = true;

            // Build infinite track: [cloneLast | …real slides… | cloneFirst]
            var cloneLast  = slides[n - 1].cloneNode(true);
            var cloneFirst = slides[0].cloneNode(true);
            cloneLast.classList.add('is-carousel-clone');
            cloneFirst.classList.add('is-carousel-clone');
            inner.insertBefore(cloneLast, inner.firstChild);
            inner.appendChild(cloneFirst);

            // Measure slot width (slide + right margin)
            var firstChild = inner.firstElementChild;
            var cs = getComputedStyle(firstChild);
            slot = firstChild.offsetWidth
                 + parseInt(cs.marginLeft)
                 + parseInt(cs.marginRight);

            inner.style.transition = 'left 350ms';
            inner.style.left = -slot + 'px';

            // Touch swipe via Hammer.js
            new Hammer(c).on('swipeleft swiperight', function (e) {
                goTo(idx + (e.type === 'swipeleft' ? 1 : -1));
            });

            // Arrow buttons
            var prevBtn = c.querySelector(prevSel);
            var nextBtn = c.querySelector(nextSel);
            if (prevBtn) prevBtn.addEventListener('click', function () { goTo(idx - 1); });
            if (nextBtn) nextBtn.addEventListener('click', function () { goTo(idx + 1); });

            // Dots (optional)
            if (dotsSel) {
                var dotsEl = c.querySelector(dotsSel);
                if (dotsEl) {
                    for (var i = 1; i <= n; i++) {
                        var btn = document.createElement('button');
                        btn.type = 'button';
                        btn.dataset.idx = i;
                        dotsEl.appendChild(btn);
                    }
                    dotsEl.addEventListener('click', function (e) {
                        var target = e.target.closest('[data-idx]');
                        if (target) goTo(+target.dataset.idx);
                    });
                    setDot(1);
                }
            }
        }

        // ── Navigate to track index `target` ──────────────────────────────────
        function goTo(target) {
            if (busy) return;
            busy = true;
            idx  = target;
            setDot(target <= 0 ? n : target > n ? 1 : target);

            var inner = getInner();
            if (!inner) { busy = false; return; }

            inner.style.left = (-target * slot) + 'px';

            inner.addEventListener('transitionend', function onEnd() {
                inner.removeEventListener('transitionend', onEnd);
                // Silently teleport from clone to real counterpart
                if (target === 0 || target === n + 1) {
                    inner.style.transition = 'none';
                    if (target === 0) {
                        idx = n;
                        inner.style.left = (-n * slot) + 'px';
                    } else {
                        idx = 1;
                        inner.style.left = -slot + 'px';
                    }
                    inner.offsetWidth; // force reflow before re-enabling transition
                    inner.style.transition = 'left 350ms';
                }
                busy = false;
            });
        }

        // ── Activate dot n (1-based) ───────────────────────────────────────────
        function setDot(dotIdx) {
            if (!dotsSel) return;
            var c = document.querySelector(cSel);
            if (!c) return;
            var dotsEl = c.querySelector(dotsSel);
            if (!dotsEl) return;
            var btns = dotsEl.querySelectorAll('button');
            btns.forEach(function (btn, i) {
                btn.classList.toggle('active', i === dotIdx - 1);
            });
        }

        // Called from DOMContentLoaded by the host page script
        setup();
    }

    window.hdxCarousel = { init: initCarousel };
})();
