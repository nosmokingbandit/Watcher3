# -*- coding:ascii -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1530755949.559927
_enable_loop = True
_template_filename = 'templates/library/manage.html'
_template_uri = 'templates/library/manage.html'
_source_encoding = 'ascii'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        _ = context.get('_', UNDEFINED)
        head = context.get('head', UNDEFINED)
        movies = context.get('movies', UNDEFINED)
        url_base = context.get('url_base', UNDEFINED)
        profiles = context.get('profiles', UNDEFINED)
        navbar = context.get('navbar', UNDEFINED)
        __M_writer = context.writer()

        applied_profiles = {i['quality'] for i in movies}
        status_colors = {'Finished': 'success', 'Snatched': 'primary', 'Found': 'info', 'Available': 'info', 'Wanted': 'warning', 'Waiting': 'dark', 'Bad': 'danger'}
        
        
        __M_locals_builtin_stored = __M_locals_builtin()
        __M_locals.update(__M_dict_builtin([(__M_key, __M_locals_builtin_stored[__M_key]) for __M_key in ['applied_profiles','status_colors','i'] if __M_key in __M_locals_builtin_stored]))
        __M_writer('\r\n\r\n<!DOCTYPE HTML5>\r\n<html>\r\n    <head>\r\n        ')
        __M_writer(str(head))
        __M_writer('\r\n        <link href="')
        __M_writer(str(url_base))
        __M_writer('/static/css/library/manage.css?v=010" rel="stylesheet">\r\n\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/lib/echo.min.js?v=010" type="text/javascript"></script>\r\n        <script src="')
        __M_writer(str(url_base))
        __M_writer('/static/js/library/manage.js?v=013" type="text/javascript"></script>\r\n    <body>\r\n        ')
        __M_writer(str(navbar))
        __M_writer('\r\n        <div class="container">\r\n            <div class="row mb-3">\r\n                <div class="col-md-6 text-center">\r\n                    <div class="btn-group">\r\n                        <button class="btn btn-light border" onclick="select_all()" title="Select All">\r\n                            <i class="mdi mdi-checkbox-multiple-marked"></i>\r\n                        </button>\r\n                        <button class="btn btn-light border" onclick="select_none()" title="De-Select All">\r\n                            <i class="mdi mdi-checkbox-multiple-blank-outline"></i>\r\n                        </button>\r\n                        <button class="btn btn-light border" onclick="select_inverse()" title="Invert Selection">\r\n                            <i class="mdi mdi-minus-box"></i>\r\n                        </button>\r\n                        <div class="dropdown">\r\n                            <button type="button" class="btn btn-light border dropdown-toggle rounded-0 " data-toggle="dropdown">\r\n                                ')
        __M_writer(str(_('Attribute')))
        __M_writer('\r\n                                <span class="caret"></span>\r\n                            </button>\r\n                            <div class="dropdown-menu">\r\n                                <h6 class="dropdown-header">')
        __M_writer(str(_('Status')))
        __M_writer('</h6>\r\n                                <a class="dropdown-item" href="#" data-key="status" data-value="Waiting" onclick="select_attrib(event, this, \'status\', \'Waiting\')">')
        __M_writer(str(_('Waiting')))
        __M_writer('</a>\r\n                                <a class="dropdown-item" href="#" data-key="status" data-value="Wanted" onclick="select_attrib(event, this, \'status\', \'Wanted\')">')
        __M_writer(str(_('Wanted')))
        __M_writer('</a>\r\n                                <a class="dropdown-item" href="#" data-key="status" data-value="Found" onclick="select_attrib(event, this, \'status\', \'Found\')">')
        __M_writer(str(_('Found')))
        __M_writer('</a>\r\n                                <a class="dropdown-item" href="#" data-key="status" data-value="Snatched" onclick="select_attrib(event, this, \'status\', \'Snatched\')">')
        __M_writer(str(_('Snatched')))
        __M_writer('</a>\r\n                                <a class="dropdown-item" href="#" data-key="status" data-value="Finished" onclick="select_attrib(event, this, \'status\', \'Finished\')">')
        __M_writer(str(_('Finished')))
        __M_writer('</a>\r\n\r\n                                <div class="divider"></div>\r\n                                <h6 class="dropdown-header">')
        __M_writer(str(_('Quality Profile')))
        __M_writer('</h6>\r\n')
        for i in applied_profiles:
            __M_writer('                                <a class="dropdown-item" href="#" onclick="select_attrib(event, this, \'quality\', \'')
            __M_writer(str(i))
            __M_writer('\')">')
            __M_writer(str(i))
            __M_writer('</a>\r\n')
        __M_writer('                            </div>\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n                <div class="col-md-6 text-center">\r\n                    <div class="btn-group">\r\n                        <button class="btn btn-secondary" onclick="show_modal(event, this, \'backlog_search\')">\r\n                            <i class="mdi mdi-magnify" title="')
        __M_writer(str(_('Force Backlog Search')))
        __M_writer('"></i>\r\n                        </a>\r\n                        <button class="btn btn-secondary" onclick="show_modal(event, this, \'update_metadata\')">\r\n                            <i class="mdi mdi-tag-text-outline" title="')
        __M_writer(str(_('Update Metadata')))
        __M_writer('"></i>\r\n                        </a>\r\n                        <button class="btn btn-secondary" onclick="show_modal(event, this, \'change_quality\')">\r\n                            <i class="mdi mdi-video" title="')
        __M_writer(str(_('Change Quality&nbsp;Profile')))
        __M_writer('"></i>\r\n                        </a>\r\n                        <button class="btn btn-secondary" onclick="show_modal(event, this, \'reset\')">\r\n                            <i class="mdi mdi-backup-restore" title="')
        __M_writer(str(_('Reset')))
        __M_writer('"></i>\r\n                        </a>\r\n                        <button class="btn btn-secondary" onclick="show_modal(event, this, \'remove\')">\r\n                            <i class="mdi mdi-delete" title="')
        __M_writer(str(_('Remove')))
        __M_writer('"></i>\r\n                        </a>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n\r\n            <ul id="movie_list">\r\n')
        for movie in movies:
            __M_writer('                ')

            _status = 'Finished' if movie['status'] == 'Disabled' else movie['status']
            _poster = url_base + '/posters/' + movie['poster'] if movie.get('poster') else url_base + '/static/images/missing_poster.jpg'
                            
            
            __M_locals_builtin_stored = __M_locals_builtin()
            __M_locals.update(__M_dict_builtin([(__M_key, __M_locals_builtin_stored[__M_key]) for __M_key in ['_status','_poster'] if __M_key in __M_locals_builtin_stored]))
            __M_writer('\r\n                <li data-imdbid="')
            __M_writer(str(movie['imdbid']))
            __M_writer('" data-status="')
            __M_writer(str(_status))
            __M_writer('" data-quality="')
            __M_writer(str(movie['quality']))
            __M_writer('">\r\n                    <div class="card">\r\n                        <img data-echo="')
            __M_writer(str(_poster))
            __M_writer('" src="')
            __M_writer(str(url_base))
            __M_writer('/static/images/missing_poster.jpg" class="card-img-top">\r\n                        <div class="card-body" data-imdbid="')
            __M_writer(str(movie['imdbid']))
            __M_writer('" data-tmdbid="')
            __M_writer(str(movie['tmdbid']))
            __M_writer('">\r\n                            <i class="mdi mdi-checkbox-blank-outline c_box" value="False"></i>\r\n                            <span class="badge badge-')
            __M_writer(str(status_colors[_status]))
            __M_writer(' status">')
            __M_writer(str(_status))
            __M_writer('</span>\r\n                            <span class="badge badge-dark quality">')
            __M_writer(str(movie['quality']))
            __M_writer('</span>\r\n                            <i class="mdi mdi-table-edit float-right" onclick="edit_movie(event, this)"></i>\r\n                            <h6 class="card-title">\r\n                                ')
            __M_writer(str(movie['title']))
            __M_writer('\r\n                                <span class="year">\r\n                                    ')
            __M_writer(str(movie['year']))
            __M_writer('\r\n                                </span>\r\n                            </h6>\r\n                        </div>\r\n                    </div>\r\n                </li>\r\n')
        __M_writer('            </ul>\r\n        </div>\r\n\r\n    <!-- Modals for Management Actions -->\r\n\r\n        <template id="template_modal">\r\n            <div class="modal fade" id="task_modal">\r\n                <div class="modal-dialog modal-wide">\r\n                    <div class="modal-content">\r\n                        <div class="modal-header">\r\n                            <h4 class="modal-title">\r\n                                {title}\r\n                            </h4>\r\n                            <button class="btn btn-light border btn-sm float-right" data-dismiss="modal">\r\n                                <i class="mdi mdi-close"></i>\r\n                            </button>\r\n                        </div>\r\n                        <div class="modal-body">\r\n                            <p class="body">\r\n                                {body}\r\n                            </p>\r\n                            <div class="progress mb-3 bg-dark">\r\n                                <div class="progress-bar w-0" role="progressbar"></div>\r\n                            </div>\r\n                            <table class="table table-striped">\r\n                                <thead>\r\n                                    <tr>\r\n                                        <th>IMDB ID</th>\r\n                                        <th>')
        __M_writer(str(_('Error')))
        __M_writer('</th>\r\n                                    </tr>\r\n                                </thead>\r\n                                <tbody>\r\n                                </tbody>\r\n                            </table>\r\n                        </div>\r\n                        <div class="modal-footer">\r\n                            <button class="btn btn-success" onclick="begin_task(event, this, \'{task}\')">\r\n                                <i class="mdi mdi-checkbox-marked-circle-outline"></i>\r\n                            </button>\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n        </template>\r\n\r\n        <template id="quality_select">\r\n            <select class="form-control btn-light border mt-3 border" id="quality" value="">\r\n                <option value="" selected="selected">')
        __M_writer(str(_('Choose a Quality Profile')))
        __M_writer('</option>\r\n')
        for i in profiles:
            __M_writer('                <option value="')
            __M_writer(str(i))
            __M_writer('">')
            __M_writer(str(i))
            __M_writer('</option>\r\n')
        __M_writer('            </select>\r\n        </template>\r\n\r\n        <template id="template_edit">\r\n            <div class="modal fade" id="edit_modal">\r\n                <div class="modal-dialog modal-wide">\r\n                    <div class="modal-content">\r\n                        <div class="modal-header">\r\n                            <h4 class="modal-title">\r\n                                Edit Database\r\n                            </h4>\r\n                            <button class="btn btn-light border btn-sm float-right" data-dismiss="modal">\r\n                                <i class="mdi mdi-close"></i>\r\n                            </button>\r\n                        </div>\r\n                        <div class="modal-body pt-0">\r\n                            <div class="alert alert-warning mt-3" role="alert">\r\n                                Editing a movie\'s database entry may cause problems. Proceed with caution.\r\n                                <button type="button" class="close" data-dismiss="alert" aria-label="Close">\r\n                                    <i class="mdi mdi-close"></i>\r\n                                </button>\r\n                            </div>\r\n\r\n                            <table id=\'edit_movie_table\' class="table">\r\n                                <thead>\r\n                                    <tr>\r\n                                        <th class="w-30" scope="col">Field</th>\r\n                                        <th scope="col">Value</th>\r\n                                    </tr>\r\n                                </thead>\r\n                                <tbody>\r\n                                    <tr>\r\n                                        <td>Title</td>\r\n                                        <td>\r\n                                            <input type="text" data-id="title" class="form-control form-control-sm" value="{title}">\r\n                                        </td>\r\n                                    </tr>\r\n                                    <tr>\r\n                                        <td>Year</td>\r\n                                        <td>\r\n                                            <input type="number" data-id="year" class="form-control form-control-sm" min="0" value="{year}">\r\n                                        </td>\r\n                                    </tr>\r\n                                    <tr>\r\n                                        <td>\r\n                                            Theatrical Release Date<br/>\r\n                                            <small>[YYYY-MM-DD]</small>\r\n                                        </td>\r\n                                        <td>\r\n                                            <input type="text" data-id="release_date" class="form-control form-control-sm" value="{release_date}">\r\n                                        </td>\r\n                                    </tr>\r\n                                    <tr>\r\n                                        <td>\r\n                                            Home Media Release Date<br/>\r\n                                            <small>[YYYY-MM-DD]</small>\r\n                                        </td>\r\n                                        <td>\r\n                                            <input type="text" data-id="media_release_date" class="form-control form-control-sm" value="{media_release_date}">\r\n                                        </td>\r\n                                    </tr>\r\n                                    <tr>\r\n                                        <td>\r\n                                            Media File\r\n                                        </td>\r\n                                        <td>\r\n                                            <input type="text" data-id="finished_file" class="form-control form-control-sm" value="{finished_file}">\r\n                                        </td>\r\n                                    </tr>\r\n                                    <tr>\r\n                                        <td>\r\n                                            Alternative Titles\r\n                                        </td>\r\n                                        <td>\r\n                                            <input type="text" data-id="alternative_titles" class="form-control form-control-sm" value="{alternative_titles}">\r\n                                        </td>\r\n                                    </tr>\r\n                                </tbody>\r\n                            </table>\r\n                        </div>\r\n                        <div class="modal-footer">\r\n                            <button class="btn btn-success" onclick="save_movie_details(event, this, \'{tmdbid}\')">\r\n                                <i class="mdi mdi-content-save"></i>\r\n                            </button>\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n            </div>\r\n\r\n\r\n        </template>\r\n\r\n\r\n    </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"line_map": {"16": 0, "27": 1, "34": 4, "35": 9, "36": 9, "37": 10, "38": 10, "39": 12, "40": 12, "41": 13, "42": 13, "43": 15, "44": 15, "45": 31, "46": 31, "47": 35, "48": 35, "49": 36, "50": 36, "51": 37, "52": 37, "53": 38, "54": 38, "55": 39, "56": 39, "57": 40, "58": 40, "59": 43, "60": 43, "61": 44, "62": 45, "63": 45, "64": 45, "65": 45, "66": 45, "67": 47, "68": 54, "69": 54, "70": 57, "71": 57, "72": 60, "73": 60, "74": 63, "75": 63, "76": 66, "77": 66, "78": 73, "79": 74, "80": 74, "87": 77, "88": 78, "89": 78, "90": 78, "91": 78, "92": 78, "93": 78, "94": 80, "95": 80, "96": 80, "97": 80, "98": 81, "99": 81, "100": 81, "101": 81, "102": 83, "103": 83, "104": 83, "105": 83, "106": 84, "107": 84, "108": 87, "109": 87, "110": 89, "111": 89, "112": 96, "113": 124, "114": 124, "115": 143, "116": 143, "117": 144, "118": 145, "119": 145, "120": 145, "121": 145, "122": 145, "123": 147, "129": 123}, "source_encoding": "ascii", "uri": "templates/library/manage.html", "filename": "templates/library/manage.html"}
__M_END_METADATA
"""
