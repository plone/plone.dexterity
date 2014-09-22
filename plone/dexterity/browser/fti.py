# -*- coding: utf-8 -*-
from Products.CMFCore.browser.typeinfo import FactoryTypeInformationAddView
from plone.dexterity.fti import DexterityFTI


class FTIAddView(FactoryTypeInformationAddView):
    """Add view for the Dexterity FTI type
    """

    klass = DexterityFTI
    description = u'Factory Type Information for Dexterity Content Types'
