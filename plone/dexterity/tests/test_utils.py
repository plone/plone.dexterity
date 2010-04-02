import unittest
from plone.mocktestcase import MockTestCase

from plone.dexterity import utils
from Products.CMFCore.interfaces import ISiteRoot

class TestUtils(MockTestCase):
    
    def test_portalTypeToSchemaName_with_schema_and_prefix(self):
        self.assertEquals('prefix_0_type_0_schema',
            utils.portalTypeToSchemaName('type', 'schema', 'prefix'))
        self.assertEquals('prefix_0_type',
            utils.portalTypeToSchemaName('type', '', 'prefix'))
        self.assertEquals('prefix_0_type_1_one_2_two',
            utils.portalTypeToSchemaName('type one.two', '', 'prefix'))

    def test_portalTypeToSchemaName_looks_up_portal_for_prefix(self):
        portal_mock = self.mocker.mock()
        self.expect(portal_mock.getPhysicalPath()).result(('', 'foo', 'portalid'))
        self.mock_utility(portal_mock, ISiteRoot)
        
        self.replay()
        
        self.assertEquals('foo_4_portalid_0_type',
            utils.portalTypeToSchemaName('type'))

    def test_schemaNameToPortalType(self):
        self.assertEquals('type',
            utils.schemaNameToPortalType('prefix_0_type_0_schema'))
        self.assertEquals('type',
            utils.schemaNameToPortalType('prefix_0_type'))
        self.assertEquals('type one.two',
            utils.schemaNameToPortalType('prefix_0_type_1_one_2_two'))
        
    def test_splitSchemaName(self):
        self.assertEquals(('prefix', 'type', 'schema',),
            utils.splitSchemaName('prefix_0_type_0_schema'))
        self.assertEquals(('prefix', 'type', '',),
            utils.splitSchemaName('prefix_0_type'))
        self.assertEquals(('prefix', 'type one.two', '',),
            utils.splitSchemaName('prefix_0_type_1_one_2_two'))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
