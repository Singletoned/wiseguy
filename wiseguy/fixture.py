# -*- coding: utf-8 -*-

from collections import defaultdict
from types import ClassType, FunctionType
import datetime, itertools
import functools
import traceback

import sqlalchemy as sa
import sqlalchemy.interfaces

import path

from . import utils


class FixtureTeardownError(Exception):
    """An error that happened in Fixture.__exit__
    """

    def __init__(self, error, orig_error_type, orig_error_value, orig_error_tb):
        self.error = error
        self.orig_error = "".join(traceback.format_exception(orig_error_type, orig_error_value, orig_error_tb))

    def __str__(self):
        return """%s\n\nOriginal Error was:\n%s""".strip() % (self.error, self.orig_error)

def _get_primary_key_names(cls):
    p_keys = cls._sa_class_manager.mapper.primary_key
    p_key_names = [key.name for key in p_keys]
    return p_key_names

def _get_from_data(cls, session, data):
    p_key_names = _get_primary_key_names(cls)
    p_key = [data[key_name] for key_name in p_key_names]
    item = session.query(cls).get(p_key)
    return item

def _create_item(cls, **kwargs):
    item = cls()
    for key, value in kwargs.items():
        if item._sa_class_manager.mapper.has_property(key):
            setattr(item, key, value)
    return item

def _item_to_dict(item, **kwargs):
    column_names = [c.name for c in item._sa_class_manager.mapper.columns if not c.name.startswith("%")]
    d = dict([(k, getattr(item, k)) for k in column_names])
    for key, value in kwargs.items():
        d[key] = value
    return d

def _item_from_dict(item, d, **kwargs):
    data = {}
    data.update(d)
    data.update(kwargs)
    for key, value in data.items():
        if item._sa_class_manager.mapper.has_property(key):
            setattr(item, key, value)
    return item

def get_data_from_class(_class):
    if not _class:
        return {}
    else:
        return dict(
                (k, v) for (k, v) in _class.__dict__.items()
                    if not k.startswith('_'))

def get_data_from_bases(bases):
    data = {}
    for b in reversed(bases):
        data.update(get_data_from_class(b))
    return data

def make_datum(_class, default_data, override_data, _entity_name):
    all_bases = tuple([_class] + list(_class.__bases__) + [object])
    bases = []
    for b in all_bases:
        if not b in bases:
            bases.append(b)
    bases = tuple(bases)
    data = get_data_from_bases(bases)
    for d_key in default_data:
        if not d_key in data:
            data[d_key] = default_data[d_key]
    for o_key in override_data:
        data[o_key] = override_data[o_key]
    for data_key, data_value in data.items():
        if callable(data_value):
            data[data_key] = data_value()
        assert not callable(data[data_key])
    _entity_name = _entity_name or _class._entity_name
    data['_entity_name'] = _entity_name
    datum = DatumMeta(_class.__name__, bases, data)
    return datum


class DataMeta(type):
    def __new__(meta_class, class_name, bases, class_dict):
        data_class = type.__new__(meta_class, class_name, bases, class_dict)
        if not hasattr(data_class, '_items'):
            data_class._items = dict()
        else:
            data_class._items = dict(data_class._items)
        default_data = get_data_from_class(class_dict.get('_default', None))
        override_data = get_data_from_class(class_dict.get('_override', None))
        if not class_name == 'Data':
            _entity_name = (class_dict.get('_entity_name', None)
                            or getattr(data_class, '_entity_name', None)
                            or class_name)
            assert (class_name == 'Data') or _entity_name
            data_class._entity_name = _entity_name
        keys_to_process = set(class_dict.keys())
        keys_to_process.update(data_class._items.keys())
        for key in keys_to_process:
            if not key.startswith("_"):
                if class_dict.has_key(key):
                    value = class_dict[key]
                else:
                    value = getattr(data_class, key)
                if isinstance(value, (ClassType, DatumMeta)):
                    datum = make_datum(value, default_data, override_data, _entity_name)
                    setattr(data_class, key, datum)
                    data_class._items[key] = datum
                elif isinstance(value, FunctionType):
                    for v_name, v_dict in value():
                        value_to_make = DatumMeta(v_name, (object,), v_dict)
                        datum = make_datum(value_to_make, default_data, override_data, _entity_name)
                        setattr(data_class, v_name, datum)
                        data_class._items[v_name] = datum
                    delattr(data_class, key)

        return data_class

    def __iter__(self):
        for item in self._items.values():
            yield item

    def keys(self):
        return set(self._items.values()).keys()

    def items(self):
        return self._items.items()

    def __len__(self):
        return len(self._items.values())

    def __eq__(self, other):
        return set(self._items.values()) == other

    def __ne__(self, other):
        return not set(self._items.values()) == other

    def __lt__(self, other):
        return set(self._items.values()) < other

    def __le__(self, other):
        return set(self._items.values()) <= other

    def __gt__(self, other):
        return set(self._items.values()) > other

    def __ge__(self, other):
        return set(self._items.values()) >= other

    def __repr__(self):
        return "<Data %s (%s)>" % (self.__name__, ", ".join([item.__name__ for item in self]))


