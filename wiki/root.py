# -*- coding: utf-8 -*-

from os import path
import logging

from werkzeug import Request, ClosingIterator, SharedDataMiddleware
from werkzeug.exceptions import HTTPException, NotFound
from beaker.middleware import SessionMiddleware

from couchdb.client import Server

from utils import url_map
import views
import models

root_path = path.abspath(path.dirname(__file__))

# LOG_FILENAME = root_path + '/logs/debug.log'
# log = logging.getLogger('picard_wiki')
# log.setLevel(logging.DEBUG)
# h = logging.FileHandler(LOG_FILENAME)
# h.setLevel(logging.DEBUG)
# log.addHandler(h)
# 
# logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)

server = Server('http://localhost:5984/')

try:
   db = server.create('picard_wiki')
   print 'database created'
except:
   db = server['picard_wiki']

try:
    user_db = server.create('picard_users')
except:
    user_db = server['picard_users']

class Wiki(object):
    def __init__(self, db=None, user_db=None):
        self.models = models
        models.WikiPage.meta.db = db
        models.User.meta.db = user_db
    
    def __call__(self, environ, start_response):
        request = Request(environ)
        request.session = request.environ['beaker.session']
        request.models = self.models
        adapter = url_map.bind_to_environ(environ)
        try:
            endpoint, values = adapter.match()
            handler = getattr(views, endpoint)
            response = handler(request, **values)
        except NotFound, e:
            response = views.not_found(request, e.get_response(environ))
        except HTTPException, e:
            response = e
        return ClosingIterator(response(environ, start_response))


if __name__ == '__main__':
    from werkzeug import DebuggedApplication, run_simple
    app = Wiki(db=db, user_db=user_db)
    app = DebuggedApplication(app, evalex=True)
    app = SharedDataMiddleware(app, {'/static':  path.join(root_path, 'static')})
    app = SessionMiddleware(app, type="memory")
    
    run_simple('localhost', 8080, app, use_reloader=True)