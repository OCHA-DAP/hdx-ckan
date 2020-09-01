let _sdcMicroColumnChange;
let _sdcSettings;
let _sdcLoadedData;
let _hot;
const MAX_NUMBER_OF_SHEETS = 8;

function _sdcMicroChangeFactory(settings, col) {
  let f = (selectEl) => {
    let selection = $(selectEl).val();
    console.log(`Selected ${selection}`);
    settings.types[col] = selection;
  };

  return f;
}

function _contextMenu(settings) {
  const dataTypeItems = [
    {key: 'type:text', name: 'text'},
    {key: 'type:double', name: 'double'},
    {key: 'type:numeric', name: 'numeric'},
    {key: 'type:date', name: 'date'}
  ];


  return {
    callback: function (key, selection, clickEvent) {
      // Common callback for all options
      // console.log(key, selection, clickEvent);
      const selectedCol = selection[0].start.col;

      if (key.startsWith('type:')) {
        _sdcSettings.types[selectedCol] = key.slice(5);
        setTimeout(() => _updatedSdcHeader(), 0);
      }
    },
    items: {
      "select": {
        name: 'Select as data column',
        callback: function (key, selection, clickEvent) {
          let hot = this;
          const selectedCol = selection[0].start.col;
          if (_sdcSettings.weightColumn === selectedCol) {
            _sdcSettings.weightColumn = null;
          }
          _sdcSettings.columns[selectedCol] = !_sdcSettings.columns[selectedCol];
          hot.render();
        }
      },
      "weight": {
        name: 'Select as weight Column',
        callback: function (key, selection, clickEvent) {
          let hot = this;
          const selectedCol = selection[0].start.col;
          if (_sdcSettings.columns[selectedCol]) {
            _sdcSettings.columns[selectedCol] = false;
          }
          if (_sdcSettings.weightColumn === selectedCol) {
            _sdcSettings.weightColumn = null;
          } else {
            _sdcSettings.weightColumn = selectedCol;
          }
          hot.render();
        }
      },
      "type": {
        name: 'Data type',
        submenu: {
          items: dataTypeItems
        }
      },
      // "type2": {
      //   renderer: function(hot, wrapper, row, col, prop, itemValue) {
      //     console.log(`Rerendering ${hot.getSelectedRange()}`);
      //     _sdcMicroColumnChange = _sdcMicroChangeFactory(_sdcSettings, col);
      //
      //     let div = document.createElement('div');
      //     div.innerHTML = `
      //       <label>Column type:</label>
      //       <select onchange="_sdcMicroColumnChange(this)">
      //         ${dataTypeItems.map(({key, name}, i) => `
      //           <option name="${key}" ${key===_sdcSettings.types[col] ?`selected=selected`:``}>${name}</option>
      //         `).join('')}
      //       </select>
      //     `;
      //
      //     return div;
      //   },
      //   isCommand: false // prevent clicks from executing command and closing the menu
      // }
    }
  }
}

function _updatedSdcHeader() {
  const colHeader = _hot.getColHeader();
  _hot.updateSettings({
    nestedHeaders: [
      colHeader,
      _sdcSettings.types
    ]
  });
  _hot.render();
}

function _renderHandsonTable(data) {
  const columnsNo = data[0].length;
  let selected = Array(columnsNo).fill(false);
  let types = Array(columnsNo).fill('text');

  _sdcSettings = {
    ..._sdcSettings,
    columns: selected,
    types: types,
    weightColumn: null
  };
  _hot.updateSettings({
    data: data,
    cells: null
  });
  _hot.updateSettings({
    cells: function (row, col) {
      let cell = _hot.getCell(row, col);
      if (!cell)
        return;
      if (_sdcSettings.weightColumn === col) {
        cell.className = 'sdc-col-weight';
      }
      if (_sdcSettings.columns[col]) {
        cell.className = 'sdc-col-selected';
      }
    }
  });
  _updatedSdcHeader();
}

function _prepareHandsonSettings(datasetId, resourceId) {
  _sdcSettings = {
    datasetId: datasetId,
    resourceId: resourceId
  };

}

