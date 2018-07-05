# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755950.44644
_enable_loop = True
_template_filename = 'templates/login.html'
_template_uri = 'templates/login.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        url_base = context.get('url_base', UNDEFINED)
        uitheme = context.get('uitheme', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        <title>Watcher</title>\r\n        <meta content="')
        __M_writer(str(url_base))
        __M_writer('" name="url_base">\r\n        <meta content="width=device-width,initial-scale=1" name="viewport">\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/auth/static/css/themes/')
        __M_writer(str(uitheme or 'Default'))
        __M_writer('.css?v=010" rel="stylesheet">\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/auth/static/css/lib/materialdesignicons.min.css?v=010" rel="stylesheet">\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/auth/static/css/login.css?v=010" rel="stylesheet">\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/auth/static/js/lib/jquery.310.min.js?v=010" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/auth/static/js/login.js?v=012" type="text/javascript"></script>\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/auth/static/css/style.css?v=012" rel="stylesheet">\r\n        <meta name="enable_notifs" content="false" />\r\n    </head>\r\n    <body>\r\n        <div class="row mx-3">\r\n            <div class="col-md-6 offset-md-3">\r\n                <div class="input-group">\r\n                    <div class="input-group-prepend">\r\n                        <span class="input-group-text">\r\n                            <i class="mdi mdi-account"></i>\r\n                        </span>\r\n                    </div>\r\n                    <input type="text" id="user" class="form-control">\r\n                </div>\r\n            </div>\r\n            <div class="col-md-6 offset-md-3">\r\n                <div class="input-group">\r\n                    <div class="input-group-prepend">\r\n                        <span class="input-group-text">\r\n                            <i class="mdi mdi-lock"></i>\r\n                        </span>\r\n                    </div>\r\n                    <input type="password" id="password" class="form-control">\r\n                </div>\r\n            </div>\r\n            <div class="col-md-6 offset-md-3">\r\n                <button class="message btn btn-primary btn-block" onclick="login(event)">\r\n                    <i class="mdi mdi-login"></i>\r\n                </button>\r\n            </div>\r\n        </div>\r\n\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"32": 9, "33": 9, "34": 10, "35": 10, "36": 11, "37": 11, "38": 12, "39": 12, "45": 39, "16": 0, "23": 1, "24": 5, "25": 5, "26": 7, "27": 7, "28": 7, "29": 7, "30": 8, "31": 8}, "source_encoding": "ascii", "uri": "templates/login.html", "filename": "templates/login.html"}
__M_END_METADATA
"""
