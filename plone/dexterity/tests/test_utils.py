import unittest
import mocker

from plone.dexterity import utils

class TestUtils(mocker.MockerTestCase):
    
    def test_portal_type_to_schema_name(self):
        self.fail()

    def test_schema_name_to_portal_type(self):
        self.fail()
        
    def test_split_schema_name(self):
        self.fail()
        
    def test_sync_schema(self):
        self.fail()

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUtils))
    return suite
