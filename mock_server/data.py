#!/usr/bin/env python
# -*- coding: utf-8 -*-

JSON = "json"
XML = "xml"
TXT = "txt"
HTML = "html"
CSV = "csv"
RSS = "rss"
ATOM = "atom"

DEFAULT_FORMAT = JSON
SUPPORTED_FORMATS = {
    JSON: ("application/json", ),
    XML: ("application/xml", "text/xml", "application/x-xml"),
    TXT: ("text/plain", ),
    HTML: ("text/html", ),
    CSV: ("text/csv", ),
    RSS: ("application/rss+xml", ),
    ATOM: ("application/atom+xml", )
}


def _supported_mimes(SUPPORTED_FORMATS):
    supported_mimes = {}
    for format, mimes in SUPPORTED_FORMATS.iteritems():
        for mime in mimes:
            supported_mimes[mime] = format
    return supported_mimes

SUPPORTED_MIMES = _supported_mimes(SUPPORTED_FORMATS)
