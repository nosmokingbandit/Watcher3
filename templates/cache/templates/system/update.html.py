# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755950.346497
_enable_loop = True
_template_filename = 'templates/system/update.html'
_template_uri = 'templates/system/update.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        url_base = context.get('url_base', UNDEFINED)
        updating = context.get('updating', UNDEFINED)
        _ = context.get('_', UNDEFINED)
        head = context.get('head', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        <meta name="enable_notifs" content="false">\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/system/update.css?v=010" rel="stylesheet">\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/system/update.js?v=012" type="text/javascript"></script>\r\n        <meta name="updating" content="')
        __M_writer(str(updating))
        __M_writer('">\r\n    </head>\r\n    <body>\r\n        <div id="content" class="container">\r\n\r\n            <div class="tasks hidden">\r\n                <h4>')
        __M_writer(str(_('Waiting for tasks to finish...')))
        __M_writer('</h4>\r\n\r\n            </div>\r\n\r\n\r\n            <div class="updating hidden">')
        __M_writer(str(_('Updating')))
        __M_writer('</div>\r\n            <div id="thinker">\r\n                <i class="mdi mdi-circle animated"></i>\r\n            </div>\r\n        </div>\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"32": 8, "33": 8, "34": 14, "35": 14, "36": 19, "37": 19, "43": 37, "16": 0, "25": 1, "26": 5, "27": 5, "28": 6, "29": 6, "30": 7, "31": 7}, "source_encoding": "ascii", "uri": "templates/system/update.html", "filename": "templates/system/update.html"}
__M_END_METADATA
"""
