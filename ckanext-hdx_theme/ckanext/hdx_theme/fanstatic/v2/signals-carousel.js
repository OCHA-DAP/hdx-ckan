document.addEventListener('DOMContentLoaded', function () {
    window.hdxCarousel.init({
        containerSelector: '.hdx-v2-signals-cards',
        slideSelector:     '.hdx-v2-signal-slide',
        prevBtnSelector:   '.hdx-v2-signals-carousel__arrow--prev',
        nextBtnSelector:   '.hdx-v2-signals-carousel__arrow--next',
        dotsSelector:      '.hdx-v2-signals-dots',
        mediaQuery:        '(min-width: 80rem)',
    });
});
