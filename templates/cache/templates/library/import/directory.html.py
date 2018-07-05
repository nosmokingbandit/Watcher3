# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755949.725845
_enable_loop = True
_template_filename = 'templates/library/import/directory.html'
_template_uri = 'templates/library/import/directory.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        _ = context.get('_', UNDEFINED)
        sources = context.get('sources', UNDEFINED)
        head = context.get('head', UNDEFINED)
        current_dir = context.get('current_dir', UNDEFINED)
        url_base = context.get('url_base', UNDEFINED)
        profiles = context.get('profiles', UNDEFINED)
        file_list = context.get('file_list', UNDEFINED)
        navbar = context.get('navbar', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/library/import/directory.css?v=010" rel="stylesheet">\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/library/import/shared.js?v=011" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/library/import/directory.js?v=011" type="text/javascript"></script>\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n            <h1>')
        __M_writer(str(_('Import Directory')))
        __M_writer('</h1>\r\n            <br/>\r\n\r\n            <nav id="stepper" class="nav nav-pills nav-fill">\r\n                <span class="nav-item nav-link border active" target="connect">Connect</span>\r\n                <span class="nav-item nav-link mx-3 border" target="import">Import</span>\r\n                <span class="nav-item nav-link border" target="review">Review</span>\r\n            </nav>\r\n\r\n            <div id="progress_bar" class="progress my-3 bg-dark">\r\n                <div class="progress-bar"></div>\r\n                <span class="text-light"></span>\r\n            </div>\r\n\r\n            <form id="connect" class="form-group row bg-light rounded mx-auto py-3">\r\n                <div class="col-md-12">\r\n                    <label>')
        __M_writer(str(_('Select Directory')))
        __M_writer('</label>\r\n                    <div class="input-group">\r\n                           <input type="text" id="directory_input" class="form-control">\r\n                        <span class="input-group-append">\r\n                            <button class="btn btn-light border" data-toggle="modal" data-target="#modal_browser" onclick="(function(event){event.preventDefault()})(event)">\r\n                                <i class="mdi mdi-folder-open"></i>\r\n                            </button>\r\n                        </span>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <label>')
        __M_writer(str(_('Minimum File Size')))
        __M_writer('</label>\r\n                    <div class="input-group">\r\n                        <input type="number" id="min_file_size" class="form-control" min="0" value="500">\r\n                        <span class="input-group-append">\r\n                            <span class="input-group-text">\r\n                                ')
        __M_writer(str(_('MegaBytes')))
        __M_writer('\r\n                            </span>\r\n                        </span>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <label>')
        __M_writer(str(_('Scan Recursively')))
        __M_writer('</label>\r\n                    <div class="input-group">\r\n                        <span class="input-group-prepend">\r\n                            <span class="input-group-text">\r\n                                <i id="scan_recursive" class="mdi mdi-checkbox-marked c_box" value="True"></i>\r\n                            </span>\r\n                        </span>\r\n                        <span class="input-group-item form-control">\r\n                            ')
        __M_writer(str(_('Scan sub-folders')))
        __M_writer('\r\n                        </span>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-12 mt-3">\r\n                    <button class="btn btn-primary float-right" onclick="connect(event, this)">\r\n                        <i class="mdi mdi-file-find"></i>\r\n                        ')
        __M_writer(str(_('Scan Directory')))
        __M_writer('\r\n                    </button>\r\n                </div>\r\n            </form>\r\n\r\n            <form id="import" class="form-group row bg-light rounded mx-auto py-3 hidden">\r\n                <div id="no_imports" class="hidden">\r\n                    <div class="alert alert-info mx-3">\r\n                            ')
        __M_writer(str(_('No new movies found.')))
        __M_writer('\r\n                    </div>\r\n                    <button class="btn btn-secondary float-right mr-3">\r\n                        ')
        __M_writer(str(_('Return')))
        __M_writer('\r\n                    </button>\r\n                </div>\r\n\r\n                <div id="complete_movies" class="hidden">\r\n                    <h3 class="ml-3 d-inline-block">\r\n                        ')
        __M_writer(str(_('Found Movies')))
        __M_writer('\r\n                    </h3>\r\n                    <div class="btn-group float-right mr-3 mb-3">\r\n                        <button class="btn btn-sm btn-light border" onclick="select_all(\'complete_movies\')" title="Select All">\r\n                            <i class="mdi mdi-checkbox-multiple-marked"></i>\r\n                        </button>\r\n                        <button class="btn btn-sm btn-light border" onclick="select_none(\'complete_movies\')" title="De-Select All">\r\n                            <i class="mdi mdi-checkbox-multiple-blank-outline"></i>\r\n                        </button>\r\n                        <button class="btn btn-sm btn-light border" onclick="select_inverse(\'complete_movies\')" title="Invert Selection">\r\n                            <i class="mdi mdi-minus-box"></i>\r\n                        </button>\r\n                    </div>\r\n                    <table class="table table-hover table-sm">\r\n                        <thead>\r\n                            <tr>\r\n                                <th class="shrink">')
        __M_writer(str(_('Import')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('File')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Title')))
        __M_writer('</th>\r\n                                <th class="shrink">')
        __M_writer(str(_('TheMovieDB&nbsp;ID')))
        __M_writer('</th>\r\n                                <th class="shrink">')
        __M_writer(str(_('Source')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Size')))
        __M_writer('</th>\r\n                            </tr>\r\n                        </thead>\r\n                        <tbody>\r\n                        </tbody>\r\n                    </table>\r\n                </div>\r\n                <div id="incomplete_movies" class="hidden">\r\n                    <h3 class="ml-3">\r\n                        ')
        __M_writer(str(_('Incomplete Movies')))
        __M_writer('\r\n                    </h3>\r\n                    <span class="mx-3 d-inline-block">')
        __M_writer(str(_('The following movies are missing key information. Review and correct as needed.')))
        __M_writer('</span>\r\n                    <div class="btn-group float-right mr-3 mb-3">\r\n                        <button class="btn btn-sm btn-light border" onclick="select_all(\'incomplete_movies\')" title="Select All">\r\n                            <i class="mdi mdi-checkbox-multiple-marked"></i>\r\n                        </button>\r\n                        <button class="btn btn-sm btn-light border" onclick="select_none(\'incomplete_movies\')" title="De-Select All">\r\n                            <i class="mdi mdi-checkbox-multiple-blank-outline"></i>\r\n                        </button>\r\n                        <button class="btn btn-sm btn-light border" onclick="select_inverse(\'incomplete_movies\')" title="Invert Selection">\r\n                            <i class="mdi mdi-minus-box"></i>\r\n                        </button>\r\n                    </div>\r\n                    <table class="table table-hover table-sm">\r\n                        <thead>\r\n                            <tr>\r\n                                <th class="shrink">')
        __M_writer(str(_('Import')))
        __M_writer('</th>\r\n                                <th class="file_path">')
        __M_writer(str(_('File')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Title')))
        __M_writer('</th>\r\n                                <th class="shrink">')
        __M_writer(str(_('TheMovieDB&nbsp;ID')))
        __M_writer('</th>\r\n                                <th class="shrink">')
        __M_writer(str(_('Source')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Size')))
        __M_writer('</th>\r\n                            </tr>\r\n                        </thead>\r\n                        <tbody>\r\n                        </tbody>\r\n                    </table>\r\n                </div>\r\n\r\n                <button id="button_import" class="btn btn-primary float-right mr-3 hidden" onclick="start_import(event, this)">\r\n                    <i class="mdi mdi-archive"></i>\r\n                    ')
        __M_writer(str(_('Import Library')))
        __M_writer('\r\n                </button>\r\n            </form>\r\n\r\n            <form id="review" class="form-group row bg-light rounded mx-auto py-3 hidden">\r\n                <div id="import_success" class="hidden">\r\n                    <h3 class="ml-3">')
        __M_writer(str(_('Imported Movies')))
        __M_writer('</h3>\r\n                    <table class="table table-hover table-sm">\r\n                        <thead>\r\n                            <tr>\r\n                                <th>\r\n                                    ')
        __M_writer(str(_('Title')))
        __M_writer('\r\n                                </th>\r\n                                <th class="shrink">\r\n                                    ')
        __M_writer(str(_('TheMovieDB&nbsp;ID')))
        __M_writer('\r\n                                </th>\r\n                            </tr>\r\n                        </thead>\r\n                        <tbody>\r\n                        </tbody>\r\n                    </table>\r\n                </div>\r\n                <div id="import_error" class="hidden">\r\n                    <h3 class="ml-3">')
        __M_writer(str(_('Import Errors')))
        __M_writer('</h3>\r\n                    <table class="table table-hover table-sm">\r\n                        <thead>\r\n                            <tr>\r\n                                <th>')
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
        __M_writer('            </select>\r\n        </template>\r\n\r\n        <div id="modal_browser" class="modal fade">\r\n            <div class="modal-dialog modal-wide">\r\n                <div class="modal-content">\r\n                    <div class="modal-header">\r\n                        <h4 class="modal-title">\r\n                            ')
        __M_writer(str(_('Select Library Directory')))
        __M_writer('\r\n                        </h4>\r\n                        <button type="button" class="btn btn-light border btn-sm float-right" data-dismiss="modal">\r\n                            <i class="mdi mdi-close"></i>\r\n                        </button>\r\n                    </div>\r\n                    <div class="modal-body">\r\n                        <div class="col-md-12">\r\n                            <input type="text" id="modal_current_dir" class="form-control" value="')
        __M_writer(str(current_dir))
        __M_writer('" readonly>\r\n                        </div>\r\n                        <ul id="modal_file_list" class="mx-3 my-3 rounded">\r\n')
        for i in file_list:
            __M_writer('                            <li class="col-md-6 p-1 border">\r\n                                <i class="mdi mdi-folder"></i>\r\n                                ')
            __M_writer(str(i))
            __M_writer('\r\n                            </li>\r\n')
        __M_writer('                        </ul>\r\n                    </div>\r\n                    <div class="modal-footer">\r\n                        <button type="button" class="btn btn-primary float-right" data-toggle="modal" data-target="#modal_browser" onclick="file_browser_select(event, this)">\r\n                            ')
        __M_writer(str(_('Select')))
        __M_writer('\r\n                        </button>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n        </div>\r\n\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "29": 1, "30": 4, "31": 4, "32": 5, "33": 5, "34": 6, "35": 6, "36": 7, "37": 7, "38": 10, "39": 10, "40": 12, "41": 12, "42": 28, "43": 28, "44": 39, "45": 39, "46": 44, "47": 44, "48": 50, "49": 50, "50": 58, "51": 58, "52": 65, "53": 65, "54": 73, "55": 73, "56": 76, "57": 76, "58": 82, "59": 82, "60": 98, "61": 98, "62": 99, "63": 99, "64": 100, "65": 100, "66": 101, "67": 101, "68": 102, "69": 102, "70": 103, "71": 103, "72": 112, "73": 112, "74": 114, "75": 114, "76": 129, "77": 129, "78": 130, "79": 130, "80": 131, "81": 131, "82": 132, "83": 132, "84": 133, "85": 133, "86": 134, "87": 134, "88": 144, "89": 144, "90": 150, "91": 150, "92": 155, "93": 155, "94": 158, "95": 158, "96": 167, "97": 167, "98": 171, "99": 171, "100": 172, "101": 172, "102": 180, "103": 180, "104": 187, "105": 188, "106": 188, "107": 188, "108": 188, "109": 188, "110": 190, "111": 195, "112": 196, "113": 197, "114": 198, "115": 199, "116": 199, "117": 199, "118": 199, "119": 199, "120": 202, "121": 210, "122": 210, "123": 218, "124": 218, "125": 221, "126": 222, "127": 224, "128": 224, "129": 227, "130": 231, "131": 231, "137": 131}, "source_encoding": "ascii", "uri": "templates/library/import/directory.html", "filename": "templates/library/import/directory.html"}
__M_END_METADATA
"""
