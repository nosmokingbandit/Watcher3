# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755950.288531
_enable_loop = True
_template_filename = 'templates/settings/system.html'
_template_uri = 'templates/settings/system.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        server_time = context.get('server_time', UNDEFINED)
        _ = context.get('_', UNDEFINED)
        head = context.get('head', UNDEFINED)
        tasks = context.get('tasks', UNDEFINED)
        url_base = context.get('url_base', UNDEFINED)
        navbar = context.get('navbar', UNDEFINED)
        system = context.get('system', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/system.css?v=010" rel="stylesheet">\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/system.js?v=011" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/settings/shared.js?v=012" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/lib/liteuploader.min.js?v=010" type="text/javascript"></script>\r\n\r\n        <meta name="tasks" content=\'')
        __M_writer(str(tasks))
        __M_writer('\'>\r\n        <meta name="server_time" content="')
        __M_writer(str(server_time[1]))
        __M_writer('">\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n\r\n            <h2>')
        __M_writer(str(_('System Information')))
        __M_writer('</h2>\r\n            <div class="row">\r\n                <div class="col-md-6 my-3">\r\n                    <div class="card">\r\n                        <div class="card-header">\r\n                            <h5>\r\n                                <i class="mdi mdi-clock"></i>\r\n                                ')
        __M_writer(str(_('Server Time')))
        __M_writer('\r\n                            </h5>\r\n                        </div>\r\n                        <div id="server_time" class="card-body">\r\n                            ')
        __M_writer(str(server_time[0]))
        __M_writer('\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6 my-3">\r\n                    <div class="card">\r\n                        <div class="card-header">\r\n                            <h5>\r\n                                <i class="mdi mdi-language-python"></i>\r\n                                ')
        __M_writer(str(_('Watcher Directory')))
        __M_writer('\r\n                            </h5>\r\n                        </div>\r\n                        <div class="card-body">\r\n                            ')
        __M_writer(str(system['system']['path']))
        __M_writer('\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6 my-3">\r\n                    <div class="card">\r\n                        <div class="card-header">\r\n                            <h5>\r\n                                <i class="mdi mdi-database"></i>\r\n                                ')
        __M_writer(str(_('Database')))
        __M_writer('\r\n                            </h5>\r\n                            <span class="float-right">[')
        __M_writer(str(system['database']['size']))
        __M_writer(' KB]</span>\r\n                        </div>\r\n                        <div class="card-body">\r\n                            ')
        __M_writer(str(system['database']['file']))
        __M_writer('\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6 my-3">\r\n                    <div class="card">\r\n                        <div class="card-header">\r\n                            <h5>\r\n                                <i class="mdi mdi-settings"></i>\r\n                                ')
        __M_writer(str(_('Config')))
        __M_writer('\r\n                            </h5>\r\n                        </div>\r\n                        <div class="card-body">\r\n                            ')
        __M_writer(str(system['config']['file']))
        __M_writer('\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6 my-3">\r\n                    <div class="card">\r\n                        <div class="card-header">\r\n                            <h5>\r\n                                <i class="mdi mdi-console"></i>\r\n                                ')
        __M_writer(str(_('Launch Arugments')))
        __M_writer('\r\n                            </h5>\r\n                        </div>\r\n                        <div class="card-body">\r\n                            [Python ')
        __M_writer(str(system['system']['version']))
        __M_writer(']\r\n                            ')
        __M_writer(str(' '.join(system['system']['arguments'])))
        __M_writer('\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n\r\n            <h2>')
        __M_writer(str(_('Backup')))
        __M_writer('</h2>\r\n            <div class="col-md-12">\r\n                <button class="btn btn-outline-primary" data-toggle="modal" data-target="#modal_create_backup">\r\n                    <i class="mdi mdi-package-variant-closed"></i>\r\n                    ')
        __M_writer(str(_('Create Backup')))
        __M_writer('\r\n                </button>\r\n                <button class="btn btn-outline-primary" data-toggle="modal" data-target="#modal_restore_backup">\r\n                    <i class="mdi mdi-backup-restore"></i>\r\n                    ')
        __M_writer(str(_('Restore Backup')))
        __M_writer('\r\n                </button>\r\n            </div>\r\n            </br/>\r\n\r\n            <h2>')
        __M_writer(str(_('Task Scheduler')))
        __M_writer('</h2>\r\n            <table id="tasks" class="table table-hover">\r\n                <thead class="thead-light">\r\n                    <tr>\r\n                        <th>')
        __M_writer(str(_('Enabled')))
        __M_writer('</th>\r\n                        <th>')
        __M_writer(str(_('Name')))
        __M_writer('</th>\r\n                        <th>')
        __M_writer(str(_('Frequency')))
        __M_writer('</th>\r\n                        <th>')
        __M_writer(str(_('Last Execution')))
        __M_writer('</th>\r\n                        <th>')
        __M_writer(str(_('Next Execution')))
        __M_writer('</th>\r\n                        <th class="center">')
        __M_writer(str(_('Execute Now')))
        __M_writer('</th>\r\n                    </tr>\r\n                </thead>\r\n                <tbody>\r\n\r\n                </tbody>\r\n            </table>\r\n\r\n            <div id="donate">\r\n                <i class="mdi mdi-gift"></i>\r\n                BTC:\r\n                <a href="bitcoin:17BfQVGCsmHBNkVVbL1GxhhYFUMX2uytaT?label=Watcher">\r\n                <span>17BfQVGCsmHBNkVVbL1GxhhYFUMX2uytaT</span>\r\n                </a>\r\n            </div>\r\n        </div>\r\n\r\n        <div class="modal fade" id="modal_create_backup">\r\n            <div class="modal-dialog modal-lg">\r\n                <div class="modal-content">\r\n                    <div class="modal-header">\r\n                        <h4 class="modal-title">')
        __M_writer(str(_('Create Backup of Watcher?')))
        __M_writer('</h4>\r\n                        <button class="btn btn-secondary btn-sm float-right" data-dismiss="modal">\r\n                            <i class="mdi mdi-close"></i>\r\n                        </button>\r\n                    </div>\r\n                    <div class="modal-body">\r\n                        ')
        __M_writer(str(_('A backup will be made of your <b>database</b>, <b>posters</b>, and <b>config</b>.')))
        __M_writer('\r\n                        <div class="thinker_small">\r\n                            <i class="mdi mdi-circle animated"></i>\r\n                        </div>\r\n                    </div>\r\n                    <div class="modal-footer">\r\n                            <button class="btn btn-success" onclick="create_backup(event, this)">\r\n                                ')
        __M_writer(str(_('Create Backup')))
        __M_writer('\r\n                            </button>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n        </div>\r\n        <div class="modal fade" id="modal_restore_backup">\r\n            <div class="modal-dialog modal-wide">\r\n                <div class="modal-content">\r\n                    <div class="modal-header">\r\n                        <h4 class="modal-title">')
        __M_writer(str(_('Restore Backup of Watcher?')))
        __M_writer('</h4>\r\n                        <button class="btn btn-secondary btn-sm float-right" data-dismiss="modal">\r\n                            <i class="mdi mdi-close"></i>\r\n                        </button>\r\n                    </div>\r\n                    <div class="modal-body">\r\n                        <div class="text_content">\r\n                            ')
        __M_writer(str(_('Restoring a backup will overwrite your <b>database</b>, <b>posters</b>, and <b>config</b>.<br/>This cannot be undone.<br/>Watcher will automatically restart after backup has been restored.')))
        __M_writer('\r\n                            <br/><br/>\r\n                            <div class="input-group">\r\n                                <label for="zip_file" class="input-group-prepend rounded-left">\r\n                                    <input id="zip_file" type="file" name="fileUpload" class="fileUpload" style="display:none;" onchange="_restore_zip_selected(this)"></input>\r\n                                    <a class="btn btn-secondary text-white">\r\n                                        <i class="mdi mdi-zip-box"></i>\r\n                                        ')
        __M_writer(str(_('Select Backup Zip')))
        __M_writer('\r\n                                    </a>\r\n                                </label>\r\n                                <input id="zip_file_input" class="form-control input-group-item" disabled></input>\r\n                            </div>\r\n                        </div>\r\n                        <div class="thinker_small">\r\n                            <i class="mdi mdi-circle animated"></i>\r\n                        </div>\r\n                        <div class="progress bg-dark">\r\n                            <div class="progress-bar"></div>\r\n                        </div>\r\n                    </div>\r\n                    <div class="modal-footer">\r\n                        <div class="btn-group btn-group-justified">\r\n                            <button id="submit_restore_zip" class="btn btn-success float-right" onclick="upload_restore_zip(event, this)" disabled>\r\n                                ')
        __M_writer(str(_('Restore Backup')))
        __M_writer('\r\n                            </button>\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n        </div>\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "28": 1, "29": 4, "30": 4, "31": 5, "32": 5, "33": 6, "34": 6, "35": 7, "36": 7, "37": 8, "38": 8, "39": 10, "40": 10, "41": 11, "42": 11, "43": 14, "44": 14, "45": 17, "46": 17, "47": 24, "48": 24, "49": 28, "50": 28, "51": 37, "52": 37, "53": 41, "54": 41, "55": 50, "56": 50, "57": 52, "58": 52, "59": 55, "60": 55, "61": 64, "62": 64, "63": 68, "64": 68, "65": 77, "66": 77, "67": 81, "68": 81, "69": 82, "70": 82, "71": 88, "72": 88, "73": 92, "74": 92, "75": 96, "76": 96, "77": 101, "78": 101, "79": 105, "80": 105, "81": 106, "82": 106, "83": 107, "84": 107, "85": 108, "86": 108, "87": 109, "88": 109, "89": 110, "90": 110, "91": 131, "92": 131, "93": 137, "94": 137, "95": 144, "96": 144, "97": 154, "98": 154, "99": 161, "100": 161, "101": 168, "102": 168, "103": 184, "104": 184, "110": 104}, "source_encoding": "ascii", "uri": "templates/settings/system.html", "filename": "templates/settings/system.html"}
__M_END_METADATA
"""
