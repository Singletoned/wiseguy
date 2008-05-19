# -*- coding: utf-8 -*-

import logging

from werkzeug import Response
from werkzeug.exceptions import NotFound
from werkzeug.utils import redirect
from werkzeug.routing import Map

from picard.utils import create_expose, render

from models import ResourceNotFound

url_map = Map()

expose = create_expose(url_map)
