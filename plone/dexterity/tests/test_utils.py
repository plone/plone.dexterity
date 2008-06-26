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

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUtils))
    return suite
