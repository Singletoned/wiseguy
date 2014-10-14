# -*- coding: utf-8 -*-

import itertools

import pytest
import sqlalchemy as sa

from tests import fixture_test_schema as schema
from wiseguy import fixture, utils


def test_storage():
    def do_test(data):
        s = fixture.EnvWrapper(data)
        assert s.FooData == 'Bar'
        assert s['FooData'] == 'Bar'
        with pytest.raises(fixture.KeyAndAttributeError):
            s.plop
        with pytest.raises(fixture.KeyAndAttributeError):
            s['plop']

    datas = [
        dict(FooData='Bar'),
        utils.MockObject(Foo='Bar')
        ]

    for data in datas:
        yield do_test, data


class ArticleData(fixture.Data):
    class _default:
        score = score = itertools.count(1).next

    class article1:
        stub = "article1"
        name = "The First Article"
        body = "An article which is first\nblah, blah"

    class article2:
        stub = "article2"
        name = "The Second Article"
        body = "An article which is second\nblah, blah"


class CommentData(fixture.Data):
    class comment1:
        id = 1
        article_stub = ArticleData.article1.stub
        email = "commenter1@example.com"
        name = "Mr Smith"
        body = "Well Done.  What an incisive article"

    class comment2:
        id = 2
        article_stub = ArticleData.article2.stub
        email = "commenter1@example.com"
        name = "Mr Smith"
        body = "This one is not so good."


class FirstFixture(fixture.Fixture):
    class ArticleData:
        article1 = ArticleData.article1
    class CommentData:
        comment1 = CommentData.comment1

class SecondFixture(fixture.Fixture):
    class ArticleData:
        article2 = ArticleData.article2
    class CommentData:
        comment2 = CommentData.comment2

loader = fixture.SQLAlchemyLoader(schema, schema.Session)

def test_loader():
    loader = fixture.SQLAlchemyLoader(env=schema, session_factory=schema.Session)

    assert hasattr(schema, 'Article')
    assert isinstance(loader.env, fixture.EnvWrapper)
    assert loader.env.ArticleData == schema.Article
    assert loader.env['ArticleData'] == schema.Article

    with loader(FirstFixture) as tester:
        assert tester.Article.count() == 1
        assert tester.Comment.count() == 1


def test_Fixture_env():
    env = dict(ArticleData=schema.Article, CommentData=schema.Comment)

    assert not hasattr(FirstFixture, '_env')

    test_loader = fixture.SQLAlchemyLoader(schema, schema.Session)

    with test_loader(FirstFixture) as tester:
        assert tester.loader.env.ArticleData == schema.Article
        assert tester.loader.env.CommentData == schema.Comment
        assert tester.loader.env['ArticleData'] == schema.Article
        assert tester.loader.env['CommentData'] == schema.Comment
        assert tester._data['ArticleData'] is FirstFixture.ArticleData
        assert tester._data['CommentData'] is FirstFixture.CommentData

    with test_loader(FirstFixture) as tester:
        assert tester.loader.env.ArticleData == schema.Article
        assert tester.loader.env.CommentData == schema.Comment
        assert tester.loader.env['ArticleData'] == schema.Article
        assert tester.loader.env['CommentData'] == schema.Comment


def test_get_data_from_class():
    none_data = fixture.get_data_from_class(None)
    assert not none_data

    class test_data:
        id = 1
        _foo = "foo"
        bar = "bar"

    test_data = fixture.get_data_from_class(test_data)
    assert test_data['id'] == 1
    assert not test_data.has_key('_foo')
    assert test_data['bar'] == 'bar'


def test_callable_args():
    def body_counter():
        count = 0
        while True:
            count = count + 1
            yield "Body %s" % count

    def name_counter():
        count = 0
        while True:
            count = count + 1
            yield "Name %s" % count

    class ArticleData(fixture.Data):
        class _default:
            body = body_counter().next

        class article4:
            stub = "article4"
            name = name_counter().next

        class article5:
            stub = "article5"
            name = "The Fifth Article"

    assert ArticleData.article4.name == "Name 1"
    # Check that accessing the attribute again doesn't change it
    assert ArticleData.article4.name == "Name 1"
    assert ArticleData.article4.body == "Body 1"
    assert ArticleData.article5.name == "The Fifth Article"
    assert ArticleData.article5.body == "Body 2"
    # Check that accessing the attribute again doesn't change it
    assert ArticleData.article5.body == "Body 2"


def test_defaults():
    class ArticleData(fixture.Data):
        _entity = schema.Article

        class _default:
            name = lambda: "An Article"
            body = "foo"

        class article6:
            stub = "article6"
            name = "The Sixth Article"

    assert ArticleData.article6.name == "The Sixth Article"
    assert ArticleData.article6.body == "foo"


