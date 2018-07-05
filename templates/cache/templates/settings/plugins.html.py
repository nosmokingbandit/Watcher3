# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755950.242557
_enable_loop = True
_template_filename = 'templates/settings/plugins.html'
_template_uri = 'templates/settings/plugins.html'
_source_encoding = 'ascii'
_exports = ['render_plugins']


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        url_base = context.get('url_base', UNDEFINED)
        _ = context.get('_', UNDEFINED)
        def render_plugins(kind):
            return render_render_plugins(context._locals(__M_locals),kind)
        head = context.get('head', UNDEFINED)
        navbar = context.get('navbar', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n\r\n<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/settings/shared.css?v=010" rel="stylesheet">\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/settings/plugins.css?v=010" rel="stylesheet">\r\n\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/settings/shared.js?v=012" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/settings/plugins.js?v=013" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/lib/jquery.sortable.min.js?v=010" type="text/javascript"></script>\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n            <h1>')
        __M_writer(str(_('Plugins')))
        __M_writer('</h1>\r\n\r\n            <h3>')
        __M_writer(str(_('Added')))
        __M_writer('</h3>\r\n            <form class="form-group row bg-light rounded mx-auto py-3" data-category="added">\r\n                <ul class="sortable list-group mx-3">\r\n                    ')
        __M_writer(str(render_plugins('added')))
        __M_writer('\r\n                </ul>\r\n            </form>\r\n\r\n            <h3>')
        __M_writer(str(_('Snatched')))
        __M_writer('</h3>\r\n            <form class="form-group row bg-light rounded mx-auto py-3" data-category="snatched">\r\n                <ul class="sortable list-group mx-3">\r\n                    ')
        __M_writer(str(render_plugins('snatched')))
        __M_writer('\r\n                </ul>\r\n            </form>\r\n\r\n            <h3>')
        __M_writer(str(_('Finished')))
        __M_writer('</h3>\r\n            <form class="form-group row bg-light rounded mx-auto py-3" data-category="finished">\r\n                <ul class="sortable list-group mx-3">\r\n                    ')
        __M_writer(str(render_plugins('finished')))
        __M_writer('\r\n                </ul>\r\n            </form>\r\n\r\n            <div class="col-md-12">\r\n                ')
        __M_writer(str(_('See the Wiki for plugin instruction.')))
        __M_writer('\r\n                <a href="https://github.com/nosmokingbandit/Watcher3/wiki/Plugins", target="_blank" rel="noopener">\r\n                    <i class="mdi mdi-help-circle-outline"></i>\r\n                </a>\r\n\r\n            </div>\r\n\r\n            <button id="save_settings" class="btn btn-success float-right" onclick="save_settings(event, this)">\r\n                <i class="mdi mdi-content-save"></i>\r\n            </button>\r\n\r\n        </div>\r\n\r\n        <template id="template_config">\r\n            <div class="modal fade" id="modal_plugin_conf" data-folder="{folder}" data-filename="{filename}">\r\n                <div class="modal-dialog modal-wide">\r\n                    <div class="modal-content">\r\n                        <div class="modal-header">\r\n                            <h4 class="modal-title">{name}</h4>\r\n                            <button class="btn btn-secondary btn-sm" data-dismiss="modal">\r\n                                <i class="mdi mdi-close"></i>\r\n                            </button>\r\n                        </div>\r\n                        <div class="modal-body row">\r\n                            {config}\r\n                        </div>\r\n                        <div class="modal-footer">\r\n                            <div class="btn-group btn-group-justified">\r\n                                <button class="btn btn-success" onclick="save_plugin_conf(event, this)">\r\n                                    <i class="mdi mdi-content-save"></i>\r\n                                </button>\r\n                            </div>\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n        </template>\r\n\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_render_plugins(context,kind):
    __M_caller = context.caller_stack._push_frame()
    try:
        config = context.get('config', UNDEFINED)
        plugins = context.get('plugins', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n    ')

        fid = 0
        
        
        __M_writer('\r\n')
        for plugin in plugins[kind]:
            __M_writer('        ')

            name = plugin[0]
            enabled, sort = config[kind].get(name, (False, 900+fid))
            fid += 1
            
            
            __M_writer('\r\n        <li id="')
            __M_writer(str(kind))
            __M_writer(str(fid))
            __M_writer('" class="list-group-item" data-name="')
            __M_writer(str(plugin[0]))
            __M_writer('" data-sort="')
            __M_writer(str(sort))
            __M_writer('">\r\n            <i class="mdi mdi-drag-horizontal sortable_handle"></i>\r\n            <i class="mdi mdi-checkbox-blank-outline c_box" value="')
            __M_writer(str(enabled))
            __M_writer('"></i>\r\n            ')
            __M_writer(str(name[:-3]))
            __M_writer('\r\n')
            if plugin[1]:
                __M_writer('            <i class="mdi mdi-settings float-right" onclick="edit_plugin_conf(event, this, \'')
                __M_writer(str(kind))
                __M_writer("', '")
                __M_writer(str(plugin[1]))
                __M_writer('\')"></i>\r\n')
            __M_writer('        </li>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "27": 20, "28": 25, "29": 25, "30": 26, "31": 26, "32": 27, "33": 27, "34": 29, "35": 29, "36": 30, "37": 30, "38": 31, "39": 31, "40": 34, "41": 34, "42": 36, "43": 36, "44": 38, "45": 38, "46": 41, "47": 41, "48": 45, "49": 45, "50": 48, "51": 48, "52": 52, "53": 52, "54": 55, "55": 55, "56": 60, "57": 60, "63": 1, "69": 1, "70": 2, "74": 4, "75": 5, "76": 6, "77": 6, "83": 10, "84": 11, "85": 11, "86": 11, "87": 11, "88": 11, "89": 11, "90": 11, "91": 13, "92": 13, "93": 14, "94": 14, "95": 15, "96": 16, "97": 16, "98": 16, "99": 16, "100": 16, "101": 18, "107": 101}, "source_encoding": "ascii", "uri": "templates/settings/plugins.html", "filename": "templates/settings/plugins.html"}
__M_END_METADATA
"""
