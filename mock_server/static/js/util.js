
function getCookie(name) {
    var r = document.cookie.match('\\b' + name + '=([^;]*)\\b');
    return r ? r[1] : undefined;
}

jQuery.extend({
    postJSON: function(url, data, callback) {
      return jQuery.ajax({
        type: "POST",
        url: url,
        data: JSON.stringify(data),
        dataType: "json",
        contentType: "application/json",
        processData: false,
        headers: {'X-Xsrftoken': getCookie("_xsrf")}
      }).always(callback);
    }
});