def test_data_acts_as_set():
    items = [ArticleData.article1, ArticleData.article2]
    assert set(items) == set([item for item in ArticleData])
    assert len(ArticleData) == 2
    assert len(items) == 2
    assert ArticleData == set(items)
    assert ArticleData <= set(items)
    assert ArticleData >= set(items)
    assert ArticleData < set(items + [1])
    assert ArticleData > set(items[:-1])
    assert ArticleData != set(items[:-1])


def test_article_data():
    assert ArticleData.article1.stub == "article1"
    assert ArticleData.article1.name == "The First Article"
    assert ArticleData.article2.stub == "article2"
    assert ArticleData.article2.name == "The Second Article"


def test_comment_data():
    assert CommentData.comment1.id == 1
    assert CommentData.comment1.name == "Mr Smith"


def test_to_dict():
    d1 = ArticleData.article1.to_dict()
    assert not d1.has_key(u'foo')
    d2 = ArticleData.article1.to_dict(foo=u'bar')
    assert d2['foo'] == u'bar'


def test_data_inheritance():
    schema.with_empty_db()

    class new_article(ArticleData.article1):
        stub = "new_article"

    assert new_article.stub == "new_article"
    assert new_article.body == ArticleData.article1.body

    class NewData(fixture.Data):
        _entity = schema.Article
        class new_article(ArticleData.article1):
            stub = "new_article"

    assert NewData.new_article.stub == "new_article"
    assert NewData.new_article.body == ArticleData.article1.body
    assert NewData._items

    class NewFixture(fixture.Fixture):
        CommentData = CommentData

        class ArticleData(fixture.Data):
            # _entity = schema.Article
            class new_article(ArticleData.article1):
                stub = "new_article"

    article = NewFixture.ArticleData.new_article
    assert article.stub == "new_article"
    assert article.name == "The First Article"

    with loader(NewFixture) as tester:
        article = tester.Article.one()
        assert article.stub == "new_article"
        assert article.name == "The First Article"
        assert tester._data['ArticleData'].new_article.stub == "new_article"


def test_fixture_inheritance():
    schema.with_empty_db()

    class NewFixture(fixture.Fixture):
        CommentData = CommentData

        class ArticleData(fixture.Data):
            class new_article(ArticleData.article1):
                stub = "new_article"

            class new_article2(ArticleData.article2):
                stub = "new_article2"

        class CommentData(CommentData):
            pass

    class NewFixture2(NewFixture):
        class ArticleData(fixture.Data):
            class new_article(ArticleData.article1):
                stub = "new_article3"

    assert NewFixture2.ArticleData.new_article.stub == "new_article3"
    assert len(NewFixture2.ArticleData) == 1
    assert NewFixture2.CommentData.comment1.name == "Mr Smith"
    assert len(NewFixture2.CommentData) == 2

    with loader(NewFixture2) as tester:
        assert tester.Article.one()
        assert tester.Comment.count() == 2

    class NewFixture3(NewFixture):
        CommentData = None

    assert not NewFixture3._data.has_key('CommentData')


def test_override():
    schema.with_empty_db()

    class NewFixture(fixture.Fixture):
        class ArticleData(ArticleData):
            class _override:
                name = "overridden"

    assert NewFixture.ArticleData._items != ArticleData._items
    assert not (NewFixture.ArticleData._items is ArticleData._items)

    with loader(NewFixture) as tester:
        for article in tester.Article.all():
            assert article.name == "overridden"

    for article in ArticleData:
        assert article.name != "overridden"


def test_first_fixture():
    schema.with_empty_db()

    with loader(FirstFixture) as tester:
        article1 = tester.Article.one()
        assert tester.Article.one() == article1
        # assert article1.to_dict() == ArticleData.article1.to_dict()
        assert tester.Article.count() == 1
        assert tester.Article.all() == [article1]
        comment1 = tester.Comment.one()
        assert tester.Comment.one() == comment1
        # assert comment1.to_dict() == CommentData.comment1.to_dict()
        assert tester.Comment.count() == 1
        assert tester.Comment.all() == [comment1]


def test_multiple_inheritance():
    schema.with_empty_db()

    class FixtureOne(fixture.Fixture):
        class ArticleData(fixture.Data):
            _entity = schema.Article

            class article_1:
                stub = 'foo'
                name = 'Foo'
                body = 'The Foo article'
                score = 1

    class FixtureTwo(FixtureOne):
        class ArticleData(FixtureOne.ArticleData):
            class article_2:
                stub = 'bar'
                name = 'Bar'
                body = 'The Bar article'
                score = 2

    class FixtureThree(FixtureTwo):
        class CommentData(fixture.Data):
            _entity = schema.Comment

            class comment_1:
                id = 1
                article_stub = 'foo'
                email = 'bob@example.com'
                name = 'Bob'
                body = 'I like this article'

    with loader(FixtureThree) as tester:
        assert tester.Article.count() == 2


