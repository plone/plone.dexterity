import unittest

from plone.dexterity import utils

class TestConcreteFTI(unittest.TestCase):
    
    def test_lookup_schema(self):
        pass
    
    def test_lookup_model(self):
        pass

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestConcreteFTI))
    return suite
