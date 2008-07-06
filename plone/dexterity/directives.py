import martian

from zope.interface import implementedBy
from zope.schema import getFieldsInOrder

from plone.supermodel.directives import Schema
from plone.dexterity.content import DexterityContent

from Products.Five.fiveconfigure import registerClass

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
    
    def execute(self, class_, config, meta_type, add_permission, **kw):
        
        # 1. Register class if a meta type was specified. Most types
        # will probably not need this.
        if meta_type is not None:
            registerClass(config, class_, meta_type, add_permission)
        
        # 2. Initialise properties from schema to their default values if 
        # they are not already on the class.
        for iface in implementedBy(class_).flattened():
            if iface.extends(Schema):
                for name, field in getFieldsInOrder(iface):
                    if not hasattr(class_, name):
                        setattr(class_, name, field.default)

        # 3. Initialise security
        
        # TODO: Complete this with the other security work
        
        return True