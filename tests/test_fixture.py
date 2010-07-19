# -*- coding: utf-8 -*-

import itertools

from nose.tools import assert_raises

from wiseguy import fixture, fixture_test_schema as schema

Fixture = fixture.FixtureClassFactory(schema.Session, schema.classes)


class ArticleData(fixture.Data):
    _entity = schema.Article

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
    _entity = schema.Comment

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


class FirstFixture(Fixture):
    articles = [ArticleData.article1]
    comments = [CommentData.comment1]

class SecondFixture(Fixture):
    articles = [ArticleData.article2]
    comments = [CommentData.comment2]


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

def test_extra_value():
    def make_article3():
        class ArticleData2(fixture.Data):
            _entity = schema.Article

            class article3:
                stub = "article3"
                flibble = "foo"

    assert_raises(
        AttributeError,
        make_article3
    )

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

    class ArticleData4(fixture.Data):
        _entity = schema.Article

        class _default:
            body = body_counter().next

        class article4:
            stub = "article4"
            name = name_counter().next

        class article5:
            stub = "article5"
            name = "The Fifth Article"

    assert ArticleData4.article4.name == "Name 1"
    # Check that accessing the attribute again doesn't change it
    assert ArticleData4.article4.name == "Name 1"
    assert ArticleData4.article4.body == "Body 1"
    assert ArticleData4.article5.name == "The Fifth Article"
    assert ArticleData4.article5.body == "Body 2"
    # Check that accessing the attribute again doesn't change it
    assert ArticleData4.article5.body == "Body 2"


def test_defaults():
    class ArticleData6(fixture.Data):
        _entity = schema.Article

        class _default:
            name = lambda: "An Article"
            body = "foo"

        class article6:
            stub = "article6"
            name = "The Sixth Article"

    assert ArticleData6.article6.name == "The Sixth Article"
    assert ArticleData6.article6.body == "foo"


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

@schema.with_empty_db
def test_to_sa():
    session = schema.Session()
    item = ArticleData.article1.to_sa(session)
    item_data = item.to_dict()
    session.commit()
    session.close()
    assert session.query(schema.Article).one().to_dict() == item_data

def test_to_dict():
    d1 = ArticleData.article1.to_dict()
    assert not d1.has_key(u'foo')
    d2 = ArticleData.article1.to_dict(foo=u'bar')
    assert d2['foo'] == u'bar'

@schema.with_empty_db
def test_data_inheritance():
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

    class NewFixture(Fixture):
        comments = CommentData

        class articles(fixture.Data):
            # _entity = schema.Article
            class new_article(ArticleData.article1):
                stub = "new_article"

    article = NewFixture.articles.new_article
    assert article.stub == "new_article"
    assert article.name == "The First Article"

    with NewFixture() as tester:
        article = tester.Article.one()
        assert article.stub == "new_article"
        assert article.name == "The First Article"
        assert tester._data.articles.new_article.stub == "new_article"

@schema.with_empty_db
def test_fixture_inheritance():
    class NewFixture(Fixture):
        comments = CommentData

        class articles(fixture.Data):
            # _entity = schema.Article
            class new_article(ArticleData.article1):
                stub = "new_article"

            class new_article2(ArticleData.article2):
                stub = "new_article2"

        class comments(CommentData):
            pass

    class NewFixture2(NewFixture):
        class articles(fixture.Data):
            class new_article(ArticleData.article1):
                stub = "new_article3"

    assert NewFixture2.articles.new_article.stub == "new_article3"
    assert len(NewFixture2.articles) == 1
    assert NewFixture2.comments.comment1.name == "Mr Smith"
    assert len(NewFixture2.comments) == 2

    with NewFixture2() as tester:
        assert tester.Article.one()
        assert tester.Comment.length_is(2)

@schema.with_empty_db
def test_override():
    class NewFixture(Fixture):
        class articles(ArticleData):
            class _override:
                name = "overridden"

    assert NewFixture.articles._items != ArticleData._items
    assert not (NewFixture.articles._items is ArticleData._items)

    with NewFixture() as tester:
        for article in tester.Article.all():
            assert article.name == "overridden"

    for article in ArticleData:
        assert article.name != "overridden"

@schema.with_empty_db
def test_first_fixture():
    with FirstFixture() as tester:
        article1 = tester.session.query(schema.Article).one()
        assert tester.Article.one() == article1
        assert article1.to_dict() == ArticleData.article1.to_dict()
        assert tester.Article.length_is(1)
        assert tester.Article.all() == [article1]
        comment1 = tester.session.query(schema.Comment).one()
        assert tester.Comment.one() == comment1
        assert comment1.to_dict() == CommentData.comment1.to_dict()
        assert tester.Comment.length_is(1)
        assert tester.Comment.all() == [comment1]


@schema.with_empty_db
def test_multiple_inheritance():
    class FixtureOne(Fixture):
        class articles(fixture.Data):
            _entity = schema.Article

            class article_1:
                stub = 'foo'
                name = 'Foo'
                body = 'The Foo article'
                score = 1

    class FixtureTwo(FixtureOne):
        class articles(FixtureOne.articles):
            class article_2:
                stub = 'bar'
                name = 'Bar'
                body = 'The Bar article'
                score = 2

    class FixtureThree(FixtureTwo):
        class comments(fixture.Data):
            _entity = schema.Comment

            class comment_1:
                id = 1
                article_stub = 'foo'
                email = 'bob@example.com'
                name = 'Bob'
                body = 'I like this article'

    with FixtureThree() as tester:
        assert tester.Article.length_is(2)
