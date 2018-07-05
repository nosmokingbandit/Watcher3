# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755949.585925
_enable_loop = True
_template_filename = 'templates/library/import.html'
_template_uri = 'templates/library/import.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        url_base = context.get('url_base', UNDEFINED)
        _ = context.get('_', UNDEFINED)
        head = context.get('head', UNDEFINED)
        navbar = context.get('navbar', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/library/import.css?v=010" rel="stylesheet">\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container row">\r\n            <div class="col-md-12">\r\n                <h1>')
        __M_writer(str(_('Import Library')))
        __M_writer('</h1>\r\n            </div>\r\n            <div class="buttons col-md-12">\r\n\r\n                <a class="btn btn-secondary" href="')
        __M_writer(str(url_base))
        __M_writer('/library/import/couchpotato">\r\n                    <img alt="CouchPotato" class="import_source_icon" src="')
        __M_writer(str(url_base))
        __M_writer('/static/images/couchpotato.png"><br>\r\n                    CouchPotato\r\n                </a>\r\n\r\n                <a class="btn btn-secondary" href="')
        __M_writer(str(url_base))
        __M_writer('/library/import/kodi">\r\n                    <img alt="Kodi" class="import_source_icon" src="')
        __M_writer(str(url_base))
        __M_writer('/static/images/kodi.png"><br>\r\n                    Kodi\r\n                </a>\r\n\r\n                <a class="btn btn-secondary" href="')
        __M_writer(str(url_base))
        __M_writer('/library/import/plex">\r\n                    <img alt="Plex" class="import_source_icon" src="')
        __M_writer(str(url_base))
        __M_writer('/static/images/plex.png"><br>\r\n                    Plex\r\n                </a>\r\n\r\n                <a class="btn btn-secondary" href="')
        __M_writer(str(url_base))
        __M_writer('/library/import/directory">\r\n                    <i class="mdi mdi-folder"></i><br>\r\n                    ')
        __M_writer(str(_('Directory')))
        __M_writer('\r\n                </a>\r\n            </div>\r\n        </div>\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "25": 1, "26": 4, "27": 4, "28": 5, "29": 5, "30": 8, "31": 8, "32": 11, "33": 11, "34": 15, "35": 15, "36": 16, "37": 16, "38": 20, "39": 20, "40": 21, "41": 21, "42": 25, "43": 25, "44": 26, "45": 26, "46": 30, "47": 30, "48": 32, "49": 32, "55": 49}, "source_encoding": "ascii", "uri": "templates/library/import.html", "filename": "templates/library/import.html"}
__M_END_METADATA
"""
