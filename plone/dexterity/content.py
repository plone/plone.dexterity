from Acquisition import Explicit, aq_parent

from zope.interface import implements
from zope.interface.declarations import Implements
from zope.interface.declarations import implementedBy
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import ObjectSpecificationDescriptor

from zope.annotation import IAttributeAnnotatable

from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityItem
from plone.dexterity.interfaces import IDexterityContainer

from plone.dexterity.schema import schema_cache

from zope.app.container.contained import Contained

from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.utils import _checkPermission as checkPerm

from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin

from plone.folder.ordered import OrderedBTreeFolderBase

class FTIAwareSpecification(ObjectSpecificationDescriptor):
    """A __providedBy__ decorator that returns the interfaces provided by
    the object, plus the schema interface set in the FTI.
    """

    def __get__(self, inst, cls=None):
        if inst is None:
            return getObjectSpecification(cls)
        
        schema = self._get_schema(inst)
        
        spec = getattr(inst, '__provides__', None)
        if spec is None:
            spec = implementedBy(cls)
        
        if schema is not None and schema not in spec:
            spec = Implements(schema) + spec
        
        return spec

    def _get_schema(self, inst):
        portal_type = getattr(inst, 'portal_type', None)
        if portal_type is not None:
            try:
                return schema_cache.get(portal_type)
            except (ValueError, AttributeError,):
                pass
        return None

class AttributeValidator(Explicit):
    
    def __call__(self, name, value):

        # Short circuit for things like views or viewlets
        if name == '':
            return 1
        
        context = aq_parent(self)
        
        schema = self._get_schema(context)
        if schema is None:
            return 1
        
        info = schema.queryTaggedValue(u'dexterity.security', {})
        
        if name not in info:
            return 1
        
        perm = info['name'].get('read-permission', None)
        if perm is None:
            return 1
        
        if checkPerm(perm, context):
            return 1
        
        return 0
    
    def _get_schema(self, inst):
        portal_type = getattr(inst, 'portal_type', None)
        if portal_type is not None:
            try:
                return schema_cache.get(portal_type)
            except (ValueError, AttributeError,):
                pass
        return None

class DexterityContent(PortalContent, DefaultDublinCoreImpl, Contained):
    """Base class for Dexterity content
    """
    implements(IDexterityContent, IAttributeAnnotatable)
    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()
    
    # portal_type is set by the add view and/or factory
    portal_type = None
    
    def __getattr__(self, name):
        
        # attribute was not found; try to look it up in the schema and return
        # a default
        
        schema = schema_cache.get(self.portal_type)
        if schema is not None:
            field = schema.get(name, None)
            if field is not None:
                return field.default
        
        raise AttributeError(name)

# XXX: It'd be nice to reduce the number of base classes here

class Item(BrowserDefaultMixin, DexterityContent):
    """A non-containerish, CMFish item
    """
    
    implements(IDexterityItem)
    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()
    
    isPrincipiaFolderish = 0
    
    def __init__(self, id=None, **kwargs):
        PortalContent.__init__(self, id, **kwargs)
        DefaultDublinCoreImpl.__init__(self, **kwargs)
        
        if id is not None:
            self.id = id

class Container(BrowserDefaultMixin, CMFCatalogAware, OrderedBTreeFolderBase, DexterityContent):
    """Base class for folderish items
    """
    
    implements(IDexterityContainer)
    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()
    
    isPrincipiaFolderish = 1

    def __init__(self, id=None, **kwargs):
        OrderedBTreeFolderBase.__init__(self, id, **kwargs)
        DefaultDublinCoreImpl.__init__(self, **kwargs)
        
        if id is not None:
            self.id = id

def reindexOnModify(content, event):
    """When an object is modified, re-index it in the catalog
    """
    
    if event.object is not content:
        return
        
    content.reindexObject(idxs=getattr(event, 'descriptions', []))