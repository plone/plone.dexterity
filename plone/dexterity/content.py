from Acquisition import Explicit, aq_parent

from zope.component import queryUtility

from zope.interface import implements
from zope.interface.declarations import Implements
from zope.interface.declarations import implementedBy
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import ObjectSpecificationDescriptor

from zope.security.interfaces import IPermission

from zope.annotation import IAttributeAnnotatable

from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityItem
from plone.dexterity.interfaces import IDexterityContainer

from plone.dexterity.schema import schema_cache

from zope.app.container.contained import Contained

from AccessControl import getSecurityManager

from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware

from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin

from plone.folder.ordered import CMFOrderedBTreeFolderBase

from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.supermodel.utils import merged_tagged_value_dict

class FTIAwareSpecification(ObjectSpecificationDescriptor):
    """A __providedBy__ decorator that returns the interfaces provided by
    the object, plus the schema interface set in the FTI.
    """

    def __get__(self, inst, cls=None):
        
        if inst is None:
            return getObjectSpecification(cls)
        
        cache = getattr(inst, '_v__providedBy__', None)
        portal_type = getattr(inst, 'portal_type', None)
        
        fti_counter = -1
        if portal_type is not None:
            fti_counter = schema_cache.counter(portal_type)
        
        # See if we have a valid cache
        if cache is not None and portal_type is not None:
            cached_mtime, cached_fti_counter, cached_spec = cache
            if not inst._p_changed and inst._p_mtime == cached_mtime and fti_counter == cached_fti_counter:
                return cached_spec
        
        # Get interfaces directly provided by the instance
        
        spec = getattr(inst, '__provides__', None)
        if spec is None:
            spec = implementedBy(cls)
        
        # Add the schema from the FTI
        
        schema = self._get_schema(inst)
        if schema is not None and schema not in spec:
            spec = Implements(schema) + spec
        
        # Cache the results and return
        
        # NOTE: The schema may be none if we can't find a schema for this
        # type. This could happen if we're called before traversal, for
        # example. In this case, don't cache, as we need to catch the schema
        # the next time around.
        
        if portal_type is not None and schema is not None:
            inst._v__providedBy__ = inst._p_mtime, schema_cache.counter(portal_type), spec
        
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
    """Decide whether attributes should be accessible. This is set as the
    __allow_access_to_unprotected_subobjects__ variable in Dexterity's content
    classes.
    """
    
    def __call__(self, name, value):

        # Short circuit for things like views or viewlets
        if name == '':
            return 1
        
        context = aq_parent(self)
        
        schema = self._get_schema(context)
        if schema is None:
            return 1
        
        info = merged_tagged_value_dict(schema, READ_PERMISSIONS_KEY)
        
        if name not in info:
            return 1
        
        permission = queryUtility(IPermission, name=info[name])
        if permission is not None:
            return getSecurityManager().checkPermission(permission.title, context)
        
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

class Container(BrowserDefaultMixin, CMFCatalogAware, CMFOrderedBTreeFolderBase, DexterityContent):
    """Base class for folderish items
    """
    
    implements(IDexterityContainer)
    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()
    
    isPrincipiaFolderish = 1

    def __init__(self, id=None, **kwargs):
        CMFOrderedBTreeFolderBase.__init__(self, id, **kwargs)
        DefaultDublinCoreImpl.__init__(self, **kwargs)
        
        if id is not None:
            self.id = id

def reindexOnModify(content, event):
    """When an object is modified, re-index it in the catalog
    """
    
    if event.object is not content:
        return
        
    content.reindexObject(idxs=getattr(event, 'descriptions', []))