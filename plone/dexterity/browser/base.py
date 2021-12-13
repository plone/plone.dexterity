from ..i18n import MessageFactory as _
from ..interfaces import IDexterityFTI
from ..utils import getAdditionalSchemata
from plone.autoform.form import AutoExtensibleForm
from zope.component import getUtility


class DexterityExtensibleForm(AutoExtensibleForm):
    """Mixin class for Dexterity forms that support updatable fields"""

    default_fieldset_label = _("label_schema_default", default="Default")

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
        return getAdditionalSchemata(context=self.context, portal_type=self.portal_type)