class Data(object):
    __metaclass__ = DataMeta


class DatumMeta(type):
    def __new__(meta, class_name, bases, class_dict):
        datum = type.__new__(meta, class_name, bases, class_dict)
        # for attr in [k for k in class_dict if not k.startswith('_')]:
        #     if not hasattr(datum._entity, attr):
        #         raise AttributeError, "%r has no %r" % (datum._entity, attr)
        return datum

    def __setattr__(self, key, value):
        assert False

    def keys(self):
        for key in self.__dict__.keys():
            if not key.startswith('_'):
                yield key

    def to_dict(self, **kwargs):
        d = dict([(key, getattr(self, key)) for key in self.keys()])
        for key, value in kwargs.items():
            d[key] = value
        return d

    def to_frozenset(self):
        return frozenset(self.to_dict().items())

    def to_mock(self):
        return MockObject(**self.to_dict())

    def insert_db(self, session):
        data = {}
        for key in self.keys():
            item = getattr(self, key)
            data[key] = item
        table = self._entity._sa_class_manager.mapper.mapped_table
        q = sa.insert(table).values(data)
        r = session.execute(q)

    def to_sa(self, session):
        data = {}
        for key in self.keys():
            if isinstance(getattr(self, key), self.__class__):
                item = self[key].to_sa(session)
            # if isinstance(self[key], list):
            #     item = [i.to_sa(session) for i in self[key]]
            else:
                item = getattr(self, key)
            data[key] = item
        item = _create_item(self._entity, **data)
        session.add(item)
        return item

class Datum(object):
    __metaclass__ = DatumMeta

class TesterManager(object):
    def __init__(self, tester_base, loader):
        self.tester_base = tester_base
        self.loader = loader
        self._data = loader._data
        self.session = loader.session

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        else:
            self._add_tester_class(key)
            return self.__dict__[key]

    def _add_tester_class(self, key):
        tester_object = self.loader._make_tester_object(key)
        setattr(self, key, tester_object)

class SQLAlchemyTester(object):
    def __init__(self, session):
        self.session = session
        self.query = session.query(self._entity)

    def count(self):
        return self.query.count()

    def all(self, as_dict=False):
        _all = self.query.all()
        if as_dict:
            return [_item_to_dict(item) for item in _all]
        else:
            return _all

    def one(self):
        return self.query.one()

    def get(self, key):
        return self.query.get(key)

    def filter_by(self, *args, **kwargs):
        return self.query.filter_by(*args, **kwargs)

    def filter(self, *args, **kwargs):
        return self.query.filter(*args, **kwargs)

    def find_one(self, **kwargs):
        return self.filter_by(**kwargs).one()

class MongoTester(object):
    def __init__(self, session):
        self.session = session
        self.collection = session[self._entity.__name__]

    def count(self):
        return self.collection.count()

    def all(self):
        return self.collection.find()

    def find_one(self, **kwargs):
        return self.collection.find_one(kwargs)

class JsonTester(object):
    def __init__(self, data):
        self.data = data

    def count(self):
        return len(self.data)

    def all(self):
        return self.data

