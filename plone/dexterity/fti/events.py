from zope.interface import noLongerProvides
from zope.interface.declarations import Implements

from zope.component.interfaces import IFactory
from zope.component import getUtility, queryUtility

from zope.app.component.hooks import getSiteManager

from zope.publisher.interfaces.browser import IBrowserView
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.app.container.interfaces import IAdding

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import ITemporarySchema

from plone.dexterity.factory import DexterityFactory
from plone.dexterity.browser.add import AddViewFactory

import plone.dexterity.schema
from plone.dexterity import utils

from Products.CMFCore.interfaces import ISiteRoot

def register(fti):
    site = getUtility(ISiteRoot)
    site_manager = getSiteManager(site)
    
    portal_type = fti.getId()
    
    fti_utility = queryUtility(IDexterityFTI, name=portal_type)
    if fti_utility is None:
        site_manager.registerUtility(fti, IDexterityFTI, portal_type)
        
    factory_utility = queryUtility(IFactory, name=fti.factory)
    if factory_utility is None:
        site_manager.registerUtility(DexterityFactory(portal_type), IFactory, fti.factory)
    
    addview_factory = site_manager.adapters.lookup((Implements(IAdding), Implements(IBrowserRequest)), IBrowserView, name=fti.factory)
    if addview_factory is None:
        site_manager.registerAdapter(factory=AddViewFactory(portal_type),
                                     provided=IBrowserView,
                                     required=(IAdding, IBrowserRequest),
                                     name=fti.factory,)
        
def unregister(fti):
    site = queryUtility(ISiteRoot)
    if site is None:
        return
    
    site_manager = getSiteManager(site)
    
    portal_type = fti.getId()
    
    site_manager.unregisterUtility(provided=IDexterityFTI, name=portal_type)
    site_manager.unregisterUtility(provided=IFactory, name=fti.factory)
    site_manager.unregisterAdapter(provided=IBrowserView, required=(IAdding, IBrowserRequest), name=fti.factory)
        
def fti_added(object, event):
    """When the FTI is created, install local components
    """
    
    register(event.object)
    
def fti_removed(object, event):
    """When the FTI is removed, uninstall local coponents
    """
    
    unregister(event.object)

def fti_renamed(object, event):
    """When the FTI is modified, ensure local components are still valid
    """
    
    if event.oldParent is None or event.newParent is None or event.oldName == event.newName:
        return
    
    unregister(event.objec)
    register(event.object)

def dynamic_fti_modified(object, event):
    """When a dynamic FTI is modified, re-sync the schema
    """
    
    fti = event.object
    
    schema_name = utils.portal_type_to_schema_name(fti.getId())
    schema = getattr(plone.dexterity.schema.generated, schema_name)
    
    model = fti.lookup_model()
    utils.sync_schema(model['schemata'][u""], schema, overwrite=True)
    
    if ITemporarySchema.providedBy(schema):
        noLongerProvides(schema, ITemporarySchema)