import unittest

from plone.dexterity import utils

class TestFTI(unittest.TestCase):
    
    def test_lookup_schema_with_concrete_schema(self):
        pass

    def test_lookup_schema_with_dynamic_schema(self):
        pass

    def test_lookup_model_from_string(self):
        pass
    
    def test_lookup_model_from_file_with_package(self):
        pass
        
    def test_lookup_model_from_file_with_absolute_path(self):
        pass
    
    def test_lookup_model_from_file_with_win32_absolute_path(self):
        pass

    def test_lookup_model_with_schema_only(self):
        pass

    def test_lookup_model_failure(self):
        pass

    def test_components_registered_on_add(self):
        pass
        
    def test_components_unregistered_on_delete(self):
        pass
    
    def test_components_reregistered_on_rename(self):
        pass
        
    def test_dynamic_schema_refreshed_on_modify(self):
        pass
        
    def test_concrete_schema_not_refreshed_on_modify(self):
        pass
    
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFTI))
    return suite
