# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755949.687854
_enable_loop = True
_template_filename = 'templates/library/import/plex.html'
_template_uri = 'templates/library/import/plex.html'
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
        __M_writer('/static/css/library/import/plex.css?v=010" rel="stylesheet">\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/library/import/shared.js?v=011" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/library/import/plex.js?v=012" type="text/javascript"></script>\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n            <h1>')
        __M_writer(str(_('Import Plex Library')))
        __M_writer('</h1>\r\n            <br/>\r\n\r\n            <nav id="stepper" class="nav nav-pills nav-fill">\r\n                <span class="nav-item nav-link border active" target="connect">Connect</span>\r\n                <span class="nav-item nav-link mx-3 border" target="import">Import</span>\r\n                <span class="nav-item nav-link border" target="review">Review</span>\r\n            </nav>\r\n\r\n            <div id="progress_bar" class="progress my-3 bg-dark">\r\n                <div class="progress-bar"></div>\r\n                <span class="text-light"></span>\r\n            </div>\r\n\r\n            <form id="connect" class="form-group row bg-light rounded mx-auto py-3">\r\n                <h3 class="ml-3">')
        __M_writer(str(_('Upload Plex CSV')))
        __M_writer('</h3>\r\n                <a href="https://github.com/nosmokingbandit/Watcher3/wiki/Importing-from-other-applications#plex" target="_blank" rel="noopener">\r\n                    <i class="mdi mdi-help-circle-outline"></i>\r\n                </a>\r\n                <div class="col-md-12">\r\n                    <div class="input-group">\r\n                        <label for="csv_file" class="input-group-prepend rounded-left">\r\n                            <input id="csv_file" type="file" name="fileUpload" class="fileUpload" style="display:none;" onchange="document.getElementById(\'plex_csv_file\').value = this.value"></input>\r\n                            <a class="btn btn-light border text-white">\r\n                                <i class="mdi mdi-file-document"></i>\r\n                                ')
        __M_writer(str(_('Select CSV')))
        __M_writer('\r\n                            </a>\r\n                        </label>\r\n                        <input id="plex_csv_file" class="form-control input-group-item" disabled></input>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-12 mt-3">\r\n                    <button class="btn btn-primary float-right" onclick="connect(event, this)">\r\n                        ')
        __M_writer(str(_('Read CSV')))
        __M_writer('\r\n                    </button>\r\n                </div>\r\n            </form>\r\n\r\n            <form id="import" class="form-group row bg-light rounded mx-auto py-3 hidden">\r\n                <div id="no_imports" class="hidden">\r\n                    <div class="alert alert-info mx-3">\r\n                            ')
        __M_writer(str(_('No new movies found.')))
        __M_writer('\r\n                    </div>\r\n                    <button class="btn btn-secondary float-right mr-3">\r\n                        ')
        __M_writer(str(_('Return')))
        __M_writer('\r\n                    </button>\r\n                </div>\r\n\r\n                <div id="remote_map" class="card mx-3">\r\n                    <div class="card-header">\r\n                        <big>')
        __M_writer(str(_('Remote Paths')))
        __M_writer('</big>\r\n                    </div>\r\n                    <div class="card-body">\r\n                        ')
        __M_writer(str(_('Plex lists file locations relative to itself. If Plex is on a different device than Watcher you may need to alter file paths.')))
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
        __M_writer('\r\n                                </button>\r\n                            </div>\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n\r\n                <div id="complete_movies" class="hidden">\r\n                    <h3 class="panel-title">\r\n                        ')
        __M_writer(str(_('Plex Movies')))
        __M_writer('\r\n                    </h3>\r\n                    <table class="table table-sm table-hover">\r\n                        <thead>\r\n                            <tr>\r\n                                <th class="shrink">')
        __M_writer(str(_('Import')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('File')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Title')))
        __M_writer('</th>\r\n                                <th class="shrink">')
        __M_writer(str(_('ID')))
        __M_writer('</th>\r\n                                <th class="shrink">')
        __M_writer(str(_('Source')))
        __M_writer('</th>\r\n                            </tr>\r\n                        </thead>\r\n                        <tbody>\r\n                        </tbody>\r\n                    </table>\r\n                </div>\r\n\r\n                <div id="incomplete_movies" class="hidden">\r\n                    <h3>\r\n                        ')
        __M_writer(str(_('Incomplete Movies')))
        __M_writer('\r\n                    </h3>\r\n                    <p>')
        __M_writer(str(_('The following movies are missing key information. Review and correct as needed.')))
        __M_writer('</p>\r\n                    <table class="table table-hover">\r\n                        <thead>\r\n                            <tr>\r\n                                <th class="shrink">')
        __M_writer(str(_('Import')))
        __M_writer('</th>\r\n                                <th class="file_path">')
        __M_writer(str(_('File')))
        __M_writer('</th>\r\n                                <th>')
        __M_writer(str(_('Title')))
        __M_writer('</th>\r\n                                <th>')
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
{"line_map": {"16": 0, "27": 1, "28": 4, "29": 4, "30": 5, "31": 5, "32": 6, "33": 6, "34": 7, "35": 7, "36": 10, "37": 10, "38": 12, "39": 12, "40": 27, "41": 27, "42": 37, "43": 37, "44": 45, "45": 45, "46": 53, "47": 53, "48": 56, "49": 56, "50": 62, "51": 62, "52": 65, "53": 65, "54": 67, "55": 67, "56": 73, "57": 73, "58": 77, "59": 77, "60": 83, "61": 83, "62": 87, "63": 87, "64": 96, "65": 96, "66": 101, "67": 101, "68": 102, "69": 102, "70": 103, "71": 103, "72": 104, "73": 104, "74": 105, "75": 105, "76": 115, "77": 115, "78": 117, "79": 117, "80": 121, "81": 121, "82": 122, "83": 122, "84": 123, "85": 123, "86": 124, "87": 124, "88": 125, "89": 125, "90": 135, "91": 135, "92": 141, "93": 141, "94": 146, "95": 146, "96": 149, "97": 149, "98": 158, "99": 158, "100": 162, "101": 162, "102": 163, "103": 163, "104": 172, "105": 172, "106": 179, "107": 180, "108": 180, "109": 180, "110": 180, "111": 180, "112": 182, "113": 187, "114": 188, "115": 189, "116": 190, "117": 191, "118": 191, "119": 191, "120": 191, "121": 191, "122": 194, "128": 122}, "source_encoding": "ascii", "uri": "templates/library/import/plex.html", "filename": "templates/library/import/plex.html"}
__M_END_METADATA
"""
