document.addEventListener('DOMContentLoaded', function () {
    window.hdxCarousel.init({
        containerSelector: '.mobile-carousel',
        slideSelector:     '.highlight-slide',
        prevBtnSelector:   '.hdx-v2-highlights__arrow--prev',
        nextBtnSelector:   '.hdx-v2-highlights__arrow--next',
        mediaQuery:        '(min-width: 80rem)',
        dotsSelector:      '.highlight-dots',
    });
});
