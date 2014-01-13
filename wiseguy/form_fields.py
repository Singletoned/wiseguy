# -*- coding: utf-8 -*-

import jinja2 as j2
import lxml.html
from lxml.html import builder as html

from wiseguy import utils

_default = object()

def _gen_element_id(input_type, id):
    return id

def add_errors(context, element, id):
    "Add an error, if present, to the list of elements"
    if context.get('errors', None):
        if context['errors'].get(id, ''):
            element.append(
                html.SPAN(
                    context['errors'][id],
                    {'class': 'error'}))


def _boostrapise(func, context, id, class_=None, controls_length=1, **kwargs):
    elements = func(context=context, id=id, **kwargs)
    label = elements[0]
    rest = elements[1:]
    label.attrib['class'] = "control-label"
    input = html.DIV(
        {'class': 'controls'},
        *rest)
    fieldset_classes = ['control-group']
    if context.get('errors', None):
        if context['errors'].get(id, ''):
            fieldset_classes.append("error")
    if class_:
        fieldset_classes.append(class_)
    element = html.FIELDSET(
        label,
        input,
        {'class': " ".join(fieldset_classes)},
        )
    help = element.xpath("//span[contains(@class, 'error')]")
    if help:
        help[0].attrib['class'] = help[0].attrib['class'] + ' help-inline'
    return element


def _input(context, id, label, input_type, value=_default, class_=None, extra_attrs=None, element_id=_default):
    if value is _default:
        value = unicode((context.get('data', False) or {}).get(id, ''))
    if not extra_attrs:
        extra_attrs = dict()
    if class_:
        extra_attrs['class'] = class_
    if element_id is _default:
        element_id = _gen_element_id(input_type, id)
    if context.get('disabled_form', False):
        element = html.DIV(
            html.LABEL(
                label,
                {'for': id}),
            html.INPUT(
                extra_attrs,
                type=input_type,
                name=id,
                id=element_id,
                value=value,
                disabled="disabled"))
    else:
        element = html.DIV(
            html.LABEL(
                label,
                {'for': id}),
            html.INPUT(
                extra_attrs,
                type=input_type,
                name=id,
                id=element_id,
                value=value))
    add_errors(context, element, id)
    return element


def _search(context, id, label, input_type, value=_default,
            link_class=None, extra_attrs=None, help=None, element_id=_default):
    element = _input(context, id, label,
                     input_type="text",
                     element_id=element_id)
    if not extra_attrs:
        extra_attrs = dict()
    if link_class:
        extra_attrs['class'] =  link_class
    link = html.A(
        "Search",
        extra_attrs,
        href="#")
    element.insert(2, link)
    if help:
        help = lxml.html.fromstring(help)
        element.insert(3, help)
    return element


@j2.contextfunction
def input(context, id, label, class_=None,
          extra_attrs=None, element_id=_default):
    "A simple input element"
    return _input(context, id, label, input_type="text",
                  class_=class_, element_id=element_id)


@j2.contextfunction
def search(context, id, label, help=None, element_id=_default):
    "A basic search element with link"
    return _search(context, id, label, input_type="text",
                   help=help, element_id=element_id)


def _checkbox(context, id, label, value=_default,
              disabled=False, element_id=_default):
    elements = _input(context, id, label, input_type="checkbox", value=value,
                      element_id=element_id)
    data_value = (context.get('data', False) or {}).get(id, '')
    if isinstance(data_value, (list, tuple)):
        if value in data_value:
            elements[1].attrib['checked'] = "checked"
    if disabled or context.get('disabled_form', False):
        elements[1].attrib['disabled'] = "disabled"
    return html.DIV(*elements)


@j2.contextfunction
def checkbox(context, id, label, value=_default,
             disabled=False, element_id=_default):
    "A simple input element"
    return _checkbox(context, id, label, value, disabled, element_id)


@j2.contextfunction
def password(context, id, label, element_id=_default):
    "A password element.  Won't fill the value even if present in context['data']"
    elements = _input(context, id, label, input_type="password", element_id=element_id)
    elements[1].attrib['value'] = ""
    return elements


def _datepicker(context, id, label):
    elements = _input(context, id, label, input_type="text")
    script = html.SCRIPT(
        '''$(function() {$("#%s").datepicker({dateFormat:'yy-mm-dd'});});''' % id)
    elements.insert(len(elements), script)
    return elements


@j2.contextfunction
def datepicker(context, id, label):
    "A datepicker element that uses JQueryUI"
    elements = _datepicker(context, id, label)
    elements = [lxml.html.tostring(e) for e in elements]
    return '\n'.join(elements)


