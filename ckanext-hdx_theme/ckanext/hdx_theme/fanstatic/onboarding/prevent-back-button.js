window.history.pushState({page: 2}, null, null);

window.onpopstate = function (event) {
  if (event) {
    var r = confirm('Hold on! Your data has already been saved. Are you sure you want to go back to the previous page and reload the signup process?');
    if (r === true) {
      history.back();
    } else {
      window.history.pushState({page: 2}, '', '');
    }
  }
}
