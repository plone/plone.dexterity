# -*- coding: utf-8 -*-
from .case import MockTestCase
from datetime import date
from datetime import datetime
from DateTime import DateTime
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehavior
from plone.behavior.interfaces import IBehaviorAssignable
from plone.behavior.registration import BehaviorRegistration
from plone.dexterity.behavior import DexterityBehaviorAssignable
from plone.dexterity.content import Container
from plone.dexterity.content import Item
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import IDexterityContainer
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.schema import SCHEMA_CACHE
from plone.folder.default import DefaultOrdering
from Products.CMFCore.interfaces import ITypesTool
from Products.CMFPlone.interfaces import IConstrainTypes
from pytz import timezone
from zope.annotation.attribute import AttributeAnnotations
from zope.component import getUtility
from zope.component import provideAdapter
from zope.interface import alsoProvides
from zope.interface import Interface
from zope.globalrequest import setRequest
from zope.publisher.browser import TestRequest

import six
import zope.schema


try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


class TestContent(MockTestCase):
    def setUp(self):
        setRequest(TestRequest())
        SCHEMA_CACHE.clear()
        provideAdapter(DefaultOrdering)
        provideAdapter(AttributeAnnotations)

    def test_provided_by_item(self):
        class FauxDataManager(object):
            def setstate(self, obj):
                pass

            def oldstate(self, obj, tid):
                pass

            def register(self, obj):
                pass

        # Dummy instance
        item = Item(id=u"id")
        item.portal_type = u"testtype"
        item._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        class IMarker(Interface):
            pass

        # FTI mock
        fti_mock = Mock(wraps=DexterityFTI("testtype"))
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        alsoProvides(fti_mock, IDexterityFTI)

        self.assertFalse(ISchema.implementedBy(Item))

        # Schema as looked up in FTI is now provided by item ...
        self.assertTrue(ISchema.providedBy(item))

        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case:
        self.assertTrue(ISchema.providedBy(item))
        self.assertEqual(fti_mock.lookupSchema.call_count, 1)

        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.
        alsoProvides(item, IMarker)
        self.assertTrue(IMarker.providedBy(item))
        self.assertTrue(ISchema.providedBy(item))

    def test_provided_by_subclass(self):

        # Make sure the __providedBy__ descriptor lives in sub-classes

        # Dummy type
        class MyItem(Item):
            pass

        class FauxDataManager(object):
            def setstate(self, obj):
                pass

            def oldstate(self, obj, tid):
                pass

            def register(self, obj):
                pass

        # Dummy instance
        item = MyItem(id=u"id")
        item.portal_type = "testtype"
        item._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        class IMarker(Interface):
            pass

        # FTI mock
        fti_mock = Mock(wraps=DexterityFTI(u"testtype"))
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        alsoProvides(fti_mock, IDexterityFTI)

        self.assertFalse(ISchema.implementedBy(MyItem))

        # Schema as looked up in FTI is now provided by item ...
        self.assertTrue(ISchema.providedBy(item))

        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case:
        self.assertTrue(ISchema.providedBy(item))
        self.assertEqual(fti_mock.lookupSchema.call_count, 1)

        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.
        alsoProvides(item, IMarker)
        self.assertTrue(IMarker.providedBy(item))
        self.assertTrue(ISchema.providedBy(item))

    def test_provided_by_subclass_nojar(self):

        # Dummy type
        class MyItem(Item):
            pass

        # Dummy instance
        item = MyItem(id=u"id")
        item.portal_type = "testtype"

        # Without a persistence jar, the _p_changed check doesn't work. In
        # this case, the cache is a bit slower.
        # item._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        class IMarker(Interface):
            pass

        # FTI mock
        fti_mock = Mock(wraps=DexterityFTI(u"testtype"))
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        alsoProvides(fti_mock, IDexterityFTI)

        self.assertFalse(ISchema.implementedBy(MyItem))

        # Schema as looked up in FTI is now provided by item ...
        self.assertTrue(ISchema.providedBy(item))

        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case:
        self.assertTrue(ISchema.providedBy(item))
        self.assertEqual(fti_mock.lookupSchema.call_count, 1)

        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.
        alsoProvides(item, IMarker)
        self.assertTrue(IMarker.providedBy(item))
        self.assertTrue(ISchema.providedBy(item))

    def test_provided_by_behavior_subtype(self):

        # Dummy type
        class MyItem(Item):
            pass

        class IMarkerCustom(Interface):
            pass

        # Fake data manager
        class FauxDataManager(object):
            def setstate(self, obj):
                pass

            def oldstate(self, obj, tid):
                pass

            def register(self, obj):
                pass

        # Dummy instance
        item = MyItem(id=u"id")
        item.portal_type = "testtype"

        # Without a persistence jar, the _p_changed check doesn't work. In
        # this case, the cache is a bit slower.
        item._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        # Schema is not implemented by class or provided by instance
        self.assertFalse(ISchema.implementedBy(MyItem))
        self.assertFalse(ISchema.providedBy(item))

        # Behaviors - one with a subtype and one without
        self.mock_adapter(
            DexterityBehaviorAssignable, IBehaviorAssignable, (IDexterityContent,)
        )

        class IBehavior1(Interface):
            pass

        behavior1 = BehaviorRegistration(u"Behavior1", "", IBehavior1, None, None)
        self.mock_utility(behavior1, IBehavior, name="behavior1")

        class IBehavior2(Interface):
            baz = zope.schema.TextLine(title=u"baz", default=u"baz")

        class IMarker2(Interface):
            pass

        behavior2 = BehaviorRegistration(u"Behavior2", "", IBehavior2, IMarker2, None)
        self.mock_utility(behavior2, IBehavior, name="behavior2")

        # FTI mock
        fti_mock = Mock(wraps=DexterityFTI(u"testtype"))
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        fti_mock.behaviors = ["behavior1", "behavior2"]
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        alsoProvides(fti_mock, IDexterityFTI)

        # start clean
        SCHEMA_CACHE.clear()

        # implementedBy does not look into the fti
        self.assertFalse(ISchema.implementedBy(MyItem))

        # Main schema as looked up in FTI is now provided by item ...
        self.assertTrue(ISchema.providedBy(item))

        # behavior1 does not provide a marker, the schema interface
        # is NOT used as a marker
        self.assertFalse(IBehavior1.providedBy(item))

        # behavior2 provides a marker, so it is used as a marker
        self.assertTrue(IMarker2.providedBy(item))

        # Subtypes provide field defaults.
        self.assertEqual(u"baz", getattr(item, "baz", None))

        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.
        alsoProvides(item, IMarkerCustom)
        self.assertTrue(IMarkerCustom.providedBy(item))

        # after directly setting an interface the main-schema and behavior
        # interfaces are still there
        self.assertTrue(ISchema.providedBy(item))
        self.assertFalse(IBehavior1.providedBy(item))
        self.assertTrue(IMarker2.providedBy(item))

    def test_provided_by_behavior_subtype_invalidation(self):

        # Dummy type
        class MyItem(Item):
            pass

        # Fake data manager
        class FauxDataManager(object):
            def setstate(self, obj):
                pass

            def oldstate(self, obj, tid):
                pass

            def register(self, obj):
                pass

        # Dummy instance
        item = MyItem(id=u"id")
        item.portal_type = "testtype"

        # Without a persistence jar, the _p_changed check doesn't work. In
        # this case, the cache is a bit slower.
        item._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        # Schema is not implemented by class or provided by instance
        self.assertFalse(ISchema.implementedBy(MyItem))
        self.assertFalse(ISchema.providedBy(item))

        # Behaviors - one with a marker and one without
        class IBehavior1(Interface):
            pass

        behavior1 = BehaviorRegistration(u"Behavior1", "", IBehavior1, None, None)
        self.mock_utility(behavior1, IBehavior, name="behavior1")

        class IBehavior2(Interface):
            pass

        class IMarker2(Interface):
            pass

        behavior2 = BehaviorRegistration(u"Behavior2", "", IBehavior2, IMarker2, None)
        self.mock_utility(behavior2, IBehavior, name="behavior2")

        class IBehavior3(Interface):
            pass

        class IMarker3(Interface):
            pass

        behavior3 = BehaviorRegistration(u"Behavior3", "", IBehavior3, IMarker3, None)
        self.mock_utility(behavior3, IBehavior, name="behavior3")

        self.mock_adapter(
            DexterityBehaviorAssignable, IBehaviorAssignable, (IDexterityContent,)
        )

        # FTI mock
        fti_mock = Mock(wraps=DexterityFTI(u"testtype"))
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        alsoProvides(fti_mock, IDexterityFTI)

        # start clean
        SCHEMA_CACHE.invalidate("testtype")
        fti_mock.behaviors = ["behavior1", "behavior2"]

        # implementedBy does not look into the fti
        self.assertFalse(ISchema.implementedBy(MyItem))

        # Main schema as looked up in FTI is now provided by item ...
        self.assertTrue(ISchema.providedBy(item))

        # Behaviors with its behavior or if provided merker as looked up in
        # FTI is now provided by item ...
        self.assertFalse(IBehavior1.providedBy(item))
        self.assertTrue(IMarker2.providedBy(item))
        self.assertFalse(IMarker3.providedBy(item))

        # If we now invalidate the schema cache, we should get the
        # SECOND set of behaviors (which includes behavior3)
        SCHEMA_CACHE.invalidate("testtype")
        fti_mock.behaviors = ["behavior1", "behavior2", "behavior3"]

        # Main schema as looked up in FTI is now provided by item ...
        self.assertTrue(ISchema.providedBy(item))

        # Behaviors with its behavior or if provided merker as looked up in
        # FTI is now provided by item ...
        self.assertFalse(IBehavior1.providedBy(item))
        self.assertTrue(IMarker2.providedBy(item))
        self.assertTrue(IMarker3.providedBy(item))

        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertTrue(ISchema.providedBy(item))
        self.assertFalse(IBehavior1.providedBy(item))
        self.assertTrue(IMarker2.providedBy(item))
        self.assertTrue(IMarker3.providedBy(item))

    def test_getattr_consults_schema_item(self):

        content = Item()
        content.id = u"id"
        content.portal_type = u"testtype"

        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        # FTI mock
        fti_mock = Mock(wraps=DexterityFTI(u"testtype"))
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        alsoProvides(fti_mock, IDexterityFTI)

        SCHEMA_CACHE.invalidate("testtype")

        self.assertEqual(u"foo_default", content.foo)
        self.assertEqual(None, content.bar)
        self.assertEqual(u"id", content.id)
        self.assertRaises(AttributeError, getattr, content, "baz")

    def test_getattr_consults_schema_container(self):

        content = Container()
        content.id = u"id"
        content.portal_type = u"testtype"

        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        # FTI mock
        fti_mock = Mock(wraps=DexterityFTI(u"testtype"))
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        alsoProvides(fti_mock, IDexterityFTI)

        SCHEMA_CACHE.invalidate("testtype")

        self.assertEqual(u"foo_default", content.foo)
        self.assertEqual(None, content.bar)
        self.assertEqual(u"id", content.id)
        self.assertRaises(AttributeError, getattr, content, "baz")

    def test_getattr_consults_schema_item_default_factory_with_context(self):

        content = Item()
        content.id = u"id"
        content.portal_type = u"testtype"

        from zope.interface import provider
        from zope.schema.interfaces import IContextAwareDefaultFactory

        @provider(IContextAwareDefaultFactory)
        def defaultFactory(context):
            return u"{0:s}_{1:s}".format(context.id, context.portal_type)

        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", defaultFactory=defaultFactory)
            bar = zope.schema.TextLine(title=u"bar")

        # FTI mock
        fti_mock = Mock(wraps=DexterityFTI(u"testtype"))
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        alsoProvides(fti_mock, IDexterityFTI)

        SCHEMA_CACHE.invalidate("testtype")

        self.assertEqual(u"id_testtype", content.foo)
        self.assertEqual(None, content.bar)
        self.assertEqual(u"id", content.id)
        self.assertRaises(AttributeError, getattr, content, "baz")

    def test_getattr_on_container_returns_children(self):

        content = Container()
        content.id = u"id"
        content.portal_type = u"testtype"

        content["foo"] = Item("foo")
        content["quux"] = Item("quux")

        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")

        # FTI mock
        fti_mock = Mock(wraps=DexterityFTI(u"testtype"))
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        alsoProvides(fti_mock, IDexterityFTI)

        SCHEMA_CACHE.invalidate("testtype")

        # Schema field masks contained item
        self.assertEqual(u"foo_default", content.foo)

        # But we can still obtain an item
        self.assertTrue(isinstance(content["foo"], Item))
        self.assertEqual("foo", content["foo"].id)

        # And if the item isn't masked by an attribute, we can still getattr it
        self.assertTrue(isinstance(content["quux"], Item))
        self.assertEqual("quux", content["quux"].id)

        self.assertTrue(isinstance(getattr(content, "quux"), Item))
        self.assertEqual("quux", getattr(content, "quux").id)

    def test_ZMI_manage_options_container(self):
        # Make sure we get the expected tabs in the ZMI

        containerOptions = [o["label"] for o in Container.manage_options]
        tabs = [
            "Security",
            "Contents",
            "Properties",
        ]
        for tab in tabs:
            self.assertTrue(tab in containerOptions, "Tab %s not found" % tab)

    def test_ZMI_manage_options_item(self):
        # Make sure we get the expected tabs in the ZMI

        containerOptions = [o["label"] for o in Item.manage_options]
        tabs = [
            "Security",
            "View",
            "Properties",
        ]
        for tab in tabs:
            self.assertTrue(tab in containerOptions, "Tab %s not found" % tab)

    def test_name_and_id_in_sync(self):

        i = Item()
        self.assertEqual("", i.id)
        self.assertEqual("", i.getId())
        self.assertEqual(u"", i.__name__)

        i = Item()
        i.id = "foo"
        self.assertEqual("foo", i.id)
        self.assertEqual("foo", i.getId())
        self.assertEqual(u"foo", i.__name__)

        i = Item()
        i.__name__ = u"foo"
        self.assertEqual("foo", i.id)
        self.assertEqual("foo", i.getId())
        self.assertEqual(u"foo", i.__name__)

    def test_name_unicode_id_str(self):

        i = Item()
        if six.PY2:
            try:
                i.__name__ = b"\xc3\xb8".decode("utf-8")
            except UnicodeEncodeError:
                pass
            else:
                self.fail()
        else:
            i.__name__ = b"\xc3\xb8".decode("utf-8")

        i.__name__ = u"o"

        self.assertEqual(u"o", i.__name__)
        self.assertEqual("o", i.id)
        self.assertEqual("o", i.getId())

        self.assertTrue(isinstance(i.__name__, six.text_type))
        self.assertTrue(isinstance(i.id, str))
        self.assertTrue(isinstance(i.getId(), str))

    def test_item_dublincore(self):
        from DateTime import DateTime

        import plone.dexterity

        datetime_patcher = patch.object(plone.dexterity.content, "DateTime")
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.return_value = DateTime(2014, 6, 1)
        self.addCleanup(datetime_patcher.stop)

        i = Item(
            title=u"Emperor Penguin",
            description=u"One of the most magnificent birds.",
            subject=u"Penguins",
            contributors=u"admin",
            effective_date="08/20/2010",
            expiration_date="07/09/2013",
            format="text/plain",
            language="de",
            rights="CC",
        )

        summer_timezone = i.effective_date.timezone()
        self.assertEqual(i.title, u"Emperor Penguin")
        self.assertEqual(i.Title(), "Emperor Penguin")
        self.assertEqual(i.description, u"One of the most magnificent birds.")
        self.assertEqual(i.Description(), "One of the most magnificent birds.")
        self.assertEqual(i.subject, (u"Penguins",))
        self.assertEqual(i.Subject(), ("Penguins",))
        self.assertEqual(i.contributors, (u"admin",))
        self.assertEqual(i.listContributors(), ("admin",))
        self.assertEqual(i.Contributors(), ("admin",))
        self.assertEqual(i.format, "text/plain")
        self.assertEqual(i.effective_date, DateTime("08/20/2010"))
        self.assertEqual(i.EffectiveDate(zone=summer_timezone)[:10], "2010-08-20")
        self.assertEqual(i.effective(), DateTime("08/20/2010"))
        self.assertEqual(i.expiration_date, DateTime("07/09/2013"))
        self.assertEqual(i.ExpirationDate(zone=summer_timezone)[:10], "2013-07-09")
        self.assertEqual(i.expires(), DateTime("07/09/2013"))
        self.assertEqual(i.language, "de")
        self.assertEqual(i.Language(), "de")
        self.assertEqual(i.rights, "CC")
        self.assertEqual(i.Rights(), "CC")
        self.assertEqual(i.creation_date, i.created())
        self.assertEqual(
            i.CreationDate(zone=summer_timezone)[:19], i.creation_date.ISO()[:19]
        )
        self.assertEqual(i.modification_date, i.creation_date)
        self.assertEqual(i.modification_date, i.modified())
        self.assertEqual(
            i.ModificationDate(zone=summer_timezone)[:19],
            i.modification_date.ISO()[:19],
        )
        self.assertEqual(i.Date(), i.EffectiveDate())
        self.assertEqual(i.Identifier(), i.absolute_url())

    def test_item_dublincore_date(self):
        from DateTime import DateTime

        import plone.dexterity

        datetime_patcher = patch.object(plone.dexterity.content, "DateTime")
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.return_value = DateTime(2014, 6, 1)
        self.addCleanup(datetime_patcher.stop)

        i = Item(
            title=u"Emperor Penguin",
            description=u"One of the most magnificent birds.",
            subject=u"Penguins",
            contributors=u"admin",
            effective_date=date(2010, 8, 20),
            expiration_date=date(2013, 7, 9),
            format="text/plain",
            language="de",
            rights="CC",
        )

        summer_timezone = DateTime("2010/08/20").timezone()
        self.assertEqual(i.effective_date, DateTime("08/20/2010"))
        self.assertEqual(i.EffectiveDate(zone=summer_timezone)[:10], "2010-08-20")
        self.assertEqual(i.effective(), DateTime("08/20/2010"))
        self.assertEqual(i.expiration_date, DateTime("07/09/2013"))
        self.assertEqual(i.ExpirationDate(zone=summer_timezone)[:10], "2013-07-09")
        self.assertEqual(i.expires(), DateTime("07/09/2013"))
        self.assertEqual(i.creation_date, i.created())
        self.assertEqual(
            i.CreationDate(zone=summer_timezone)[:19], i.creation_date.ISO()[:19]
        )
        self.assertEqual(i.modification_date, i.creation_date)
        self.assertEqual(i.modification_date, i.modified())
        self.assertEqual(
            i.ModificationDate(zone=summer_timezone)[:19],
            i.modification_date.ISO()[:19],
        )
        self.assertEqual(i.Date(), i.EffectiveDate())

    def test_item_dublincore_datetime(self):
        from DateTime import DateTime

        import plone.dexterity

        datetime_patcher = patch.object(plone.dexterity.content, "DateTime")
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.return_value = DateTime(2014, 6, 1)
        self.addCleanup(datetime_patcher.stop)
        i = Item(
            title=u"Emperor Penguin",
            description=u"One of the most magnificent birds.",
            subject=u"Penguins",
            contributors=u"admin",
            effective_date=datetime(2010, 8, 20, 12, 59, 59, 0, timezone("US/Eastern")),
            expiration_date=datetime(2013, 7, 9, 12, 59, 59, 0, timezone("US/Eastern")),
            format="text/plain",
            language="de",
            rights="CC",
        )

        summer_timezone = DateTime("2010/08/20").timezone()
        self.assertEqual(i.effective_date, DateTime("2010/08/20 12:59:59 US/Eastern"))
        self.assertEqual(
            i.EffectiveDate(zone=summer_timezone),
            DateTime("2010/08/20 12:59:59 US/Eastern").toZone(summer_timezone).ISO(),
        )
        self.assertEqual(i.effective(), DateTime("2010/08/20 12:59:59 US/Eastern"))
        self.assertEqual(i.expiration_date, DateTime("07/09/2013 12:59:59 US/Eastern"))
        self.assertEqual(
            i.ExpirationDate(zone=summer_timezone),
            DateTime("2013-07-09 12:59:59 US/Eastern").toZone(summer_timezone).ISO(),
        )
        self.assertEqual(i.expires(), DateTime("2013/07/09 12:59:59 US/Eastern"))
        self.assertEqual(i.creation_date, i.created())
        self.assertEqual(i.CreationDate(zone=summer_timezone), i.creation_date.ISO())
        self.assertEqual(i.modification_date, i.creation_date)
        self.assertEqual(i.modification_date, i.modified())
        self.assertEqual(
            i.ModificationDate(zone=summer_timezone), i.modification_date.ISO()
        )
        self.assertEqual(i.Date(), i.EffectiveDate())

    def test_item_notifyModified(self):
        i = Item()

        def mock_addCreator():
            mock_addCreator.called = True

        i.addCreator = mock_addCreator

        i.setModificationDate(DateTime(0))

        i.notifyModified()
        self.assertNotEqual(i.modification_date, i.creation_date)
        self.assertNotEqual(i.modification_date, DateTime(0))
        self.assertTrue(mock_addCreator.called)

    def test_item_addCreator(self):
        i = Item()
        i.addCreator(u"harvey")
        self.assertEqual(i.creators, (u"harvey",))
        self.assertEqual(i.listCreators(), (u"harvey",))
        self.assertEqual(i.Creator(), "harvey")

    def test_item_Type(self):
        i = Item()

        def mock_getTypeInfo():
            class TypeInfo(object):
                def Title(self):
                    return "Foo"

            return TypeInfo()

        i.getTypeInfo = mock_getTypeInfo

        self.assertEqual(i.Type(), "Foo")

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
        # fix http://code.google.com/p/dexterity/issues/detail?id=145
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
        self.assertEqual("", i.Title())
        c = Container(title=None)
        self.assertEqual("", c.Title())

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
        self.assertEqual("", i.Creator())
        c = Container(creators=None)
        self.assertEqual("", c.Creator())

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
        self.assertEqual("", i.Description())
        c = Container(description=None)
        self.assertEqual("", c.Description())

    def test_Description_removes_newlines(self):
        i = Item()
        i.description = u"foo\r\nbar\nbaz\r"
        self.assertEqual("foo bar baz ", i.Description())

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
            def setstate(self, obj):
                pass

            def oldstate(self, obj, tid):
                pass

            def register(self, obj):
                pass

        # Dummy instances
        foo = Item(id=u"foo")
        foo.portal_type = "testtype"
        foo._p_jar = FauxDataManager()

        bar = Item(id=u"bar")
        bar.portal_type = "testtype"
        bar._p_jar = FauxDataManager()

        baz = Container(id=u"baz")
        baz.portal_type = "testtype"
        baz._p_jar = FauxDataManager()

        # Dummy schema
        class ISchema(Interface):
            listfield = zope.schema.List(title=u"listfield", default=[1, 2])

        # FTI mock
        fti_mock = Mock(wraps=DexterityFTI(u"testtype"))
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # Ensure that the field of foo is not the same field, also attached to
        # bar.
        self.assertTrue(foo.listfield is not bar.listfield)
        self.assertTrue(foo.listfield is not baz.listfield)
        # And just to reinforce why this is awful, we'll ensure that updating
        # the field's value on one object does not change the value on the
        # other.
        foo.listfield.append(3)
        self.assertEqual(bar.listfield, [1, 2])
        self.assertEqual(baz.listfield, [1, 2])

    def test_container_manage_delObjects(self):
        # OFS does not check the delete permission for each object being
        # deleted. We want to.
        item = Item(id="test")
        container = Container(id="testcontainer")
        container["test"] = item
        # self.layer['portal']['testcontainer'] = container
        from zExceptions import Unauthorized

        self.assertRaises(Unauthorized, container.manage_delObjects, ["test"])

        # Now permit it and try again.
        from Products.CMFCore.permissions import DeleteObjects

        # in order to use manage_permissions the permission has to be defined
        # somewhere in the mro
        # since webdav is no longer part here, where it was defined in ZServer.
        # lets add it explicit here.
        perms_before = item.__class__.__ac_permissions__
        item.__class__.__ac_permissions__ = ((DeleteObjects, ()),)
        item.manage_permission(DeleteObjects, ("Anonymous",))
        container.manage_delObjects(["test"])
        self.assertFalse("test" in container)
        item.__class__.__ac_permissions__ = perms_before

    def test_iconstraintypes_adapter(self):
        class DummyConstrainTypes(object):
            def __init__(self, context):
                self.context = context

            def allowedContentTypes(self):
                fti = getUtility(IDexterityFTI, name=u"testtype")
                return [fti]

        self.mock_adapter(DummyConstrainTypes, IConstrainTypes, (IDexterityContainer,))

        # FTI mock
        fti_mock = Mock(wraps=DexterityFTI(u"testtype"))
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        folder = Container(id="testfolder")

        self.assertEqual(folder.allowedContentTypes(), [fti_mock])
        self.assertRaises(
            ValueError, folder.invokeFactory, u"disallowed_type", id="test"
        )

    def test_verifyObjectPaste_paste_without_portal_type(self):
        original_container = Container(id="parent")
        original_container.manage_permission("View", ("Anonymous",))
        content = Item(id="test")
        content.__factory_meta_type__ = "document"
        container = Container(id="container")
        container.all_meta_types = [
            {"name": "document", "action": None, "permission": "View"}
        ]
        container.manage_permission("View", ("Anonymous",))
        container["test"] = content
        content = container["test"]
        container._verifyObjectPaste(content, True)

    def test_verifyObjectPaste_fti_does_not_allow_content(self):
        from Products.CMFCore.interfaces import ITypeInformation

        original_container = Container(id="parent")
        original_container.manage_permission("View", ("Anonymous",))
        content = Item(id="test")
        content.__factory_meta_type__ = "document"
        content.portal_type = "document"
        container = Container(id="container")
        container.all_meta_types = [
            {"name": "document", "action": None, "permission": "View"}
        ]
        container.manage_permission("View", ("Anonymous",))
        container["test"] = content
        content = container["test"]
        fti_mock = Mock()
        fti_mock.isConstructionAllowed = Mock(return_value=False)
        self.mock_utility(fti_mock, ITypeInformation, name="document")
        mock_pt = Mock()
        mock_pt.getTypeInfo = Mock(return_value=None)
        self.mock_tool(mock_pt, "portal_types")
        self.mock_utility(mock_pt, ITypesTool)

        self.assertRaises(ValueError, container._verifyObjectPaste, content, True)

    def test_verifyObjectPaste_fti_does_allow_content(self):
        from Products.CMFCore.interfaces import ITypeInformation

        original_container = Container(id="parent")
        original_container.manage_permission("View", ("Anonymous",))
        content = Item(id="test")
        content.__factory_meta_type__ = "document"
        content.portal_type = "document"
        container = Container(id="container")
        container.all_meta_types = [
            {"name": "document", "action": None, "permission": "View"}
        ]
        container.manage_permission("View", ("Anonymous",))
        container["test"] = content
        content = container["test"]
        mock_fti = Mock()
        mock_fti.isConstructionAllowed = Mock(return_value=True)
        self.mock_utility(mock_fti, ITypeInformation, name="document")
        mock_pt = Mock()
        mock_pt.getTypeInfo = Mock(return_value=None)
        self.mock_tool(mock_pt, "portal_types")
        self.mock_utility(mock_pt, ITypesTool)

        container._verifyObjectPaste(content, True)

    def test_getSize(self):
        class SizedValue(str):
            def getSize(self):
                return len(self)

        class ITest(Interface):
            field1 = zope.schema.TextLine()

        class ITestBehavior(Interface):
            field2 = zope.schema.TextLine()

        alsoProvides(ITestBehavior, IFormFieldProvider)

        self.mock_adapter(
            DexterityBehaviorAssignable, IBehaviorAssignable, (IDexterityContent,)
        )

        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=ITest)
        fti_mock.behaviors = ["test_behavior"]
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        behavior_reg = BehaviorRegistration(
            u"Test Behavior", "", ITestBehavior, ITestBehavior, None
        )
        self.mock_utility(behavior_reg, IBehavior, name="test_behavior")

        item = Item("item")
        item.portal_type = "testtype"
        item.field1 = SizedValue("1")
        item.field2 = SizedValue("22")

        self.assertEqual(3, item.getSize())
