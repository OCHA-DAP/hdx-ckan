/**
 * charts.js
 *
 * All v2 Chart.js behaviour (task 058), consolidated into one module:
 *
 *   - Org stats page (#chart-data-pageviews, #chart-data-top-downloads):
 *     downloads & page views line chart, top-downloads horizontal bar
 *     chart with clickable dataset-name labels (D2/D6), wheel zoom + drag
 *     pan via chartjs-plugin-zoom (D7), and the single-dataset special
 *     case that renders the shared weekly-downloads line chart instead (D3).
 *   - Dataset page (#dataset-downloads-chart): the same shared
 *     weekly-downloads line chart, second call site (D3).
 *
 * Every color/font/spacing value is read from a design token via token()/
 * tokenPx() — no hardcoded fallback values, since these tokens are always
 * defined in the v2 stylesheet loaded on every page this script runs on.
 *
 * Chart data is server-rendered JSON in hidden divs — no AJAX. Self-inits
 * on DOMContentLoaded, detecting which chart containers are present.
 * Requires the 'v2-chart-scripts' bundle (Chart.js UMD + date-fns adapter
 * bundle + zoom plugin) to be loaded first.
 */
(function (window, document) {
    'use strict';

    var MAX_VISIBLE_BARS = 7;      // v1 zoom window: MAX_NUMBER_OF_VALUES = 7.5
    var MAX_LABEL_WIDTH = 174;     // px — Figma: 10.875rem dataset-name column

    var token = window.hdxV2.token;
    var tokenPx = window.hdxV2.tokenPx;

    function tickFont() {
        return { family: token('--hdx-font-body'), size: tokenPx('--hdx-fs-xs') };
    }

    function reducedMotion() {
        return window.hdxV2.prefersReducedMotion();
    }

    // Wraps the container as .hdx-v2-chart and returns a canvas inside an
    // absolutely-positioned holder, so Chart.js can shrink as well as grow.
    function createCanvas(container) {
        container.classList.add('hdx-v2-chart');
        var holder = document.createElement('div');
        holder.className = 'hdx-v2-chart__canvas';
        var canvas = document.createElement('canvas');
        holder.appendChild(canvas);
        container.appendChild(holder);
        return canvas;
    }

    function readJson(id) {
        var el = document.getElementById(id);
        if (!el) return null;
        try {
            return JSON.parse(el.textContent);
        } catch (e) {
            return null;
        }
    }

    // ── y-axis helpers, ported from the v1 C3 stats-chart.js ─────────

    // "Nice" y-axis max: ceiling to one significant digit (1418 → 2000).
    function niceMax(maxValue) {
        var rounded = maxValue;
        var multiplier = 1;
        while (rounded > 1) {
            rounded /= 10;
            multiplier *= 10;
        }
        rounded = rounded * 10;
        multiplier /= 10;
        return Math.ceil(rounded) * multiplier;
    }

    // ── External tooltip driving a template-rendered c-tooltip--graph ─
    //
    // opts.title(tooltip)    → title string  (default: Chart.js title)
    // opts.value(dataPoint)  → row value string (default: raw y value)
    // Rows are matched to the tooltip's data points by dataset index, so
    // the template must render one legend row per dataset, in order.
    function makeGraphTooltip(opts) {
        opts = opts || {};
        return function (context) {
            var chart = context.chart;
            var tooltip = context.tooltip;
            var wrap = chart.canvas.closest('.hdx-v2-chart');
            var tooltipEl = wrap ? wrap.querySelector('.c-tooltip--graph') : null;
            if (!tooltipEl) return;

            if (tooltip.opacity === 0 || !tooltip.dataPoints || !tooltip.dataPoints.length) {
                tooltipEl.style.opacity = '0';
                return;
            }

            var titleEl = tooltipEl.querySelector('.c-tooltip__text');
            if (titleEl) {
                titleEl.textContent = opts.title
                    ? opts.title(tooltip)
                    : (tooltip.title || []).join(' ');
            }

            var rows = tooltipEl.querySelectorAll('.c-tooltip__legend-row');
            tooltip.dataPoints.forEach(function (dataPoint, i) {
                var row = rows[dataPoint.datasetIndex] || rows[i];
                if (!row) return;
                var valueEl = row.querySelector('.c-tooltip__legend-value');
                if (valueEl) {
                    valueEl.textContent = opts.value
                        ? opts.value(dataPoint)
                        : String(dataPoint.parsed.y);
                }
            });

            // Above the caret, horizontally centered, clamped to the chart
            var offset = tokenPx('--hdx-space-3');
            tooltipEl.style.opacity = '1';
            var left = tooltip.caretX - tooltipEl.offsetWidth / 2;
            left = Math.max(0, Math.min(left, wrap.clientWidth - tooltipEl.offsetWidth));
            var top = tooltip.caretY - tooltipEl.offsetHeight - offset;
            if (top < 0) top = tooltip.caretY + offset;
            tooltipEl.style.left = left + 'px';
            tooltipEl.style.top = top + 'px';
        };
    }

    // ── Shared weekly-downloads line chart (Charts C & D) ─────────────
    //
    // options.height      {number} container height in px  (default 120)
    // options.seriesLabel {string} tooltip row label        (default 'Downloads')
    function setupDatasetDownloads(dataDivId, containerId, options) {
        options = options || {};
        var dataEl = document.querySelector(dataDivId);
        var container = document.querySelector(containerId);
        if (!dataEl || !container || !window.Chart) return null;

        var chartData;
        try {
            chartData = JSON.parse(dataEl.textContent);
        } catch (e) {
            return null;
        }
        if (!chartData || !chartData.length) return null;

        var maxValue = 0;
        chartData.forEach(function (item) {
            if (item.value > maxValue) maxValue = item.value;
        });

        var yMax = niceMax(maxValue);
        var tickValues = [];
        var seenTicks = {};
        [yMax / 4, yMax / 2, (3 * yMax) / 4, yMax].forEach(function (value) {
            var rounded = Math.round(value);
            if (!seenTicks[rounded]) {
                seenTicks[rounded] = true;
                tickValues.push(rounded);
            }
        });

        var lineColor = token('--hdx-primary-5');
        var lastIndex = chartData.length - 1;

        container.style.height = (options.height || 120) + 'px';
        var canvas = createCanvas(container);

        return new window.Chart(canvas, {
            type: 'line',
            data: {
                labels: chartData.map(function (item) { return item.date; }),
                datasets: [{
                    label: options.seriesLabel || 'Downloads',
                    data: chartData.map(function (item) { return item.value; }),
                    borderColor: lineColor,
                    backgroundColor: lineColor,
                    borderWidth: 2,
                    pointRadius: 2.5,
                    pointHoverRadius: 4,
                    clip: false,
                    // v1's C3 'dashed' region on the most recent (partial) week
                    segment: {
                        borderDash: function (ctx) {
                            return ctx.p1DataIndex === lastIndex ? [2, 2] : undefined;
                        }
                    }
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: reducedMotion() ? false : undefined,
                interaction: { mode: 'index', intersect: false },
                layout: { padding: tokenPx('--hdx-space-2') },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month',
                            displayFormats: { month: 'MMM' },
                            tooltipFormat: 'dd MMM yyyy'
                        },
                        grid: { display: false },
                        border: { display: false },
                        ticks: { color: token('--hdx-neutral-8'), font: tickFont() }
                    },
                    y: {
                        min: 0,
                        max: yMax,
                        afterBuildTicks: function (axis) {
                            axis.ticks = tickValues.map(function (value) {
                                return { value: value };
                            });
                        },
                        ticks: {
                            color: token('--hdx-neutral-8'),
                            font: tickFont()
                        },
                        grid: { color: token('--hdx-neutral-3') },
                        border: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false, external: makeGraphTooltip() }
                }
            }
        });
    }

    // ── Chart A: downloads & page views per week (org stats page) ─────

    function initPageviewsChart() {
        var container = document.getElementById('chart-data-pageviews');
        var data = readJson('stats-data-pageviews');
        if (!container || !data) return;

        var pageviewsColor = token('--hdx-primary-5');
        var downloadsColor = token('--hdx-primary-2');
        var lastIndex = data.length - 1;

        function dashLastSegment(ctx) {
            // v1's C3 'dashed' region on the most recent (partial) week
            return ctx.p1DataIndex === lastIndex ? [2, 2] : undefined;
        }

        var canvas = createCanvas(container);
        new window.Chart(canvas, {
            type: 'line',
            data: {
                labels: data.map(function (item) { return item.date; }),
                datasets: [
                    {
                        label: 'Page views',
                        data: data.map(function (item) { return item.pageviews; }),
                        borderColor: pageviewsColor,
                        backgroundColor: pageviewsColor,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 5,
                        clip: false,
                        segment: { borderDash: dashLastSegment }
                    },
                    {
                        label: 'Downloads',
                        data: data.map(function (item) { return item.downloads; }),
                        borderColor: downloadsColor,
                        backgroundColor: downloadsColor,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 5,
                        clip: false,
                        segment: { borderDash: dashLastSegment }
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: reducedMotion() ? false : undefined,
                interaction: { mode: 'index', intersect: false },
                layout: { padding: tokenPx('--hdx-space-2') },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month',
                            displayFormats: { month: 'MMM yyyy' },
                            tooltipFormat: 'dd MMM yyyy'
                        },
                        grid: { display: false },
                        border: { display: false },
                        ticks: { color: token('--hdx-neutral-8'), font: tickFont() }
                    },
                    y: {
                        grid: { color: token('--hdx-neutral-3') },
                        border: { display: false },
                        ticks: {
                            color: token('--hdx-neutral-8'),
                            font: tickFont(),
                            precision: 0
                        }
                    }
                },
                plugins: {
                    legend: { display: false },     // template renders the Figma legend
                    tooltip: { enabled: false, external: makeGraphTooltip() }
                }
            }
        });
    }

    // ── Chart B: top downloaded datasets, org stats page (horizontal bars) ─

    function initTopDownloadsChart() {
        var container = document.getElementById('chart-data-top-downloads');
        var data = readJson('stats-data-top-downloads');
        if (!container || !data) return;

        // Single-dataset org: render the shared weekly-downloads line
        // chart instead of a one-bar chart, exactly like v1 (D3)
        if (data.length === 1) {
            var nameEl = document.getElementById('stats-data-single-dataset-name');
            var datasetName = (nameEl ? nameEl.textContent : '').trim();
            setupDatasetDownloads(
                '#stats-data-single-dataset-downloads', '#chart-data-top-downloads',
                { height: 320, seriesLabel: datasetName || 'Downloads' }
            );
            renderSingleDatasetLegend(container, datasetName);
            return;
        }

        var barColor = token('--hdx-primary-5');
        var tickColor = token('--hdx-neutral-8');
        var font = tickFont();
        var fontStr = font.size + 'px ' + font.family;

        var config = {
            type: 'bar',
            data: {
                labels: data.map(function (item) { return item.name || ''; }),
                datasets: [{
                    label: 'Downloads',
                    data: data.map(function (item) { return item.value; }),
                    backgroundColor: barColor,
                    barThickness: tokenPx('--hdx-space-4'),
                    borderRadius: tokenPx('--hdx-space-15')
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                animation: reducedMotion() ? false : undefined,
                interaction: { mode: 'index', axis: 'y', intersect: false },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: token('--hdx-neutral-3') },
                        border: { display: false },
                        ticks: { color: tickColor, font: font, precision: 0 }
                    },
                    y: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: {
                            font: font,
                            // clickable labels (D2): hovered tick turns primary
                            color: function (ctx) {
                                return ctx.chart.$hdxTickHover === ctx.index
                                    ? barColor : tickColor;
                            },
                            // long names ellipsized at a fixed width (D8);
                            // the full name stays available in the tooltip
                            callback: function (value) {
                                var label = this.getLabelForValue(value);
                                return truncateToWidth(this.chart.ctx, label, MAX_LABEL_WIDTH, fontStr);
                            }
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: false,
                        external: makeGraphTooltip({
                            title: function (tooltip) {
                                var item = data[tooltip.dataPoints[0].dataIndex];
                                return item ? item.name : '';
                            },
                            // v1 format: "1418 (12.34% out of 60000)"
                            value: function (dataPoint) {
                                var item = data[dataPoint.dataIndex];
                                var percent = item.total
                                    ? ((item.value / item.total) * 100).toFixed(2) + '%'
                                    : '0%';
                                return item.value + ' (' + percent + ' out of ' + item.total + ')';
                            }
                        })
                    }
                }
            },
            plugins: [datasetLinksPlugin(data)]
        };

        // Wheel zoom + drag pan through the bars (D7), windowed like v1
        if (data.length > MAX_VISIBLE_BARS) {
            config.options.scales.y.min = 0;
            config.options.scales.y.max = MAX_VISIBLE_BARS;
            config.options.plugins.zoom = {
                limits: { y: { min: 0, max: data.length - 1, minRange: 3 } },
                zoom: { wheel: { enabled: true }, mode: 'y' },
                pan: { enabled: true, mode: 'y' }
            };
        }

        var canvas = createCanvas(container);
        new window.Chart(canvas, config);
    }

    // Hit-tests pointer events against the y-axis dataset-name labels and
    // opens the dataset page on click (D6 — canvas ticks can't be <a>).
    function datasetLinksPlugin(items) {
        return {
            id: 'hdxDatasetLinks',
            afterEvent: function (chart, args) {
                var event = args.event;
                var scale = chart.scales.y;
                if (!scale || event.x === null || event.y === null) return;

                var index = null;
                var inLabelArea = event.x < chart.chartArea.left &&
                    event.y >= chart.chartArea.top && event.y <= chart.chartArea.bottom;
                if (inLabelArea) {
                    var rounded = Math.round(scale.getValueForPixel(event.y));
                    if (rounded >= 0 && rounded < items.length) index = rounded;
                }

                if (event.type === 'mousemove' || event.type === 'mouseout') {
                    var hover = event.type === 'mouseout' ? null : index;
                    if (chart.$hdxTickHover !== hover) {
                        chart.$hdxTickHover = hover;
                        args.changed = true;   // repaint so the hovered label recolors
                    }
                    chart.canvas.style.cursor = hover === null ? '' : 'pointer';
                } else if (event.type === 'click' && index !== null) {
                    var item = items[index];
                    if (item && item.url) window.open(item.url, '_blank', 'noopener');
                }
            }
        };
    }

    // v1 showed a C3 legend naming the org's single dataset under the chart
    function renderSingleDatasetLegend(container, datasetName) {
        if (!datasetName) return;
        var legend = document.createElement('div');
        legend.className = 'hdx-v2-org-stats__legend';
        var item = document.createElement('span');
        item.className = 'hdx-v2-org-stats__legend-item';
        var swatch = document.createElement('span');
        swatch.className = 'hdx-v2-org-stats__legend-swatch hdx-v2-org-stats__legend-swatch--pageviews';
        item.appendChild(swatch);
        item.appendChild(document.createTextNode(datasetName));
        legend.appendChild(item);
        container.insertAdjacentElement('afterend', legend);
    }

    // Ellipsize text so it fits maxWidth when drawn on the given canvas ctx
    function truncateToWidth(ctx2d, text, maxWidth, fontStr) {
        ctx2d.save();
        ctx2d.font = fontStr;
        var result = text;
        if (ctx2d.measureText(result).width > maxWidth) {
            while (result.length > 1 && ctx2d.measureText(result + '…').width > maxWidth) {
                result = result.slice(0, -1);
            }
            result += '…';
        }
        ctx2d.restore();
        return result;
    }

    // ── Chart C/D call site: dataset page weekly downloads widget ─────

    function initDatasetPageChart() {
        var dataEl = document.getElementById('dataset-downloads-data');
        if (!dataEl) return;

        var chartData;
        try {
            chartData = JSON.parse(dataEl.textContent);
        } catch (e) {
            chartData = [];
        }

        if (chartData && chartData.length) {
            setupDatasetDownloads('#dataset-downloads-data', '#dataset-downloads-chart');
        } else {
            var noData = document.getElementById('dataset-downloads-chart-no-data');
            if (noData) noData.style.display = 'block';
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        if (!window.Chart) return;
        initPageviewsChart();
        initTopDownloadsChart();
        initDatasetPageChart();
    });
})(window, document);
