from zope.interface import implements
from zope.component import queryUtility

from zope.annotation import IAttributeAnnotatable

from grokcore.component.interfaces import IContext

from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityItem
from plone.dexterity.interfaces import IDexterityContainer
from plone.dexterity.interfaces import IDexterityFTI

from zope.app.container.contained import Contained

from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware

from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin

from plone.folder.ordered import OrderedBTreeFolderBase

class DexterityContent(PortalContent, DefaultDublinCoreImpl, Contained):
    """Base class for content, primarily to support isinstance() and the 
    grokker in directives.py
    """
    implements(IDexterityContent, IAttributeAnnotatable, IContext)
    
    # portal_type must be set by factory or derived class
    meta_type = portal_type = None
    
    def __getattr__(self, name):
        
        # attribute was not found; try to look it up in the schema and return
        # a default
        
        fti = self.__dict__.get('_v_fti_utility', None)
        if fti is None:
            self._v_fti_utility = fti = queryUtility(IDexterityFTI, name=self.portal_type)
        if fti is not None:
            schema = fti.lookup_schema()
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