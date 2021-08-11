# -*- coding: utf-8 -*-
from .case import MockTestCase
from plone.dexterity.content import Item
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.primary import PrimaryFieldInfo
from plone.rfc822.interfaces import IPrimaryField
from zope import schema
from zope.interface import alsoProvides
from zope.interface import Interface


try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


class PrimaryFieldInfoTestCase(MockTestCase):
    def test_primary_field_info(self):
        class ITest(Interface):
            title = schema.TextLine()
            body = schema.Text()

        alsoProvides(ITest["body"], IPrimaryField)

        fti = DexterityFTI(u"testtype")
        fti.lookupSchema = Mock(return_value=ITest)
        fti.behaviors = []
        self.mock_utility(fti, IDexterityFTI, name=u"testtype")

        item = Item("item")
        item.portal_type = "testtype"
        item.body = u"body text"

        info = PrimaryFieldInfo(item)
        assert info.fieldname == "body"
        assert info.field == ITest["body"]
        assert info.value == "body text"