class FixtureMeta(type):
    def __new__(meta, class_name, bases, class_dict):
        fixture = type.__new__(meta, class_name, bases, class_dict)
        fixture._data = {}
        data = dict()
        for base in bases:
            data.update(getattr(base, '_data', {}))
        for key, value in class_dict.items():
            if not key.startswith("_"):
                if value:
                    if type(value) == ClassType:
                        bases = (Data, )
                        value = DataMeta(key, bases, value.__dict__)
                        setattr(fixture, key, value)
                    data[key] = value
                else:
                    if data.has_key(key):
                        del data[key]
        fixture._data = data
        return fixture

class TesterManagerDataDict(dict):
    def __getattr__(self, key):
        if self.has_key(key):
            return self[key]
        else:
            return getattr(dict, key)

class KeyAndAttributeError(Exception):
    def __init__(self, item, key):
        self.item = item
        self.key = key

    def __str__(self):
        return "%s has no key or attribute %s" % (self.item, self.key)

class EnvWrapper(object):
    def __init__(self, data):
        self._data = data

    def __repr__(self):
        return "<EnvWrapper for %s>" % self._data

    def _get(self, key):
        try:
            return self._data[key]
        except (KeyError, TypeError):
            try:
                return getattr(self._data, key[:-4])
            except AttributeError:
                raise KeyAndAttributeError(self._data, key)

    def __getattr__(self, key):
        return self._get(key)

    def __getitem__(self, key):
        return self._get(key)

def make_whereclause(table, p_key):
    clauses = []
    for key, value in p_key.items():
        clauses.append(getattr(table.c, key)==value)
    return sa.and_(*clauses)

def get_primary_keys(table, data):
    p_keys = dict()
    for key in table.primary_key:
        p_keys[key.name] = data[key.name]
    return p_keys

def get_pkeys_dict(entity_class, data):
    p_key_names = [key.name for key in entity_class._sa_class_manager.mapper.primary_key]
    dicts = [dict([(key, item[key]) for key in p_key_names]) for item in data]
    return dicts


class MyProxy(sa.interfaces.ConnectionProxy):
    def __init__(self, tracker):
        self.tracker = tracker

    def execute(self, conn, execute, clauseelement, *multiparams, **params):
        if isinstance(clauseelement, sa.sql.expression.Insert):
            table = clauseelement.table
            data = clauseelement.parameters or {}
            data.update(multiparams[0])
            primary_keys = get_primary_keys(table, data)
            self.tracker.setdefault(table, []).append(primary_keys)
        return execute(clauseelement, *multiparams, **params)


class Fixture(object):
    __metaclass__ = FixtureMeta

    def __init__(self):
        self._data = TesterManagerDataDict(self._data)


class no_autoflush(object):
    def __init__(self, session):
        self.session = session
        self.autoflush = session.autoflush

    def __enter__(self):
        self.session.autoflush = False

    def __exit__(self, type, value, traceback):
        self.session.autoflush = self.autoflush


class NoConstraints(object):
    def __init__(self, session):
        self.session = session
        if hasattr(self.session, 'default_engine_name'):
            self.engine_name = self.session.default_engine_name
        else:
            self.engine_name = self.session.bind.engine.name

    def __enter__(self):
        self.session.close()
        "Disable all constraints on the session"
        # if self.engine_name == 'mssql':
        #     self.session.execute(
        #         '''EXEC sp_msforeachtable "ALTER TABLE ? NOCHECK CONSTRAINT all"''')
        self.session.commit()
        self.session.close()

    def __exit__(self, excp_type, value, traceback):
        "Restore all constraints on the session"
        self.session.close()
        # if self.engine_name == 'mssql':
        #     self.session.execute(
        #         '''EXEC sp_msforeachtable "ALTER TABLE ? WITH CHECK CHECK CONSTRAINT all"''')
        self.session.commit()
        self.session.close()


class EmptyWith(object):
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self, *args, **kwargs):
        pass

    def __exit__(self, type, value, traceback):
        pass

