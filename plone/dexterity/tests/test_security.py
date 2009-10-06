import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface
import zope.schema

from zope.security.interfaces import IPermission
from zope.security.permission import Permission

from plone.dexterity.schema import SCHEMA_CACHE

from plone.dexterity.content import Item, Container

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.fti import DexterityFTI

from plone.autoform.interfaces import READ_PERMISSIONS_KEY

class TestAttributeProtection(MockTestCase):

    def setUp(self):
        SCHEMA_CACHE.clear()
            
    def test_item(self):
        
        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")
        ITestSchema.setTaggedValue(READ_PERMISSIONS_KEY, dict(test='zope2.View', foo='foo.View'))
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(ITestSchema)

        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Mock permissions
        self.mock_utility(Permission(u'zope2.View', u"View"), IPermission, u'zope2.View')
        self.mock_utility(Permission(u'foo.View', u"View foo"), IPermission, u'foo.View')

        # Content item
        item = Item('test')
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"
        
        # Check permission
        
        securityManager_mock = self.mocker.mock()
        self.expect(securityManager_mock.checkPermission("View", item)).result(False)
        self.expect(securityManager_mock.checkPermission("View foo", item)).result(True)
        getSecurityManager_mock = self.mocker.replace('AccessControl.getSecurityManager')
        self.expect(getSecurityManager_mock()).result(securityManager_mock).count(2)

        self.mocker.replay()
        
        self.assertFalse(item.__allow_access_to_unprotected_subobjects__('test', u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('foo', u"bar"))
        
        # Unknown attributes are allowed
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('random', u"stuff"))

    def test_container(self):
        
        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")
        ITestSchema.setTaggedValue(READ_PERMISSIONS_KEY, dict(test='zope2.View', foo='foo.View'))
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(ITestSchema)

        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Mock permissions
        self.mock_utility(Permission(u'zope2.View', u"View"), IPermission, u'zope2.View')
        self.mock_utility(Permission(u'foo.View', u"View foo"), IPermission, u'foo.View')

        # Content item
        container = Container('test')
        container.portal_type = u"testtype"
        container.test = u"foo"
        container.foo = u"bar"
        
        # Check permission
        securityManager_mock = self.mocker.mock()
        self.expect(securityManager_mock.checkPermission("View", container)).result(False)
        self.expect(securityManager_mock.checkPermission("View foo", container)).result(True)
        getSecurityManager_mock = self.mocker.replace('AccessControl.getSecurityManager')
        self.expect(getSecurityManager_mock()).result(securityManager_mock).count(2)

        self.mocker.replay()
        
        self.assertFalse(container.__allow_access_to_unprotected_subobjects__('test', u"foo"))
        self.assertTrue(container.__allow_access_to_unprotected_subobjects__('foo', u"bar"))
        
        # Unknown attributes are allowed
        self.assertTrue(container.__allow_access_to_unprotected_subobjects__('random', u"stuff"))

    def test_subclass(self):
        
        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")
        ITestSchema.setTaggedValue(READ_PERMISSIONS_KEY, dict(test='zope2.View', foo='foo.View'))
        
        class Foo(Item):
            pass
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(ITestSchema)

        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Mock permissions
        self.mock_utility(Permission(u'zope2.View', u"View"), IPermission, u'zope2.View')
        self.mock_utility(Permission(u'foo.View', u"View foo"), IPermission, u'foo.View')

        # Content item
        item = Foo('test')
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"
        
        # Check permission
        securityManager_mock = self.mocker.mock()
        self.expect(securityManager_mock.checkPermission("View", item)).result(False)
        self.expect(securityManager_mock.checkPermission("View foo", item)).result(True)
        getSecurityManager_mock = self.mocker.replace('AccessControl.getSecurityManager')
        self.expect(getSecurityManager_mock()).result(securityManager_mock).count(2)

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
        self.expect(fti_mock.lookupSchema()).result(ITestSchema)

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
        ITestSchema.setTaggedValue(READ_PERMISSIONS_KEY, dict(foo='foo.View'))
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(ITestSchema)

        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Mock permissions
        self.mock_utility(Permission(u'foo.View', u"View foo"), IPermission, u'foo.View')

        # Content item
        item = Item('test')
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"
        
        # Check permission
        securityManager_mock = self.mocker.mock()
        self.expect(securityManager_mock.checkPermission("View foo", item)).result(True)
        getSecurityManager_mock = self.mocker.replace('AccessControl.getSecurityManager')
        self.expect(getSecurityManager_mock()).result(securityManager_mock).count(1)

        self.mocker.replay()
        
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('test', u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('foo', u"bar"))
        
        # Unknown attributes are allowed
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('random', u"stuff"))

    def test_no_schema(self):
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(None).count(3) # not cached this time

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
        
        self.expect(fti_mock.lookupSchema()).count(3).throw(AttributeError)

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

    def test_empty_name(self):
        
        # Mock FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).count(0)
        self.mock_utility(fti_mock, IDexterityFTI, u'testtype')

        # Content item
        item = Item('test')
        item.portal_type = u"testtype"
        
        self.mocker.replay()
        
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__('', u"foo"))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
