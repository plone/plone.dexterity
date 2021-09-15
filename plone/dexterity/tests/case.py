# -*- coding: utf-8 -*-
from plone.dexterity.bbb import HAS_WEBDAV

import gc
import six
import unittest
import zope.component
import zope.component.testing
import zope.globalrequest

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


class MockTestCase(unittest.TestCase):
    """Base class for tests using mocks."""

    _getToolByName_return_values = None
    _replaced_globals = None

    # Ensure that we tear down the CA after each test method

    def tearDown(self):
        zope.component.testing.tearDown(self)
        zope.globalrequest.setRequest(None)

        if self._replaced_globals is not None:
            for mock, orig in self._replaced_globals.items():
                _global_replace(mock, orig)

    # Helper to create a dummy object with a particular __dict__

    def create_dummy(self, **kw):
        return Dummy(**kw)

    # Help register mock components. The tear-down method will
    # wipe the registry each time.

    def mock_utility(self, mock, provides, name=u""):
        """Register the mock as a utility providing the given interface"""
        zope.component.provideUtility(provides=provides, component=mock, name=name)

    def mock_adapter(self, mock, provides, adapts, name=u""):
        """Register the mock as an adapter providing the given interface
        and adapting the given interface(s)
        """
        zope.component.provideAdapter(
            factory=mock, adapts=adapts, provides=provides, name=name
        )

    def mock_subscription_adapter(self, mock, provides, adapts):
        """Register the mock as a utility providing the given interface"""
        zope.component.provideSubscriptionAdapter(
            factory=mock, provides=provides, adapts=adapts
        )

    def mock_handler(self, mock, adapts):
        """Register the mock as a utility providing the given interface"""
        zope.component.provideHandler(factory=mock, adapts=adapts)

    def mock_tool(self, mock, name):
        """Register a mock tool that will be returned when getToolByName()
        is called.
        """
        if self._getToolByName_return_values is None:
            self._getToolByName_return_values = return_values = {}

            def get_return_value(context, name, default=None):
                return return_values.get(name, default)

            from Products.CMFCore.utils import getToolByName

            self.patch_global(getToolByName, side_effect=get_return_value)
        self._getToolByName_return_values[name] = mock

    def patch_global(self, orig, mock=None, **kw):
        if mock is None:
            mock = Mock(**kw)
        elif kw:
            raise Exception(
                "Keyword arguments are ignored if a mock instance is passed."
            )
        _global_replace(orig, mock)
        if self._replaced_globals is None:
            self._replaced_globals = {}
        self._replaced_globals[mock] = orig
        return mock


class Dummy(object):
    """Dummy object with arbitrary attributes"""

    def __init__(self, **kw):
        self.__dict__.update(kw)


class ItemDummy(Dummy):
    """Dummy objects with title getter and setter"""

    title = ""
    portal_type = "foo"

    def Title(self):
        return self.title

    def setTitle(self, title):
        self.title = title

    def getId(self):
        return self.__dict__.get("id", "")


# from mocker
def _global_replace(remove, install):
    """Replace object 'remove' with object 'install' on all dictionaries."""
    for referrer in gc.get_referrers(remove):
        if type(referrer) is dict:
            for key, value in list(six.iteritems(referrer)):
                if value is remove:
                    referrer[key] = install
