import unittest
from plone.dexterity.content import Item
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.primary import PrimaryFieldInfo
from plone.mocktestcase import MockTestCase
from plone.rfc822.interfaces import IPrimaryField
from plone.rfc822.interfaces import IPrimaryFieldInfo
from zope import schema
from zope.interface import Interface
from zope.interface import alsoProvides

class PrimaryFieldInfoTestCase(MockTestCase):
    def test_primary_field_info(self):

        class ITest(Interface):
            title = schema.TextLine()
            body = schema.Text()
        alsoProvides(ITest['body'], IPrimaryField)

        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(ITest).count(0, None)
        self.expect(fti_mock.behaviors).result([]).count(0, None)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")        
        self.replay()

        item = Item('item')
        item.portal_type = 'testtype'
        item.body = u'body text'

        info = PrimaryFieldInfo(item)
        assert info.fieldname == 'body'
        assert info.field == ITest['body']
        assert info.value == 'body text'


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
