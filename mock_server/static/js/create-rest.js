
function CreateRestMethodManager(supportedFormats) {
    this._supportedFormats = supportedFormats;
    this._tabs = $('#response-tabs');
    this._tabsContent = $('#response-tabs-content');
    this._addResponseLi = $('#add-response-li');

    this._form = {
        'urlPath': $('#url_path'),
        'method': $('#method'),
        'category': $('#category'),
        'description': $('#wmd-input')
    };

    this._tabIndex = 0;
    this._responses = [];

    var context = this;
    $('#add-response').click(function() {
        context.addResponse().show();
    });

    $('#save-resource').click(function() {
        context._handleSave();
    });
}

CreateRestMethodManager.prototype._handleSave = function() {
    var data = {
        'url_path': this._form.urlPath.val(),
        'method': this._form.method.val(),
        'category': this._form.category.val(),
        'description': this._form.description.val(),
        'responses': []
    };

    for (var i = 0, length = this._responses.length; i < length; i++) {
        var responseData = this._responses[i].getData();
        if (!responseData) {
            return false;
        }
        data.responses.push(responseData);
    }

    if (!data.responses.length) {
        alert("Response body can't be empty.");
        return null;
    }

    $.postJSON('/__manage/create', data, function(response) {
        window.location.href = '/__manage';
    });
    return true;
};

CreateRestMethodManager.prototype._showFirst = function() {
    if (this._responses.length) {
        this._responses[0].show();
    } else {
        this.addResponse().show();
    }
};

CreateRestMethodManager.prototype.removeResponse = function(response) {
    this._responses.splice(this._responses.indexOf(response), 1);
    this._showFirst();
};

CreateRestMethodManager.prototype.addResponse = function() {
    var li = document.createElement('li');
    var tabA = document.createElement('a');
    tabA.href = '#tab' + this._tabIndex;
    tabA.setAttribute('data-toggle', 'tab');
    li.appendChild(tabA);

    var response = new Response(this._tabIndex);
    response.removeCallback = this.removeResponse.bind(this);
    response.setTab(tabA);

    this._tabsContent.append(response.build(this._supportedFormats));
    this._responses.push(response);

    this._addResponseLi.before(li);

    this._tabIndex++;

    return response;
};


function Response(id) {
    this._id = id;
    this._tab = null;
    this._tabText = null;

    this.removeCallback = null;
}

Response.formatMode = {
    'xml': 'xml',
    'csv': 'text',
    'json': 'json',
    'html': 'html',
    'atom': 'xml',
    'txt': 'text',
    'rss': 'xml',
    'md': 'markdown'
};

Response.prototype.setTab = function(tab) {
    this._tabText = document.createElement('span');
    this._tabText.innerHTML = 'Response (200 - json) ';

    var removeButton = document.createElement('i');
    removeButton.className = 'icon-remove';

    var context = this;
    $(removeButton).click(function() {
        context._handleRemove();
    });

    tab.appendChild(this._tabText);
    tab.appendChild(removeButton);

    this._tab = tab;
};

Response.prototype._handleRemove = function() {
    $(this._container).remove();
    $(this._tab).remove();

    this.removeCallback(this);
};

Response.prototype.show = function() {
    $(this._tab).tab('show');
};

Response.prototype._handleFormatChange = function(target) {
    this._setResponseBodyMode($(target).val());
    this._updateTabTitle();
};

Response.prototype._setResponseBodyMode = function(format) {
    this._responseBodyEditor.getSession().setMode(
        'ace/mode/' + Response.formatMode[format]);
};

Response.prototype._updateTabTitle = function() {
    var statusCode = this._statusCode.value;
    var format = this._format.value;
    this._tabText.innerHTML = 'Response (' + statusCode + ' - ' + format + ') ';
};

Response.prototype.setDefaults = function(data) {
    this._statusCode.value = data['status_code'];
    this._format.value = data['format'];
    this._responseBodyEditor.setValue(data['body']);
    this._responseHeadersEditor.setValue(data['headers']);

    this._updateTabTitle();
};

Response.prototype.build = function(supportedFormats) {

    this._container = document.createElement('div');
    this._container.className = 'tab-pane';
    this._container.id = 'tab' + this._id;

    var context = this;

    // status code
    var statusCodeContainer = document.createElement('div');
    statusCodeContainer.className = 'control-group';
    var label = document.createElement('label');
    label.setAttribute('for', 'status_code');
    label.innerHTML = 'Status code';

    this._statusCode = document.createElement('input');
    this._statusCode.type = 'text';
    this._statusCode.value = '200';

    $(this._statusCode).change(function() {
        context._updateTabTitle();
    });

    statusCodeContainer.appendChild(label);
    statusCodeContainer.appendChild(this._statusCode);

    this._container.appendChild(statusCodeContainer);

    // format
    var formatContainer = document.createElement('div');
    formatContainer.className = 'control-group';
    label = document.createElement('label');
    label.setAttribute('for', 'format');
    label.innerHTML = 'Response format';
    this._format = document.createElement('select');

    var option = null;
    var supportedFormat = null;
    for (var i = 0, length = supportedFormats.length; i < length; i++) {
        option = document.createElement('option');
        supportedFormat = supportedFormats[i];
        option.value = supportedFormat;
        option.innerHTML = supportedFormat;
        if (supportedFormat === 'json') {
            option.selected = true;
        }
        this._format.appendChild(option);
    }

    $(this._format).change(function() {
        context._handleFormatChange(this);
    });

    formatContainer.appendChild(label);
    formatContainer.appendChild(this._format);

    this._container.appendChild(formatContainer);

    // response body
    var responseBodyContainer = document.createElement('div');
    responseBodyContainer.className = 'control-group';
    label = document.createElement('label');
    label.setAttribute('for', 'response_body');
    label.innerHTML = 'Response body';
    var responseBodyEditorDiv = document.createElement('div');
    this._responseBodyEditor = ace.edit(responseBodyEditorDiv);
    this._setResponseBodyMode(this._format.value);

    responseBodyContainer.appendChild(label);
    responseBodyContainer.appendChild(responseBodyEditorDiv);

    this._container.appendChild(responseBodyContainer);

    // response headers
    var responseHeadersContainer = document.createElement('div');
    responseHeadersContainer.className = 'control-group';
    label = document.createElement('label');
    label.setAttribute('for', 'response_headers');
    label.innerHTML = 'Response headers';
    var responseHeadersEditorDiv = document.createElement('div');
    this._responseHeadersEditor = ace.edit(responseHeadersEditorDiv);

    responseHeadersContainer.appendChild(label);
    responseHeadersContainer.appendChild(responseHeadersEditorDiv);

    this._container.appendChild(responseHeadersContainer);

    return this._container;
};

Response.prototype.getData = function() {
    var data = {
        'status_code': this._statusCode.value,
        'format': this._format.value,
        'body': this._responseBodyEditor.getValue(),
        'headers': this._responseHeadersEditor.getValue()
    };

    if (!data['body']) {
        alert("Response body can't be empty.");
        return null;
    }

    return data;
};
