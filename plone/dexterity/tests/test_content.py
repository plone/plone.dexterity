import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface, alsoProvides

import zope.schema

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.fti import DexterityFTI
from plone.dexterity.schema import schema_cache
from plone.dexterity.content import Item, Container

class TestContent(MockTestCase):
    
    def setUp(self):
        schema_cache.clear()

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
        self.expect(fti_mock.lookup_schema()).result(ISchema).count(1)
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
        self.expect(fti_mock.lookup_schema()).result(ISchema).count(1)
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
        self.expect(fti_mock.lookup_schema()).result(ISchema).count(1)
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
    
    def test_getattr_consults_schema_item(self):
        
        content = Item()
        content.id = u"id"
        content.portal_type = u"testtype"
        
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")
        
        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookup_schema()).result(ISchema)
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
        self.expect(fti_mock.lookup_schema()).result(ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        self.assertEquals(u"foo_default", content.foo)
        self.assertEquals(None, content.bar)
        self.assertEquals(u"id", content.id)
        self.assertRaises(AttributeError, getattr, content, 'baz')
        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestContent))
    return suite
