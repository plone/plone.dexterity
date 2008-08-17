import martian

from martian.error import GrokImportError

from zope.interface import implementedBy
from zope.schema import getFieldsInOrder

from zope.component import queryUtility
from zope.component import provideUtility

from zope.component.interfaces import IFactory
from zope.component.factory import Factory

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

        # 4. Set portal type if not set
        
        class_portal_type = getattr(class_, 'portal_type', None)
        if not class_portal_type:
            class_.portal_type = portal_type
        elif class_portal_type and class_portal_type != portal_type:
            raise GrokImportError(u"Inconsistent portal_type for class %s" % class_)
    
        # 5. Register factory if not already registered
        factory = queryUtility(IFactory, name=portal_type)
        if factory is None:
            provideUtility(Factory(class_), IFactory, portal_type)
    
__all__ = ('portal_type', 'meta_type', 'add_permission',)