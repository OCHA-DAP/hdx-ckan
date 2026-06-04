document.addEventListener('DOMContentLoaded', function () { hlInit(); });

var hlIdx   = 1;      // current track index  (1 = first real card)
var hlSlot  = 0;      // slot width in px     (card + margin-right)
var hlN     = 0;      // number of real cards
var hlBusy  = false;  // animation lock
var hlReady = false;  // initialised flag

// Reuse the same MediaQueryList throughout.
var hlMql = window.matchMedia && window.matchMedia('(min-width: 80rem)');

// ── Breakpoint change listener ────────────────────────────────────────────────
if (hlMql) hlMql.addEventListener('change', function (e) {
    var inner = document.querySelector('.mobile-carousel .mobile-carousel-inner');
    if (!inner) return;
    if (e.matches) {
        inner.style.left = '0px';       // → XL: reset offset for static flex row
    } else if (!hlReady) {
        hlInit();                       // → SM/MD first time: initialise
    } else {
        hlIdx = 1;                      // → SM/MD return: show card 1
        inner.style.left = -hlSlot + 'px';
        hlSetDot(1);
    }
});

// ── Initialise ────────────────────────────────────────────────────────────────
function hlInit() {
    var c = document.querySelector('.mobile-carousel');
    if (!c || hlReady)          return;
    if (hlMql && hlMql.matches) return;  // XL: static flex row, no carousel needed

    var inner  = c.querySelector('.mobile-carousel-inner');
    var slides = Array.from(inner.querySelectorAll(':scope > .highlight-slide'));
    hlN = slides.length;
    if (!hlN) return;
    hlReady = true;

    // Build infinite track: [cloneLast | …real cards… | cloneFirst]
    var cloneLast  = slides[hlN - 1].cloneNode(true);
    var cloneFirst = slides[0].cloneNode(true);
    cloneLast.classList.add('highlight-slide--clone');
    cloneFirst.classList.add('highlight-slide--clone');
    inner.insertBefore(cloneLast, inner.firstChild);
    inner.appendChild(cloneFirst);

    // Measure slot width (card + left margin + right margin)
    var firstChild = inner.firstElementChild;
    var cs = getComputedStyle(firstChild);
    hlSlot = firstChild.offsetWidth + parseInt(cs.marginLeft) + parseInt(cs.marginRight);

    inner.style.transition = 'left 350ms';
    inner.style.left = -hlSlot + 'px';  // position at real card 1

    // Touch swipe
    new Hammer(c).on('swipeleft swiperight', function (e) {
        hlGoTo(hlIdx + (e.type === 'swipeleft' ? 1 : -1));
    });

    // Arrow buttons
    var prevBtn = c.querySelector('.hdx-v2-highlights__arrow--prev');
    var nextBtn = c.querySelector('.hdx-v2-highlights__arrow--next');
    if (prevBtn) prevBtn.addEventListener('click', function () { hlGoTo(hlIdx - 1); });
    if (nextBtn) nextBtn.addEventListener('click', function () { hlGoTo(hlIdx + 1); });

    // Dots — one delegated listener instead of one per button
    var dots = c.querySelector('.highlight-dots');
    for (var i = 1; i <= hlN; i++) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.dataset.idx = i;
        dots.appendChild(btn);
    }
    dots.addEventListener('click', function (e) {
        var target = e.target.closest('[data-idx]');
        if (target) hlGoTo(+target.dataset.idx);
    });
    hlSetDot(1);
}

// ── Navigate to track index `target` ─────────────────────────────────────────
function hlGoTo(target) {
    if (hlBusy) return;
    hlBusy = true;
    hlIdx  = target;
    hlSetDot(target <= 0 ? hlN : target > hlN ? 1 : target);

    var inner = document.querySelector('.mobile-carousel .mobile-carousel-inner');
    if (!inner) { hlBusy = false; return; }

    inner.style.left = (-target * hlSlot) + 'px';

    inner.addEventListener('transitionend', function onEnd() {
        inner.removeEventListener('transitionend', onEnd);
        // Silently teleport from clone to real counterpart (identical content = invisible jump)
        if (target === 0 || target === hlN + 1) {
            inner.style.transition = 'none';
            if (target === 0) {
                hlIdx = hlN;
                inner.style.left = (-hlN * hlSlot) + 'px';
            } else {
                hlIdx = 1;
                inner.style.left = -hlSlot + 'px';
            }
            inner.offsetWidth; // force reflow before re-enabling transition
            inner.style.transition = 'left 350ms';
        }
        hlBusy = false;
    });
}

// ── Activate dot n (1-based) ──────────────────────────────────────────────────
function hlSetDot(n) {
    var btns = document.querySelectorAll('.mobile-carousel .highlight-dots button');
    btns.forEach(function (btn, i) {
        btn.classList.toggle('active', i === n - 1);
    });
}
