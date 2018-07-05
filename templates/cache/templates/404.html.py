# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755950.362488
_enable_loop = True
_template_filename = 'templates/404.html'
_template_uri = 'templates/404.html'
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
        __M_writer('\r\n<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/404.css?v=010" rel="stylesheet">\r\n        <meta name="enable_notifs" content="false" />\r\n    </head>\r\n    <body>\r\n        <div class="message">\r\n            404\r\n            <br/>\r\n            ')
        __M_writer(str(_('Page Not Found')))
        __M_writer('\r\n        </div>\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "36": 30, "24": 1, "25": 5, "26": 5, "27": 6, "28": 6, "29": 13, "30": 13}, "source_encoding": "ascii", "uri": "templates/404.html", "filename": "templates/404.html"}
__M_END_METADATA
"""
