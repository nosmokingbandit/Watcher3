# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755950.263546
_enable_loop = True
_template_filename = 'templates/settings/logs.html'
_template_uri = 'templates/settings/logs.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        _ = context.get('_', UNDEFINED)
        head = context.get('head', UNDEFINED)
        logfiles = context.get('logfiles', UNDEFINED)
        logdir = context.get('logdir', UNDEFINED)
        url_base = context.get('url_base', UNDEFINED)
        navbar = context.get('navbar', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/settings/shared.css?v=010" rel="stylesheet">\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/settings/log.css?v=010" rel="stylesheet">\r\n\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/settings/shared.js?v=012" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/settings/logs.js?v=011" type="text/javascript"></script>\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n            <h1>')
        __M_writer(str(_('Logs')))
        __M_writer('</h1>\r\n\r\n            <div class="row bg-light rounded mx-auto pb-3">\r\n                <div class="col-md-12 my-3">\r\n                    <label>')
        __M_writer(str(_('Log Directory')))
        __M_writer('</label>\r\n                    <input type="text" class="form-control border" value="')
        __M_writer(str(logdir))
        __M_writer('" readonly>\r\n                </div>\r\n\r\n                <div class="col-md-12">\r\n                    <label>')
        __M_writer(str(_('Log Files')))
        __M_writer('</label>\r\n                    <div class="input-group">\r\n                        <select id="log_file" class="form-control">\r\n')
        for log in logfiles:
            __M_writer('                            <option value="')
            __M_writer(str(log))
            __M_writer('">')
            __M_writer(str(log))
            __M_writer('</option>\r\n')
        __M_writer('                        </select>\r\n                        <div class="input-group-append">\r\n                            <button id="view" class="btn btn-outline-primary" onclick="view_log()" title="')
        __M_writer(str(_('View')))
        __M_writer('">\r\n                                <i class="mdi mdi-clipboard-text"></i>\r\n                            </button>\r\n                        </div>\r\n                        <div class="input-group-append">\r\n                            <button class="btn btn-outline-primary" onclick="download_log()" title="')
        __M_writer(str(_('Download')))
        __M_writer('">\r\n                                <i class="mdi mdi-download"></i>\r\n                            </button>\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n\r\n            <samp id="log_text" class=\'bg-light rounded px-3 py-3 mt-3\'></samp>\r\n        </div>\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"64": 58, "16": 0, "27": 1, "28": 4, "29": 4, "30": 5, "31": 5, "32": 6, "33": 6, "34": 8, "35": 8, "36": 9, "37": 9, "38": 12, "39": 12, "40": 14, "41": 14, "42": 18, "43": 18, "44": 19, "45": 19, "46": 23, "47": 23, "48": 26, "49": 27, "50": 27, "51": 27, "52": 27, "53": 27, "54": 29, "55": 31, "56": 31, "57": 36, "58": 36}, "source_encoding": "ascii", "uri": "templates/settings/logs.html", "filename": "templates/settings/logs.html"}
__M_END_METADATA
"""
