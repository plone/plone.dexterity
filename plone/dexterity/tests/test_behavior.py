import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.fti import DexterityFTI

from plone.dexterity.behavior import DexterityBehaviorAssignable

class IOne(Interface):
    pass

class ITwo(Interface):
    pass

class TestBehavior(MockTestCase):
    
    def test_supports(self):
        
        # Context mock
        context_dummy = self.create_dummy(portal_type=u"testtype")
        
        # FTI mock
        fti = DexterityFTI(u"testtype")
        fti.behaviors = [IOne.__identifier__]
        self.mock_utility(fti, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        assignable = DexterityBehaviorAssignable(context_dummy)
        
        self.assertEquals(True, assignable.supports(IOne))
        self.assertEquals(False, assignable.supports(ITwo))
        
        
    def test_enumerate(self):
        
        # Context mock
        context_dummy = self.create_dummy(portal_type=u"testtype")
        
        # FTI mock
        fti = DexterityFTI(u"testtype")
        fti.behaviors = [IOne.__identifier__]
        self.mock_utility(fti, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        assignable = DexterityBehaviorAssignable(context_dummy)
        
        self.assertEquals((IOne.__identifier__,), assignable.enumerate_behaviors())
    
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBehavior))
    return suite