function _initHandsonTable(data) {
  $("#sdc-micro-spinner").show();
  let container = document.getElementById("sdc-micro-table");

  const contextMenu = _contextMenu(_sdcSettings);
  const settings = {
    readOnly: true,
    rowHeaders: true,
    colHeaders: true,
    filters: true,
    // as per HDX-7042, cells were not rendered and couldn't be selected from the menu
    viewportColumnRenderingOffset: 1000,
    viewportRowRenderingOffsetNumber: 25,
    dropdownMenu: contextMenu,
    contextMenu: contextMenu,
    afterInit: () => {
      $("#sdc-micro-spinner").hide();
    },
    licenseKey: 'non-commercial-and-evaluation'
  };

  if (_hot) {
    _hot.destroy();
  }

  _hot = new Handsontable(container, settings);

  let adaptRunButtonState = () => {
    let reducer = (accumulator, currentValue) => accumulator + currentValue ? 1 : 0;
    let selectedNum = _sdcSettings.columns.reduce(reducer, 0);
    if (selectedNum > 0) {
      $("#qa-sdc-popup-save").removeClass('disabled');
    } else {
      $("#qa-sdc-popup-save").addClass('disabled');
    }
  };
  Handsontable.hooks.add('afterRender', adaptRunButtonState, _hot);

  _renderHandsonTable(data);
}

function _loadSheetNames(resourceURL) {
  let hxlProxyUrl = $('#qa-sdc-hxl-proxy').text();
  let encodedResourceUrl = encodeURIComponent(resourceURL);

  return new Promise((resolve, reject) => {
    let data = {
      url: resourceURL,
      sheets: 1,
      sheetNames: ['Data']
    };
    $.get(`${hxlProxyUrl}/api/data-preview-sheets.json?url=${encodedResourceUrl}`)
      .done((sheets) => {
        data.sheets = sheets.length;
        data.sheetNames = sheets;
      })
      .fail(() => {
        alert('Error getting list of sheets. Trying to get just the first sheet.')
      })
      .always(() => {
        resolve(data);
      });
  });
}

function _loadData(data) {
  let hxlProxyUrl = $('#qa-sdc-hxl-proxy').text();
  let encodedResourceUrl = encodeURIComponent(data.url);

  return new Promise((resolve, reject) => {
    let ajaxCalls = Array.from(Array(data.sheets).keys()).map((sheet) => $.get(`${hxlProxyUrl}/api/data-preview.json?rows=20&sheet=${sheet}&url=${encodedResourceUrl}`));
    $.when(...ajaxCalls)
      .done((...results) => {
        if (data.sheets > 1) {
          data.content = results.map((result) => result[0]);
        } else {
          data.content = [results[0]];
        }

        resolve(data);
      })
      .fail(() => reject('Cannot load data'));
  });
}

function _loadSheet(el, sheet) {
  $('#qa-sdc-widget .nav .nav-item').removeClass('active');
  $(el).parent('.nav-item').addClass('active');
  _sdcSettings.sheet = sheet;
  _initHandsonTable(_sdcLoadedData.content[sheet]);
}

function _generateTabs(data) {
  let tabs = $("#qa-sdc-widget .nav");
  const navTabs = Array.from(Array(data.sheets));
  const firstNavTabs = navTabs.slice(0, 4);
  const lastNavTabs = navTabs.slice(4);

  function __computeDisplaySheetName(sheetName) {
    return sheetName.length < 25 ? sheetName : sheetName.substring(0, 25) + '...';
  }

  let content = firstNavTabs.map((_, i) => {
    const sheetName = data.sheetNames[i];
    const displaySheetName = __computeDisplaySheetName(sheetName);
    return `
    <li class="nav-item ${i === 0 ? 'active' : ''}">
      <a title="${sheetName}" class="nav-link sdc-sheet-name normal-sheets"
            href="#" data-sheet="${i}">${displaySheetName}</a>
    </li>
    `
  }).join('');

  if (lastNavTabs.length > 0) {
    const offset = firstNavTabs.length;
    const dropupContent = lastNavTabs.map(((_, i) => {
      const realIdx = offset + i;
      const sheetName = data.sheetNames[realIdx];
      const displaySheetName = __computeDisplaySheetName(sheetName);
      return `
       <li>
            <a title="${sheetName}" class="sdc-sheet-name extra-sheets"
                href="#" data-sheet="${realIdx}">${displaySheetName}</a>
       </li>
      `
    })).join('');

    content += `
    <li role="presentation" class="dropup" id="extra-sheets-dropup">
      <a class="dropdown-toggle" data-toggle="dropdown" href="#" role="button"
        aria-haspopup="true" aria-expanded="false">
        More tabs ... <span class="caret"></span>
      </a>
      <ul class="dropdown-menu">
        ${dropupContent}
      </ul>
    </li>
    `;
  }

  tabs.html(content);
  tabs.find('.sdc-sheet-name').click((ev) => {
    const clickedSheet = $(ev.currentTarget);
    let sheet = clickedSheet.attr('data-sheet');

    // reset state
    $('.extra-sheets').removeClass('active');

    const extraSheetsDropup = $('#extra-sheets-dropup');
    extraSheetsDropup.removeClass('active');
    if (clickedSheet.hasClass('extra-sheets')) {
      clickedSheet.addClass('active');
      extraSheetsDropup.addClass('active');
    }
    _loadSheet(ev.currentTarget, sheet);
  });
}

