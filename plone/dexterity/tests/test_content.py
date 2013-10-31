# -*- coding: utf-8 -*-
import unittest
from plone.mocktestcase import MockTestCase

from datetime import date, datetime
from pytz import timezone

from zope.annotation.attribute import AttributeAnnotations
from zope.interface import Interface, alsoProvides
from zope.component import provideAdapter, getUtility
import zope.schema

from Products.CMFPlone.interfaces import IConstrainTypes
from plone.dexterity.interfaces import IDexterityFTI, IDexterityContainer
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.schema import SCHEMA_CACHE
from plone.dexterity.content import Item, Container
from plone.behavior.interfaces import IBehavior
from plone.behavior.registration import BehaviorRegistration
from plone.folder.default import DefaultOrdering


class TestContent(MockTestCase):

    def setUp(self):
        SCHEMA_CACHE.clear()
        provideAdapter(DefaultOrdering)
        provideAdapter(AttributeAnnotations)

    def test_provided_by_item(self):

        class FauxDataManager(object):
            def setstate(self, obj): pass
            def oldstate(self, obj, tid): pass
            def register(self, obj): pass

        # Dummy instance
        item = Item(id=u'id')
        item.portal_type = 'testtype'
        item._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        class IMarker(Interface):
            pass

        # Schema is not implemented by class or provided by instance
        self.assertEqual(False, ISchema.implementedBy(Item))
        self.assertEqual(False, ISchema.providedBy(item))

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema).count(1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        self.assertEqual(False, ISchema.implementedBy(Item))

        # Schema as looked up in FTI is now provided by item ...
        self.assertEqual(True, ISchema.providedBy(item))

        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEqual(True, ISchema.providedBy(item))

        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.

        alsoProvides(item, IMarker)

        self.assertEqual(True, IMarker.providedBy(item))
        self.assertEqual(True, ISchema.providedBy(item))

    def test_provided_by_subclass(self):

        # Make sure the __providedBy__ descriptor lives in sub-classes

        # Dummy type
        class MyItem(Item):
            pass

        class FauxDataManager(object):
            def setstate(self, obj): pass
            def oldstate(self, obj, tid): pass
            def register(self, obj): pass

        # Dummy instance
        item = MyItem(id=u'id')
        item.portal_type = 'testtype'
        item._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        class IMarker(Interface):
            pass

        # Schema is not implemented by class or provided by instance
        self.assertEqual(False, ISchema.implementedBy(MyItem))
        self.assertEqual(False, ISchema.providedBy(item))

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema).count(1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        self.assertEqual(False, ISchema.implementedBy(MyItem))

        # Schema as looked up in FTI is now provided by item ...
        self.assertEqual(True, ISchema.providedBy(item))

        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEqual(True, ISchema.providedBy(item))


        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.

        alsoProvides(item, IMarker)

        self.assertEqual(True, IMarker.providedBy(item))
        self.assertEqual(True, ISchema.providedBy(item))

    def test_provided_by_subclass_nojar(self):

        # Dummy type
        class MyItem(Item):
            pass

        # Dummy instance
        item = MyItem(id=u'id')
        item.portal_type = 'testtype'

        # Without a persistence jar, the _p_changed check doesn't work. In
        # this case, the cache is a bit slower.
        # item._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        class IMarker(Interface):
            pass

        # Schema is not implemented by class or provided by instance
        self.assertEqual(False, ISchema.implementedBy(MyItem))
        self.assertEqual(False, ISchema.providedBy(item))

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema).count(1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        self.assertEqual(False, ISchema.implementedBy(MyItem))

        # Schema as looked up in FTI is now provided by item ...
        self.assertEqual(True, ISchema.providedBy(item))

        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEqual(True, ISchema.providedBy(item))


        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.

        alsoProvides(item, IMarker)

        self.assertEqual(True, IMarker.providedBy(item))
        self.assertEqual(True, ISchema.providedBy(item))

    def test_provided_by_behavior_subtype(self):

        # Dummy type
        class MyItem(Item):
            pass

        # Fake data manager
        class FauxDataManager(object):
            def setstate(self, obj): pass
            def oldstate(self, obj, tid): pass
            def register(self, obj): pass


        # Dummy instance
        item = MyItem(id=u'id')
        item.portal_type = 'testtype'

        # Without a persistence jar, the _p_changed check doesn't work. In
        # this case, the cache is a bit slower.
        item._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        class IMarker(Interface):
            pass

        # Schema is not implemented by class or provided by instance
        self.assertEqual(False, ISchema.implementedBy(MyItem))
        self.assertEqual(False, ISchema.providedBy(item))

        # Behaviors - one with a subtype and one without

        class IBehavior1(Interface):
            pass

        class IBehavior2(Interface):
            pass

        class ISubtype(Interface):
            baz = zope.schema.TextLine(title=u"baz", default=u"baz")

        behavior1 = BehaviorRegistration(u"Behavior1", "", IBehavior1, None, None)
        behavior2 = BehaviorRegistration(u"Behavior2", "", IBehavior2, ISubtype, None)

        self.mock_utility(behavior1, IBehavior, name="behavior1")
        self.mock_utility(behavior2, IBehavior, name="behavior2")

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema).count(1)
        self.expect(fti_mock.behaviors).result(['behavior1', 'behavior2']).count(1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        self.assertEqual(False, ISchema.implementedBy(MyItem))

        # Schema as looked up in FTI is now provided by item ...
        self.assertEqual(True, ISubtype.providedBy(item))
        self.assertEqual(True, ISchema.providedBy(item))

        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEqual(True, ISubtype.providedBy(item))
        self.assertEqual(True, ISchema.providedBy(item))

        # Subtypes provide field defaults.
        self.assertEqual(u"baz", getattr(item, "baz", None))

        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.

        alsoProvides(item, IMarker)

        self.assertEqual(True, IMarker.providedBy(item))
        self.assertEqual(True, ISubtype.providedBy(item))
        self.assertEqual(True, ISchema.providedBy(item))

    def test_provided_by_behavior_subtype_invalidation(self):

        # Dummy type
        class MyItem(Item):
            pass

        # Fake data manager
        class FauxDataManager(object):
            def setstate(self, obj): pass
            def oldstate(self, obj, tid): pass
            def register(self, obj): pass


        # Dummy instance
        item = MyItem(id=u'id')
        item.portal_type = 'testtype'

        # Without a persistence jar, the _p_changed check doesn't work. In
        # this case, the cache is a bit slower.
        item._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        # Schema is not implemented by class or provided by instance
        self.assertEqual(False, ISchema.implementedBy(MyItem))
        self.assertEqual(False, ISchema.providedBy(item))

        # Behaviors - one with a subtype and one without

        class IBehavior1(Interface):
            pass

        class IBehavior2(Interface):
            pass

        class IBehavior3(Interface):
            pass

        class ISubtype1(Interface):
            pass

        class ISubtype2(Interface):
            pass

        behavior1 = BehaviorRegistration(u"Behavior1", "", IBehavior1, None, None)
        behavior2 = BehaviorRegistration(u"Behavior2", "", IBehavior2, ISubtype1, None)
        behavior3 = BehaviorRegistration(u"Behavior3", "", IBehavior3, ISubtype2, None)

        self.mock_utility(behavior1, IBehavior, name="behavior1")
        self.mock_utility(behavior2, IBehavior, name="behavior2")
        self.mock_utility(behavior3, IBehavior, name="behavior3")

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema).count(2) # twice, since we invalidate

        # First time around, we have only these behaviors
        self.expect(fti_mock.behaviors).result(['behavior1', 'behavior2']).count(1)

        # Second time around, we add another one
        self.expect(fti_mock.behaviors).result(['behavior1', 'behavior2', 'behavior3']).count(1)

        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        self.assertEqual(False, ISchema.implementedBy(MyItem))

        # Schema as looked up in FTI is now provided by item ...
        self.assertEqual(True, ISubtype1.providedBy(item))
        self.assertEqual(False, ISubtype2.providedBy(item))
        self.assertEqual(True, ISchema.providedBy(item))

        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEqual(True, ISubtype1.providedBy(item))
        self.assertEqual(False, ISubtype2.providedBy(item))
        self.assertEqual(True, ISchema.providedBy(item))

        # If we now invalidate the schema cache, we should get the second set
        # of behaviors
        SCHEMA_CACHE.invalidate('testtype')

        # Schema as looked up in FTI is now provided by item ...

        self.assertEqual(True, ISubtype1.providedBy(item))
        self.assertEqual(True, ISubtype2.providedBy(item))
        self.assertEqual(True, ISchema.providedBy(item))

        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEqual(True, ISubtype1.providedBy(item))
        self.assertEqual(True, ISubtype2.providedBy(item))
        self.assertEqual(True, ISchema.providedBy(item))

    def test_getattr_consults_schema_item(self):

        content = Item()
        content.id = u"id"
        content.portal_type = u"testtype"

        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        self.assertEqual(u"foo_default", content.foo)
        self.assertEqual(None, content.bar)
        self.assertEqual(u"id", content.id)
        self.assertRaises(AttributeError, getattr, content, 'baz')

    def test_getattr_consults_schema_container(self):

        content = Container()
        content.id = u"id"
        content.portal_type = u"testtype"

        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        self.assertEqual(u"foo_default", content.foo)
        self.assertEqual(None, content.bar)
        self.assertEqual(u"id", content.id)
        self.assertRaises(AttributeError, getattr, content, 'baz')

    def test_getattr_on_container_returns_children(self):

        content = Container()
        content.id = u"id"
        content.portal_type = u"testtype"

        content['foo'] = Item('foo')
        content['quux'] = Item('quux')

        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()
        # Schema field masks contained item
        self.assertEqual(u"foo_default", content.foo)

        # But we can still obtain an item
        self.assertTrue(isinstance(content['foo'], Item))
        self.assertEqual('foo', content['foo'].id)

        # And if the item isn't masked by an attribute, we can still getattr it
        self.assertTrue(isinstance(content['quux'], Item))
        self.assertEqual('quux', content['quux'].id)

        self.assertTrue(isinstance(getattr(content, 'quux'), Item))
        self.assertEqual('quux', getattr(content, 'quux').id)

    def test_ZMI_manage_options_container(self):
        # Make sure we get the expected tabs in the ZMI

        containerOptions = [o['label'] for o in Container.manage_options]
        for tab in ['Security', 'View', 'Contents', 'Properties', 'Undo', 'Ownership', 'Interfaces']:
            self.assertTrue(tab in containerOptions, "Tab %s not found" % tab)

    def test_ZMI_manage_options_item(self):
        # Make sure we get the expected tabs in the ZMI

        containerOptions = [o['label'] for o in Item.manage_options]
        for tab in ['Security', 'View', 'Properties', 'Undo', 'Ownership', 'Interfaces']:
            self.assertTrue(tab in containerOptions, "Tab %s not found" % tab)

    def test_name_and_id_in_sync(self):

        i = Item()
        self.assertEqual('', i.id)
        self.assertEqual('', i.getId())
        self.assertEqual(u'', i.__name__)

        i = Item()
        i.id = "foo"
        self.assertEqual('foo', i.id)
        self.assertEqual('foo', i.getId())
        self.assertEqual(u'foo', i.__name__)

        i = Item()
        i.__name__ = u"foo"
        self.assertEqual('foo', i.id)
        self.assertEqual('foo', i.getId())
        self.assertEqual(u'foo', i.__name__)

    def test_name_unicode_id_str(self):

        i = Item()

        try:
            i.__name__ = '\xc3\xb8'.decode('utf-8')
        except UnicodeEncodeError:
            pass
        else:
            self.fail()

        i.__name__ = u"o"

        self.assertEqual(u"o", i.__name__)
        self.assertEqual("o", i.id)
        self.assertEqual("o", i.getId())

        self.assertTrue(isinstance(i.__name__, unicode))
        self.assertTrue(isinstance(i.id, str))
        self.assertTrue(isinstance(i.getId(), str))

    def test_item_dublincore(self):
        from DateTime.DateTime import DateTime

        i = Item(
            title=u"Emperor Penguin",
            description=u'One of the most magnificent birds.',
            subject=u'Penguins',
            contributors=u'admin',
            effective_date="08/20/2010",
            expiration_date="07/09/2013",
            format='text/plain',
            language='de',
            rights='CC',
            )

        summer_timezone=i.effective_date.timezone()
        self.assertEqual(i.title, u"Emperor Penguin")
        self.assertEqual(i.Title(), 'Emperor Penguin')
        self.assertEqual(i.description, u'One of the most magnificent birds.')
        self.assertEqual(i.Description(), 'One of the most magnificent birds.')
        self.assertEqual(i.subject, (u'Penguins',))
        self.assertEqual(i.Subject(), ('Penguins',))
        self.assertEqual(i.contributors, (u'admin',))
        self.assertEqual(i.listContributors(), ('admin',))
        self.assertEqual(i.Contributors(), ('admin',))
        self.assertEqual(i.format, 'text/plain')
        self.assertEqual(i.effective_date, DateTime('08/20/2010'))
        self.assertEqual(i.EffectiveDate(zone=summer_timezone)[:10], '2010-08-20')
        self.assertEqual(i.effective(), DateTime('08/20/2010'))
        self.assertEqual(i.expiration_date, DateTime('07/09/2013'))
        self.assertEqual(i.ExpirationDate(zone=summer_timezone)[:10], '2013-07-09')
        self.assertEqual(i.expires(), DateTime('07/09/2013'))
        self.assertEqual(i.language, 'de')
        self.assertEqual(i.Language(), 'de')
        self.assertEqual(i.rights, 'CC')
        self.assertEqual(i.Rights(), 'CC')
        self.assertEqual(i.creation_date, i.created())
        self.assertEqual(i.CreationDate()[:19], i.creation_date.ISO()[:19])
        self.assertEqual(i.modification_date, i.creation_date)
        self.assertEqual(i.modification_date, i.modified())
        self.assertEqual(i.ModificationDate()[:19], i.modification_date.ISO()[:19])
        self.assertEqual(i.Date(), i.EffectiveDate())
        self.assertEqual(i.Identifier(), i.absolute_url())

    def test_item_dublincore_date(self):
        from DateTime.DateTime import DateTime

        i = Item(
            title=u"Emperor Penguin",
            description=u'One of the most magnificent birds.',
            subject=u'Penguins',
            contributors=u'admin',
            effective_date=date(2010, 8, 20),
            expiration_date=date(2013, 7, 9),
            format='text/plain',
            language='de',
            rights='CC',
            )

        summer_timezone=DateTime('2010/08/20').timezone()
        self.assertEqual(i.effective_date, DateTime('08/20/2010'))
        self.assertEqual(i.EffectiveDate(zone=summer_timezone)[:10], '2010-08-20')
        self.assertEqual(i.effective(), DateTime('08/20/2010'))
        self.assertEqual(i.expiration_date, DateTime('07/09/2013'))
        self.assertEqual(i.ExpirationDate(zone=summer_timezone)[:10], '2013-07-09')
        self.assertEqual(i.expires(), DateTime('07/09/2013'))
        self.assertEqual(i.creation_date, i.created())
        self.assertEqual(i.CreationDate()[:19], i.creation_date.ISO()[:19])
        self.assertEqual(i.modification_date, i.creation_date)
        self.assertEqual(i.modification_date, i.modified())
        self.assertEqual(i.ModificationDate()[:19], i.modification_date.ISO()[:19])
        self.assertEqual(i.Date(), i.EffectiveDate())

    def test_item_dublincore_datetime(self):
        from DateTime.DateTime import DateTime

        i = Item(
            title=u"Emperor Penguin",
            description=u'One of the most magnificent birds.',
            subject=u'Penguins',
            contributors=u'admin',
            effective_date=datetime(2010, 8, 20, 12, 59, 59, 0, timezone('US/Eastern')),
            expiration_date=datetime(2013, 7, 9, 12, 59, 59, 0, timezone('US/Eastern')),
            format='text/plain',
            language='de',
            rights='CC',
            )

        summer_timezone=DateTime('2010/08/20').timezone()
        self.assertEqual(i.effective_date, DateTime('08/20/2010 12:59:59 GMT-5'))
        self.assertEqual(i.EffectiveDate(zone=summer_timezone), 
                         DateTime('2010-08-20 12:59:59 GMT-5').toZone(summer_timezone).ISO())
        self.assertEqual(i.effective(), DateTime('08/20/2010 12:59:59 GMT-5'))
        self.assertEqual(i.expiration_date, DateTime('07/09/2013 12:59:59 GMT-5'))
        self.assertEqual(i.ExpirationDate(zone=summer_timezone), 
                         DateTime('2013-07-09 12:59:59 GMT-5').toZone(summer_timezone).ISO())
        self.assertEqual(i.expires(), DateTime('2013/07/09 12:59:59 GMT-5'))
        self.assertEqual(i.creation_date, i.created())
        self.assertEqual(i.CreationDate(), i.creation_date.ISO())
        self.assertEqual(i.modification_date, i.creation_date)
        self.assertEqual(i.modification_date, i.modified())
        self.assertEqual(i.ModificationDate(), i.modification_date.ISO())
        self.assertEqual(i.Date(), i.EffectiveDate())

    def test_item_notifyModified(self):
        i = Item()

        def mock_addCreator():
            mock_addCreator.called = True
        i.addCreator = mock_addCreator

        i.notifyModified()
        self.assertNotEqual(i.modification_date, i.creation_date)
        self.assertTrue(mock_addCreator.called)

    def test_item_addCreator(self):
        i = Item()
        i.addCreator(u'harvey')
        self.assertEqual(i.creators, (u'harvey',))
        self.assertEqual(i.listCreators(), (u'harvey',))
        self.assertEqual(i.Creator(), 'harvey')

    def test_item_Type(self):
        i = Item()

        def mock_getTypeInfo():
            class TypeInfo(object):
                def Title(self):
                    return 'Foo'
            return TypeInfo()
        i.getTypeInfo = mock_getTypeInfo

        self.assertEqual(i.Type(), 'Foo')

    def test_item_init_nondc_kwargs(self):
        i = Item(foo="bar")
        self.assertEqual(i.foo, "bar")

    def test_container_init_dublincore(self):
        from DateTime.DateTime import DateTime
        c = Container(title=u"Test title", language="en", effective_date="2010-08-20")
        self.assertEqual(c.title, u"Test title")
        self.assertEqual(c.language, "en")
        self.assertTrue(isinstance(c.effective_date, DateTime))

    def test_container_init_nondc_kwargs(self):
        c = Container(foo="bar")
        self.assertEqual(c.foo, "bar")

    def test_setTitle_converts_to_unicode(self):
        #fix http://code.google.com/p/dexterity/issues/detail?id=145
        i = Item()
        i.setTitle("é")
        self.assertEqual(i.title, u"é")
        i.setTitle(u"é")
        self.assertEqual(i.title, u"é")
        c = Container()
        c.setTitle("é")
        self.assertEqual(c.title, u"é")
        c.setTitle(u"é")
        self.assertEqual(c.title, u"é")

    def test_Title_converts_to_utf8(self):
        i = Item()
        i.title = u"é"
        self.assertEqual("é", i.Title())
        i.title = "é"
        self.assertEqual("é", i.Title())
        c = Container()
        c.title = u"é"
        self.assertEqual("é", c.Title())
        c.title = "é"
        self.assertEqual("é", c.Title())

    def test_Title_handles_None(self):
        i = Item(title=None)
        self.assertEqual('', i.Title())
        c = Container(title=None)
        self.assertEqual('', c.Title())

    def test_Creator_converts_to_utf8(self):
        i = Item()
        i.creators = (u"é",)
        self.assertEqual("é", i.Creator())
        i.creators = ("é",)
        self.assertEqual("é", i.Creator())
        c = Container()
        c.creators = (u"é",)
        self.assertEqual("é", c.Creator())
        self.assertEqual((u"é",), c.creators)

    def test_Creator_handles_None(self):
        i = Item(creators=None)
        self.assertEqual('', i.Creator())
        c = Container(creators=None)
        self.assertEqual('', c.Creator())

    def test_Description_converts_to_utf8(self):
        i = Item()
        i.description = u"é"
        self.assertEqual("é", i.Description())
        i.description = "é"
        self.assertEqual("é", i.Description())
        c = Container()
        c.description = u"é"
        self.assertEqual("é", c.Description())
        c.description = "é"
        self.assertEqual("é", c.Description())

    def test_setDescription_converts_to_unicode(self):
        i = Item()
        i.setDescription("é")
        self.assertEqual(i.description, u"é")
        i.setDescription(u"é")
        self.assertEqual(i.description, u"é")
        c = Container()
        c.setDescription("é")
        self.assertEqual(c.description, u"é")
        c.setDescription(u"é")
        self.assertEqual(c.description, u"é")

    def test_Description_handles_None(self):
        i = Item(description=None)
        self.assertEqual('', i.Description())
        c = Container(description=None)
        self.assertEqual('', c.Description())

    def test_Subject_converts_to_utf8(self):
        i = Item()
        i.subject = (u"é",)
        self.assertEqual(("é",), i.Subject())
        i.subject = ("é",)
        self.assertEqual(("é",), i.Subject())
        c = Container()
        c.subject = (u"é",)
        self.assertEqual(("é",), c.Subject())
        c.subject = ("é",)
        self.assertEqual(("é",), c.Subject())

    def test_setSubject_converts_to_unicode(self):
        i = Item()
        i.setSubject(("é",))
        self.assertEqual(i.subject, (u"é",))
        i.setSubject((u"é",))
        self.assertEqual(i.subject, (u"é",))
        c = Container()
        c.setSubject(("é",))
        self.assertEqual(c.subject, (u"é",))
        c.setSubject((u"é",))
        self.assertEqual(c.subject, (u"é",))

    def test_Subject_handles_None(self):
        i = Item()
        i.subject = None
        self.assertEqual((), i.Subject())
        c = Container()
        c.subject = None
        self.assertEqual((), c.Subject())

    def test_field_default_independence(self):
        # Ensure that fields using the default value aren't being assigned
        # shallow copies.

        class FauxDataManager(object):
            def setstate(self, obj): pass
            def oldstate(self, obj, tid): pass
            def register(self, obj): pass

        # Dummy instances
        foo = Item(id=u'foo')
        foo.portal_type = 'testtype'
        foo._p_jar = FauxDataManager()

        bar = Item(id=u'bar')
        bar.portal_type = 'testtype'
        bar._p_jar = FauxDataManager()

        baz = Container(id=u'baz')
        baz.portal_type = 'testtype'
        baz._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            listfield = zope.schema.List(title=u"listfield", default=[1,2])

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema).count(1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        # Ensure that the field of foo is not the same field, also attached to
        # bar.
        self.assertTrue(foo.listfield is not bar.listfield)
        self.assertTrue(foo.listfield is not baz.listfield)
        # And just to reinforce why this is awful, we'll ensure that updating
        # the field's value on one object does not change the value on the
        # other.
        foo.listfield.append(3)
        self.assertEqual(bar.listfield, [1,2])
        self.assertEqual(baz.listfield, [1,2])

    def test_container_manage_delObjects(self):
        # OFS does not check the delete permission for each object being
        # deleted. We want to.
        item = Item(id='test')
        container = Container(id='container')
        container['test'] = item
        from zExceptions import Unauthorized
        self.assertRaises(Unauthorized, container.manage_delObjects, ['test'])

        # Now permit it and try again.
        from Products.CMFCore.permissions import DeleteObjects
        item.manage_permission(DeleteObjects, ('Anonymous',))
        container.manage_delObjects(['test'])
        self.assertFalse('test' in container)

    def test_iconstraintypes_adapter(self):

        class DummyConstrainTypes(object):

            def __init__(self, context):
                self.context = context

            def allowedContentTypes(self):
                fti = getUtility(IDexterityFTI, name=u"testtype")
                return [fti]

        self.mock_adapter(DummyConstrainTypes, IConstrainTypes, (IDexterityContainer, ))

        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.getId()).result(u"testtype")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.replay()

        folder = Container(id="testfolder")

        self.assertEqual(folder.allowedContentTypes(), [fti_mock])
        self.assertRaises(ValueError, folder.invokeFactory, u"disallowed_type", id="test")

    def test_verifyObjectPaste_paste_without_portal_type(self):
        original_container = Container(id='parent')
        original_container.manage_permission('View', ('Anonymous',))
        content = Item(id='test')
        content.__factory_meta_type__ = 'document'
        container = Container(id='container')
        container.all_meta_types = [{'name': 'document',
                                     'action': None,
                                     'permission': 'View'}]
        container.manage_permission('View', ('Anonymous',))
        container['test'] = content
        content = container['test']
        container._verifyObjectPaste(content, True)

    def test_verifyObjectPaste_fti_does_not_allow_content(self):
        from Products.CMFCore.interfaces import ITypeInformation
        original_container = Container(id='parent')
        original_container.manage_permission('View', ('Anonymous',))
        content = Item(id='test')
        content.__factory_meta_type__ = 'document'
        content.portal_type = 'document'
        container = Container(id='container')
        container.all_meta_types = [{'name': 'document',
                                     'action': None,
                                     'permission': 'View'}]
        container.manage_permission('View', ('Anonymous',))
        container['test'] = content
        content = container['test']
        fti = self.mocker.mock()
        self.expect(fti.isConstructionAllowed(container)).result(False)
        self.mock_utility(fti, ITypeInformation, name='document')
        pt = self.mocker.mock()
        self.expect(pt.getTypeInfo('document')).result(None)
        self.expect(pt.getTypeInfo(container)).result(None)
        self.mock_tool(pt, 'portal_types')
        self.replay()
        self.assertRaises(ValueError, container._verifyObjectPaste, content, True)

    def test_verifyObjectPaste_fti_does_allow_content(self):
        from Products.CMFCore.interfaces import ITypeInformation
        original_container = Container(id='parent')
        original_container.manage_permission('View', ('Anonymous',))
        content = Item(id='test')
        content.__factory_meta_type__ = 'document'
        content.portal_type = 'document'
        container = Container(id='container')
        container.all_meta_types = [{'name': 'document',
                                     'action': None,
                                     'permission': 'View'}]
        container.manage_permission('View', ('Anonymous',))
        container['test'] = content
        content = container['test']
        fti = self.mocker.mock()
        self.expect(fti.isConstructionAllowed(container)).result(True)
        self.mock_utility(fti, ITypeInformation, name='document')
        pt = self.mocker.mock()
        self.expect(pt.getTypeInfo('document')).result(None)
        self.expect(pt.getTypeInfo(container)).result(None)
        self.mock_tool(pt, 'portal_types')
        self.replay()
        container._verifyObjectPaste(content, True)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
