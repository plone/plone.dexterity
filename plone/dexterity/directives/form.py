import martian

from zope.interface.interface import TAGGED_DATA

from plone.supermodel.directives import Schema

TEMP_KEY = '__form_directive_values__'

class FormMetadataStorage(object):
    """Stores a value in the 'dexterity.form' metadata format.
    """

    def set(self, locals_, directive, value):
        tags = locals_.setdefault(TAGGED_DATA, {}).setdefault(TEMP_KEY, {})
        tags.setdefault(directive.key, []).extend(value)

    def get(self, directive, component, default):
        return component.queryTaggedValue(TEMP_KEY, {}).get(directive.key, default)

    def setattr(self, context, directive, value):
        tags = context.queryTaggedValue(TEMP_KEY, {})
        tags.setdefault(directive.key, []).extend(value)

FORM_METADATA = FormMetadataStorage()        

class omitted(martian.Directive):
    
    scope = martian.CLASS
    store = FORM_METADATA
    
    key = u"omitted"
    
    def factory(self, *args):
        return [(a, "true") for a in args]

class mode(martian.Directive):
    
    scope = martian.CLASS
    store = FORM_METADATA
    
    key = u"modes"
    
    def factory(self, **kw):
        return kw.items()

class widget(martian.Directive):
    
    scope = martian.CLASS
    store = FORM_METADATA
    
    key = u"widgets"
    
    def factory(self, **kw):
        items = []
        for field_name, widget in kw.items():
            if not isinstance(widget, basestring):
                widget = "%s.%s" % (widget.__module__, widget.__name__)
            items.append((field_name, widget))
        return items
        
class fieldset(martian.Directive):
    
    scope = martian.CLASS
    store = FORM_METADATA
    
    key = u"fieldsets"
    
    def factory(self, **kw):
        return kw.items()
        
class order_before(martian.Directive):
    
    scope = martian.CLASS
    store = FORM_METADATA
    
    key = u"moves"
    
    def factory(self, **kw):
        return kw.items()

class SchemaGrokker(martian.InstanceGrokker):
    martian.component(Schema.__class__)
    
    martian.directive(omitted)
    martian.directive(mode)
    martian.directive(widget)
    martian.directive(fieldset)
    martian.directive(order_before)
    
    def execute(self, interface, config, **kw):
        
        if not interface.extends(Schema):
            return False
            
        # Copy from temporary to real value
        directive_supplied = interface.queryTaggedValue(TEMP_KEY, None)
        if directive_supplied is None:
            return False
        
        real = interface.queryTaggedValue(u'dexterity.form', {})
        for k, v in directive_supplied.items():
            real.setdefault(k, []).extend(v)
        
        if not real:
            return False
            
        interface.setTaggedValue(u'dexterity.form', real)
        interface.setTaggedValue(TEMP_KEY, None)
        
        return True

__all__ = ('omitted', 'mode', 'widget', 'fieldset', 'order_before',)