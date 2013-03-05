var responseBodyEditor = ace.edit('response-body-editor');
var responseHeadersEditor = ace.edit('response-headers-editor');

(function CreateResources() {
    var formatMode = {
        'xml': 'xml',
        'csv': 'text',
        'json': 'json',
        'html': 'html',
        'atom': 'xml',
        'txt': 'text',
        'rss': 'rss'
    };

    responseBodyEditor.getSession().setMode(
        'ace/mode/' + formatMode[$('#format').val()]);

    $('#url_path').focus();

    $('#format').change(function() {
        responseBodyEditor.getSession().setMode(
            'ace/mode/' + formatMode[$(this).val()]);
    });

    $('#create-resource-form').submit(function(event) {

        if (!responseBodyEditor.getValue()) {
            alert("Response body can't be empty.");
            event.preventDefault();
            return;
        }

        $('#response_body').val(responseBodyEditor.getValue());
        $('#response_headers').val(responseHeadersEditor.getValue());
    });
})();