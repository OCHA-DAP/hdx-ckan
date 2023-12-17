$(document).ready(() => {
    let resourceUrl = $("#resource-url").html();
    let hxlProxyUrl = $("#hxl-proxy-url").html();
    console.log(`Loading URL: ${resourceUrl}`);
    let previewUrl =`${hxlProxyUrl}/api/data-preview.json?rows=20&sheet=0&url=${resourceUrl}`;
    $.get(previewUrl).done((response) => {
        console.log(response.slice(1));
        let columns = response.slice(0,1)[0].map((item) => { return {"title": item}; });
        let table = new DataTable('#myTable', {
            responsive: true,
            data: response.slice(1),
            "columns": columns
        });
    })

    
});