def _textarea(context, id, label, element_id=_default):
    data = context.get('data', False) or {}
    text = data.get(id, '')
    if isinstance(text, str):
        text = text.decode('utf8')
    else:
        text = unicode(text)
    if element_id is _default:
        element_id = _gen_element_id('textarea', id)
    if context.get('disabled_form', False):
        element = html.DIV(
            html.LABEL(
                label,
                {'for': element_id}),
            html.TEXTAREA(
                text,
                name=id,
                id=element_id,
                disabled="disabled",
                ))
    else:
        element = html.DIV(
            html.LABEL(
                label,
                {'for': element_id}),
            html.TEXTAREA(
                text,
                name=id,
                id=element_id,
                ))
    add_errors(context, element, id)
    return element


@j2.contextfunction
def textarea(context, id, label, element_id=_default):
    return _textarea(context, id, label, element_id)


def _editor(context, id, label, script, class_):
    elements = _textarea(context, id, label)
    elements[1].attrib['class'] = class_
    script = html.SCRIPT(
        script,
        type="text/javascript")
    elements.insert(len(elements), script)
    return elements


def _tinymce(context, id, label):
    script = '''
tinyMCE.init({
mode : "textareas",
theme : "simple",
editor_selector : "mceEditor",
editor_deselector : "mceNoEditor"
});
'''
    elements = _editor(context, id, label, script, class_="mceEditor")
    return elements


@j2.contextfunction
def tinymce(context, id, label):
    return _tinymce(context, id, label)


def _ckeditor(context, id, label, ckeditor_config):
    if context.get('disabled_form', False):
        ckeditor_config['readOnly'] = "true"
    ck_options = ["%s: %s" % (k,v) for (k,v) in ckeditor_config.items()]
    ck_options = ",\n        ".join(ck_options)
    script = '''
CKEDITOR.replace(
    '%(id)s',
    {
        %(options)s});
''' % dict(id=id, options=ck_options)
    elements = _editor(context, id, label, script, class_="ckeditor")
    return elements


@j2.contextfunction
def ckeditor(context, id, label, ckeditor_config=None):
    elements = _ckeditor(context, id, label, ckeditor_config or dict())
    return html.DIV(*elements)


def _wysihtml5(context, id, label):
    options = {
        'name': "'foo'",
        'toolbar': "'toolbar'",
        'parserRules': "{tags: {strong: {}, b: {}, i: {}, em: {}, br: {}, p: {}, span: {}, a: {set_attributes: {target: '_blank',}, check_attributes: {href: 'url'}}}}"}
    options = ["%s: %s" % (k,v) for (k,v) in options.items()]
    options = ",\n    ".join(options)
    script = '''
new wysihtml5.Editor(
    '%(id)s',
    {
    %(options)s});
''' % dict(id=id, options=options)
    elements = _editor(context, id, label, script, class_="wysihtml5")
    toolbar = _wysihtml5_toolbar(id)
    return utils.listify(elements[0], toolbar, *elements[1:])

def _wysihtml5_button(name, command):
    return html.A(name, {"data-wysihtml5-command": command, 'class': "btn"})

def _wysihtml5_toolbar(id):
    toolbar = html.DIV(
        {'class': "btn-toolbar", 'id': "toolbar"},
        html.DIV(
            {'class': "btn-group"},
            _wysihtml5_button("Bold", "bold"),
            _wysihtml5_button("Italic", "Italic"),
            _wysihtml5_button("Insert Link", "createLink"),
        html.DIV(
            {
                'data-wysihtml5-dialog': "createLink",
                'style': "display: none;",
                'class': "modal"},
            html.DIV(
                html.H3("Insert Link"),
                {'class': "modal-header"}),
            html.DIV(
                {"class": "modal-form"},
                html.FIELDSET(
                    {'class': "control-group"},
                    html.LABEL(
                        "Href:",
                        {'for': id+"-input", "class": "control-label"}),
                    html.DIV(
                        {'class': "controls"},
                        html.INPUT(
                            {'data-wysihtml5-dialog-field': "href"},
                            id=id+"-input",
                            value="http://")))),
            html.DIV(
                {"class": "modal-footer"},
                html.A(
                    "Save",
                    {
                        'data-wysihtml5-dialog-action': "save",
                        'class': "btn"}),
                html.A(
                    "Cancel",
                    {
                        'data-wysihtml5-dialog-action': "cancel",
                        'class': "btn"})))))
    return toolbar

@j2.contextfunction
def wysihtml5(context, id, label):
    elements = _wysihtml5(context, id, label)
    return html.DIV(*elements)


