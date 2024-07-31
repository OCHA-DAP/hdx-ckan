(function () {
  const ALLOWED_COLUMN_TYPES = ['character varying', 'integer', 'numeric'];
  const NOT_ALLOWED_PROPERTIES = ['ogc_fid', '__geometryDimension', 'srid'];

  let info;

  const options = {
    pcode: null,
    value: null,
    pcodeSelectorId: '#pcode',
    valueSelectorId: '#value',
    baseLayer: null,
    invertLatLong: true,
    boundaryPoly: {
      minLat: null,
      maxLat: null,
      minLong: null,
      maxLong: null,
      overlap: true,
    },
    data: null,
    fields: null,
    geoData: null,
    pcodeMap: {},
  };

  const defaultStyle = {
    type: 'fill',
    paint: {
      'fill-color': 'hsl(4, 100%, 62%)',
      'fill-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 0.8, 0.6],
      'fill-outline-color': 'hsl(4, 100%, 31%)',
    },
  };
  const defaultLineStyle = {
    type: 'line',
    paint: {
      'line-width': ['case', ['boolean', ['feature-state', 'hover'], false], 6, 3],
      'line-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 0.8, 0.6],
      'line-color': 'hsl(4, 100%, 62%)',
    },
  };
  const defaultPointStyle = {
    type: 'circle',
    paint: {
      'circle-color': 'hsl(4, 100%, 62%)',
      'circle-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 0.8, 0.6],
      'circle-radius': ['case', ['boolean', ['feature-state', 'hover'], false], 11, 8],
    },
  };

  let vectorTileBaseMapConfig = {
    baseMapUrl: null,
    token: null,
  };
  let vectorTileHDXLayerConfig = {
    serverUrl: null,
  };

  /**
   * Class implementing the information panel that appears when hovering over the layer
   */
  class InfoControl {
    onAdd(map) {
      this._map = map;
      this._container = document.createElement('div');
      this._container.className = 'map-info maplibregl-ctrl';
      this._container.textContent = 'Hello, world';
      return this._container;
    }
    onRemove() {
      this._container.parentNode.removeChild(this._container);
      this._map = undefined;
    }
    update(props) {
      let innerData = '';
      if (props) {
        for (const key in props) {
          if (!NOT_ALLOWED_PROPERTIES.includes(key)) {
            const value = props[key];
            innerData +=
              '<tr><td style="text-align: right;">' +
              key +
              '</td><td>&nbsp;&nbsp; <b>' +
              value +
              '</b><td></tr>';
          }
        }
      }
      this._container.innerHTML =
        '<h4>' +
        'Shape info' +
        '</h4>' +
        (props ? '<table>' + innerData + '</table>' : 'Hover over a shape');
    }
    showOtherMessage(message) {
      this._container.innerHTML = message;
    }
  }

  /**
   * Class implementing layers control to allow toggling the visibility of the layers
   */
  class LayersControl {
    constructor(ctrls) {
      this._container = document.createElement('div');
      this._container.classList.add('maplibregl-ctrl', 'maplibregl-ctrl-group', 'layers-control');
      this._ctrls = ctrls;
      this._inputs = [];
      const hover = document.createElement('a');
      hover.classList.add('layers-control-toggle');
      hover.href = '#';
      const list = document.createElement('div');
      list.classList.add('layers-control-list');
      this._container.appendChild(hover);
      this._container.appendChild(list);
      for (const [key, [value, bounds]] of Object.entries(this._ctrls)) {
        const labeled_checkbox = this._createLabeledCheckbox(key, value, bounds);
        list.appendChild(labeled_checkbox);
      }
    }

    _createLabeledCheckbox(key, value, bounds) {
      const label = document.createElement('label');
      label.classList.add('layer-control');
      const text = document.createTextNode(key);
      const input = document.createElement('input');
      this._inputs.push(input);
      input.type = 'checkbox';
      input.id = key;
      input.value = value;
      input.bounds = bounds;
      input.addEventListener('change', (e) => {
        const layer = e.target.value;
        const visibility = e.target.checked ? 'visible' : 'none';
        this._map.setLayoutProperty(layer, 'visibility', visibility);
        if (e.target.checked) this._map.fitBounds(e.target.bounds);
      });
      label.appendChild(input);
      label.appendChild(text);
      return label;
    }

    onAdd(map) {
      this._map = map;
      for (const input of this._inputs) {
        const layername = this._ctrls[input.id][0];
        let isVisible = true;
        isVisible = isVisible && this._map.getLayoutProperty(layername, 'visibility') !== 'none';
        input.checked = isVisible;
      }
      return this._container;
    }

    onRemove(map) {
      this._container.parentNode.removeChild(this._container);
      this._map = undefined;
    }
  }

  /**
   * Determine HDX vector tile server config (especially base/origin URL) from vector tile layer URL
   * @param {string} layerUrl
   */
  function setVectorTileHDXLayerConfig(layerUrl) {
    let hdxVectorTileServerUrl = null;
    try {
      const urlObj = new URL(layerUrl);
      hdxVectorTileServerUrl = urlObj.origin;
    }
    catch (e) {
      hdxVectorTileServerUrl= window.location.origin;
    }
    vectorTileHDXLayerConfig.serverUrl= hdxVectorTileServerUrl;
  }


  /**
   * Determine vector tile base map config (base map URL and token) from hidden <div>
   */
  function setVectorTileBaseMapConfig() {
    let baseMapUrl = null;
    let token = null;
    let urlObj = null;
    try {
      const config = JSON.parse($('#mapbox-baselayer-url-div').text());
      baseMapUrl = config.baseMapUrl;
      token = config.token;
      urlObj = new URL(baseMapUrl);
    }
    catch (e) {
      baseMapUrl = baseMapUrl || '/mapbox';
      token = token || 'cacheToken';
      urlObj = new URL(baseMapUrl, window.location.href);
    }
    vectorTileBaseMapConfig.baseMapUrl = urlObj.href;
    vectorTileBaseMapConfig.token = token;
  }

  function getLayerStyling(geomType) {
    const geomTypeUpper = geomType.toUpperCase();
    if (['POINT', 'MULTIPOINT', 'ST_POINT', 'ST_MULTIPOINT'].includes(geomTypeUpper)) {
      return defaultPointStyle;
    } else if (
      ['LINESTRING', 'MULTILINESTRING', 'ST_LINESTRING', 'ST_MULTILINESTRING'].includes(
        geomTypeUpper
      )
    ) {
      return defaultLineStyle;
    } else return defaultStyle;
  }

  function getBounds(BBOX) {
    const bboxArray = BBOX.replace('BOX(', '').replace(')', '').split(',');
    const xmin = Number(bboxArray[0].split(' ')[0]);
    const ymin = Number(bboxArray[0].split(' ')[1]);
    const xmax = Number(bboxArray[1].split(' ')[0]);
    const ymax = Number(bboxArray[1].split(' ')[1]);
    const bounds = [
      [xmin, ymin],
      [xmax, ymax],
    ];
    return bounds;
  }

  /**
   * Compute full URL for HDX vector tiles
   * @param {string} url
   * @returns {string}
   */
  function computeHDXVectorTilesUrl(url) {
    let tilesBaseUrl = url;
    if (url.startsWith('//')) {
      tilesBaseUrl = vectorTileHDXLayerConfig.serverUrl.startsWith('https://') ? 'https:' + url : 'http:' + url;
    }
    else if (!url.startsWith('https://') && !url.startsWith('http://')) {
      tilesBaseUrl = vectorTileHDXLayerConfig.serverUrl + url;
    }
    return tilesBaseUrl + '?geom=wkb_geometry&fields=ogc_fid';
  }

  async function getFieldListAndBuildLayer(layerData, info, firstAdded, options, layers) {
    const tilesURL = computeHDXVectorTilesUrl(layerData.url);
    const bounds = getBounds(layerData.bounding_box);
    const res = await fetch(`${vectorTileHDXLayerConfig.serverUrl}/gis/layer-type/${layerData.layer_id}`);
    let geomType;
    if (res.ok) {
      const resJSON = await res.json();
      geomType = resJSON.result;
    } else {
      const tile0 = tilesURL.replace('{z}', '0').replace('{x}', '0').replace('{y}', '0');
      const r = await fetch(tile0);
      const buffer = await r.arrayBuffer();
      const tileLayer = new VectorTile(new Pbf(buffer)).layers[layerData.layer_id];
      geomType = tileLayer ?
        tileLayer.feature(0).toGeoJSON(0, 0, 0).geometry.type
        : 'ST_MultiPolygon';
    }

    /**
     * Create a layer with the given extra fields
     * @param {string} extraFields - extra fields given as URL params string to be added to the URL requesting PBFs
     */
    function createLayer(extraFields) {
      const map = options.map;
      map.addSource(layerData.layer_id, {
        type: 'vector',
        promoteId: 'ogc_fid',
        tiles: [tilesURL + extraFields],
      });
      map.addLayer({
        id: layerData.layer_id,
        source: layerData.layer_id,
        'source-layer': layerData.layer_id,
        ...getLayerStyling(geomType),
      });
      const visibility = firstAdded ? 'visible' : 'none';
      map.setLayoutProperty(layerData.layer_id, 'visibility', visibility);

      let featureId;

      function onMouseMove(e) {
        if (e.features.length > 0) {
          map.getCanvas().style.cursor = 'pointer';
          if (featureId) {
            map.setFeatureState(
              { source: layerData.layer_id, sourceLayer: layerData.layer_id, id: featureId },
              { hover: false }
            );
          }
          featureId = e.features[0].id;
          info.update(e.features[0].properties);
          map.setFeatureState(
            { source: layerData.layer_id, sourceLayer: layerData.layer_id, id: featureId },
            { hover: true }
          );
        }
      }

      function onMouseLeave() {
        if (featureId) {
          map.getCanvas().style.cursor = '';
          map.setFeatureState(
            { source: layerData.layer_id, sourceLayer: layerData.layer_id, id: featureId },
            { hover: false }
          );
        }
        featureId = undefined;
        info.update();
      }

      map.on('mousemove', layerData.layer_id, onMouseMove);
      map.on('mouseleave', layerData.layer_id, onMouseLeave);

      if (firstAdded) options.map.fitBounds(bounds, { animate: false });
    }

    let promise = null;
    const layer_fields = layerData.layer_fields;
    if (layer_fields && layer_fields.length > 0) {
      // New way in which the fields are stored in 'shape_info' in CKAN

      let extraFields = '';
      for (let i = 0; i < layer_fields.length; i++) {
        const field = layer_fields[i];
        if (field.field_name !== 'ogc_fid' && ALLOWED_COLUMN_TYPES.indexOf(field.data_type) >= 0) {
          const escaped_field_name = encodeURIComponent(field.field_name);
          extraFields += ',"' + escaped_field_name + '"';
        }
      }
      createLayer(extraFields);
    }
    return promise;
  }

  async function getData(options) {

    /**
     * List of shape info for each geopreviewable resource
     * @type {[{resource_name: string, url: string, bounding_box: string, layer_fields: Array, layer_id: string}]}
     */
    const data = options.data;
    const layers = [];

    info = new InfoControl();
    options.map.addControl(info, 'top-left');
    info.update();

    const promises = [];
    let firstAdded = true;
    for (let idx = 0; idx < data.length; idx++) {
      const promise = await getFieldListAndBuildLayer(
        data[idx],
        info,
        firstAdded,
        options,
        layers,
        data[idx].resource_name
      );
      if (firstAdded) {
        firstAdded = false;
      }
      if (promise) promises.push(promise);
    }

    $.when.apply($, promises).done(() => {
      layerConfig = {};
      for (const row of data) {
        layerConfig[row.resource_name] = [row.layer_id, getBounds(row.bounding_box)];
      }
      options.map.addControl(new LayersControl(layerConfig), 'top-right');
    });

    $('.map-info').mousedown(function (event) {
      event.stopPropagation();
    });
  }

  /**
   * Function that runs when the map is being initialized by MapLibre
   */
  function initMap() {
    const map = options.map;
    const customAttributionConfig = {
      compact: true,
      customAttribution: '<a href="https://www.maplibre.org/" target="_blank">MapLibre</a>' +
        ' | <a href="https://www.mapbox.com/about/maps/" target="_blank">Mapbox</a>'
    };
    map.addControl(new maplibregl.AttributionControl(customAttributionConfig), 'top-right');
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
    map.scrollZoom.disable();
    map.dragRotate.disable();
    map.keyboard.disable();
    map.touchZoomRotate.disableRotation();
    getData(options);
  }

  function isMapboxURL(r) {
    return 0 === r.indexOf('mapbox:');
  }
  function transformMapboxUrl(r, t, o) {
    return r.indexOf('/styles/') > -1 && -1 === r.indexOf('/sprite')
      ? { url: normalizeStyleURL(r, o) }
      : r.indexOf('/sprites/') > -1
      ? { url: normalizeSpriteURL(r, o) }
      : r.indexOf('/fonts/') > -1
      ? { url: normalizeGlyphsURL(r, o) }
      : r.indexOf('/v4/') > -1 || 'Source' === t
      ? { url: normalizeSourceURL(r, o) }
      : void 0;
  }
  function parseUrl(r) {
    const t = r.match(/^(\w+):\/\/([^/?]*)(\/[^?]+)?\??(.+)?/);
    if (!t) throw new Error('Unable to parse URL object');
    return {
      protocol: t[1],
      authority: t[2],
      path: t[3] || '/',
      params: t[4] ? t[4].split('&') : [],
    };
  }
  function formatUrl(r, t) {
    const o = parseUrl(vectorTileBaseMapConfig.baseMapUrl);
    (r.protocol = o.protocol), (r.authority = o.authority),
      (r.path = o.path + r.path), r.params.push(`access_token=${t}`);
    const n = r.params.length ? `?${r.params.join('&')}` : '';
    return `${r.protocol}://${r.authority}${r.path}${n}`;
  }
  function normalizeStyleURL(r, t) {
    const o = parseUrl(r);
    return (o.path = `/styles/v1${o.path}`), formatUrl(o, t);
  }
  function normalizeGlyphsURL(r, t) {
    const o = parseUrl(r);
    return (o.path = `/fonts/v1${o.path}`), formatUrl(o, t);
  }
  function normalizeSourceURL(r, t) {
    const o = parseUrl(r);
    return (o.path = `/v4/${o.authority}.json`), o.params.push('secure'), formatUrl(o, t);
  }
  function normalizeSpriteURL(r, t) {
    const o = parseUrl(r);
    let n = o.path.split('.'),
      e = n[0];
    const a = n[1];
    let s = '';
    return (
      e.indexOf('@2x') && ((e = e.split('@2x')[0]), (s = '@2x')),
      (o.path = `/styles/v1${e}/sprite${s}.${a}`),
      formatUrl(o, t)
    );
  }
  function normalizeTiles(r, t) {
    const o = parseUrl(r);
    for (let i = 0; i < o.params.length; i++) {
      const key = o.params[i].split('=');
      if ('access_token' === key[0]) {
        o.params.splice(i, 1); // remove item from params
        break;
      }
    }
    return formatUrl(o, t);
  }

  function buildMap(options) {

    /**
     * Transform requests URLs
     * @param {string} url
     * @param {string} resourceType
     * @returns {{url: string}}
     */
    function transformRequest(url, resourceType) {
      if (isMapboxURL(url)) return transformMapboxUrl(url, resourceType, vectorTileBaseMapConfig.token);
      if (url.indexOf('tiles.mapbox') > 0) return {url: normalizeTiles(url, vectorTileBaseMapConfig.token)};
      return { url };
    }

    options.data = JSON.parse($('#shapeData').text());
    setVectorTileHDXLayerConfig(options.data[0].url);
    options.map = new maplibregl.Map({
      container: 'map',
      attributionControl: false,
      style: 'mapbox://styles/humdata/cl3lpk27k001k15msafr9714b',
      transformRequest,
      bounds: getBounds(options.data[0].bounding_box),
    });
    options.map.once('load', initMap);
  }

  $(function () {
    setVectorTileBaseMapConfig();
    buildMap(options);
  });
})();
