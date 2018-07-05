# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755950.405465
_enable_loop = True
_template_filename = 'templates/navbar.html'
_template_uri = 'templates/navbar.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        url_base = context.get('url_base', UNDEFINED)
        username = context.get('username', UNDEFINED)
        _ = context.get('_', UNDEFINED)
        current = context.get('current', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<nav class="navbar navbar-expand-md navbar-light bg-light shadow">\r\n    <div class="container">\r\n        <div class="navbar-header">\r\n            <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">\r\n                <span>\r\n                    <i class="mdi mdi-menu"></i>\r\n                </span>\r\n            </button>\r\n            <a href="')
        __M_writer(str(url_base))
        __M_writer('/library/status">\r\n                <img src="')
        __M_writer(str(url_base))
        __M_writer('/static/images/logo.png" alt="" class="">\r\n            </a>\r\n        </div>\r\n        <div class="collapse navbar-collapse" id="navbarSupportedContent">\r\n\r\n            <ul class="navbar-nav mr-auto">\r\n                <li class="nav-item dropdown ')
        __M_writer(str('active' if current == 'library' else ''))
        __M_writer('">\r\n                    <a href="')
        __M_writer(str(url_base))
        __M_writer('/library/status" class="nav-link dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">\r\n                        ')
        __M_writer(str(_('Library')))
        __M_writer('\r\n                    </a>\r\n                    <ul class="dropdown-menu" role="menu">\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/library/status" class="nav-link">\r\n                                <i class="mdi mdi-bookmark"></i> ')
        __M_writer(str(_('Status')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/library/manage" class="nav-link">\r\n                                <i class="mdi mdi-briefcase"></i> ')
        __M_writer(str(_('Manage')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/library/import" class="nav-link">\r\n                                <i class="mdi mdi-archive"></i> ')
        __M_writer(str(_('Import')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/library/stats" class="nav-link">\r\n                                <i class="mdi mdi-chart-bar"></i> ')
        __M_writer(str(_('Stats')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                    </ul>\r\n                </li>\r\n                <li class="nav-item ')
        __M_writer(str('active' if current == 'add_movie' else ''))
        __M_writer('">\r\n                    <a href="')
        __M_writer(str(url_base))
        __M_writer('/add_movie" class="nav-link">')
        __M_writer(str(_('Add Movie')))
        __M_writer('</a>\r\n                </li>\r\n                <li class="nav-item dropdown ')
        __M_writer(str('active' if current == 'settings' else ''))
        __M_writer('">\r\n                    <a href="')
        __M_writer(str(url_base))
        __M_writer('/settings/server" class="nav-link dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">\r\n                        ')
        __M_writer(str(_('Settings')))
        __M_writer('\r\n                    </a>\r\n                    <ul class="dropdown-menu" role="menu">\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/settings/server" class="nav-link">\r\n                                <i class="mdi mdi-server"></i> ')
        __M_writer(str(_('Server')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/settings/search" class="nav-link">\r\n                                <i class="mdi mdi-magnify"></i> ')
        __M_writer(str(_('Search')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/settings/quality" class="nav-link">\r\n                                <i class="mdi mdi-video"></i> ')
        __M_writer(str(_('Quality')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/settings/indexers" class="nav-link">\r\n                                <i class="mdi mdi-sitemap"></i> ')
        __M_writer(str(_('Indexers')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/settings/downloader" class="nav-link">\r\n                                <i class="mdi mdi-download"></i> ')
        __M_writer(str(_('Downloader')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/settings/postprocessing" class="nav-link">\r\n                                <i class="mdi mdi-file-video"></i> ')
        __M_writer(str(_('Postprocessing')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/settings/plugins" class="nav-link">\r\n                                <i class="mdi mdi-puzzle"></i> ')
        __M_writer(str(_('Plugins')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/settings/logs" class="nav-link">\r\n                                <i class="mdi mdi-clipboard-text"></i> ')
        __M_writer(str(_('Logs')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a href="')
        __M_writer(str(url_base))
        __M_writer('/settings/system" class="nav-link">\r\n                                <i class="mdi mdi-memory"></i> ')
        __M_writer(str(_('System')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li class="dropdown-divider"></li>\r\n')
        if username:
            __M_writer('                        <li>\r\n                            <a class="nav-link active">\r\n                                <i class="mdi mdi-account-circle"></i>\r\n                                <b>')
            __M_writer(str(username))
            __M_writer('</b>\r\n                            </a>\r\n                        </li>\r\n                        <li data-toggle="modal" data-target="#modal_logout">\r\n                            <a class="nav-link">\r\n                                <i class="mdi mdi-logout"></i> ')
            __M_writer(str(_('Log Out')))
            __M_writer('\r\n                            </a>\r\n                        </li>\r\n')
        __M_writer('                        <li>\r\n                            <a data-toggle="modal" data-target="#modal_restart" class="nav-link">\r\n                                <i class="mdi mdi-restart"></i> ')
        __M_writer(str(_('Restart')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                        <li>\r\n                            <a data-toggle="modal" data-target="#modal_shutdown" class="nav-link">\r\n                                <i class="mdi mdi-power"></i> ')
        __M_writer(str(_('Shut Down')))
        __M_writer('\r\n                            </a>\r\n                        </li>\r\n                    </ul>\r\n                </li>\r\n            </ul>\r\n\r\n            <div class="navbar-right btn-group">\r\n                <a class="btn text-primary" href="https://www.reddit.com/r/watcher/" target="_blank" rel="noopener">\r\n                    <i class="mdi mdi-reddit"></i>\r\n                </a>\r\n                <a class="btn text-primary" href="https://github.com/nosmokingbandit/watcher3" target="_blank" rel="noopener">\r\n                    <i class="mdi mdi-github-circle"></i>\r\n                </a>\r\n            </div>\r\n        </div>\r\n    </div>\r\n</nav>\r\n\r\n\r\n<!-- Modal for Log Out, Restart, and Shutdown -->\r\n<div class="modal fade" id="modal_logout">\r\n    <div class="modal-dialog modal-sm">\r\n        <div class="modal-content">\r\n            <div class="modal-header">\r\n                <h4 class="modal-title">\r\n                    ')
        __M_writer(str(_('Log Out?')))
        __M_writer('\r\n                </h4>\r\n                <button class="btn btn-secondary btn-sm float-right" data-dismiss="modal">\r\n                    <i class="mdi mdi-close"></i>\r\n                </button>\r\n            </div>\r\n            <div class="modal-footer">\r\n                <div class="btn-group btn-group-justified">\r\n                    <a class="btn btn-warning" onclick="logout(event)">\r\n                        ')
        __M_writer(str(_('Log Out')))
        __M_writer('\r\n                    </a>\r\n                </div>\r\n            </div>\r\n        </div>\r\n    </div>\r\n</div>\r\n\r\n<div class="modal fade" id="modal_shutdown">\r\n    <div class="modal-dialog modal-sm">\r\n        <div class="modal-content">\r\n            <div class="modal-header">\r\n                <h4 class="modal-title">\r\n                    ')
        __M_writer(str(_('Shut Down Watcher?')))
        __M_writer('\r\n                </h4>\r\n                <button class="btn btn-secondary btn-sm float-right" data-dismiss="modal">\r\n                    <i class="mdi mdi-close"></i>\r\n                </button>\r\n            </div>\r\n            <div class="modal-footer">\r\n                <a href="')
        __M_writer(str(url_base))
        __M_writer('/system/shutdown" class="btn btn-outline-danger">\r\n                    ')
        __M_writer(str(_('Shut Down')))
        __M_writer('\r\n                </a>\r\n            </div>\r\n        </div>\r\n    </div>\r\n</div>\r\n\r\n<div class="modal fade" id="modal_restart">\r\n    <div class="modal-dialog modal-sm">\r\n        <div class="modal-content">\r\n            <div class="modal-header">\r\n                <h4 class="modal-title">\r\n                    ')
        __M_writer(str(_('Restart Watcher?')))
        __M_writer('\r\n                </h4>\r\n                <button class="btn btn-secondary btn-sm float-right" data-dismiss="modal">\r\n                    <i class="mdi mdi-close"></i>\r\n                </button>\r\n            </div>\r\n            <div class="modal-footer">\r\n                <a href="')
        __M_writer(str(url_base))
        __M_writer('/system/restart" class="btn btn-warning">\r\n                    ')
        __M_writer(str(_('Restart')))
        __M_writer('\r\n                </a>\r\n            </div>\r\n        </div>\r\n    </div>\r\n</div>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "25": 1, "26": 9, "27": 9, "28": 10, "29": 10, "30": 16, "31": 16, "32": 17, "33": 17, "34": 18, "35": 18, "36": 22, "37": 22, "38": 23, "39": 23, "40": 27, "41": 27, "42": 28, "43": 28, "44": 32, "45": 32, "46": 33, "47": 33, "48": 37, "49": 37, "50": 38, "51": 38, "52": 43, "53": 43, "54": 44, "55": 44, "56": 44, "57": 44, "58": 46, "59": 46, "60": 47, "61": 47, "62": 48, "63": 48, "64": 52, "65": 52, "66": 53, "67": 53, "68": 57, "69": 57, "70": 58, "71": 58, "72": 62, "73": 62, "74": 63, "75": 63, "76": 67, "77": 67, "78": 68, "79": 68, "80": 72, "81": 72, "82": 73, "83": 73, "84": 77, "85": 77, "86": 78, "87": 78, "88": 82, "89": 82, "90": 83, "91": 83, "92": 87, "93": 87, "94": 88, "95": 88, "96": 92, "97": 92, "98": 93, "99": 93, "100": 97, "101": 98, "102": 101, "103": 101, "104": 106, "105": 106, "106": 110, "107": 112, "108": 112, "109": 117, "110": 117, "111": 143, "112": 143, "113": 152, "114": 152, "115": 165, "116": 165, "117": 172, "118": 172, "119": 173, "120": 173, "121": 185, "122": 185, "123": 192, "124": 192, "125": 193, "126": 193, "132": 126}, "source_encoding": "ascii", "uri": "templates/navbar.html", "filename": "templates/navbar.html"}
__M_END_METADATA
"""
