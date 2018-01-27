# -*- coding: utf-8 -*-
from persistent import Persistent
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IDexterityFactory
from plone.dexterity.utils import resolveDottedName
from zope.component import getUtility
from zope.component.factory import Factory
from zope.interface import implementer
from zope.interface.declarations import Implements


@implementer(IDexterityFactory)
class DexterityFactory(Persistent, Factory):
    """A factory for Dexterity content.
    """

    def __init__(self, portal_type):
        self.portal_type = portal_type

    @property
    def title(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        return fti.title

    @property
    def description(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        return fti.description

    def __call__(self, *args, **kw):
        fti = getUtility(IDexterityFTI, name=self.portal_type)

        klass = resolveDottedName(fti.klass)
        if klass is None or not callable(klass):
            raise ValueError(
                "Content class %s set for type %s is not valid" %
                (fti.klass, self.portal_type)
            )

        try:
            obj = klass(*args, **kw)
        except TypeError as e:
            raise ValueError(
                "Error whilst constructing content for %s using class %s: %s"
                % (self.portal_type, fti.klass, str(e))
            )

        # Set portal_type if not set, but avoid creating an instance variable
        # if possible
        if getattr(obj, 'portal_type', '') != self.portal_type:
            obj.portal_type = self.portal_type

        return obj

    def getInterfaces(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        spec = Implements(fti.lookupSchema())
        spec.__name__ = self.portal_type
        return spec

    def __repr__(self):
        return '<%s for %s>' % (self.__class__.__name__, self.portal_type)
