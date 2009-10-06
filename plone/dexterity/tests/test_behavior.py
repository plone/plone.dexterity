import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface

from plone.behavior.interfaces import IBehavior

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.fti import DexterityFTI

from plone.dexterity.behavior import DexterityBehaviorAssignable

class IOne(Interface):
    pass

class ITwo(Interface):
    pass

class IThree(Interface):
    pass

class IFour(IThree):
    pass

class TestBehavior(MockTestCase):
    
    def test_supports(self):
        
        # Context mock
        context_dummy = self.create_dummy(portal_type=u"testtype")
        
        # Behavior mock
        behavior_dummy_1 = self.create_dummy(interface = IOne)
        self.mock_utility(behavior_dummy_1, IBehavior, name=IOne.__identifier__)
        behavior_dummy_4 = self.create_dummy(interface = IFour)
        self.mock_utility(behavior_dummy_4, IBehavior, name=IFour.__identifier__)
        
        # FTI mock
        fti = DexterityFTI(u"testtype")
        fti.behaviors = [IOne.__identifier__, IFour.__identifier__]
        self.mock_utility(fti, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        assignable = DexterityBehaviorAssignable(context_dummy)
        
        self.assertEquals(True, assignable.supports(IOne))
        self.assertEquals(False, assignable.supports(ITwo))
        self.assertEquals(True, assignable.supports(IThree))
        self.assertEquals(True, assignable.supports(IFour))

    def test_enumerate(self):
        
        # Context mock
        context_dummy = self.create_dummy(portal_type=u"testtype")
        
        # Behavior mock
        behavior_dummy = self.create_dummy()
        self.mock_utility(behavior_dummy, IBehavior, name=IOne.__identifier__)
        
        # FTI mock
        fti = DexterityFTI(u"testtype")
        fti.behaviors = [IOne.__identifier__]
        self.mock_utility(fti, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        assignable = DexterityBehaviorAssignable(context_dummy)
        
        self.assertEquals([behavior_dummy], list(assignable.enumerateBehaviors()))
    
def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
