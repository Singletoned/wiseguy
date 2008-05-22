# -*- coding: utf-8 -*-

import os
from os import path

from werkzeug import redirect, Response
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.routing import Rule, Map, RuleTemplate

from formencode import Invalid

from picard.helpers import flash
from picard.templating import TemplateResponse, render_template
from utils import flatten_multidict, create_render

root_path = path.abspath(path.dirname(__file__))

crud_map = RuleTemplate([
    Rule('/$name',                 endpoint='index',  methods=['GET']),
    Rule('/$name/<int:id>',        endpoint='show',   methods=['GET']),
    Rule('/$name/new',             endpoint='new',    methods=['GET']),
    Rule('/$name',                 endpoint='create', methods=['POST']),
    Rule('/$name/<int:id>/edit',   endpoint='edit',   methods=['GET']),
    Rule('/$name/<int:id>',        endpoint='update', methods=['POST']),
    Rule('/$name/<int:id>/delete', endpoint='delete', methods=['POST'])
])

def make_url_for(request):
    def url_for(endpoint, **kwargs):
        method = kwargs.pop('method', 'GET')
        return request.adapter.build(endpoint, kwargs, method)
    return url_for





class Controller(object):
    pass


class CrudController(Controller):
    """ TODO: Documentation!!! """
    
    class Meta:
        pass
    
    def __init__(self, model_name, object_name, objects_name=None, path=None, template_root=None, controller_name=None):
        print self.__class__.__name__
        self.model_name = model_name
        self.object_name = object_name
        self.objects_name = objects_name or object_name + "s"
        self.path = path or object_name
        self.url_map = Map([crud_map(name=self.path)])
        self.template_root = template_root or self.path
        self.controller_name = controller_name or object_name
                            
    def __call__(self, request, **values):
        print self.url_map._rules
        adapter = self.url_map.bind_to_environ(request.environ)
        request.adapter = adapter
    # try:
        endpoint, values = adapter.match()
        print "Endpoint", endpoint
        print "Vlaues", values
        handler = getattr(self, endpoint)
        response = handler(request, **values)
    # except HTTPException, e:
        # response = e
        return response
    
    def current_objects(self, request):
        return getattr(request.models, self.model_name).get_all()
        
    def current_object(self, request, id):
        """ TODO: Allow variable args/kwargs. """
        return getattr(request.models, self.model_name).get(id)
        
    def template_path(self, template_name):
        return os.path.join(self.template_root, template_name)
    
    def default_context(self, request):
        return {
            'controller': self.controller_name,
            'objects_name': self.objects_name,
            'object_name': self.object_name,
            'template_root': self.template_root,
            'url_for': make_url_for(request)
        }
    
    def render(self, template_name, mimetype='text/html', **values):
        try:
            return Response(render_template(self.template_root + '/' + template_name, **values), mimetype=mimetype)
        except TypeError:
            return values
    
    """ Actions. """

    def index(self, request):
        # TODO: Pagination.
        current_objects = self.current_objects()
        
        return self.render('index.html', **dict(self.default_context(request), objects=current_objects))

    def show(self, request, id):
        current_object = self.current_object(id)
        if not current_object:
            raise NotFound()

        return self.render('show.html', **dict(self.default_context(request), object=current_object))
    
    def new(self, request):
        current_object = getattr(request.models, self.model_name)()

        return self.render('new.html', **dict(self.default_context(request), object=current_object))

    def create(self, request):
        current_object = getattr(request.models, self.model_name)(**flatten_multidict(request.form))
        
        self.before_create(current_object)
        
        self.after_create(current_object)
        return redirect(make_url_for(request)('%s.index' % self.Meta.controller))
        
        

    def edit(self, request, id):
        current_object = self.current_object(id)
        if not current_object:
            raise NotFound()

        return self.render('edit.html', **dict(self.default_context(request), object=current_object))

    def update(self, request, id):
        current_object = self.current_object(id)

        self.before_update(current_object)

        # Show a delete confirmation form.
        if request.form.get('op') == 'Delete':
            return self.render('delete.html', **dict(self.default_context(request), object=current_object))

        current_object.set(**flatten_multidict(request.form))

        # try:
        #     session.flush()
        # except Invalid, e:
        #     return TemplateResponse(self.template_path('edit.html'), 
        #         **dict(self.default_context(request), object=current_object,   
        #                errors=e.error_dict))
                       
        self.after_update(current_object)
        return redirect(make_url_for(request)('%s.show' % self.Meta.controller, id=current_object.id))
        

    def delete(self, request, id):
        current_object = self.current_object(id)
        self.before_delete(current_object)
        current_object.delete()
        self.after_delete()
        return redirect(make_url_for(request)('%s.index' % self.Meta.controller))
        


    """ Callbacks. """
    
    def before_create(self, current_object):
        pass
        
    def after_create(self, current_object):
        # flash(u'%s saved!' % self.object_name)
        pass
        
    def before_update(self, current_object):
        pass
        
    def after_update(self, current_object):
        # flash(u'%s updated!' % self.Meta.object_name)
        pass
        
    def before_delete(self, current_object):
        pass
        
    def after_delete(self):
        # flash(u'%s deleted!' % self.Meta.object_name)
        pass


class ArchiveController(Controller):
    
    pass
