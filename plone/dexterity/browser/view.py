from zope.component import getUtility

from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform.view import WidgetsView

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import resolveDottedName

class DefaultView(WidgetsView):
    """The default view for Dexterity content. This uses a WidgetsView and
    renders all widgets in display mode.
    """
 
    @property
    def schema(self):
        fti = getUtility(IDexterityFTI, name=self.context.portal_type)
        return fti.lookupSchema()
    
    @property
    def additionalSchemata(self):
        fti = getUtility(IDexterityFTI, name=self.context.portal_type)
        for behavior_name in fti.behaviors:
            try:
                behavior_interface = resolveDottedName(behavior_name)
            except ValueError:
                continue
            if behavior_interface is not None:
                behavior_schema = IFormFieldProvider(behavior_interface, None)
                if behavior_schema is not None:
                    yield behavior_schema