import unittest

from plone.dexterity import schema

class TestSchemaModuleFactory(unittest.TestCase):
    
    def test_default_schema(self):
        self.fail()
        
    def test_named_schema(self):
        self.fail()
        
    def test_without_fti(self):
        self.fail()

class TestSchemaPolicy(unittest.TestCase):
        
    def test_bases(self):
        self.fail()
        
    def test_naming(self):
        self.fail()

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSchemaModuleFactory))
    suite.addTest(unittest.makeSuite(TestSchemaPolicy))
    return suite
