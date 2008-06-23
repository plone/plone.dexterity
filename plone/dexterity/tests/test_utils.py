import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface
from zope.schema import getFieldNamesInOrder
from zope import schema

from plone.dexterity import utils
from Products.CMFCore.interfaces import ISiteRoot

class TestUtils(MockTestCase):
    
    def test_portal_type_to_schema_name_with_schema_and_prefix(self):
        self.assertEquals('prefix_0_type_0_schema',
            utils.portal_type_to_schema_name('type', 'schema', 'prefix'))
        self.assertEquals('prefix_0_type',
            utils.portal_type_to_schema_name('type', '', 'prefix'))
        self.assertEquals('prefix_0_type_1_one_2_two',
            utils.portal_type_to_schema_name('type one.two', '', 'prefix'))

    def test_portal_type_to_schema_name_looks_up_portal_for_prefix(self):
        portal_mock = self.mocker.mock()
        self.expect(portal_mock.getId()).result('portalid')
        self.mock_utility(portal_mock, ISiteRoot)
        
        self.replay()
        
        self.assertEquals('portalid_0_type',
            utils.portal_type_to_schema_name('type'))

    def test_schema_name_to_portal_type(self):
        self.assertEquals('type',
            utils.schema_name_to_portal_type('prefix_0_type_0_schema'))
        self.assertEquals('type',
            utils.schema_name_to_portal_type('prefix_0_type'))
        self.assertEquals('type one.two',
            utils.schema_name_to_portal_type('prefix_0_type_1_one_2_two'))
        
    def test_split_schema_name(self):
        self.assertEquals(('prefix', 'type', 'schema',),
            utils.split_schema_name('prefix_0_type_0_schema'))
        self.assertEquals(('prefix', 'type', '',),
            utils.split_schema_name('prefix_0_type'))
        self.assertEquals(('prefix', 'type one.two', '',),
            utils.split_schema_name('prefix_0_type_1_one_2_two'))
        
    def test_sync_schema(self):
        
        class ISource(Interface):
            one = schema.TextLine(title=u"A") # order: 0
            two = schema.Int(title=u"B")      # order: 1
        
        class IDest(Interface):
            one = schema.TextLine(title=u"C") # order: 0
            three = schema.Int(title=u"D")    # order: 1
            
        utils.sync_schema(ISource, IDest)
        
        self.assertEquals(u"C", IDest['one'].title)
        
        self.assertEquals(['one', 'two'], getFieldNamesInOrder(ISource))
        self.assertEquals(['two', 'one', 'three'], getFieldNamesInOrder(IDest))
    
    def test_sync_schema_overwrite(self):
        
        class ISource(Interface):
            one = schema.TextLine(title=u"A")
            two = schema.Int(title=u"B")
        
        class IDest(Interface):
            one = schema.TextLine(title=u"C")
            three = schema.Int(title=u"D")
            
        utils.sync_schema(ISource, IDest, overwrite=True)
        
        self.assertEquals(u"A", IDest['one'].title)
        
        self.assertEquals(['one', 'two'], getFieldNamesInOrder(ISource))
        self.assertEquals(['one', 'two'], getFieldNamesInOrder(IDest))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUtils))
    return suite
