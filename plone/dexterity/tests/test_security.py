# -*- coding: utf-8 -*-
from .case import MockTestCase
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.dexterity.content import Container
from plone.dexterity.content import Item
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.schema import SCHEMA_CACHE
from zope.interface import Interface
from zope.interface import provider
from zope.security.interfaces import IPermission
from zope.security.permission import Permission
from zope.globalrequest import setRequest
from zope.publisher.browser import TestRequest

import zope.schema


try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


class TestAttributeProtection(MockTestCase):
    def setUp(self):
        setRequest(TestRequest())
        SCHEMA_CACHE.clear()

    def test_item(self):

        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")

        ITestSchema.setTaggedValue(
            READ_PERMISSIONS_KEY, dict(test="zope2.View", foo="foo.View")
        )

        from plone.autoform.interfaces import IFormFieldProvider

        @provider(IFormFieldProvider)
        class ITestBehavior(Interface):
            test2 = zope.schema.TextLine(title=u"Test")

        ITestBehavior.setTaggedValue(
            READ_PERMISSIONS_KEY, dict(test2="zope2.View", foo2="foo.View")
        )

        # Mock a test behavior
        from plone.behavior.registration import BehaviorRegistration

        registration = BehaviorRegistration(
            title=u"Test Behavior",
            description=u"Provides test behavior",
            interface=ITestBehavior,
            marker=Interface,
            factory=None,
        )
        from plone.behavior.interfaces import IBehavior

        self.mock_utility(registration, IBehavior, ITestBehavior.__identifier__)
        from plone.behavior.interfaces import IBehaviorAssignable
        from plone.dexterity.behavior import DexterityBehaviorAssignable
        from plone.dexterity.interfaces import IDexterityContent

        self.mock_adapter(
            DexterityBehaviorAssignable, IBehaviorAssignable, (IDexterityContent,)
        )

        # Mock FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.behaviors = ()
        fti_mock.lookupSchema = Mock(return_value=ITestSchema)
        self.mock_utility(fti_mock, IDexterityFTI, u"testtype")

        # Mock permissions
        self.mock_utility(
            Permission(u"zope2.View", u"View"), IPermission, u"zope2.View"
        )
        self.mock_utility(
            Permission(u"foo.View", u"View foo"), IPermission, u"foo.View"
        )

        # Content item
        item = Item("test")
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"

        # mock security manager
        security_manager_mock = Mock()
        from AccessControl import getSecurityManager

        self.patch_global(getSecurityManager, return_value=security_manager_mock)

        # run 1: schema and no behavior access to schema protected attribute
        security_manager_mock.checkPermission = Mock(return_value=False)
        SCHEMA_CACHE.clear()
        self.assertFalse(
            item.__allow_access_to_unprotected_subobjects__("test", u"foo")
        )
        security_manager_mock.checkPermission.assert_called_with("View", item)

        # run 2: schema and no behavior access to known non schema attribute
        security_manager_mock.checkPermission = Mock(return_value=True)
        SCHEMA_CACHE.clear()
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__("foo", u"bar"))
        security_manager_mock.checkPermission.assert_called_with("View foo", item)

        # run 3: schema and no behavior, unknown attributes are allowed
        SCHEMA_CACHE.clear()
        self.assertTrue(
            item.__allow_access_to_unprotected_subobjects__("random", u"stuff")
        )

        # run 4: schema and behavior
        security_manager_mock.checkPermission = Mock(return_value=True)
        fti_mock.behaviors = [ITestBehavior.__identifier__]
        SCHEMA_CACHE.clear()
        self.assertTrue(
            item.__allow_access_to_unprotected_subobjects__("test2", u"foo2")
        )
        security_manager_mock.checkPermission.assert_called_with("View", item)

        # run 5: no schema but behavior
        security_manager_mock.checkPermission = Mock(return_value=True)
        fti_mock.lookupSchema = Mock(return_value=None)
        SCHEMA_CACHE.clear()
        self.assertTrue(
            item.__allow_access_to_unprotected_subobjects__("test2", u"foo2")
        )
        security_manager_mock.checkPermission.assert_called_with("View", item)

    def test_container(self):

        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")

        ITestSchema.setTaggedValue(
            READ_PERMISSIONS_KEY, dict(test="zope2.View", foo="foo.View")
        )

        from plone.autoform.interfaces import IFormFieldProvider

        @provider(IFormFieldProvider)
        class ITestBehavior(Interface):
            test2 = zope.schema.TextLine(title=u"Test")

        ITestBehavior.setTaggedValue(
            READ_PERMISSIONS_KEY, dict(test2="zope2.View", foo2="foo.View")
        )

        # Mock a test behavior
        from plone.behavior.registration import BehaviorRegistration

        registration = BehaviorRegistration(
            title=u"Test Behavior",
            description=u"Provides test behavior",
            interface=ITestBehavior,
            marker=Interface,
            factory=None,
        )
        from plone.behavior.interfaces import IBehavior

        self.mock_utility(registration, IBehavior, ITestBehavior.__identifier__)
        from plone.behavior.interfaces import IBehaviorAssignable
        from plone.dexterity.behavior import DexterityBehaviorAssignable
        from plone.dexterity.interfaces import IDexterityContent

        self.mock_adapter(
            DexterityBehaviorAssignable, IBehaviorAssignable, (IDexterityContent,)
        )

        # Mock FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=ITestSchema)
        fti_mock.behaviors = ()
        self.mock_utility(fti_mock, IDexterityFTI, u"testtype")

        # Mock permissions
        self.mock_utility(
            Permission(u"zope2.View", u"View"), IPermission, u"zope2.View"
        )
        self.mock_utility(
            Permission(u"foo.View", u"View foo"), IPermission, u"foo.View"
        )

        # Content item
        container = Container("test")
        container.portal_type = u"testtype"
        container.test = u"foo"
        container.foo = u"bar"

        # mock security manager
        security_manager_mock = Mock()
        from AccessControl import getSecurityManager

        self.patch_global(getSecurityManager, return_value=security_manager_mock)

        # run 1: schema and no behavior access to schema protected attribute
        security_manager_mock.checkPermission = Mock(return_value=False)
        SCHEMA_CACHE.clear()
        self.assertFalse(
            container.__allow_access_to_unprotected_subobjects__("test", u"foo")
        )
        security_manager_mock.checkPermission.assert_called_with("View", container)

        # run 2: schema and no behavior access to known non schema attribute
        security_manager_mock.checkPermission = Mock(return_value=True)
        SCHEMA_CACHE.clear()
        self.assertTrue(
            container.__allow_access_to_unprotected_subobjects__("foo", u"bar")
        )
        security_manager_mock.checkPermission.assert_called_with("View foo", container)

        # run 3: schema and no behavior, unknown attributes are allowed
        SCHEMA_CACHE.clear()
        self.assertTrue(
            container.__allow_access_to_unprotected_subobjects__("random", u"stuff")
        )

        # run 4: schema and behavior
        security_manager_mock.checkPermission = Mock(return_value=True)
        fti_mock.behaviors = [ITestBehavior.__identifier__]
        SCHEMA_CACHE.clear()
        self.assertTrue(
            container.__allow_access_to_unprotected_subobjects__("test2", u"foo2")
        )
        security_manager_mock.checkPermission.assert_called_with("View", container)

        # run 5: no schema but behavior
        fti_mock.lookupSchema = Mock(return_value=None)
        security_manager_mock.checkPermission = Mock(return_value=True)
        SCHEMA_CACHE.clear()
        self.assertTrue(
            container.__allow_access_to_unprotected_subobjects__("test2", u"foo2")
        )
        security_manager_mock.checkPermission.assert_called_with("View", container)

    def test_no_tagged_value(self):

        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")

        # Mock FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=ITestSchema)
        fti_mock.behaviors = ()
        self.mock_utility(fti_mock, IDexterityFTI, u"testtype")

        # Content item
        item = Item("test")
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"

        SCHEMA_CACHE.clear()

        # Everything allowed
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__("test", u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__("foo", u"bar"))

        # Unknown attributes are allowed
        self.assertTrue(
            item.__allow_access_to_unprotected_subobjects__("random", u"stuff")
        )

    def test_no_read_permission(self):

        # Mock schema model
        class ITestSchema(Interface):
            test = zope.schema.TextLine(title=u"Test")

        ITestSchema.setTaggedValue(READ_PERMISSIONS_KEY, dict(foo="foo.View"))

        # Mock FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=ITestSchema)
        fti_mock.behaviors = ()

        self.mock_utility(fti_mock, IDexterityFTI, u"testtype")

        # Mock permissions
        self.mock_utility(
            Permission(u"foo.View", u"View foo"), IPermission, u"foo.View"
        )

        # Content item
        item = Item("test")
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"

        # Check permission
        security_manager_mock = Mock()
        security_manager_mock.checkPermission = Mock(return_value=True)
        from AccessControl import getSecurityManager

        self.patch_global(getSecurityManager, return_value=security_manager_mock)

        SCHEMA_CACHE.clear()

        self.assertTrue(item.__allow_access_to_unprotected_subobjects__("test", u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__("foo", u"bar"))

        # Unknown attributes are allowed
        self.assertTrue(
            item.__allow_access_to_unprotected_subobjects__("random", u"stuff")
        )

    def test_no_schema(self):

        # Mock FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=None)
        fti_mock.behaviors = ()
        self.mock_utility(fti_mock, IDexterityFTI, u"testtype")

        # Content item
        item = Item("test")
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"

        SCHEMA_CACHE.clear()

        self.assertTrue(item.__allow_access_to_unprotected_subobjects__("test", u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__("foo", u"bar"))
        self.assertTrue(
            item.__allow_access_to_unprotected_subobjects__("random", u"stuff")
        )

    def test_schema_exception(self):

        # Mock FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(side_effect=AttributeError)
        fti_mock.behaviors = ()

        self.mock_utility(fti_mock, IDexterityFTI, u"testtype")

        # Content item
        item = Item("test")
        item.portal_type = u"testtype"
        item.test = u"foo"
        item.foo = u"bar"

        SCHEMA_CACHE.clear()

        self.assertTrue(item.__allow_access_to_unprotected_subobjects__("test", u"foo"))
        self.assertTrue(item.__allow_access_to_unprotected_subobjects__("foo", u"bar"))
        self.assertTrue(
            item.__allow_access_to_unprotected_subobjects__("random", u"stuff")
        )

    def test_empty_name(self):

        # Mock FTI
        fti_mock = DexterityFTI(u"testtype")
        self.mock_utility(fti_mock, IDexterityFTI, u"testtype")

        # Content item
        item = Item("test")
        item.portal_type = u"testtype"

        SCHEMA_CACHE.clear()

        self.assertTrue(item.__allow_access_to_unprotected_subobjects__("", u"foo"))
