from zope.component import getUtility

from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform.form import AutoExtensibleForm

from plone.dexterity.i18n import MessageFactory as _
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import resolveDottedName

class DexterityExtensibleForm(AutoExtensibleForm):
    """Mixin class for Dexterity forms that support updatable fields
    """

    default_fieldset_label = _(u"Content")

    @property
    def description(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        return fti.description
    
    # AutoExtensibleForm contract
    
    @property
    def schema(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        return fti.lookupSchema() 
    
    @property
    def additionalSchemata(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        for behavior_name in fti.behaviors:
            try:
                behavior_interface = resolveDottedName(behavior_name)
            except ValueError:
                continue
            if behavior_interface is not None:
                behavior_schema = IFormFieldProvider(behavior_interface, None)
                if behavior_schema is not None:
                    yield behavior_schema
