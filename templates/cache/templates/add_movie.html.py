# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755949.768807
_enable_loop = True
_template_filename = 'templates/add_movie.html'
_template_uri = 'templates/add_movie.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        url_base = context.get('url_base', UNDEFINED)
        profiles = context.get('profiles', UNDEFINED)
        _ = context.get('_', UNDEFINED)
        head = context.get('head', UNDEFINED)
        navbar = context.get('navbar', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/add_movie.css?v=011" rel="stylesheet">\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/add_movie.js?v=012" type="text/javascript"></script>\r\n    </head>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n\r\n            <ul class="nav nav-pills mb-3">\r\n                <li class="nav-item border rounded mx-2 mb-3">\r\n                    <a class="nav-link active" href="#tab_search" data-toggle="pill" data-cat="search">\r\n                        Search\r\n                    </a>\r\n                </li>\r\n                <li class="nav-item border rounded mx-2 mb-3">\r\n                    <a class="nav-link" href="#tab_popular" data-toggle="pill" data-cat="popular">\r\n                        Popular\r\n                    </a>\r\n                </li>\r\n                <li class="nav-item border rounded mx-2 mb-3">\r\n                    <a class="nav-link" href="#tab_now_playing" data-toggle="pill" data-cat="now_playing">\r\n                        Now Playing\r\n                    </a>\r\n                </li>\r\n                <li class="nav-item border rounded mx-2 mb-3">\r\n                    <a class="nav-link" href="#tab_top_rated" data-toggle="pill" data-cat="top_rated">\r\n                        Top Rated\r\n                    </a>\r\n                </li>\r\n                <li class="nav-item border rounded mx-2 mb-3">\r\n                    <a class="nav-link" href="#tab_upcoming" data-toggle="pill" data-cat="upcoming">\r\n                        Upcoming\r\n                    </a>\r\n                </li>\r\n                <li class="nav-item border rounded mx-2 mb-3">\r\n                    <a class="nav-link" href="#tab_similar" data-toggle="pill" data-cat="similar">\r\n                        Similar\r\n                    </a>\r\n                </li>\r\n            </ul>\r\n            <div class="tab-content rounded mx-auto">\r\n\r\n                <div id="tab_search" class="tab-pane bg-light fade show active p-3 m-2 rounded">\r\n                    <div class="input-group" id="search_bar">\r\n                        <input type="text" id="apikey" class="form-control form-control-lg">\r\n                        <div class="input-group-append">\r\n                            <button id="search_button" class="btn btn-secondary" onclick="search(event, this)">\r\n                                <i class="mdi mdi-magnify"></i>\r\n                            </button>\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n\r\n                <div id="tab_popular"></div>\r\n\r\n                <div id="tab_now_playing"></div>\r\n\r\n                <div id="tab_top_rated"></div>\r\n\r\n                <div id="tab_upcoming"></div>\r\n\r\n                <div id="tab_similar" class="tab-pane bg-light fade show p-3 m-2 rounded">\r\n                    <div class="input-group">\r\n                        <select id="movie_names" class="form-control form-control-lg">\r\n\r\n                        </select>\r\n                        <div class="input-group-append">\r\n                            <button class="btn btn-secondary" onclick="load_suggestions(\'similar\')">\r\n                                <i class="mdi mdi-find-replace"></i>\r\n                            </button>\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n\r\n            <ul id="movies">\r\n\r\n            </ul>\r\n        </div>\r\n\r\n        <template id="movie_template">\r\n            <li>\r\n                <div class="card">\r\n                    <img src="{img_url}" class="card-img-top">\r\n                    <div class=\'btn-group\'>\r\n                        <div class="dropdown w-75">\r\n                            <button type="button" class="btn btn-secondary dropdown-toggle w-100 rounded-0" data-toggle="dropdown">\r\n                                ')
        __M_writer(str(_('Add')))
        __M_writer('\r\n                            </button>\r\n                            <div class="dropdown-menu">\r\n')
        for profile in profiles:
            __M_writer('                                <a class="dropdown-item" href="#" onclick="add_movie(event, this, \'')
            __M_writer(str(profile[0]))
            __M_writer('\')">\r\n                                    ')
            __M_writer(str(profile[0]))
            __M_writer('\r\n')
            if profile[1]:
                __M_writer('                                        <i class="mdi mdi-star"></i>\r\n')
            __M_writer('                                </a>\r\n')
        __M_writer('                            </div>\r\n                        </div>\r\n                        <button class="btn btn-secondary w-25 rounded-0 show_details" onclick="show_details(event, this)">\r\n                            <i class="mdi mdi-open-in-new"></i>\r\n                        </button>\r\n                    </div>\r\n                    <div class="card-body">\r\n                        <span class="title px-2">{title}</span>\r\n                        <span class="year pb-2">{year}</span>\r\n                    </div>\r\n                </div>\r\n            </li>\r\n        </template>\r\n        <template id="details_template">\r\n            <div class="modal fade" id="modal_details">\r\n                <div class="modal-dialog modal-wide">\r\n                    <div class="modal-content">\r\n                        <div class="modal-header">\r\n                            <h4 class="modal-title">\r\n                                {title}\r\n                                <span class="year">{year}</span>\r\n                            </h4>\r\n                            <button class="btn btn-light border btn-sm float-right" data-dismiss="modal">\r\n                                <i class="mdi mdi-close"></i>\r\n                            </button>\r\n                        </div>\r\n                        <div class="modal-badges">\r\n                            <a class="badge badge-info" href="https://www.themoviedb.org/movie/{id}" target="_blank" rel="noopener">\r\n                                TheMovieDB <i class="mdi mdi-earth"></i>\r\n                            </a>\r\n                            <span class="badge badge-dark">\r\n                                <i class="mdi mdi-theater" title="')
        __M_writer(str(_('Theatrical Release')))
        __M_writer('"></i>\r\n                                {release_date}\r\n                            </span>\r\n                            <span class="badge badge-dark">\r\n                                <i class="mdi mdi-star" title="')
        __M_writer(str(_('Score')))
        __M_writer('"></i>\r\n                                {vote_average}\r\n                            </span>\r\n                        </div>\r\n\r\n                        <div class="modal-body pb-0">\r\n                            <div class="row">\r\n                                <div class="col-md-5 text-center">\r\n                                    <img src="{poster_url}" class="img-responsive">\r\n                                </div>\r\n                                <div class="col-md-7">\r\n                                    <div class="embed-responsive embed-responsive-16by9">\r\n                                        <iframe src="" id="trailer"></iframe>\r\n                                    </div>\r\n                                    <p class="plot">{overview}</p>\r\n                                </div>\r\n                            </div>\r\n                        </div>\r\n\r\n                        <div class="modal-footer">\r\n                            <div class="dropdown">\r\n                                <button type="button" class="btn btn-secondary dropdown-toggle" data-toggle="dropdown">\r\n                                    ')
        __M_writer(str(_('Add')))
        __M_writer('\r\n                                </button>\r\n                                <div class="dropdown-menu">\r\n')
        for profile in profiles:
            __M_writer('                                    <a class="dropdown-item" href="#" onclick="add_movie(event, this, \'')
            __M_writer(str(profile[0]))
            __M_writer('\', modal=true)">\r\n                                        ')
            __M_writer(str(profile[0]))
            __M_writer('\r\n')
            if profile[1]:
                __M_writer('                                            <i class="mdi mdi-star"></i>\r\n')
            __M_writer('                                    </a>\r\n')
        __M_writer('                                </div>\r\n                            </div>\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n        </template>\r\n\r\n        <div id="thinker">\r\n            <i class="mdi mdi-circle animated"></i>\r\n        </div>\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"68": 62, "16": 0, "26": 1, "27": 4, "28": 4, "29": 5, "30": 5, "31": 6, "32": 6, "33": 9, "34": 9, "35": 91, "36": 91, "37": 94, "38": 95, "39": 95, "40": 95, "41": 96, "42": 96, "43": 97, "44": 98, "45": 100, "46": 102, "47": 133, "48": 133, "49": 137, "50": 137, "51": 159, "52": 159, "53": 162, "54": 163, "55": 163, "56": 163, "57": 164, "58": 164, "59": 165, "60": 166, "61": 168, "62": 170}, "source_encoding": "ascii", "uri": "templates/add_movie.html", "filename": "templates/add_movie.html"}
__M_END_METADATA
"""
