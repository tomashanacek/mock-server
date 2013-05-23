# -*- coding: utf-8 -*-

JSON = "json"
XML = "xml"
TXT = "txt"
HTML = "html"
CSV = "csv"
RSS = "rss"
ATOM = "atom"
MARKDOWN = "md"

DEFAULT_FORMAT = JSON
SUPPORTED_FORMATS = {
    JSON: ("application/json", ),
    XML: ("application/xml", "text/xml", "application/x-xml"),
    TXT: ("text/plain", ),
    HTML: ("text/html", ),
    CSV: ("text/csv", ),
    RSS: ("application/rss+xml", ),
    ATOM: ("application/atom+xml", ),
    MARKDOWN: ("text/x-markdown", "text/html")
}


def _supported_mimes(SUPPORTED_FORMATS):
    supported_mimes = {}
    for format, mimes in SUPPORTED_FORMATS.iteritems():
        for mime in mimes:
            supported_mimes[mime] = format
    return supported_mimes

SUPPORTED_MIMES = _supported_mimes(SUPPORTED_FORMATS)

SUPPORTED_METHODS = ("GET", "HEAD", "POST", "DELETE", "PATCH",
                     "PUT", "OPTIONS")
