# -*- coding: utf-8 -*-

from werkzeug import Response
from helpers import do_date, do_highlight, html_attrs

from jinja import Environment, FileSystemLoader


jinja_env = Environment(loader=FileSystemLoader('templates'))
jinja_env.filters['date']       = do_date
jinja_env.filters['highlight']  = do_highlight
jinja_env.globals['html_attrs'] = html_attrs


def render_template(template_name, **context):
    context.update(
        url_for=url_for,
        flash=flash()
    )
    
    template = jinja_env.get_template(template_name)
    return template.render(context)


class TemplateResponse(Response):
    def __init__(self, template_name, **context):
        Response.__init__(self, render_template(template_name, **context))
