import martian

from zope.interface import implementedBy
from zope.schema import getFieldsInOrder

from zope.component import getGlobalSiteManager, queryUtility
from zope.component import provideUtility, provideAdapter

from zope.component.interfaces import IFactory
from zope.component.factory import Factory

from plone.dexterity.browser.add import AddViewFactory

from zope.publisher.interfaces.browser import IBrowserView
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.app.container.interfaces import IAdding

from plone.supermodel.directives import Schema
from plone.dexterity.content import DexterityContent

from Products.Five.fiveconfigure import registerClass

class portal_type(martian.Directive):
    """Directive used to specify the portal type of an object
    """
    scope = martian.CLASS
    store = martian.ONCE
    default = None
    validate = martian.validateText
    
    def factory(self, portal_type):
        return portal_type

class meta_type(martian.Directive):
    """Directive used to specify the meta type of an object
    """
    scope = martian.CLASS
    store = martian.ONCE
    default = None
    validate = martian.validateText
    
    def factory(self, meta_type):
        return meta_type

class add_permission(martian.Directive):
    """Directive used to specify the add permission of an object
    """
    scope = martian.CLASS
    store = martian.ONCE
    default = u"cmf.AddPortalContent"
    validate = martian.validateText
    
    def factory(self, permission):
        return permission

class ContentGrokker(martian.ClassGrokker):
    martian.component(DexterityContent)

    martian.directive(meta_type)
    martian.directive(add_permission)
    martian.directive(portal_type)
    
    def execute(self, class_, config, portal_type, meta_type, add_permission, **kw):
        
        # 1. Register class if a meta type was specified. Most types
        # will probably not need this.
        if meta_type is not None:
            registerClass(config, class_, meta_type, add_permission)
        
        config.action(
                discriminator=('plone.dexterity.content', class_, portal_type),
                callable=register_content,
                args=(class_, portal_type,),
                order=9999,
                )
        
        return True
        
def register_content(class_, portal_type):

    # 2. Initialise properties from schema to their default values if 
    # they are not already on the class.
    for iface in implementedBy(class_).flattened():
        if iface.extends(Schema):
            for name, field in getFieldsInOrder(iface):
                if not hasattr(class_, name):
                    setattr(class_, name, field.default)

    # 3. Initialise security
    
    # TODO: Complete this with the other security work
    
    if portal_type:
    
        # 4. Register factory if not already registered
        factory = queryUtility(IFactory, name=portal_type)
        if factory is None:
            provideUtility(Factory(class_), IFactory, portal_type)
    
        # 5. Register add view if not already registered
        sm = getGlobalSiteManager()
        addview_adapters = [a for a in sm.registeredAdapters() if 
                                len(a.required) == 2 and a.required[0] == IAdding and a.name == portal_type]
        if len(addview_adapters) == 0:
            provideAdapter(factory=AddViewFactory(portal_type),
                           adapts=(IAdding, IBrowserRequest,),
                           provides=IBrowserView,
                           name=portal_type)

__all__ = ('portal_type', 'meta_type', 'add_permission',)