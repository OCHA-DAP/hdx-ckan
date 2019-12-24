let _sdcMicroColumnChange;
let _sdcSettings;
let _hot;

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
    {key: 'type:auto', name: 'auto'},
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
        let value = key.slice(5);
        // console.log(value);
        _sdcSettings.types[selectedCol] = value;
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
          hot.updateSettings({});
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
          hot.updateSettings({});
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


function _initHandsonTable(datasetId, resourceId, data) {
  let container = document.getElementById("sdc-micro-table");
  const columnsNo = data[0].length;
  let selected = Array(columnsNo).fill(false);
  let types = Array(columnsNo).fill('auto');
  const sdcSettings = {
    datasetId: datasetId,
    resourceId: resourceId,
    columns: selected,
    types: types,
    weightColumn: null
  };
  _sdcSettings = sdcSettings;
  const contextMenu = _contextMenu(sdcSettings);
  const settings = {
    data: data,
    readOnly: true,
    rowHeaders: true,
    colHeaders: true,
    filters: true,
    dropdownMenu: contextMenu,
    contextMenu: contextMenu,
    afterInit: () => {
      $("#sdc-micro-spinner").remove();
    },
    licenseKey: 'non-commercial-and-evaluation'
  };
  let hot = new Handsontable(container, settings);

  hot.updateSettings({
    cells: function (row, col) {
      let cell = hot.getCell(row,col);
      if (sdcSettings.weightColumn === col) {
        cell.style.backgroundColor = "rgba(0,124,224,0.5)";
      }
      if (sdcSettings.columns[col]) {
        cell.style.backgroundColor = "rgba(30,191,179,0.51)";
      }
    }
  });
}
function _loadResourcePreviewData(datasetId, resourceId, resourceURL) {
  $.get(`/hxlproxy/api/data-preview.json?rows=20&url=${resourceURL}`)
    .done((result) => {
      console.log(result);
      _initHandsonTable(datasetId, resourceId, result);
    });
}

function _onSaveSDCMicro(ev) {
  _updateLoadingMessage("Launching SDC Micro, please wait ...");
  _showLoading();
  let dataColumnList = _sdcSettings.columns
    .map((el, idx) => { return { "column": idx, "selected": el }})
    .filter((el) => el.selected)
    .map(el => el.column);

  let data = {
    dataset_id: _sdcSettings.datasetId,
    resource_id: _sdcSettings.resourceId,
    data_columns_list: dataColumnList,
    weight_column: _sdcSettings.weightColumn,
    columns_type_list: _sdcSettings.types,
  };
  $.post("/api/action/qa_sdcmicro_run", JSON.stringify(data))
    .done((result) => {
      if (result.success) {
        _updateLoadingMessage("SDC Micro successfully launched! Reloading page ...");
      } else {
        alert("Error, SDC Micro could not be started!");
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
  $("#qaSDCMicro").show();
  _registerSDCMicroPopupEvents();
  _loadResourcePreviewData(packageId, resourceId, resourceUrl);
}
