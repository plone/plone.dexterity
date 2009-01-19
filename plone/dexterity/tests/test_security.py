import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface
import zope.schema

from plone.dexterity.schema import schema_cache

from plone.dexterity.content import Item, Container

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.fti import DexterityFTI

class TestAttributeProtection(MockTestCase):

    def setUp(self):
        schema_cache.clear()
            
    def test_item(self):
        
        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")
        ITestSchema.setTaggedValue(u'dexterity.security', dict(test={'read-permission': 'View'},
                                                               foo={'read-permission': 'View foo'}))
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookup_schema()).result(ITestSchema)

        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Content item
        item = Item('test')
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"
        
        # Check permission
        checkPermission_mock = self.mocker.replace('Products.CMFCore.utils._checkPermission')
        self.expect(checkPermission_mock('View', item)).result(False)
        self.expect(checkPermission_mock('View foo', item)).result(True)

        self.mocker.replay()
        
        self.assertFalse(item.__allow_access_to_unprotected_subobjects__('test', u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('foo', u"bar"))
        
        # Unknown attributes are allowed
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('random', u"stuff"))

    def test_container(self):
        
        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")
        ITestSchema.setTaggedValue(u'dexterity.security', dict(test={'read-permission': 'View'},
                                                               foo={'read-permission': 'View foo'}))
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookup_schema()).result(ITestSchema)

        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Content item
        container = Container('test')
        container.portal_type = u"testtype"
        container.test = u"foo"
        container.foo = u"bar"
        
        # Check permission
        checkPermission_mock = self.mocker.replace('Products.CMFCore.utils._checkPermission')
        self.expect(checkPermission_mock('View', container)).result(False)
        self.expect(checkPermission_mock('View foo', container)).result(True)

        self.mocker.replay()
        
        self.assertFalse(container.__allow_access_to_unprotected_subobjects__('test', u"foo"))
        self.assertTrue(container.__allow_access_to_unprotected_subobjects__('foo', u"bar"))
        
        # Unknown attributes are allowed
        self.assertTrue(container.__allow_access_to_unprotected_subobjects__('random', u"stuff"))

    def test_subclass(self):
        
        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")
        ITestSchema.setTaggedValue(u'dexterity.security', dict(test={'read-permission': 'View'},
                                                               foo={'read-permission': 'View foo'}))
        
        class Foo(Item):
            pass
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookup_schema()).result(ITestSchema)

        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Content item
        item = Foo('test')
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"
        
        # Check permission
        checkPermission_mock = self.mocker.replace('Products.CMFCore.utils._checkPermission')
        self.expect(checkPermission_mock('View', item)).result(False)
        self.expect(checkPermission_mock('View foo', item)).result(True)

        self.mocker.replay()
        
        self.assertFalse(item.__allow_access_to_unprotected_subobjects__('test', u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('foo', u"bar"))
        
        # Unknown attributes are allowed
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('random', u"stuff"))

    def test_no_tagged_value(self):
        
        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookup_schema()).result(ITestSchema)

        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Content item
        item = Item('test')
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"
        
        self.mocker.replay()
        
        # Everything allowed
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('test', u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('foo', u"bar"))
        
        # Unknown attributes are allowed
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('random', u"stuff"))

    def test_no_read_permission(self):
        
        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")
        ITestSchema.setTaggedValue(u'dexterity.security', dict(test={'write-permission': 'Write test'},
                                                               foo={'read-permission': 'View foo'}))
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookup_schema()).result(ITestSchema)

        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Content item
        item = Item('test')
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"
        
        # Check permission
        checkPermission_mock = self.mocker.replace('Products.CMFCore.utils._checkPermission')
        self.expect(checkPermission_mock('View foo', item)).result(True)

        self.mocker.replay()
        
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('test', u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('foo', u"bar"))
        
        # Unknown attributes are allowed
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('random', u"stuff"))

    def test_no_schema(self):
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookup_schema()).result(None).count(3) # not cached this time

        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Content item
        item = Item('test')
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"
        
        self.mocker.replay()
        
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('test', u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('foo', u"bar"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('random', u"stuff"))

    def test_schema_exception(self):
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        
        self.expect(fti_mock.lookup_schema()).count(3).throw(AttributeError)

        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Content item
        item = Item('test')
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"
        
        self.mocker.replay()
        
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('test', u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('foo', u"bar"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('random', u"stuff"))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAttributeProtection))
    return suite
