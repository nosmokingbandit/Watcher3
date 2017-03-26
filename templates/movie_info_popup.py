import json

import core
from core.movieinfo import Trailer
from dominate.tags import *


class MovieInfoPopup():

    def html(self, data_json):
        '''
        data: str json object movie data dict
        '''

        data = json.loads(data_json)

        trailer = Trailer()

        title_date = data['title'] + ' ' + data['release_date'][:4]
        youtube_id = trailer.get_trailer(title_date)
        tmdb_url = u"https://www.themoviedb.org/movie/{}".format(data['id'])

        if youtube_id:
            trailer_embed = u"https://www.youtube.com/embed/{}?&showinfo=0".format(youtube_id)
        else:
            trailer_embed = ''
        if data['poster_path'] is None:
            data['poster_path'] = core.URL_BASE + '/static/images/missing_poster.jpg'
        else:
            data['poster_path'] = u'http://image.tmdb.org/t/p/w300{}'.format(data['poster_path'])

        container = div(id='container')
        with container:
            script(type='text/javascript', src=core.URL_BASE + '/static/js/add_movie/movie_info_popup.js?v=02.02b')
            with div(id='title'):
                span(title_date, id='title')
                i(cls='fa fa-plus', id='button_add')
                with div('Quality profile: ', cls='hidden', id='quality'):
                    with select(id='quality_profile', value='Default'):
                        options = core.CONFIG['Quality']['Profiles'].keys()
                        for opt in options:
                            if opt == 'Default':
                                option(opt, value='Default')
                            else:
                                option(opt, value=opt)
                    i(id='button_save', cls='fa fa-save')
            with div(id='media'):
                img(id='poster', src=data['poster_path'])
                iframe(id='trailer', width="640", height="360", src=trailer_embed, frameborder="0")

            with div(id='plot'):
                p(data['overview'])
            with div(id='additional_info'):
                with a(href=tmdb_url, target='_blank'):
                    p(u'TMDB Score: {}'.format(data['vote_average']))
                span(u'Theatrical Release Date: {}'.format(data['release_date']))
            div(data_json, id='hidden_data', cls='hidden')

        return str(container)

    def no_data(self):
        message = "<div id='container'><span>Unable to retrive movie information. Try again in a few minutes or check logs for more information.</span></div>"
        return str(message)

# pylama:ignore=W0401
