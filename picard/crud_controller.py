# -*- coding: utf-8 -*-

import os

from werkzeug import redirect, Response
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.routing import Rule, Map, RuleTemplate

from formencode import Invalid

from picard.helpers import flash
from picard.templating import TemplateResponse
from utils import flatten_multidict

__all__ = ['CrudController']

crud_map = RuleTemplate([
    Rule('/$name',                 endpoint='index',  methods=['GET']),
    Rule('/$name/<int:id>',        endpoint='show',   methods=['GET']),
    Rule('/$name/new',             endpoint='new',    methods=['GET']),
    Rule('/$name',                 endpoint='create', methods=['POST']),
    Rule('/$name/<int:id>/edit',   endpoint='edit',   methods=['GET']),
    Rule('/$name/<int:id>',        endpoint='update', methods=['POST']),
    Rule('/$name/<int:id>/delete', endpoint='delete', methods=['POST'])
])

def url_for(request, endpoint, **kwargs):
    method = kwargs.pop('method', 'GET')

    """ Simple function for URL generation. """
    return request.adapter.build(endpoint, kwargs, method)

class Controller(object):
    pass


class CrudController(Controller):
    """ TODO: Documentation!!! """
    
    class Meta:
        pass
    
    def __init__(self, model_name, object_name, objects_name=None, path=None, template_root=None):
        self.model_name = model_name
        self.object_name = object_name
        self.objects_name = objects_name or object_name + "s"
        self.path = path or object_name
        self.url_map = Map([crud_map(name=self.path)])
        self.template_root = template_root
                            
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
        response = e
        return response
    
    def current_objects(self, request):
        return getattr(request.models, self.model_name).get_all()
        
    def current_object(self, request, id):
        """ TODO: Allow variable args/kwargs. """
        return getattr(request.models, self.model_name).get(id)
        
    def template_path(self, template_name):
        return os.path.join(self.template_root, template_name)
    
    def default_context(self):
        return {
            'controller':    self.Meta.controller,
            'objects_name':  self.Meta.objects_name,
            'object_name':   self.Meta.object_name,
            'template_root': self.Meta.template_root
        }
    
    
    """ Actions. """

    def index(self, request):
        # TODO: Pagination.
        current_objects = self.current_objects()
        
        return TemplateResponse(self.template_path('index.html'),
            **dict(self.default_context(), objects=current_objects))

    def show(self, request, id):
        current_object = self.current_object(id)
        if not current_object:
            raise NotFound()

        return TemplateResponse(self.template_path('show.html'),
            **dict(self.default_context(), object=current_object))

    def new(self, request):
        current_object = getattr(request.models, self.model_name)()

        return TemplateResponse(self.template_path('new.html'), 
            **dict(self.default_context(), object=current_object))

    def create(self, request):
        current_object = getattr(request.models, self.model_name)(**flatten_multidict(request.form))
        
        self.before_create(current_object)
        
        return self.after_create(current_object)
        

    def edit(self, request, id):
        current_object = self.current_object(id)
        if not current_object:
            raise NotFound()

        return TemplateResponse(self.template_path('edit.html'), 
            **dict(self.default_context(), object=current_object))

    def update(self, request, id):
        current_object = self.current_object(id)

        self.before_update(current_object)

        # Show a delete confirmation form.
        if request.form.get('op') == 'Delete':
            return TemplateResponse(self.template_path('delete.html'), 
                **dict(self.default_context(), object=current_object))

        current_object.set(**flatten_multidict(request.form))

        try:
            session.flush()
        except Invalid, e:
            return TemplateResponse(self.template_path('edit.html'), 
                **dict(self.default_context(), object=current_object,   
                       errors=e.error_dict))
                       
        return self.after_update(current_object)

    def delete(self, request, id):
        current_object = self.current_object(id)
        
        self.before_delete(current_object)
        
        current_object.delete()
        session.flush()

        self.after_delete()


    """ Callbacks. """
    
    def before_create(self, current_object):
        pass
        
    def after_create(self, current_object):
        flash(u'%s saved!' % self.object_name)
        return redirect(url_for('%s.index' % self.Meta.controller))
        
    def before_update(self, current_object):
        pass
        
    def after_update(self, current_object):
        flash(u'%s updated!' % self.Meta.object_name)
        return redirect(url_for('%s.show' % self.Meta.controller, 
                                id=current_object.id))
        
    def before_delete(self, current_object):
        pass
        
    def after_delete(self):
        flash(u'%s deleted!' % self.Meta.object_name)
        return redirect(url_for('%s.index' % self.Meta.controller))


class ArchiveController(Controller):
    
    pass
