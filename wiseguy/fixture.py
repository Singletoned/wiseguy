# -*- coding: utf-8 -*-

from collections import defaultdict
from types import ClassType
import datetime

import sqlalchemy as sa
import sqlalchemy.interfaces
import sqlalchemy.orm


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
                if type(value) in [ClassType, DatumMeta]:
                    datum = make_datum(value, default_data, override_data, _entity_name)
                    setattr(data_class, key, datum)
                    data_class._items[key] = datum
        return data_class

    def __iter__(self):
        for item in self._items.values():
            yield item

    def keys(self):
        return set(self._items.values()).keys()

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
        return utils.MockObject(**self.to_dict())

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
        item = self._entity.create(**data)
        session.add(item)
        return item

class Datum(object):
    __metaclass__ = DatumMeta

class BaseTester(object):
    def __init__(self, session):
        self.session = session
        self.query = session.query(self._entity)

    def length_is(self, length):
        return self.query.count() == length

    def count(self):
        return self.query.count()

    def all(self, as_dict=False):
        _all = self.query.all()
        if as_dict:
            return [item.to_dict() for item in _all]
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

class FixtureMeta(type):
    def __new__(meta, class_name, bases, class_dict):
        fixture = type.__new__(meta, class_name, bases, class_dict)
        fixture._data = {}
        data = dict()
        for base in bases:
            data.update(getattr(base, '_data', {}))
        for key, value in class_dict.items():
            if not key.startswith("_"):
                if type(value) == ClassType:
                    bases = (Data, )
                    value = DataMeta(key, bases, value.__dict__)
                    setattr(fixture, key, value)
                data[key] = value
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
        clauses.append(
            getattr(table.c, key)==value
            )
    return sa.and_(*clauses)

def get_primary_keys(table, data):
    p_keys = dict()
    for key in table.primary_key:
        p_keys[key.name] = data[key.name]
    return p_keys

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


def FixtureClassFactory(uri, metadata, sa_classes, env, overrides=None):
    env = EnvWrapper(env)

    class TesterManager(object):
        tester_classes = []

        def __init__(self, _data, env, add_data):
            self._tracked_data = {}
            engine = sa.create_engine(uri, proxy=MyProxy(self._tracked_data))
            metadata.bind = engine
            Session = sa.orm.sessionmaker(bind=engine)
            self.session = Session()
            self._data = TesterManagerDataDict(_data)
            self._date_created = datetime.datetime.now()
            self._env = env
            self._data_added = None
            if add_data:
                self.add_data()
            for _class in self.tester_classes:
                attr_name = _class._entity.__name__
                # self.foo = FooTester(session)
                setattr(self, attr_name, _class(self.session))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, value, traceback):
            self.remove_tracked_data()
            if self._data_added:
                self.remove_data()
            self.session.close()

        def create(self, *args):
            for group in args:
                for item in group:
                    item.to_sa(self.session)
            self.session.commit()
            self.session.close()

        def add_data(self):
            data_to_add = defaultdict(list)
            for data_class in self._data.values():
                entity_class = env[data_class._entity_name]
                for item in data_class:
                    data_to_add[entity_class].append(item)
            # Add the items in the order defined by sa_classes
            for sa_class in sa_classes:
                for datum in data_to_add[sa_class]:
                    data = datum.to_dict()
                    p_keys = sa_class._sa_class_manager.mapper.primary_key
                    p_key_names = [key.name for key in p_keys]
                    p_key = [data[key_name] for key_name in p_key_names]
                    item = self.session.query(sa_class).get(p_key)
                    if not item:
                        item = sa_class()
                        for key, value in data.items():
                            setattr(item, key, value)
                    self.session.add(item)
            self.session.commit()
            self.session.close()
            self._data_added = data_to_add

        def remove_data(self):
            self.session.expire_all()
            for entity_class, data in self._data_added.items():
                p_key_names = [key.name for key in
                               entity_class._sa_class_manager.mapper.primary_key]
                for item in data:
                    p_key = [getattr(item, key) for key in p_key_names]
                    item = self.session.query(entity_class).get(p_key)
                    if item:
                        self.session.delete(item)
            self.session.commit()

        def remove_tracked_data(self):
            self.session.close()
            for table, p_keys in self._tracked_data.items():
                clauses = [make_whereclause(table, p_key) for p_key in p_keys]
                where_clause = sa.or_(*clauses)
                q = table.delete().where(where_clause)
                self.session.execute(q)
            self.session.commit()

    for _class in sa_classes:
        t_class_name = "%sTester" % _class.__name__
        t_base_name = "%sBase" % t_class_name
        if overrides and t_base_name in overrides:
            t_class_bases = (BaseTester, overrides[t_base_name])
        else:
            t_class_bases = (BaseTester,)
        # Create the FooTester
        t_class = type(
            t_class_name,
            t_class_bases,
            {'_entity': _class})
        TesterManager.tester_classes.append(t_class)
        # TesterManager.FooTester = FooTester
        setattr(TesterManager, t_class_name, t_class)


    class Fixture(object):
        __metaclass__ = FixtureMeta
        _data = TesterManagerDataDict()
        _env = env

        def __new__(cls, add_data=True):
            return TesterManager(cls._data, env, add_data=add_data)

    return Fixture