class BaseLoadManager(object):
    def __init__(self, fixture):
        self.fixture = fixture()
        self._data = fixture._data
        self._tester_classes = set()

    def __enter__(self):
        self.session = self.session_factory()
        entity_classes, self._data_added, self._data_updated = self.add_data()
        return TesterManager(SQLAlchemyTester, self)

    def __exit__(self, exc_type, value, traceback):
        try:
            self.delete_data(self._data_added)
            self.restore_data(self._data_updated)
        except sa.exc.IntegrityError, e:
            raise FixtureTeardownError(e, exc_type, value, traceback)

    def __call__(self, func):
        @functools.wraps(func)
        def inner():
            with self:
                return func(TesterManager(SQLAlchemyTester, self))
        return inner

    def _make_tester_object(self, key):
        entity_class = self.session_factory.classes[key]
        t_class_name = "%sTester" % entity_class.__name__
        t_base_name = "%sBase" % t_class_name
        t_class_bases = (self.tester_base,)
        # Create the FooTester
        t_class = type(
            t_class_name,
            t_class_bases,
            {'_entity': entity_class})
        return t_class(self.session)


class BaseLoader(object):
    """A base class for loaders.

    The first argument to Loader needs to be either a dict of {'DataClassname': sa_class} or if every DataClass is named after the sa_class with 'Data' appended (as ours are), then you can just pass it an object that has the sa_classes as attrs (eg our mappers module).Obviously replace the call to `init_simple` with a call to a more complicated `Session` creation func."""
    def __init__(self, env, session_factory):
        self.env = EnvWrapper(env)
        self.session_factory = session_factory

    def __call__(self, fixture):
        return self.load_manager(fixture)


class MongoLoadManager(BaseLoadManager):
    """A loader for MongoDB"""
    def add_data(self):
        session = self.session_factory()
        entity_classes = set()
        data_added = defaultdict(list)
        for data_class in self._data.values():
            entity_class = self.env[data_class._entity_name]
            entity_classes.add(entity_class)
            for datum in data_class:
                item_data = datum.to_dict()
                item_id = session[entity_class.__name__].insert(item_data)
                data_added[entity_class].append(item_id)
        return (entity_classes, data_added, [])

    def delete_data(self, data_added):
        session = self.session_factory()
        for collection_name in session.collection_names():
            if not collection_name == 'system.indexes':
                session.drop_collection(collection_name)

    def restore_data(self, data):
        pass

    def _make_tester_class(self, entity_class, session):
        t_class_name = "%sTester" % entity_class.__name__
        t_base_name = "%sBase" % t_class_name
        t_class_bases = (MongoTester,)
        # Create the FooTester
        t_class = type(
            t_class_name,
            t_class_bases,
            {'_entity': entity_class})
        return t_class


class MongoLoader(BaseLoader):
    load_manager = MongoLoadManager


class SQLAlchemyLoadManager(BaseLoadManager):
    """A basic holder for an env and a session."""
    tester_base = SQLAlchemyTester

    def __init__(self, env, session_factory, fixture):
        super(SQLAlchemyLoadManager, self).__init__(fixture)
        self.env = EnvWrapper(env)
        self.session_factory = session_factory

    def add_data(self, overwrite_data=True, keep_constraints=False):
        session = self.session_factory()
        entity_classes = set()
        data_added = defaultdict(list)
        data_updated = defaultdict(list)
        if keep_constraints:
            constraint_checker = EmptyWith
        else:
            constraint_checker = NoConstraints
        with constraint_checker(session):
            with no_autoflush(session):
                for data_class in self._data.values():
                    entity_class = self.env[data_class._entity_name]
                    entity_classes.add(entity_class)
                    for datum in data_class:
                        item_data = datum.to_dict()
                        item = _get_from_data(entity_class, session, item_data)
                        if item:
                            if overwrite_data:
                                data_updated[entity_class].append(_item_to_dict(item))
                                _item_from_dict(item, item_data)
                                session.add(item)
                        else:
                            item = _create_item(entity_class, **item_data)
                            session.add(item)
                            data_added[entity_class].append(_item_to_dict(item))
                session.commit()
        session.close()
        return (entity_classes, data_added, data_updated)

    def _process_data(self, data_to_process):
        items = [
            (entity_class._sa_class_manager.mapper.mapped_table, get_pkeys_dict(entity_class, data))
            for (entity_class, data) in data_to_process.items()]
        processed_items = []

        def process_item(table, p_keys):
            # Break joins into seperate tables
            result = []
            # if isinstance(table, sqlalchemy.types.expression.Join):
            #     for join_table in [table.left, table.right]:
            #         data = [dict(
            #             [(key, datum[key]) for key in datum
            #              if hasattr(join_table.c, key)]) for datum in p_keys]
            #         result.append((join_table, data))
            # else:
            result.append((table, p_keys))
            return result

        for table, p_keys in items:
            processed_items.extend(process_item(table, p_keys))

        return processed_items

    def delete_data(self, data_added):
        session = self.session_factory()

        processed_items = self._process_data(data_added)

        with NoConstraints(session):
            with no_autoflush(session):
                for table, p_key_list in processed_items:
                    for p_keys in batch(p_key_list, 100):
                        clauses = [make_whereclause(table, p_key) for p_key in p_keys]
                        where_clause = sa.or_(*clauses)
                        q = table.delete().where(where_clause)
                        session.execute(q)
                session.commit()
            session.close()

    def restore_data(self, data_updated):
        session = self.session_factory()

        with no_autoflush(session):
            with NoConstraints(session):
                for entity_class, data_list in data_updated.items():
                    for original_data in data_list:
                        item = _get_from_data(entity_class, session, original_data)
                        assert item
                        _item_from_dict(item, original_data)
                session.commit()
        session.close()


