import gettext
import os
import core

locale_dir = os.path.join(core.PROG_PATH, 'locale')


def get():
    ''' Sets core.LANGUAGES to a dict {'en': <object gettext.translation>}

    Does not return
    '''
    for lang in os.listdir(locale_dir):
        if not os.path.isdir(os.path.join(locale_dir, lang)):
            continue

        core.LANGUAGES[lang] = gettext.translation('watcher', localedir=locale_dir, languages=[lang])

    core.LANGUAGES['en'] = gettext.translation('watcher', localedir=locale_dir, languages=[''], fallback=True)


def install(**kwargs):
    ''' Set/install language of choice
    kwargs:
        language (str): language code of language to apply  <optional - default read from config>

    Does not return
    '''
    lang = kwargs.get('language', core.CONFIG['Server']['language'])

    core.LANGUAGES.get(lang, core.LANGUAGES['en']).install()
    core.LANGUAGE = lang