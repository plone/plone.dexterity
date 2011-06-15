from zope.component import getUtility

from plone.autoform.form import AutoExtensibleForm

from plone.dexterity.i18n import MessageFactory as _
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import getAdditionalSchemata


class DexterityExtensibleForm(AutoExtensibleForm):
    """Mixin class for Dexterity forms that support updatable fields
    """

    default_fieldset_label = _(u"Content")

    @property
    def description(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        return fti.Description()

    # AutoExtensibleForm contract

    @property
    def schema(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        return fti.lookupSchema()

    @property
    def additionalSchemata(self):
        return getAdditionalSchemata(context=self.context,
                                     portal_type=self.portal_type)