class SQLAlchemyLoader(BaseLoader):
    load_manager = SQLAlchemyLoadManager

    def __call__(self, fixture):
        return self.load_manager(self.env, self.session_factory, fixture)


class NoDataLoadManager(SQLAlchemyLoadManager):
    """A Loader that doesn't load data"""
    def add_data(self):
        entity_classes = set()
        for data_class in self._data.values():
            entity_class = self.env[data_class._entity_name]
            entity_classes.add(entity_class)
        return (entity_classes, [], [])

    def delete_data(self, data):
        pass

    def restore_data(self, data):
        pass


class NoDataLoader(SQLAlchemyLoader):
    load_manager = NoDataLoadManager


class JsonLoadManager(BaseLoadManager):
    """For loading data into a specialised JSON format"""
    tester_base = JsonTester

    def __init__(self, data_dir, fixture):
        super(JsonLoadManager, self).__init__(fixture)
        self.data_dir = path.path(data_dir)
        self.session = None
        self.session_factory = None

    def __enter__(self):
        entity_classes, self._data_added, self._data_updated = self.add_data()
        return TesterManager(JsonTester, self)

    def __exit__(self, exc_type, value, traceback):
        pass

    def add_data(self):
        entity_classes = set()
        data_added = defaultdict(list)
        for data_class in self._data.values():
            entity_class = data_class._entity_name[:-4]
            entity_classes.add(entity_class)
            data_added = defaultdict(list)
            data = dict()
            for e in data_class:
                data.setdefault(e.venue_id, []).append(e.to_dict())
            for venue_id in data:
                data_added[entity_class].extend(data[venue_id])
                data_dir = self.data_dir / "venues" / venue_id
                if not data_dir.exists():
                    data_dir.makedirs()
                data_file =  data_dir / entity_class+".json"
                with open(data_file, 'w') as f:
                    newman.utils.json.dump(data[venue_id], f)
        return (entity_classes, data_added, [])

    def _make_tester_object(self, key):
        t_class_name = "%sTester" % key
        t_base_name = "%sBase" % t_class_name
        t_class_bases = (JsonTester,)
        # Create the FooTester
        t_class = type(
            t_class_name,
            t_class_bases,
            {})
        return t_class(self._data_added[key])

class JsonLoader(BaseLoader):
    """For loading data into a specialised JSON format"""
    def __init__(self, env, data_dir):
        self.env = env
        self.data_dir = path.path(data_dir)

    def __call__(self, fixture):
        return JsonLoadManager(self.data_dir, fixture)


def batch(items, count):
    "Return the items in groups of count"
    items = iter(items)
    while True:
        result = list(itertools.islice(items, count))
        if len(result) > 0:
            yield result
        else:
            raise StopIteration
