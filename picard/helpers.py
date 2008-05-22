# -*- coding: utf-8 -*-

from werkzeug.utils import escape

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.styles import get_style_by_name

# from utils import url_adapter


__all__ = ('do_date', 'do_highlight', 'html_attrs', 'url_for', 'flash')


# Helpers/filters passed to Jinja.
def do_date(format='%d/%m/%Y – %H:%M:%S'):
    def wrapped(env, context, value):
        return value.strftime(format)
    return wrapped


def do_highlight(language='', line_numbers=True, no_classes=True):
    """ Renders the code using the Pygments syntax highlighter. """
    def wrapped(env, context, value):
        lexer = get_lexer_by_name(language, stripall=True)
        formatter = HtmlFormatter(linenos=line_numbers, noclasses=no_classes)
        return highlight(value, lexer, formatter)
    return wrapped


def html_attrs(**kwargs):
    return u''.join([u' %s="%s"' % (k, escape(v)) for k, v in kwargs.items()])


# def url_for(endpoint, **kwargs):
#     method = kwargs.pop('method', 'GET')
# 
#     """ Simple function for URL generation. """
#     return url_adapter.build(endpoint, kwargs, method)


def flash(message=None): 
    """ Simple flash message stored in a secure cookie. """
    if message:
        request.session['flash'] = message
    else:
        message = request.session.get('flash', None)
        if message:
            del request.session['flash']
        return message
