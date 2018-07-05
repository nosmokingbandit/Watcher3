# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755949.608899
_enable_loop = True
_template_filename = 'templates/library/import/couchpotato.html'
_template_uri = 'templates/library/import/couchpotato.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        _ = context.get('_', UNDEFINED)
        sources = context.get('sources', UNDEFINED)
        head = context.get('head', UNDEFINED)
        url_base = context.get('url_base', UNDEFINED)
        profiles = context.get('profiles', UNDEFINED)
        navbar = context.get('navbar', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/library/import/couchpotato.css?v=010" rel="stylesheet">\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/library/import/shared.js?v=011" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/library/import/couchpotato.js?v=011" type="text/javascript"></script>\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n            <h1>')
        __M_writer(str(_('Import CouchPotato Library')))
        __M_writer('</h1>\r\n            <br/>\r\n\r\n            <nav id="stepper" class="nav nav-pills nav-fill">\r\n                <span class="nav-item nav-link border active" target="connect">Connect</span>\r\n                <span class="nav-item nav-link mx-3 border" target="import">Import</span>\r\n                <span class="nav-item nav-link border" target="review">Review</span>\r\n            </nav>\r\n\r\n            <div id="progress_bar" class="progress my-3 bg-dark">\r\n                <div class="progress-bar"></div>\r\n                <span class="text-light"></span>\r\n            </div>\r\n\r\n            <form id="connect" class="form-group row bg-light rounded mx-auto py-3">\r\n                <div class="col-md-6">\r\n                    <label>')
        __M_writer(str(_('Address')))
        __M_writer('</label>\r\n                    <input type="text" id="address" class="form-control" placeholder="http://localhost">\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <label>')
        __M_writer(str(_('Port')))
        __M_writer('</label>\r\n                    <input type="number" id="port" class="form-control" min="0" placeholder="5050">\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <label>')
        __M_writer(str(_('API Key')))
        __M_writer('</label>\r\n                    <input type="text" id="apikey" class="form-control" placeholder="123456789abcdef">\r\n                </div>\r\n                <div class="col-md-12 mt-3">\r\n                    <button class="btn btn-primary float-right" onclick="connect(event, this)">\r\n                        <i class="mdi mdi-file-find"></i>\r\n                        ')
        __M_writer(str(_('Scan Library')))
        __M_writer('\r\n                    </button>\r\n                </div>\r\n            </form>\r\n\r\n            <form id="import" class="form-group row bg-light rounded mx-auto py-3 hidden">\r\n                <div id="no_imports" class="hidden">\r\n                    <div class="alert alert-info mx-3">\r\n                            ')
        __M_writer(str(_('No new movies have been found in CouchPotato\'s library.')))
        __M_writer('\r\n                    </div>\r\n                    <button class="btn btn-secondary float-right mr-3">\r\n                        ')
        __M_writer(str(_('Return')))
        __M_writer('\r\n                    </button>\r\n                </div>\r\n                <div id="wanted_movies" class="hidden">\r\n                    <h3 class="ml-3">')
        __M_writer(str(_('Wanted Movies')))
        __M_writer('</h3>\r\n                    <table class="table table-sm table-hover">\r\n                        <thead>\r\n                            <tr>\r\n                                <th class="shrink">')
        __M_writer(str(_('Import')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Title')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('IMDB ID')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Quality&nbsp;Profile')))
        __M_writer('</th>\r\n                            </tr>\r\n                        </thead>\r\n                        <tbody>\r\n                        </tbody>\r\n                    </table>\r\n                </div>\r\n                <div id="finished_movies" class="hidden">\r\n                    <h3 class="ml-3">')
        __M_writer(str(_('Finished Movies')))
        __M_writer('</h3>\r\n                    <table class="table table-striped table-hover">\r\n                        <thead>\r\n                            <tr>\r\n                                <th class="shrink">')
        __M_writer(str(_('Import')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Title')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('IMDB ID')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Source')))
        __M_writer('</th>\r\n                            </tr>\r\n                        </thead>\r\n                        <tbody>\r\n                        </tbody>\r\n                    </table>\r\n                </div>\r\n                <button id="button_import" class="btn btn-primary float-right mr-3 hidden" onclick="start_import(event, this)">\r\n                    <i class="mdi mdi-archive"></i>\r\n                    ')
        __M_writer(str(_('Import Library')))
        __M_writer('\r\n                </button>\r\n            </form>\r\n\r\n            <form id="review" class="form-group row bg-light rounded mx-auto py-3 hidden">\r\n                <div id="import_success" class="hidden">\r\n                    <h3 class="panel-title">')
        __M_writer(str(_('Imported Movies')))
        __M_writer('</h3>\r\n                    <table class="table table-sm table-hover">\r\n                        <thead>\r\n                            <tr>\r\n                                <th>')
        __M_writer(str(_('Title')))
        __M_writer('</th>\r\n                                <th class="shrink">')
        __M_writer(str(_('IMDB ID')))
        __M_writer('</th>\r\n                            </tr>\r\n                        </thead>\r\n                        <tbody>\r\n                        </tbody>\r\n                    </table>\r\n                </div>\r\n                <div id="import_error" class="hidden">\r\n                    <h3 class="panel-title">')
        __M_writer(str(_('Import Errors')))
        __M_writer('</h3>\r\n                    <table class="table table-sm table-hover">\r\n                        <thead>\r\n                            <tr>\r\n                                <th>')
        __M_writer(str(_('Title')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Error')))
        __M_writer('</th>\r\n                            </tr>\r\n                        </thead>\r\n                        <tbody>\r\n                        </tbody>\r\n                    </table>\r\n                </div>\r\n                <button class="btn btn-secondary float-right mr-3">\r\n                    ')
        __M_writer(str(_('Return')))
        __M_writer('\r\n                </button>\r\n            </form>\r\n        </div>\r\n\r\n        <template id="source_select">\r\n            <select class="source_select btn btn-sm btn-light border">\r\n')
        for source in sources:
            __M_writer('                <option value="')
            __M_writer(str(source))
            __M_writer('">')
            __M_writer(str(source))
            __M_writer('</option>\r\n')
        __M_writer('            </select>\r\n        </template>\r\n\r\n        <template id="quality_select">\r\n            <select class="quality_select btn btn-sm btn-light border">\r\n')
        for profile in profiles:
            if profile == "Default":
                __M_writer('                    <option value="Default" selected="true">Default</option>\r\n')
            else:
                __M_writer('                    <option value="')
                __M_writer(str(profile))
                __M_writer('">')
                __M_writer(str(profile))
                __M_writer('</option>\r\n')
        __M_writer('            </select>\r\n        </template>\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "27": 1, "28": 4, "29": 4, "30": 5, "31": 5, "32": 6, "33": 6, "34": 7, "35": 7, "36": 10, "37": 10, "38": 12, "39": 12, "40": 28, "41": 28, "42": 32, "43": 32, "44": 36, "45": 36, "46": 42, "47": 42, "48": 50, "49": 50, "50": 53, "51": 53, "52": 57, "53": 57, "54": 61, "55": 61, "56": 62, "57": 62, "58": 63, "59": 63, "60": 64, "61": 64, "62": 72, "63": 72, "64": 76, "65": 76, "66": 77, "67": 77, "68": 78, "69": 78, "70": 79, "71": 79, "72": 88, "73": 88, "74": 94, "75": 94, "76": 98, "77": 98, "78": 99, "79": 99, "80": 107, "81": 107, "82": 111, "83": 111, "84": 112, "85": 112, "86": 120, "87": 120, "88": 127, "89": 128, "90": 128, "91": 128, "92": 128, "93": 128, "94": 130, "95": 135, "96": 136, "97": 137, "98": 138, "99": 139, "100": 139, "101": 139, "102": 139, "103": 139, "104": 142, "110": 104}, "source_encoding": "ascii", "uri": "templates/library/import/couchpotato.html", "filename": "templates/library/import/couchpotato.html"}
__M_END_METADATA
"""
