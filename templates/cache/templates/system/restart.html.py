# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755950.32751
_enable_loop = True
_template_filename = 'templates/system/restart.html'
_template_uri = 'templates/system/restart.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        url_base = context.get('url_base', UNDEFINED)
        _ = context.get('_', UNDEFINED)
        head = context.get('head', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/system/restart.css?v=010" rel="stylesheet">\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/system/restart.js?v=010" type="text/javascript"></script>\r\n        <meta name="enable_notifs" content="false">\r\n    </head>\r\n    <body>\r\n        <div id="content" class="container">\r\n            <div class="message">')
        __M_writer(str(_('Restarting')))
        __M_writer('</div>\r\n            <div id="thinker">\r\n                <i class="mdi mdi-circle animated"></i>\r\n            </div>\r\n        </div>\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "32": 11, "38": 32, "24": 1, "25": 4, "26": 4, "27": 5, "28": 5, "29": 6, "30": 6, "31": 11}, "source_encoding": "ascii", "uri": "templates/system/restart.html", "filename": "templates/system/restart.html"}
__M_END_METADATA
"""
