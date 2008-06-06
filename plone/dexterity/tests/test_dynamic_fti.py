import unittest

from plone.dexterity import utils

class TestDynamicFTI(unittest.TestCase):
    
    def test_lookup_schema(self):
        self.fail()
        
    def test_lookup_model_from_source(self):
        self.fail()
    
    def test_lookup_model_from_file_with_package(self):
        self.fail()
        
    def test_lookup_model_from_file_with_absolute_path(self):
        self.fail()
    
    def test_lookup_model_from_file_with_win32_absolute_path(self):
        self.fail()

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDynamicFTI))
    return suite
