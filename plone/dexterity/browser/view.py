from zope.component import getUtility

from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform.view import WidgetsView

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import resolve_dotted_name

class DefaultView(WidgetsView):
    """The default view for Dexterity content. This uses a WidgetsView and
    renders all widgets in display mode.
    """
    
    @property
    def schema(self):
        fti = getUtility(IDexterityFTI, name=self.context.portal_type)
        return fti.lookup_schema()
    
    @property
    def additional_schemata(self):
        fti = getUtility(IDexterityFTI, name=self.context.portal_type)
        for behavior_name in fti.behaviors:
            try:
                behavior_interface = resolve_dotted_name(behavior_name)
            except ValueError:
                continue
            if behavior_interface is not None:
                behavior_schema = IFormFieldProvider(behavior_interface, None)
                if behavior_schema is not None:
                    yield behavior_schema