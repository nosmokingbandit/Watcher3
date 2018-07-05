# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755950.376481
_enable_loop = True
_template_filename = 'templates/head.html'
_template_uri = 'templates/head.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        url_base = context.get('url_base', UNDEFINED)
        uitheme = context.get('uitheme', UNDEFINED)
        language = context.get('language', UNDEFINED)
        notifications = context.get('notifications', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<title>Watcher</title>\r\n<meta content="noindex, nofollow" name="robots">\r\n<meta content="')
        __M_writer(str(url_base))
        __M_writer('" name="url_base">\r\n<meta content="true" name="enable_notifs">\r\n<meta content="')
        __M_writer(str(language))
        __M_writer('" name="language">\r\n<meta content="width=device-width,initial-scale=1" name="viewport">\r\n\r\n<link rel="icon" type="image/png" href="')
        __M_writer(str(url_base))
        __M_writer('/static/images/favicon.png" />\r\n<link rel="apple-touch-icon" href="')
        __M_writer(str(url_base))
        __M_writer('/static/images/logo_bg.png" />\r\n\r\n<link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/themes/')
        __M_writer(str(uitheme or 'Default'))
        __M_writer('.css?v=010" rel="stylesheet">\r\n<link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/lib/materialdesignicons.min.css?v=010" rel="stylesheet">\r\n<link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/style.css?v=012" rel="stylesheet">\r\n\r\n<script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/lib/jquery.310.min.js?v=010" type="text/javascript"></script>\r\n<script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/lib/bootstrap.bundle.min.js?v=010" type="text/javascript"></script>\r\n<script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/lib/bootstrap-notify.min.js?v=010" type="text/javascript"></script>\r\n<script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/shared.js?v=013" type="text/javascript"></script>\r\n<script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/localization.js?v=010" type="text/javascript"></script>\r\n\r\n<script id="notifications_json">\r\n    ')
        __M_writer(str(notifications))
        __M_writer('\r\n</script>\r\n\r\n\r\n\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "25": 1, "26": 3, "27": 3, "28": 5, "29": 5, "30": 8, "31": 8, "32": 9, "33": 9, "34": 11, "35": 11, "36": 11, "37": 11, "38": 12, "39": 12, "40": 13, "41": 13, "42": 15, "43": 15, "44": 16, "45": 16, "46": 17, "47": 17, "48": 18, "49": 18, "50": 19, "51": 19, "52": 22, "53": 22, "59": 53}, "source_encoding": "ascii", "uri": "templates/head.html", "filename": "templates/head.html"}
__M_END_METADATA
"""
