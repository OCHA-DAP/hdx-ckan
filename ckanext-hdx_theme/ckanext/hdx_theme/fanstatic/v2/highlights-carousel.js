$(document).ready(function () { hlInit(); });

var hlIdx   = 1;      // current track index  (1 = first real card)
var hlSlot  = 0;      // slot width in px     (card + margin-right)
var hlN     = 0;      // number of real cards
var hlBusy  = false;  // animation lock
var hlReady = false;  // initialised flag

// Reuse the same MediaQueryList throughout.
var hlMql = window.matchMedia && window.matchMedia('(min-width: 80rem)');

// ── Breakpoint change listener ────────────────────────────────────────────────
if (hlMql) hlMql.addEventListener('change', function (e) {
    var $inner = $('.mobile-carousel .mobile-carousel-inner');
    if (e.matches) {
        $inner.css('left', 0);          // → XL: reset offset for static flex row
    } else if (!hlReady) {
        hlInit();                       // → SM/MD first time: initialise
    } else {
        hlIdx = 1;                      // → SM/MD return: show card 1
        $inner.css('left', -hlSlot);
        hlSetDot(1);
    }
});

// ── Initialise ────────────────────────────────────────────────────────────────
function hlInit() {
    var $c = $('.mobile-carousel');
    if (!$c.length || hlReady)    return;
    if (hlMql && hlMql.matches)   return;  // XL: static flex row, no carousel needed

    var $inner  = $c.find('.mobile-carousel-inner');
    var $slides = $inner.children('.highlight-slide');
    hlN = $slides.length;
    if (!hlN) return;
    hlReady = true;

    // Build infinite track: [cloneLast | …real cards… | cloneFirst]
    $inner
        .prepend($slides.last().clone().addClass('highlight-slide--clone'))
        .append($slides.first().clone().addClass('highlight-slide--clone'));

    hlSlot = $inner.children().first().outerWidth(true);
    $inner.css('left', -hlSlot);   // position at real card 1

    // Touch swipe
    new Hammer($c[0]).on('swipeleft swiperight', function (e) {
        hlGoTo(hlIdx + (e.type === 'swipeleft' ? 1 : -1));
    });

    // Arrow buttons
    $c.find('.hdx-v2-highlights__arrow--prev').on('click', function () { hlGoTo(hlIdx - 1); });
    $c.find('.hdx-v2-highlights__arrow--next').on('click', function () { hlGoTo(hlIdx + 1); });

    // Dots — one delegated listener instead of one per button
    var $dots = $c.find('.highlight-dots');
    for (var i = 1; i <= hlN; i++) {
        $dots.append('<button type="button" data-idx="' + i + '"></button>');
    }
    $dots.on('click', '[data-idx]', function () { hlGoTo(+$(this).data('idx')); });
    hlSetDot(1);
}

// ── Navigate to track index `target` ─────────────────────────────────────────
function hlGoTo(target) {
    if (hlBusy) return;
    hlBusy = true;
    hlIdx  = target;
    hlSetDot(target <= 0 ? hlN : target > hlN ? 1 : target);

    $('.mobile-carousel .mobile-carousel-inner').animate({ left: -target * hlSlot }, 350, function () {
        // Silently teleport from clone to real counterpart (identical content = invisible jump)
        if      (target === 0)       { hlIdx = hlN; $(this).css('left', -hlN  * hlSlot); }
        else if (target === hlN + 1) { hlIdx = 1;   $(this).css('left', -hlSlot); }
        hlBusy = false;
    });
}

// ── Activate dot n (1-based) ──────────────────────────────────────────────────
function hlSetDot(n) {
    $('.mobile-carousel .highlight-dots button').removeClass('active').eq(n - 1).addClass('active');
}
