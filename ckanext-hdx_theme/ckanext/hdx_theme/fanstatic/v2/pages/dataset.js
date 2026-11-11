/**
 * dataset.js
 *
 * Behaviour for the v2 full dataset page:
 *   - Section accordion (collapsible sections)
 *   - Interactive data (custom dataviz) tab switching
 *   - Sysadmin QA actions: per-resource menu and the header CTA's bulk drawer
 *
 * Smooth scroll, mobile anchor-nav dropdown and active-section tracking
 * are handled by fanstatic/v2/components/anchor-links.js.
 */

document.addEventListener('DOMContentLoaded', function () {
    initSectionAccordions();
    initCustomDataviz();
    initQaActions();
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

// ── Interactive data (custom dataviz) ───────────────────────────

function initCustomDataviz() {
    var triggers = document.querySelectorAll('[data-custom-dataviz-trigger]');
    triggers.forEach(function (trigger) {
        trigger.addEventListener('click', function () {
            activateCustomDataviz(trigger);
        });
    });
}

function activateCustomDataviz(trigger) {
    var iframe = document.getElementById(trigger.getAttribute('data-custom-dataviz-target'));
    var url = trigger.getAttribute('data-custom-dataviz-url');
    if (iframe) iframe.src = url;

    var fullscreenLink = document.querySelector('[data-custom-dataviz-fullscreen]');
    if (fullscreenLink) fullscreenLink.href = url;
}

// ── QA actions (sysadmins) ──────────────────────────────────────

var QA_RESOURCE_ERROR = 'The resource could not be updated. Please try again.';
var QA_BULK_ERROR     = 'Not all resources could be updated. Reload the page to see their current state.';

function setQuarantine(resourceId, value) {
    var body = new URLSearchParams();
    body.append('id', resourceId);
    body.append('in_quarantine', value);
    return window.hdxV2.post('/api/3/action/hdx_mark_resource_in_quarantine', body)
        .then(function (resp) {
            if (!resp || !resp.success) throw new Error('hdx_mark_resource_in_quarantine failed');
        });
}

function initQaActions() {
    var sectionAlert = document.querySelector('#data-and-resources [data-qa-error]');

    document.addEventListener('click', function (e) {
        var item = e.target.closest && e.target.closest('[data-qa-quarantine][data-resource-id]');
        if (!item) return;
        var trigger = item.closest('.c-dropdown').querySelector('.c-dropdown__trigger');
        trigger.click();
        window.hdxV2.setDisabled(trigger, true);
        if (sectionAlert) sectionAlert.hidden = true;

        setQuarantine(item.getAttribute('data-resource-id'), item.getAttribute('data-qa-quarantine'))
            .then(function () { window.location.reload(); })
            .catch(function () {
                window.hdxV2.setDisabled(trigger, false);
                trigger.focus();
                if (sectionAlert) window.hdxV2.showAlert(sectionAlert, QA_RESOURCE_ERROR);
            });
    });

    var bulk = document.querySelector('[data-qa-bulk]');
    if (!bulk) return;
    var confirmBtn = bulk.querySelector('[data-qa-bulk-confirm]');
    var bulkAlert  = bulk.querySelector('[data-qa-error]');

    confirmBtn.addEventListener('click', function () {
        var ids   = bulk.getAttribute('data-resource-ids').split(' ').filter(Boolean);
        var value = bulk.getAttribute('data-qa-quarantine');
        bulkAlert.hidden = true;
        window.hdxV2.setDisabled(confirmBtn, true);

        ids.reduce(function (chain, id) {
            return chain.then(function () { return setQuarantine(id, value); });
        }, Promise.resolve())
            .then(function () { window.location.reload(); })
            .catch(function () {
                window.hdxV2.setDisabled(confirmBtn, false);
                confirmBtn.focus();
                window.hdxV2.showAlert(bulkAlert, QA_BULK_ERROR);
            });
    });
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
