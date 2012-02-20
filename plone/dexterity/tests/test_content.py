# -*- coding: utf-8 -*-
import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface, alsoProvides
from zope.component import provideAdapter

import zope.schema

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.fti import DexterityFTI
from plone.dexterity.schema import SCHEMA_CACHE
from plone.dexterity.content import Item, Container

from plone.behavior.interfaces import IBehavior
from plone.behavior.registration import BehaviorRegistration

from plone.folder.default import DefaultOrdering
from zope.annotation.attribute import AttributeAnnotations

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
        self.assertEquals(False, ISchema.implementedBy(Item))
        self.assertEquals(False, ISchema.providedBy(item))
        
        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema).count(1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        self.assertEquals(False, ISchema.implementedBy(Item))
        
        # Schema as looked up in FTI is now provided by item ...
        self.assertEquals(True, ISchema.providedBy(item))
        
        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEquals(True, ISchema.providedBy(item))
        
        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.
    
        alsoProvides(item, IMarker)
        
        self.assertEquals(True, IMarker.providedBy(item))
        self.assertEquals(True, ISchema.providedBy(item))
    
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
        self.assertEquals(False, ISchema.implementedBy(MyItem))
        self.assertEquals(False, ISchema.providedBy(item))
        
        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema).count(1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        self.assertEquals(False, ISchema.implementedBy(MyItem))
        
        # Schema as looked up in FTI is now provided by item ...
        self.assertEquals(True, ISchema.providedBy(item))
        
        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEquals(True, ISchema.providedBy(item))
    
        
        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.
    
        alsoProvides(item, IMarker)
        
        self.assertEquals(True, IMarker.providedBy(item))
        self.assertEquals(True, ISchema.providedBy(item))
    
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
        self.assertEquals(False, ISchema.implementedBy(MyItem))
        self.assertEquals(False, ISchema.providedBy(item))
        
        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema).count(1)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        self.assertEquals(False, ISchema.implementedBy(MyItem))
        
        # Schema as looked up in FTI is now provided by item ...
        self.assertEquals(True, ISchema.providedBy(item))
        
        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEquals(True, ISchema.providedBy(item))
    
        
        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.
    
        alsoProvides(item, IMarker)
        
        self.assertEquals(True, IMarker.providedBy(item))
        self.assertEquals(True, ISchema.providedBy(item))
    
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
        self.assertEquals(False, ISchema.implementedBy(MyItem))
        self.assertEquals(False, ISchema.providedBy(item))
        
        # Behaviors - one with a subtype and one without
        
        class IBehavior1(Interface):
            pass
        
        class IBehavior2(Interface):
            pass
        
        class ISubtype(Interface):
            pass
        
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
        
        self.assertEquals(False, ISchema.implementedBy(MyItem))
        
        # Schema as looked up in FTI is now provided by item ...
        self.assertEquals(True, ISubtype.providedBy(item))
        self.assertEquals(True, ISchema.providedBy(item))
        
        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEquals(True, ISubtype.providedBy(item))
        self.assertEquals(True, ISchema.providedBy(item))
        
        # We also need to ensure that the _v_ attribute doesn't hide any
        # interface set directly on the instance with alsoProvides() or
        # directlyProvides(). This is done by clearing the cache when these
        # are invoked.
    
        alsoProvides(item, IMarker)
        
        self.assertEquals(True, IMarker.providedBy(item))
        self.assertEquals(True, ISubtype.providedBy(item))
        self.assertEquals(True, ISchema.providedBy(item))      

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
        self.assertEquals(False, ISchema.implementedBy(MyItem))
        self.assertEquals(False, ISchema.providedBy(item))
        
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
        
        self.assertEquals(False, ISchema.implementedBy(MyItem))
        
        # Schema as looked up in FTI is now provided by item ...
        self.assertEquals(True, ISubtype1.providedBy(item))
        self.assertEquals(False, ISubtype2.providedBy(item))
        self.assertEquals(True, ISchema.providedBy(item))
        
        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEquals(True, ISubtype1.providedBy(item))
        self.assertEquals(False, ISubtype2.providedBy(item))
        self.assertEquals(True, ISchema.providedBy(item))
        
        # If we now invalidate the schema cache, we should get the second set
        # of behaviors
        SCHEMA_CACHE.invalidate('testtype')
        
        # Schema as looked up in FTI is now provided by item ...
        
        self.assertEquals(True, ISubtype1.providedBy(item))
        self.assertEquals(True, ISubtype2.providedBy(item))
        self.assertEquals(True, ISchema.providedBy(item))
        
        # If the _v_ attribute cache does not work, then we'd expect to have
        # to look up the schema more than once (since we invalidated)
        # the cache. This is not the case, as evidenced by .count(1) above.
        self.assertEquals(True, ISubtype1.providedBy(item))
        self.assertEquals(True, ISubtype2.providedBy(item))
        self.assertEquals(True, ISchema.providedBy(item))
    
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
        
        self.assertEquals(u"foo_default", content.foo)
        self.assertEquals(None, content.bar)
        self.assertEquals(u"id", content.id)
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
        
        self.assertEquals(u"foo_default", content.foo)
        self.assertEquals(None, content.bar)
        self.assertEquals(u"id", content.id)
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
        self.assertEquals(u"foo_default", content.foo)
        
        # But we can still obtain an item
        self.failUnless(isinstance(content['foo'], Item))
        self.assertEquals('foo', content['foo'].id)
        
        # And if the item isn't masked by an attribute, we can still getattr it
        self.failUnless(isinstance(content['quux'], Item))
        self.assertEquals('quux', content['quux'].id)
        
        self.failUnless(isinstance(getattr(content, 'quux'), Item))
        self.assertEquals('quux', getattr(content, 'quux').id)
    
    def test_ZMI_manage_options_container(self):
        # Make sure we get the expected tabs in the ZMI
        
        containerOptions = [o['label'] for o in Container.manage_options]        
        for tab in ['Security', 'View', 'Contents', 'Properties', 'Undo', 'Ownership', 'Interfaces']:
            self.failUnless(tab in containerOptions, "Tab %s not found" % tab)
        
    def test_ZMI_manage_options_item(self):
        # Make sure we get the expected tabs in the ZMI
        
        containerOptions = [o['label'] for o in Item.manage_options]        
        for tab in ['Security', 'View', 'Undo', 'Ownership', 'Interfaces', 'Dublin Core']:
            self.failUnless(tab in containerOptions, "Tab %s not found" % tab)        

    def test_name_and_id_in_sync(self):
        
        i = Item()
        self.assertEquals('', i.id)
        self.assertEquals('', i.getId())
        self.assertEquals(u'', i.__name__)
        
        i = Item()
        i.id = "foo"
        self.assertEquals('foo', i.id)
        self.assertEquals('foo', i.getId())
        self.assertEquals(u'foo', i.__name__)
        
        i = Item()
        i.__name__ = u"foo"
        self.assertEquals('foo', i.id)
        self.assertEquals('foo', i.getId())
        self.assertEquals(u'foo', i.__name__)
        
    def test_name_unicode_id_str(self):
        
        i = Item()
        
        try:
            i.__name__ = '\xc3\xb8'.decode('utf-8')
        except UnicodeEncodeError:
            pass
        else:
            self.fail()
        
        i.__name__ = u"o"
        
        self.assertEquals(u"o", i.__name__)
        self.assertEquals("o", i.id)
        self.assertEquals("o", i.getId())
        
        self.failUnless(isinstance(i.__name__, unicode))
        self.failUnless(isinstance(i.id, str))
        self.failUnless(isinstance(i.getId(), str))

    def test_item_init_dublincore(self):
        from DateTime.DateTime import DateTime
        i = Item(title=u"Test title", language="en", effective_date="2010-08-20")
        self.assertEqual(i.title, u"Test title")
        self.assertEqual(i.language, "en")
        self.assertTrue(isinstance(i.effective_date, DateTime))
    
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
        self.assertEquals(bar.listfield, [1,2])
        self.assertEquals(baz.listfield, [1,2])
        
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


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
