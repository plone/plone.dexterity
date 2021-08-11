# -*- coding: utf-8 -*-
from plone.testing.zca import UNIT_TESTING

import unittest


# TODO: End to end tests that ensure components are properly wired up
#  - for now, we have some tests in example.dexterity, but we should have
#    more specific tests here.


class TestUUIDIntegration(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        from zope.configuration import xmlconfig

        import plone.uuid
        import zope.component.testing

        zope.component.testing.setUp()
        xmlconfig.file("configure.zcml", plone.uuid)

    def test_uuid_assigned_on_creation(self):
        from plone.dexterity.content import Item
        from plone.uuid.interfaces import IUUID
        from zope.event import notify
        from zope.lifecycleevent import ObjectCreatedEvent

        item = Item()
        notify(ObjectCreatedEvent(item))
        self.assertTrue(IUUID(item) is not None)
        self.assertEqual(IUUID(item), item.UID())
