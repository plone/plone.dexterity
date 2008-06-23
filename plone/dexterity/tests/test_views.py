import unittest

from plone.dexterity import utils

class TestAddView(unittest.TestCase):
    
    def test_factory(self):
        pass
    
    def test_form_fields(self):
        pass
        
    def test_form_create(self):
        pass
    
    def test_call_checks_fti_is_allowed(self):
        pass
        
    def test_label(self):
        pass
    
class TestEditView(unittest.TestCase):
    
    def test_form_fields(self):
        pass
        
    def test_label(self):
        pass
    
class TestDefaultView(unittest.TestCase):
    
    def test_fields(self):
        pass
        
    def test_ignored(self):
        pass
    
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAddView))
    suite.addTest(unittest.makeSuite(TestEditView))
    suite.addTest(unittest.makeSuite(TestDefaultView))
    return suite
