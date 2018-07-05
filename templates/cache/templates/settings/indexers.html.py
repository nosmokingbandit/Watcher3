# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755950.089645
_enable_loop = True
_template_filename = 'templates/settings/indexers.html'
_template_uri = 'templates/settings/indexers.html'
_source_encoding = 'ascii'
_exports = ['render_indexer']


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        _ = context.get('_', UNDEFINED)
        head = context.get('head', UNDEFINED)
        def render_indexer(indexer):
            return render_render_indexer(context._locals(__M_locals),indexer)
        url_base = context.get('url_base', UNDEFINED)
        config = context.get('config', UNDEFINED)
        navbar = context.get('navbar', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n\r\n\r\n<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/settings/shared.css?v=010" rel="stylesheet">\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/settings/indexers.css?v=010" rel="stylesheet">\r\n\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/settings/shared.js?v=012" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/settings/indexers.js?v=012" type="text/javascript"></script>\r\n\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n\r\n            <h1>')
        __M_writer(str(_('NewzNab Indexers')))
        __M_writer('</h1>\r\n            <form class="form-group row bg-light rounded mx-auto">\r\n                <table class="table">\r\n                    <thead class="thead-light">\r\n                        <th class="indexer_input_header">\r\n                            <span>\r\n                                ')
        __M_writer(str(_('URL')))
        __M_writer('\r\n                            </span>\r\n                            <span>\r\n                                ')
        __M_writer(str(_('API Key')))
        __M_writer('\r\n                            </span>\r\n                        </th>\r\n                        <th></th>\r\n                    </thead>\r\n                    <tbody data-category="newznab">\r\n')
        for indexer in config['NewzNab'].values():
            __M_writer('                        ')
            __M_writer(str(render_indexer(indexer)))
            __M_writer('\r\n')
        __M_writer('                    </tbody>\r\n                </table>\r\n                <div class=\'col-md-12\'>\r\n                    <button class="btn btn-outline-primary" onclick="add_indexer(event, \'newznab\')">\r\n                        <i class="mdi mdi-plus"></i>\r\n                    </button>\r\n                </div>\r\n            </form>\r\n\r\n            <h1>')
        __M_writer(str(_('TorzNab Indexers')))
        __M_writer('</h1>\r\n            <form class="form-group row bg-light rounded mx-auto">\r\n                <table class="table">\r\n                    <thead class="thead-light">\r\n                        <th class="indexer_input_header">\r\n                            <span>\r\n                                ')
        __M_writer(str(_('URL')))
        __M_writer('\r\n                            </span>\r\n                            <span>\r\n                                ')
        __M_writer(str(_('API Key')))
        __M_writer('\r\n                            </span>\r\n                        </th>\r\n                        <th></th>\r\n                    </thead>\r\n                    <tbody data-category="torznab">\r\n')
        for indexer in config['TorzNab'].values():
            __M_writer('                        ')
            __M_writer(str(render_indexer(indexer)))
            __M_writer('\r\n')
        __M_writer('                    </tbody>\r\n                </table>\r\n                <div class=\'col-md-12\'>\r\n                    <button class="btn btn-outline-primary" onclick="add_indexer(event, \'torznab\')">\r\n                        <i class="mdi mdi-plus"></i>\r\n                    </button>\r\n                </div>\r\n            </form>\r\n\r\n            <h1>')
        __M_writer(str(_('Torrent Indexers')))
        __M_writer('</h1>\r\n            <form class="form-group row bg-light rounded mx-auto py-3" data-category="torrent">\r\n                <div class="col-md-6">\r\n                    <div class="input-group">\r\n                        <div class="input-group-prepend">\r\n                            <span class="input-group-text">\r\n                                <i class="mdi mdi-checkbox-blank-outline c_box" id="limetorrents" value="')
        __M_writer(str(config['Torrent']['limetorrents']))
        __M_writer('"></i>\r\n                            </span>\r\n                        </div>\r\n                        <span class="input-group-item form-control">\r\n                            LimeTorrents\r\n                        </span>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <div class="input-group">\r\n                        <div class="input-group-prepend">\r\n                            <span class="input-group-text">\r\n                                <i class="mdi mdi-checkbox-blank-outline c_box" id="rarbg" value="')
        __M_writer(str(config['Torrent']['rarbg']))
        __M_writer('"></i>\r\n                            </span>\r\n                        </div>\r\n                        <span class="input-group-item form-control">\r\n                            Rarbg\r\n                        </span>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <div class="input-group">\r\n                        <div class="input-group-prepend">\r\n                            <span class="input-group-text">\r\n                                <i class="mdi mdi-checkbox-blank-outline c_box" id="thepiratebay" value="')
        __M_writer(str(config['Torrent']['thepiratebay']))
        __M_writer('"></i>\r\n                            </span>\r\n                        </div>\r\n                        <span class="input-group-item form-control">\r\n                            ThePirateBay\r\n                        </span>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <div class="input-group">\r\n                        <div class="input-group-prepend">\r\n                            <span class="input-group-text">\r\n                                <i class="mdi mdi-checkbox-blank-outline c_box" id="torrentdownloads" value="')
        __M_writer(str(config['Torrent']['torrentdownloads']))
        __M_writer('"></i>\r\n                            </span>\r\n                        </div>\r\n                        <span class="input-group-item form-control">\r\n                            TorrentDownloads\r\n                        </span>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <div class="input-group">\r\n                        <div class="input-group-prepend">\r\n                            <span class="input-group-text">\r\n                                <i class="mdi mdi-checkbox-blank-outline c_box" id="torrentz2" value="')
        __M_writer(str(config['Torrent']['torrentz2']))
        __M_writer('"></i>\r\n                            </span>\r\n                        </div>\r\n                        <span class="input-group-item form-control">\r\n                            Torrentz2\r\n                        </span>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <div class="input-group">\r\n                        <div class="input-group-prepend">\r\n                            <span class="input-group-text">\r\n                                <i class="mdi mdi-checkbox-blank-outline c_box" id="yts" value="')
        __M_writer(str(config['Torrent']['yts']))
        __M_writer('"></i>\r\n                            </span>\r\n                        </div>\r\n                        <span class="input-group-item form-control">\r\n                            YTS\r\n                        </span>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6">\r\n                    <div class="input-group">\r\n                        <div class="input-group-prepend">\r\n                            <span class="input-group-text">\r\n                                <i class="mdi mdi-checkbox-blank-outline c_box" id="zooqle" value="')
        __M_writer(str(config['Torrent']['zooqle']))
        __M_writer('"></i>\r\n                            </span>\r\n                        </div>\r\n                        <span class="input-group-item form-control">\r\n                            Zooqle (')
        __M_writer(str(_('backlog only')))
        __M_writer(')\r\n                        </span>\r\n                    </div>\r\n                </div>\r\n            </form>\r\n\r\n            <h1>Private Torrent Indexers</h1>\r\n            <form class="mx-auto" data-category="privtorrent">\r\n                <div class="row bg-light rounded mx-auto py-3" data-id="danishbits">\r\n                    <div class="input-group col-md-6 col-sm-12">\r\n                        <div class="input-group-prepend">\r\n                            <span class="input-group-text">\r\n                                <i class="mdi mdi-checkbox-blank-outline c_box" data-id="enabled" title="Enabled" value="')
        __M_writer(str(config['PrivateTorrent']['danishbits']['enabled']))
        __M_writer('"></i>\r\n                            </span>\r\n                        </div>\r\n                        <span class="input-group-item form-control">\r\n                            DanishBits\r\n                        </span>\r\n                    </div>\r\n                    <div class="input-group col-md-6 col-sm-12">\r\n                        <input class="form-control" type="text" data-id="username" placeholder="Username" value="')
        __M_writer(str(config['PrivateTorrent']['danishbits']['username']))
        __M_writer('"/>\r\n                        <input class="form-control" type="text" data-id="passkey" placeholder="Passkey" value="')
        __M_writer(str(config['PrivateTorrent']['danishbits']['passkey']))
        __M_writer('"/>\r\n                    </div>\r\n                </div>\r\n            </form>\r\n\r\n            <button id="save_settings" class="btn btn-success float-right" onclick="save_settings(event, this)">\r\n                <i class="mdi mdi-content-save"></i>\r\n\r\n            </button>\r\n        </div>\r\n\r\n        <template id="new_indexer">\r\n            ')
        __M_writer(str(render_indexer(['', '', 'False'])))
        __M_writer('\r\n        </template>\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_render_indexer(context,indexer):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_writer = context.writer()
        __M_writer('\r\n    <tr>\r\n        <td>\r\n            <div class="input-group">\r\n                <div class="input-group-prepend">\r\n                    <span class="input-group-text">\r\n                        <i class="mdi mdi-checkbox-blank-outline c_box" value="')
        __M_writer(str(indexer[2]))
        __M_writer('"></i>\r\n                    </span>\r\n                </div>\r\n                <input type="text" data-id="url" class="form-control" placeholder="http://www.indexer.com/" value="')
        __M_writer(str(indexer[0]))
        __M_writer('">\r\n                <input type="text" data-id="api" class="form-control" placeholder="123456789abcdef" value="')
        __M_writer(str(indexer[1]))
        __M_writer('">\r\n            </div>\r\n        </td>\r\n        <td>\r\n            <button class="btn btn-outline-success" title="Test Indexer Connection" onclick="test_indexer(event, this)">\r\n                <i class="mdi mdi-lan-pending"></i>\r\n            </button>\r\n\r\n            <button class="btn btn-outline-danger" onclick="remove_indexer(event, this)">\r\n                <i class="mdi mdi-delete"></i>\r\n            </button>\r\n        </td>\r\n    </tr>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "28": 24, "29": 30, "30": 30, "31": 32, "32": 32, "33": 33, "34": 33, "35": 35, "36": 35, "37": 36, "38": 36, "39": 40, "40": 40, "41": 43, "42": 43, "43": 49, "44": 49, "45": 52, "46": 52, "47": 58, "48": 59, "49": 59, "50": 59, "51": 61, "52": 70, "53": 70, "54": 76, "55": 76, "56": 79, "57": 79, "58": 85, "59": 86, "60": 86, "61": 86, "62": 88, "63": 97, "64": 97, "65": 103, "66": 103, "67": 115, "68": 115, "69": 127, "70": 127, "71": 139, "72": 139, "73": 151, "74": 151, "75": 163, "76": 163, "77": 175, "78": 175, "79": 179, "80": 179, "81": 191, "82": 191, "83": 199, "84": 199, "85": 200, "86": 200, "87": 212, "88": 212, "94": 1, "98": 1, "99": 7, "100": 7, "101": 10, "102": 10, "103": 11, "104": 11, "110": 104}, "source_encoding": "ascii", "uri": "templates/settings/indexers.html", "filename": "templates/settings/indexers.html"}
__M_END_METADATA
"""