def _select(context, id, label, options, disabled, blank_option, element_id):
    option_elements = []
    selected = unicode((context.get('data', False) or {}).get(id, ''))
    if blank_option:
        o = html.OPTION(value="")
        option_elements.append(o)
    for option in options:
        if isinstance(option, (list, tuple)):
            value, text = option
        else:
            value, text = (option, option)
        value = unicode(value)
        text = unicode(text)
        if value == selected:
            o = html.OPTION(text, value=value, selected="selected")
        else:
            o = html.OPTION(text, value=value)
        option_elements.append(o)
    if element_id is _default:
        element_id = _gen_element_id('select', id)
    if disabled or context.get('disabled_form', False):
        element = html.DIV(
            html.LABEL(
                label,
                {'for': element_id}),
            html.SELECT(
                "\n",
                *option_elements,
                name=id,
                id=element_id,
                disabled="disabled"))
    else:
        element = html.DIV(
            html.LABEL(
                label,
                {'for': element_id}),
            html.SELECT(
                "\n",
                *option_elements,
                name=id,
                id=element_id))
    add_errors(context, element, id)
    return element


@j2.contextfunction
def select(context, id, label, options, disabled=False,
           blank_option=True, element_id=_default):
    "A select element.  Accepts a list of value, text pairs"
    return _select(context, id, label, options,
                   disabled, blank_option, element_id)


@j2.contextfunction
def submit(context, id="submit", label="Submit", class_=""):
    "A simple submit button"
    kwargs = dict(
        type="submit",
        id=id,
        value=label)
    if context.get('disabled_form', False):
        kwargs['disabled'] = 'disabled'
    if class_:
        args = ({'class': class_},)
    else:
        args = tuple()
    element = html.INPUT(
        *args,
        **kwargs)
    return element


class BootstrapFormFields(object):
    def __init__(self, ckeditor_config=None):
        self.ckeditor_config = ckeditor_config

    @j2.contextfunction
    def input(self, context, id, label, extra_attrs=None):
        "A Bootstrap input element"
        return _boostrapise(
            _input,
            context=context,
            id=id,
            label=label,
            input_type="text",
            extra_attrs=extra_attrs)

    @j2.contextfunction
    def search(self, context, id, label, extra_attrs=None, help=None):
        "A Bootstrap input element"
        return _boostrapise(
            _search,
            controls_length=3,
            context=context,
            id=id,
            label=label,
            input_type="text",
            link_class="btn search",
            extra_attrs=extra_attrs,
            help=help)

    @j2.contextfunction
    def password(self, context, id, label):
        "A Bootstrap input element"
        element = _boostrapise(
            _input,
            context=context,
            id=id,
            label=label,
            input_type="password")
        element.xpath('//input')[0].attrib['value'] = ""
        return element

    @j2.contextfunction
    def select(self, context, id, label, options, disabled=False, blank_option=True, element_id=_default):
        "A Bootstrap input element"
        return _boostrapise(
            _select,
            context=context,
            id=id,
            label=label,
            options=options,
            disabled=disabled,
            blank_option=blank_option,
            element_id=element_id)

    @j2.contextfunction
    def checkbox(self, context, id, label, value=_default):
        "A Bootstrap checkbox element"
        return _boostrapise(
            _checkbox,
            context=context,
            id=id,
            label=label,
            value=value)

    @j2.contextfunction
    def textarea(self, context, id, label):
        "A Bootstrap textarea element"
        return _boostrapise(
            _textarea,
            context=context,
            id=id,
            label=label)

    @j2.contextfunction
    def datepicker(self, context, id, label):
        "A Bootstrap datepicker element"
        return _boostrapise(
            _datepicker,
            context=context,
            id=id,
            label=label)

    @j2.contextfunction
    def tinymce(self, context, id, label):
        "A Bootstrap tinymce element"
        return _boostrapise(
            _tinymce,
            context=context,
            id=id,
            label=label)

    @j2.contextfunction
    def ckeditor(self, context, id, label):
        "A Bootstrap tinymce element"
        return _boostrapise(
            _ckeditor,
            context=context,
            id=id,
            label=label,
            ckeditor_config=self.ckeditor_config)

    @j2.contextfunction
    def wysihtml5(self, context, id, label):
        "A Bootstrap tinymce element"
        return _boostrapise(
            _wysihtml5,
            context=context,
            id=id,
            label=label)

    @j2.contextfunction
    def submit(self, context, id="submit", label="Submit", class_="btn-primary"):
        "A Bootstrap submit element"
        return submit(
            context=context,
            id=id,
            label=label,
            class_=class_)
