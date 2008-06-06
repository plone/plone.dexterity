from Products.CMFCore.browser.typeinfo import FactoryTypeInformationAddView

from plone.dexterity.fti.dynamic import DynamicFTI
from plone.dexterity.fti.concrete import ConcreteFTI

class DynamicFTIAddView(FactoryTypeInformationAddView):
    """Add view for the Dynamic FTI type
    """

    klass = DynamicFTI
    description = u'Factory Type Information for Dynamic Dexterity Content Types'

class ConcreteFTIAddView(FactoryTypeInformationAddView):
    """Add view for the Concrete FTI type
    """

    klass = ConcreteFTI
    description = u'Factory Type Information for Concrete Dexterity Content Types'