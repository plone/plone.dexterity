from ..interfaces import IDexterityFTI
from ..utils import getAdditionalSchemata
from plone.autoform.view import WidgetsView
from zope.component import getUtility


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
        return getAdditionalSchemata(context=self.context)
