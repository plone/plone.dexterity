from zope.interface import implements
from zope.component import adapts, getUtility

from plone.behavior.interfaces import IBehavior
from plone.behavior.interfaces import IBehaviorAssignable

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IDexterityContent

class DexterityBehaviorAssignable(object):
    """Support plone.behavior behaviors stored in the FTI
    """
    
    implements(IBehaviorAssignable)
    adapts(IDexterityContent)
    
    def __init__(self, context):
        self.fti = getUtility(IDexterityFTI, name=context.portal_type)
    
    def supports(self, behavior_interface):
        for behavior in self.enumerate_behaviors():
            if behavior_interface in behavior.interface._implied:
                return True
        return False
        
    def enumerate_behaviors(self):
        for name in self.fti.behaviors:
            yield getUtility(IBehavior, name=name)