function _getS3ResourceURL(resourceId, resolve, reject) {
  $.get(`/api/action/hdx_get_s3_link_for_resource?id=${resourceId}`)
    .done((data) => {
      console.log(data);
      resolve(data.result.s3_url);
    })
    .fail((error) => {
      reject(error);
    });
}

function _loadResourcePreviewData(datasetId, resourceId, resourceURL) {
  const emptyData = {content: [], sheets: 0};

  let promise = new Promise((resolve, reject) => _getS3ResourceURL(resourceId, resolve, reject));
  promise
    .then((url) => {
      return _loadSheetNames(url);
    })
    .then((data) => {
      return _loadData(data);
    })
    .then((data) => {
      _sdcLoadedData = data;
      _generateTabs(_sdcLoadedData);
      _prepareHandsonSettings(datasetId, resourceId);
      _initHandsonTable(_sdcLoadedData.content[0]);
    })
    .catch((error) => {
      console.error(error);
    });
}

function _onSaveSDCMicro(ev) {
  _updateLoadingMessage("Launching SDC Micro, please wait ...");
  _showLoading();
  let dataColumnList = _sdcSettings.columns
    .map((el, idx) => {
      return {"column": idx, "selected": el}
    })
    .filter((el) => el.selected)
    .map(el => el.column);

  let data = {
    dataset_id: _sdcSettings.datasetId,
    resource_id: _sdcSettings.resourceId,
    data_columns_list: dataColumnList,
    weight_column: _sdcSettings.weightColumn,
    columns_type_list: _sdcSettings.types,
    sheet: _sdcSettings.sheet
  };

  $.post("/api/action/qa_sdcmicro_run", JSON.stringify(data))
    .done((result) => {
      if (result.success) {
        _updateLoadingMessage("SDC Micro successfully launched! Reloading page ...");
      } else {
        let extraMsg = '';
        if( error && error.responseJSON){
          extraMsg = JSON.stringify(error.responseJSON.error.message);
        }
        alert("Error, SDC Micro could not be started!!  " + extraMsg);
        $("#loadingScreen").hide();
      }
    })
    .fail((fail) => {
      alert("Error, SDC Micro could not be started!");
      $("#loadingScreen").hide();
    })
    .always(() => {
      location.reload();
    });
}

function _registerSDCMicroPopupEvents() {
  $("#qa-sdc-popup-close").click((ev) => $(ev.currentTarget).parents(".popup").hide());
  $("#qa-sdc-popup-save").click(_onSaveSDCMicro);
}

function openSDCMicro(packageId, resourceId, resourceUrl) {
  $("#sdc-micro-table")
    .html(`
      <div id="sdc-micro-spinner" class="center-spinner">
        <div class="spinkit-spinner">
          <div class="bounce1"></div>
          <div class="bounce2"></div>
          <div class="bounce3"></div>
        </div>
      </div>`);
  $("#qa-sdc-widget .nav").html('');
  $("#qaSDCMicro").show();
  _registerSDCMicroPopupEvents();
  _loadResourcePreviewData(packageId, resourceId, resourceUrl);
}
