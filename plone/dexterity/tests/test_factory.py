import unittest

from plone.dexterity import utils

class TestFactory(unittest.TestCase):
    
    def test_title(self):
        pass
    
    def test_description(self):
        pass
    
    def test_create_basic(self):
        pass
    
    def test_create_sets_portal_type(self):
        pass
    
    def test_create_initialises_schema(self):
        pass
    
    def test_create_does_not_apply_schema_twice(self):
        pass
    
    def test_create_does_not_overwrite_attributes(self):
        pass
        
    def test_create_initializes_security(self):
        pass
        
    def test_get_interfaces(self):
        pass

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFactory))
    return suite
