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
    if (!isOpen && section.id === 'activity') {
        fetchActivitiesIfNeeded(section);
    }
}

function fetchActivitiesIfNeeded(section) {
    var wrapper = section.querySelector('.dataset-activity-wrapper');
    if (!wrapper || wrapper.dataset.fetched !== 'false') return;
    wrapper.dataset.fetched = 'true';
    var datasetId = wrapper.dataset.datasetId;
    $.ajax({
        url: '/api/3/action/hdx_package_activity_stream',
        type: 'POST',
        headers: hdxUtil.net.getCsrfTokenAsObject(),
        contentType: 'application/json',
        data: JSON.stringify({ id: datasetId, limit: 7 }),
        success: function (response) {
            if (response.success) {
                $(wrapper).html(response.result);
                var $stream = $(wrapper).find('.c-activity-stream');
                var $empty  = $(wrapper).find('.c-activity-stream__empty');
                if ($empty.length === 0 && ($stream.length === 0 || $.trim($stream.text()) === '')) {
                    $(wrapper).html('<p class="c-activity-stream__empty">' + 'No activities found.' + '</p>');
                }
            }
        }
    });
}
