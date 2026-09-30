// ============================================================
// data-use-survey-drawer.js — "HDX Data Use Survey" c-drawer
// Renders from templates/v2/data-use-survey-drawer.html (dataset page,
// only when the organisation has a user_survey_url). v2 port of the
// survey popup in resource-list.js: a v2 resource card Download click
// opens the drawer with an intro; "Take the survey" loads the survey in
// an iframe ("Not now" closes via data-drawer-close). Shown until the user
// completes the survey. While pending it takes precedence over the
// download-triggered notifications drawer (notification_platform/subscribe.js).
// ============================================================
document.addEventListener('DOMContentLoaded', function () {
  'use strict';

  var DRAWER_ID = 'dataUseSurveyDrawer';

  var drawer = document.getElementById(DRAWER_ID);
  if (!drawer) return;
  var intro = drawer.querySelector('[data-survey-intro]');
  var startButton = drawer.querySelector('[data-survey-start]');
  var iframe = drawer.querySelector('.hdx-v2-data-use-survey-drawer__iframe');

  var orgName = iframe.getAttribute('data-org-name');
  // Same key as resource-list.js, so a survey completed on v1 stays completed.
  var SURVEY_KEY = '/organization:hdx-data-use-survey-popup-' + orgName;
  var resourceId = '';
  var loadCount = 0;

  function isPending() {
    return !window.localStorage.getItem(SURVEY_KEY);
  }

  function buildSurveyUrl() {
    return iframe.getAttribute('data-survey-url')
      .replaceAll('hdx_organization_name', orgName)
      .replaceAll('hdx_dataset_id', iframe.getAttribute('data-dataset-url'))
      .replaceAll('hdx_resource_id', resourceId);
  }

  window.hdxV2.dataUseSurvey = { isPending: isPending };

  startButton.addEventListener('click', function () {
    hdxUtil.analytics.sendSurveyEvent('confirm popup');
    intro.setAttribute('hidden', '');
    iframe.removeAttribute('hidden');
    loadCount = 0;
    iframe.src = buildSurveyUrl();
    iframe.focus();
  });

  // The first load is the survey itself; a further load means the survey
  // navigated after being submitted.
  iframe.addEventListener('load', function () {
    if (!drawer.classList.contains('is-open') || iframe.hidden) return;
    loadCount++;
    if (loadCount > 1) window.localStorage.setItem(SURVEY_KEY, 'true');
  });

  // Unload the survey so the next open starts fresh.
  drawer.addEventListener('drawer:close', function () {
    iframe.src = 'about:blank';
  });

  document.addEventListener('click', function (e) {
    var clickTarget = e.target instanceof Element ? e.target : e.target.parentElement;
    if (!clickTarget) return;

    var downloadButton = clickTarget.closest('.resource-download-button');
    if (!downloadButton) return;
    if (!downloadButton.closest('.c-resource-card')) return;

    if (!isPending()) return;

    resourceId = downloadButton.getAttribute('data-resource-id') || '';
    intro.removeAttribute('hidden');
    iframe.setAttribute('hidden', '');
    window.hdxV2Drawer(DRAWER_ID).open();
    hdxUtil.analytics.sendSurveyEvent('show popup');
  });
});
