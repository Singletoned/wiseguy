# -*- coding: utf-8 -*-

from os import path
import logging

from werkzeug import Request, ClosingIterator, SharedDataMiddleware
from werkzeug.exceptions import HTTPException, NotFound

from utils import local, local_manager, url_map, session
import views

root_path = path.abspath(path.dirname(__file__))

LOG_FILENAME = root_path + '/logs/debug.log'
log = logging.getLogger('picard_wiki')
log.setLevel(logging.DEBUG)
h = logging.FileHandler(LOG_FILENAME)
h.setLevel(logging.DEBUG)
log.addHandler(h)

logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)


class Wiki(object):
    def __init__(self):
        local.application = self
        # self.database_engine = create_engine(db_uri, convert_unicode=True)
        
    def __call__(self, environ, start_response):
        local.application = self
        request = Request(environ)
        local.url_adapter = adapter = url_map.bind_to_environ(environ)
        try:
            endpoint, values = adapter.match()
            handler = getattr(views, endpoint)
            response = handler(request, **values)
        except NotFound, e:
            response = views.not_found(request, e.get_response(environ))
        except HTTPException, e:
            response = e
        return ClosingIterator(response(environ, start_response),
                                [local_manager.cleanup])


if __name__ == '__main__':
    from werkzeug import DebuggedApplication, run_simple
    app = Wiki()
    app = DebuggedApplication(app, evalex=True)
    app = SharedDataMiddleware(app, {'/static':  path.join(root_path, 'static')})

    
    run_simple('localhost', 8080, app, use_reloader=True)