def test_generator_functions():
    class ArticleData(fixture.Data):
        class _default:
            score = score = itertools.count(1).next

        def make_data():
            for i in range(1,5):
                var_name = "article_%s" % i
                data = dict(
                    stub="article_%s" % i,
                    name="Article %s" % i,
                    body="blah, blah")
                yield var_name, data

    assert ArticleData.article_1.stub == "article_1"
    assert ArticleData.article_4.name == "Article 4"

    assert len(ArticleData) == 4

    assert not getattr(ArticleData, 'make_data', None)

    class GeneratorFixture(fixture.Fixture):
        ArticleData2 = ArticleData

    assert len(GeneratorFixture._data['ArticleData2']) == 4

    with loader(GeneratorFixture) as tester:
        assert tester.Article.count() == 4


def test_fixture_teardown():
    class TeardownFixture(fixture.Fixture):
        class ArticleData:
            article1 = ArticleData.article1
            article2 = ArticleData.article2
        class CommentData:
            comment1 = CommentData.comment1
            comment2 = CommentData.comment2

    with loader(TeardownFixture) as tester:
        expected = [
            TeardownFixture.ArticleData.article1.to_dict(),
            TeardownFixture.ArticleData.article2.to_dict()]
        result = [item for item in tester.loader._data_added[schema.Article]]
        assert sorted(expected) == sorted(result)

    session = schema.Session()

    assert session.query(schema.Article).count() == 0

def test_make_whereclause():
    clause = fixture.make_whereclause(schema.article_table, dict(stub='foo', name='bar'))
    expected = sa.and_(
        schema.article_table.c.stub=='foo',
        schema.article_table.c.name=='bar')
    assert str(expected) == str(clause)

def test_NoDataLoader():
    null_loader = fixture.NoDataLoader(schema, schema.Session)
    with null_loader(FirstFixture) as tester:
        assert tester.Article.count() == 0
        assert tester.Comment.count() == 0

# @pytest.mark.skipif('True')
# def test_tracking_inserts():
#     class TrackingFixture(fixture.Fixture):
#         class ArticleData:
#             article1 = ArticleData.article1
#             article2 = ArticleData.article2
#         class CommentData:
#             comment1 = CommentData.comment1
#             comment2 = CommentData.comment2

#     with loader(TrackingFixture) as tester:
#         article3 = schema.Article()
#         article3.stub = "article3"
#         article3.name = "The Third Article"
#         article3.body = "An article which is third\nblah, blah"
#         tester.session.add(article3)
#         tester.session.commit()
#         expected = [{'stub': 'article2'}, {'stub': 'article1'}, {'stub': 'article3'}]
#         assert tester._tracked_data[schema.article_table] == expected

#     assert tester.session.query(schema.Article).count() == 0

def test_restoring_overwritten_data():
    class ExistingFixture(fixture.Fixture):
        class ArticleData:
            article1 = ArticleData.article1
        class CommentData:
            comment1 = CommentData.comment1

    class UpdatedFixture(fixture.Fixture):
        class ArticleData(fixture.Data):
            class article1:
                stub = "article1"
                name = "The Updated First Article"
                body = "An updated article which is first\nblah, blah"
                score = 3

            class article2:
                stub = "article2"
                name = "The Second Article"
                body = "An article which is second\nblah, blah"
                score = 2

        class CommentData(fixture.Data):
            class comment1:
                id = 1
                article_stub = ArticleData.article1.stub
                email = "redacted"
                name = "redacted"
                body = "This has been redacted"

            class comment2:
                id = 2
                article_stub = ArticleData.article2.stub
                email = "commenter1@example.com"
                name = "Mr Smith"
                body = "This one is not so good."

    with loader(ExistingFixture) as T1:
        assert T1.Article.count() == 1
        assert T1.Comment.count() == 1

        original_article = T1.Article.one()
        assert original_article.name == "The First Article"

        with loader(UpdatedFixture) as T2:
            assert T1.Article.count() == 2
            assert T1.Comment.count() == 2

            assert T2.Article.count() == 2
            assert T2.Comment.count() == 2

            article = T2.Article.get("article1")
            assert article.name == "The Updated First Article"

        assert T1.Article.count() == 1
        assert T1.Comment.count() == 1

        assert T2.Article.count() == 1
        assert T2.Comment.count() == 1

        T2.session.expire_all()
        restored_article = T2.Article.get("article1")
        assert restored_article.name == "The First Article"

def test_decorator():
    @loader(FirstFixture)
    def test_foo(T):
        article1 = T.session.query(schema.Article).one()
        assert T.Article.one() == article1
        # assert article1.to_dict() == ArticleData.article1.to_dict()
        assert T.Article.count() == 1
        assert T.Article.all() == [article1]

    assert test_foo.__name__ == "test_foo"
    test_foo()
