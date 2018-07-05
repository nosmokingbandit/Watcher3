# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755949.651874
_enable_loop = True
_template_filename = 'templates/library/import/kodi.html'
_template_uri = 'templates/library/import/kodi.html'
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
        __M_writer('/static/css/library/import/kodi.css?v=010" rel="stylesheet">\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/library/import/shared.js?v=011" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/library/import/kodi.js?v=011" type="text/javascript"></script>\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n            <h1>')
        __M_writer(str(_('Import Kodi Library')))
        __M_writer('</h1>\r\n            <br/>\r\n\r\n            <nav id="stepper" class="nav nav-pills nav-fill">\r\n                <span class="nav-item nav-link border active" target="connect">Connect</span>\r\n                <span class="nav-item nav-link border mx-3" target="import">Import</span>\r\n                <span class="nav-item nav-link border" target="review">Review</span>\r\n            </nav>\r\n\r\n            <div id="progress_bar" class="progress my-3 bg-dark">\r\n                <div class="progress-bar"></div>\r\n                <span class="text-light"></span>\r\n            </div>\r\n\r\n            <form id="connect" class="form-group row bg-light rounded mx-auto py-3">\r\n                <div class="col-md-6">\r\n                    <label>')
        __M_writer(str(_('Address')))
        __M_writer('</label>\r\n                    <input type="text" id="address" class="form-control" placeholder="http://localhost">\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <label>')
        __M_writer(str(_('Port')))
        __M_writer('</label>\r\n                    <input type="number" id="port" class="form-control" min="0" placeholder="8080">\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <label>')
        __M_writer(str(_('User Name')))
        __M_writer('</label>\r\n                    <input type="text" id="user" class="form-control" placeholder="Kodi">\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <label>')
        __M_writer(str(_('Password')))
        __M_writer('</label>\r\n                    <input type="text" id="password" class="form-control" placeholder="password">\r\n                </div>\r\n                <div class="col-md-12 mt-3">\r\n                    <button class="btn btn-primary float-right" onclick="connect(event, this)">\r\n                        <i class="mdi mdi-file-find"></i>\r\n                        ')
        __M_writer(str(_('Scan Library')))
        __M_writer('\r\n                    </button>\r\n                </div>\r\n            </form>\r\n\r\n            <form id="import" class="form-group row bg-light rounded mx-auto py-3 hidden">\r\n                <div id="no_imports" class="hidden">\r\n                    <div class="alert alert-info mx-3">\r\n                            ')
        __M_writer(str(_('No new movies found.')))
        __M_writer('\r\n                    </div>\r\n                    <button class="btn btn-secondary float-right mr-3">\r\n                        ')
        __M_writer(str(_('Return')))
        __M_writer('\r\n                    </button>\r\n                </div>\r\n\r\n                <div id="remote_map" class="card mx-3 hidden">\r\n                    <div class="card-header">\r\n                        <big>')
        __M_writer(str(_('Remote Paths')))
        __M_writer('</big>\r\n                    </div>\r\n                    <div class="card-body">\r\n                        ')
        __M_writer(str(_('Kodi lists file locations relative to itself. If Kodi is on a different device than Watcher you may need to alter file paths.')))
        __M_writer('\r\n                        <br/><br/>\r\n                        ')
        __M_writer(str(_('To alter a remote path, enter the information in the following form and click Apply. Multiple changes can be applied. Use the same principles as described in the wiki.')))
        __M_writer('\r\n                        <a href="https://github.com/nosmokingbandit/Watcher3/wiki/Remote-Mapping" target="_blank" rel="noopener">\r\n                            <i class="mdi mdi-help-circle-outline"></i>\r\n                        </a>\r\n                        <div class="row">\r\n                            <div class="col-md-6">\r\n                                <label>')
        __M_writer(str(_('Local Path')))
        __M_writer('</label>\r\n                                <input type="text" id="local_path" class="form-control" placeholder="//Movies">\r\n                            </div>\r\n                            <div class="col-md-6">\r\n                                <label>')
        __M_writer(str(_('Remote Path')))
        __M_writer('</label>\r\n                                <input type="text" id="remote_path" class="form-control" placeholder="//Movies">\r\n                            </div>\r\n                            <div id="remote_actions" class="col-md-12 mt-3">\r\n                                <button class="btn btn-secondary float-right" onclick="apply_remote(event)">\r\n                                    <i class="mdi mdi-check"></i>\r\n                                    ')
        __M_writer(str(_('Apply')))
        __M_writer('\r\n                                </button>\r\n                                <button class="btn btn-secondary float-right mr-3" onclick="reset_remote(event)">\r\n                                    <i class="mdi mdi-undo"></i>\r\n                                    ')
        __M_writer(str(_('Reset')))
        __M_writer('\r\n                                </button>\r\n                            </div>\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n\r\n                <div id="complete_movies" class="hidden">\r\n                    <h3 class="ml-3">\r\n                        ')
        __M_writer(str(_('Kodi Movies')))
        __M_writer('\r\n                    </h3>\r\n                    <table class="table table-sm table-hover">\r\n                        <thead>\r\n                            <tr>\r\n                                <th class="shrink">')
        __M_writer(str(_('Import')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('File')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Title')))
        __M_writer('</th>\r\n                                <th class="shrink">')
        __M_writer(str(_('IMDB ID')))
        __M_writer('</th>\r\n                                <th class="shrink">')
        __M_writer(str(_('Source')))
        __M_writer('</th>\r\n                            </tr>\r\n                        </thead>\r\n                        <tbody>\r\n                        </tbody>\r\n                    </table>\r\n                </div>\r\n\r\n                <button id="button_import" class="btn btn-primary float-right mr-3 hidden" onclick="start_import(event, this)">\r\n                    <i class="mdi mdi-archive"></i>\r\n                    ')
        __M_writer(str(_('Import Library')))
        __M_writer('\r\n                </button>\r\n            </form>\r\n\r\n            <form id="review" class="form-group row bg-light rounded mx-auto py-3 hidden">\r\n                <div id="import_success" class="hidden">\r\n                    <h3 class="ml-3">')
        __M_writer(str(_('Imported Movies')))
        __M_writer('</h3>\r\n                    <table class="table table-hover">\r\n                        <thead>\r\n                            <tr>\r\n                                <th>\r\n                                    ')
        __M_writer(str(_('Title')))
        __M_writer('\r\n                                </th>\r\n                                <th class="shrink">\r\n                                    ')
        __M_writer(str(_('IMDB ID')))
        __M_writer('\r\n                                </th>\r\n                            </tr>\r\n                        </thead>\r\n                        <tbody>\r\n                        </tbody>\r\n                    </table>\r\n                </div>\r\n                <div id="import_error" class="hidden">\r\n                    <h3 class="ml-3">')
        __M_writer(str(_('Import Errors')))
        __M_writer('</h3>\r\n                    <table class="table table-sm table-hover">\r\n                        <thead>\r\n                            <tr>\r\n                                <th>')
        __M_writer(str(_('Title')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Error')))
        __M_writer('</th>\r\n                            </tr>\r\n                        </thead>\r\n                        <tbody>\r\n                        </tbody>\r\n                    </table>\r\n                </div>\r\n\r\n                <button class="btn btn-secondary float-right mr-3">\r\n                    ')
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
{"line_map": {"16": 0, "27": 1, "28": 4, "29": 4, "30": 5, "31": 5, "32": 6, "33": 6, "34": 7, "35": 7, "36": 10, "37": 10, "38": 12, "39": 12, "40": 28, "41": 28, "42": 32, "43": 32, "44": 36, "45": 36, "46": 40, "47": 40, "48": 46, "49": 46, "50": 54, "51": 54, "52": 57, "53": 57, "54": 63, "55": 63, "56": 66, "57": 66, "58": 68, "59": 68, "60": 74, "61": 74, "62": 78, "63": 78, "64": 84, "65": 84, "66": 88, "67": 88, "68": 97, "69": 97, "70": 102, "71": 102, "72": 103, "73": 103, "74": 104, "75": 104, "76": 105, "77": 105, "78": 106, "79": 106, "80": 116, "81": 116, "82": 122, "83": 122, "84": 127, "85": 127, "86": 130, "87": 130, "88": 139, "89": 139, "90": 143, "91": 143, "92": 144, "93": 144, "94": 153, "95": 153, "96": 160, "97": 161, "98": 161, "99": 161, "100": 161, "101": 161, "102": 163, "103": 168, "104": 169, "105": 170, "106": 171, "107": 172, "108": 172, "109": 172, "110": 172, "111": 172, "112": 175, "118": 112}, "source_encoding": "ascii", "uri": "templates/library/import/kodi.html", "filename": "templates/library/import/kodi.html"}
__M_END_METADATA
"""
