import json
import core
import os
from dominate.tags import *
import logging

logging = logging.getLogger(__name__)


class PluginConfPopup(object):

    @staticmethod
    def html(folder, conf):

        conf_file = os.path.join(core.PROG_PATH, core.PLUGIN_DIR, folder, conf)

        container = div(id='container')
        with container:
            script(src=core.URL_BASE + '/static/js/settings/plugin_conf_popup.js?v=03.28')
            with div(cls='title'):
                span(conf.split('.')[0], cls='name')
                i(id='close', cls='fa fa-close')
                i(id='save_plugin_conf', cls='fa fa-save')
            with ul(id='plugin_conf', conf=conf, folder=folder):
                try:
                    f = open(conf_file)
                    data = json.load(f)
                    for k, v in data.items():
                        with li():
                            span(k)
                            input(id=k, type='text', value=v)
                    f.close()
                except Exception as e: #noqa
                    f.close()
                    logging.error('Read plugin config.', exc_info=True)
                    return ''

        return str(container)

# pylama:ignore=W0401
