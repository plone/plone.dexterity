import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface

import zope.schema

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.fti import DexterityFTI
from plone.dexterity.schema import schema_cache
from plone.dexterity.content import DexterityContent, Item

class TestContent(MockTestCase):
    
    def setUp(self):
        schema_cache.clear()
    
    def test_provided_by(self):

        # Dummy type
        class MyItem(Item):
            pass
        
        # Dummy instance
        item = MyItem(id=u'id')
        item.portal_type = 'testtype'
        
        # Dummy schema
        class ISchema(Interface):
            foo = zope.schema.TextLine(title=u"foo", default=u"foo_default")
            bar = zope.schema.TextLine(title=u"bar")
        
        # Schema is not implemented by class or provided by instance
        self.assertEquals(False, ISchema.implementedBy(MyItem))
        self.assertEquals(False, ISchema.providedBy(item))
        
        # FTI mock
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookup_schema()).result(ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        # We would've accidentally kicked this one before
        del item._v__providedBy__
        
        self.replay()
        
        # Schema as looked up in FTI is now provided by item
        self.assertEquals(False, ISchema.implementedBy(MyItem))
        self.assertEquals(True, ISchema.providedBy(item))
    
    def test_getattr_consults_schema(self):
        
        content = DexterityContent()
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
