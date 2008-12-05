from zope.component import getUtility

from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform.formbase import AutoExtensibleForm

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import resolve_dotted_name

class DexterityExtensibleForm(AutoExtensibleForm):
    """Mixin class for Dexterity forms that support updatable fields
    """

    @property
    def description(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        return fti.description
    
    # AutoExtensibleForm contract
    
    @property
    def schema(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        return fti.lookup_schema() 
    
    @property
    def additional_schemata(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        for behavior_name in fti.behaviors:
            behavior_interface = resolve_dotted_name(behavior_name)
            if behavior_interface is not None:
                behavior_schema = IFormFieldProvider(behavior_interface, None)
                if behavior_schema is not None:
                    yield behavior_schema
