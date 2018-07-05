# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755950.059675
_enable_loop = True
_template_filename = 'templates/settings/quality.html'
_template_uri = 'templates/settings/quality.html'
_source_encoding = 'ascii'
_exports = ['generate_profile']


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        _ = context.get('_', UNDEFINED)
        head = context.get('head', UNDEFINED)
        sources = context.get('sources', UNDEFINED)
        def generate_profile(name,profile):
            return render_generate_profile(context._locals(__M_locals),name,profile)
        url_base = context.get('url_base', UNDEFINED)
        config = context.get('config', UNDEFINED)
        navbar = context.get('navbar', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n\r\n\r\n<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/settings/shared.css?v=010" rel="stylesheet">\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/settings/quality.css?v=010" rel="stylesheet">\r\n\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/settings/shared.js?v=012" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/settings/quality.js?v=012" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/lib/jquery.sortable.min.js?v=010" type="text/javascript"></script>\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n            <h1>')
        __M_writer(str(_('Quality Profiles')))
        __M_writer('</h1>\r\n            <form id=\'profiles\' class="mx-auto">\r\n')
        for name, profile in config['Profiles'].items():
            __M_writer('                ')
            __M_writer(str(generate_profile(name, profile)))
            __M_writer('\r\n')
        __M_writer('            </form>\r\n\r\n            <div class=\'col-md-12\' id="add_profile">\r\n                <button class="btn btn-outline-primary" onclick="add_profile(event)">\r\n                    <i class="mdi mdi-plus"></i>\r\n                </button>\r\n            </div>\r\n\r\n            <h1 class="mt-4">')
        __M_writer(str(_('Sources')))
        __M_writer('</h1>\r\n            <form class="form-group row bg-light rounded mx-auto py-3" data-category="sources">\r\n                <div class="col-md-12">\r\n                    ')
        __M_writer(str(_('Specify acceptable size ranges (in MegaBytes) for source media.')))
        __M_writer('\r\n                </div>\r\n                <table class="table table-hover">\r\n                    <thead class="thead-light">\r\n                        <tr>\r\n                            <th></th>\r\n                            <th>')
        __M_writer(str(_('Min Size')))
        __M_writer('</th>\r\n                            <th>')
        __M_writer(str(_('Max Size')))
        __M_writer('</th>\r\n                        </tr>\r\n                    </thead>\r\n                    <tbody>\r\n')
        for src in sources:
            __M_writer('                        ')

            v = config['Sources'][src]
                                    
            
            __M_locals_builtin_stored = __M_locals_builtin()
            __M_locals.update(__M_dict_builtin([(__M_key, __M_locals_builtin_stored[__M_key]) for __M_key in ['v'] if __M_key in __M_locals_builtin_stored]))
            __M_writer('\r\n                        <tr id="')
            __M_writer(str(src))
            __M_writer('">\r\n                            <td>')
            __M_writer(str(src))
            __M_writer('</td>\r\n                            <td>\r\n                                <input type="number" class="form-control form-control-sm" data-range="min" min="0" value=')
            __M_writer(str(v['min']))
            __M_writer('>\r\n                            </td>\r\n                            <td>\r\n                                <input type="number" class="form-control form-control-sm" data-range="max" min="0" value=')
            __M_writer(str(v['max']))
            __M_writer('>\r\n                            </td>\r\n                        </tr>\r\n')
        __M_writer('                    </tbody>\r\n                </table>\r\n            </form>\r\n\r\n            <h2>')
        __M_writer(str(_('Aliases')))
        __M_writer('</h2>\r\n            <form class="form-group row bg-light rounded mx-auto py-3" data-category="aliases">\r\n                <div class="col-md-12">\r\n                    ')
        __M_writer(str(_('Keywords used to determine source media')))
        __M_writer('\r\n                </div>\r\n                <table id="aliases" class="table table-hover" data-toggle="tooltip"title="')
        __M_writer(str(_('Separate Keywords with commas')))
        __M_writer('">\r\n                    <tbody>\r\n')
        for name, alias in config['Aliases'].items():
            __M_writer('                        <tr>\r\n                            <td>')
            __M_writer(str(name))
            __M_writer('</td>\r\n                            <td>\r\n                                <input type="text" id="')
            __M_writer(str(name))
            __M_writer('" class="form-control form-control-sm" value="')
            __M_writer(str(', '.join(alias)))
            __M_writer('">\r\n                            </td>\r\n                        </tr>\r\n')
        __M_writer('                    </tbody>\r\n                </table>\r\n            </form>\r\n\r\n            <button id="save_settings" class="btn btn-success float-right" onclick="save_settings(event, this)">\r\n                <i class="mdi mdi-content-save"></i>\r\n\r\n            </button>\r\n        </div>\r\n\r\n        <template id="profile_template">\r\n            ')
        __M_writer(str(generate_profile("", {'Sources': {'BluRay-1080P': [True, 1], 'BluRay-4K': [False, 0], 'BluRay-720P': [True, 2], 'CAM-SD': [False, 13], 'DVD-SD': [False, 9], 'Screener-1080P': [False, 10], 'Screener-720P': [False, 11], 'Telesync-SD': [False, 12], 'WebDL-1080P': [True, 4], 'WebDL-4K': [False, 3], 'WebDL-720P': [True, 5], 'WebRip-1080P': [True, 7], 'WebRip-4K': [False, 6], 'WebRip-720P': [True, 8]}, 'ignoredwords': 'subs,german,dutch,french,truefrench,danish,swedish,spanish,italian,korean,dubbed,swesub,korsub,dksubs,vain,HC,blurred', 'preferredwords': '', 'prefersmaller': False, 'requiredwords': '', 'scoretitle': True})))
        __M_writer('\r\n        </template>\r\n\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_generate_profile(context,name,profile):
    __M_caller = context.caller_stack._push_frame()
    try:
        _ = context.get('_', UNDEFINED)
        sources = context.get('sources', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n    <div id="')
        __M_writer(str(name))
        __M_writer('" class="quality_profile row bg-light rounded mx-auto py-3">\r\n        <div class="col-md-6 input-group my-0">\r\n            <div class="input-group-prepend">\r\n                <span class="input-group-text">\r\n                    <i class="mdi radio ')
        __M_writer(str('mdi-star' if profile.get('default') else 'mdi-star-outline'))
        __M_writer('" value="')
        __M_writer(str('True' if profile.get('default') else 'False'))
        __M_writer('" title="')
        __M_writer(str(_('Use as Default profile')))
        __M_writer('"></i>\r\n                </span>\r\n            </div>\r\n            <input type="text" id="name" class="form-control" value="')
        __M_writer(str(name))
        __M_writer('">\r\n        </div>\r\n        <div class="col-md-6">\r\n            <button class="btn btn-light border float-right" onclick="edit_profile(event, this)">\r\n                <i class="mdi mdi-chevron-down"></i>\r\n            </button>\r\n        </div>\r\n\r\n        <div class="col-md-12 profile_contents mt-3">\r\n            <div class="row">\r\n                <div class="col-md-6">\r\n                    <h5>')
        __M_writer(str(_('Sources')))
        __M_writer('</h5>\r\n                    <div class="card">\r\n                        <ul class="sources sortable">\r\n')
        for src in sources:
            __M_writer('                            <li class="source rounded pl-2 my-1" data-source="')
            __M_writer(str(src))
            __M_writer('" data-sort="')
            __M_writer(str(profile['Sources'].get(src, [None, 99])[1]))
            __M_writer('">\r\n                                <i class="mdi mdi-drag-horizontal sortable_handle"></i>\r\n                                <i class="mdi mdi-checkbox-blank-outline c_box" value="')
            __M_writer(str(profile['Sources'].get(src, [False, None])[0]))
            __M_writer('"></i>\r\n                                ')
            __M_writer(str(src))
            __M_writer('\r\n                            </li>\r\n')
        __M_writer('                        </ul>\r\n                    </div>\r\n                </div>\r\n\r\n                <div class="col-md-6">\r\n                    <h5>')
        __M_writer(str(_('Filters')))
        __M_writer('</h5>\r\n                    <div data-sub-category="filters" data-toggle="tooltip" title="')
        __M_writer(str(_('Group words with ampersands and split groups with commas')))
        __M_writer('">\r\n                        <label>')
        __M_writer(str(_('Required Words')))
        __M_writer('</label>\r\n                        <input type="text" id="requiredwords" class="form-control" value="')
        __M_writer(str(profile['requiredwords']))
        __M_writer('">\r\n\r\n                        <label>')
        __M_writer(str(_('Preferred Words')))
        __M_writer('</label>\r\n                        <input type="text" id="preferredwords" class="form-control" placeholder=\'this&is&a&group, one, two, three\' value="')
        __M_writer(str(profile['preferredwords']))
        __M_writer('">\r\n\r\n                        <label>')
        __M_writer(str(_('Ignored Words')))
        __M_writer('</label>\r\n                        <input type="text" id="ignoredwords" class="form-control" value="')
        __M_writer(str(profile['ignoredwords']))
        __M_writer('">\r\n                    </div>\r\n\r\n                    <h5 class="mt-4">')
        __M_writer(str(_('Misc.')))
        __M_writer('</h5>\r\n                    <div data-sub-category="misc">\r\n                        <div class="input-group">\r\n                            <div class="input-group-prepend">\r\n                                <span class="input-group-text">\r\n                                    <i id="scoretitle" class="mdi mdi-checkbox-blank-outline c_box" value="')
        __M_writer(str(profile['scoretitle']))
        __M_writer('"></i>\r\n                                </span>\r\n                            </div>\r\n                            <span class="input-group-item form-control">\r\n                                    ')
        __M_writer(str(_('Score and filter release titles')))
        __M_writer('\r\n                            </span>\r\n                        </div>\r\n                        <div class="input-group">\r\n                            <div class="input-group-prepend">\r\n                                <span class="input-group-text">\r\n                                    <i id="prefersmaller" class="mdi mdi-checkbox-blank-outline c_box" value="')
        __M_writer(str(profile['prefersmaller']))
        __M_writer('"></i>\r\n                                </span>\r\n                            </div>\r\n                            <span class="input-group-item form-control">\r\n                                    ')
        __M_writer(str(_('Prefer smaller file sizes')))
        __M_writer('\r\n                            </span>\r\n                        </div>\r\n                    </div>\r\n                    <button class="btn btn-outline-danger float-right" onclick="delete_profile(event, this)">\r\n                        <i class="mdi mdi-delete"></i>\r\n                    </button>\r\n                </div>\r\n            </div>\r\n        </div>\r\n    </div>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "29": 77, "30": 83, "31": 83, "32": 84, "33": 84, "34": 85, "35": 85, "36": 87, "37": 87, "38": 88, "39": 88, "40": 89, "41": 89, "42": 92, "43": 92, "44": 94, "45": 94, "46": 96, "47": 97, "48": 97, "49": 97, "50": 99, "51": 107, "52": 107, "53": 110, "54": 110, "55": 116, "56": 116, "57": 117, "58": 117, "59": 121, "60": 122, "61": 122, "67": 124, "68": 125, "69": 125, "70": 126, "71": 126, "72": 128, "73": 128, "74": 131, "75": 131, "76": 135, "77": 139, "78": 139, "79": 142, "80": 142, "81": 144, "82": 144, "83": 146, "84": 147, "85": 148, "86": 148, "87": 150, "88": 150, "89": 150, "90": 150, "91": 154, "92": 165, "93": 165, "99": 1, "105": 1, "106": 2, "107": 2, "108": 6, "109": 6, "110": 6, "111": 6, "112": 6, "113": 6, "114": 9, "115": 9, "116": 20, "117": 20, "118": 23, "119": 24, "120": 24, "121": 24, "122": 24, "123": 24, "124": 26, "125": 26, "126": 27, "127": 27, "128": 30, "129": 35, "130": 35, "131": 36, "132": 36, "133": 37, "134": 37, "135": 38, "136": 38, "137": 40, "138": 40, "139": 41, "140": 41, "141": 43, "142": 43, "143": 44, "144": 44, "145": 47, "146": 47, "147": 52, "148": 52, "149": 56, "150": 56, "151": 62, "152": 62, "153": 66, "154": 66, "160": 154}, "source_encoding": "ascii", "uri": "templates/settings/quality.html", "filename": "templates/settings/quality.html"}
__M_END_METADATA
"""
