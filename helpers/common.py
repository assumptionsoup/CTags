"""
common utilities used by all ctags modules
"""
import re
import sys
import os

# Helper functions

try:
    import sublime
    import sublime_plugin
    from sublime import status_message, error_message

    # hack the system path to prevent the following issue in ST3
    #     ImportError: No module named 'ctags'
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
except ImportError:  # running tests
    from tests.sublime_fake import sublime
    from tests.sublime_fake import sublime_plugin

    sys.modules['sublime'] = sublime
    sys.modules['sublime_plugin'] = sublime_plugin


def get_settings():
    """Load settings.
    :returns: dictionary containing settings
    """
    _settings = sublime.load_settings("CTags.sublime-settings")
    try:
        _projectData = sublime.active_window().project_data()["settings"]["CTags"]
        try:
            _settings.set("debug", _projectData["debug"])
        except KeyError:
            pass
        try:
            _settings.set("autocomplete", _projectData["autocomplete"])
        except KeyError:
            pass
        try:
            _settings.set("command", _projectData["command"])
        except KeyError:
            pass
        try:
            _settings.set("recursive", _projectData["recursive"])
        except KeyError:
            pass
        try:
            _settings.set("tag_file", _projectData["tag_file"])
        except KeyError:
            pass
        try:
            _settings.set("opts", list(set(_projectData["opts"] + _settings.get("opts", []))))
        except KeyError:
            pass
        try:
            _settings.set("filters", dict(_settings.get("filters", {}).items() + _projectData["filters"].items()))
        except KeyError:
            pass
        try:
            _settings.set("definition_filters", dict(_settings.get("definition_filters", {}).items() + _projectData["definition_filters"].items()))
        except KeyError:
            pass
        try:
            _settings.set("definition_current_first", _projectData["definition_current_first"])
        except KeyError:
            pass
        try:
            _settings.set("show_context_menus", _projectData["show_context_menus"])
        except KeyError:
            pass
        try:
            _settings.set("extra_tag_files", list(set(_projectData["extra_tag_files"])))
        except KeyError:
            pass
        try:
            _settings.set("extra_tag_paths", _projectData["extra_tag_paths"])
        except KeyError:
            pass
        try:
            _settings.set("select_searched_symbol", _projectData["select_searched_symbol"])
        except KeyError:
            pass
    except KeyError:
        pass
    return _settings


def get_setting(key, default=None):
    """
    Load individual setting.

    :param key: setting key to get value for
    :param default: default value to return if no value found

    :returns: value for ``key`` if ``key`` exists, else ``default``
    """
    return get_settings().get(key, default)

setting = get_setting


def concat_re(reList, escape=False, wrapCapture=False):
    """
    concat list of regex into a single regex, used by re.split
    wrapCapture - if true --> adds () around the result regex --> split will keep the splitters in its output array.
    """
    ret = "|".join((re.escape(spl) if escape else spl) for spl in reList)
    if (wrapCapture):
        ret = "(" + ret + ")"
    return ret


def dict_extend(dct, base):
    if not dct:
        dct = {}
    if base:
        deriv = base
        deriv = merge_two_dicts_deep(deriv, dct)
    else:
        deriv = dct
    return deriv


def merge_two_dicts_shallow(x, y):
    """
    Given two dicts, merge them into a new dict as a shallow copy.
    y members overwrite x members with the same keys.
    """
    z = x.copy()
    z.update(y)
    return z


def merge_two_dicts_deep(a, b, path=None):
    "Merges b into a including sub-dictionaries - recursive"
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_two_dicts_deep(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a

RE_SPECIAL_CHARS = re.compile(
    '(\\\\|\\*|\\+|\\?|\\||\\{|\\}|\\[|\\]|\\(|\\)|\\^|\\$|\\.|\\#|\\ )')


def escape_regex(s):
    return RE_SPECIAL_CHARS.sub(lambda m: '\\%s' % m.group(1), s)


def get_source(view):
    """
    return the language used in current caret or selection location
    """
    scope_name = view.scope_name(
        view.sel()[0].begin())  # ex: 'source.python meta.function-call.python '
    source = re.split(' ', scope_name)[0]  # ex: 'source.python'
    return source


def get_lang_setting(source):
    """
    given source (ex: 'source.python') --> return its language_syntax settings.
    A language can inherit its settings from another language, overidding as needed.
    """
    lang = setting('language_syntax').get(source)
    if lang is not None:
        base = setting('language_syntax').get(lang.get('inherit'))
        lang = dict_extend(lang, base)
    else:
        lang = {}
    return lang


def compile_filters(view):
    filters = []
    for selector, regexes in list(setting('filters', {}).items()):
        if view.match_selector(view.sel() and view.sel()[0].begin() or 0,
                               selector):
            filters.append(regexes)
    return filters
