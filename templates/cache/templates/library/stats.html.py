# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755949.750817
_enable_loop = True
_template_filename = 'templates/library/stats.html'
_template_uri = 'templates/library/stats.html'
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
        __M_writer('/static/css/library/stats.css?v=010" rel="stylesheet">\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/lib/morris.css?v=010" rel="stylesheet">\r\n        <script type="text/javascript" src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/lib/raphael.min.js?v=010"></script>\r\n        <script type="text/javascript" src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/lib/morris.min.js?v=010"></script>\r\n        <script type="text/javascript" src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/library/stats.js?v=011"></script>\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n            <div class="row">\r\n                <div id="chart_status" class="col-md-6 my-3">\r\n                    <div class="card">\r\n                        <div class="card-header">\r\n                            ')
        __M_writer(str(_('Status')))
        __M_writer('\r\n                        </div>\r\n                        <div class="chart">\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n                <div id="chart_profiles" class="col-md-6 my-3">\r\n                    <div class="card">\r\n                        <div class="card-header">\r\n                            ')
        __M_writer(str(_('Quality Profiles')))
        __M_writer('\r\n                        </div>\r\n                        <div class="chart">\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n                <div id="chart_years" class="col-md-12 my-3">\r\n                    <div class="card">\r\n                        <div class="card-header">\r\n                            ')
        __M_writer(str(_('Movies By Year')))
        __M_writer('\r\n                        </div>\r\n                        <div class="chart">\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n                <div id="chart_added" class="col-md-12 my-3">\r\n                    <div class="card">\r\n                        <div class="card-header">\r\n                            ')
        __M_writer(str(_('Library Growth')))
        __M_writer('\r\n                        </div>\r\n                        <div class="chart">\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n                <div id="chart_scores" class="col-md-12 my-3">\r\n                    <div class="card">\r\n                        <div class="card-header">\r\n                            ')
        __M_writer(str(_('Scores')))
        __M_writer('\r\n                        </div>\r\n                        <div class="chart">\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n        </div>\r\n\r\n        <div id="status_colors" class="hidden">\r\n            <span class="badge-dark"></span>\r\n            <span class="badge-warning"></span>\r\n            <span class="badge-info"></span>\r\n            <span class="badge-primary"></span>\r\n            <span class="badge-success"></span>\r\n        </div>\r\n        <div id="profile_colors" class="hidden">\r\n            <span class="bg-primary"></span>\r\n            <span class="bg-success"></span>\r\n            <span class="bg-info"></span>\r\n        </div>\r\n\r\n        </textarea>\r\n\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "25": 1, "26": 4, "27": 4, "28": 5, "29": 5, "30": 6, "31": 6, "32": 7, "33": 7, "34": 8, "35": 8, "36": 9, "37": 9, "38": 12, "39": 12, "40": 18, "41": 18, "42": 27, "43": 27, "44": 36, "45": 36, "46": 45, "47": 45, "48": 54, "49": 54, "55": 49}, "source_encoding": "ascii", "uri": "templates/library/stats.html", "filename": "templates/library/stats.html"}
__M_END_METADATA
"""
