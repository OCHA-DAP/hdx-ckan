/**
 * dataset.js
 *
 * Behaviour for the v2 full dataset page:
 *   - Section accordion (collapsible sections)
 *
 * Smooth scroll, mobile anchor-nav dropdown and active-section tracking
 * are handled by fanstatic/v2/components/anchor-links.js.
 */

document.addEventListener('DOMContentLoaded', function () {
    initSectionAccordions();
});

// ── Section accordions ────────────────────────────────────────

function initSectionAccordions() {
    var headers = document.querySelectorAll(
        '.hdx-v2-dataset-section--collapsible .hdx-v2-dataset-section__header'
    );

    headers.forEach(function (header) {
        header.addEventListener('click', toggleSection);
        header.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleSection.call(header);
            }
        });
    });
}

function toggleSection() {
    var section = this.closest('.hdx-v2-dataset-section--collapsible');
    if (!section) return;
    var isOpen  = section.classList.contains('is-open');
    section.classList.toggle('is-open', !isOpen);
    this.setAttribute('aria-expanded', String(!isOpen));
}
