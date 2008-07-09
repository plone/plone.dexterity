import martian

from zope.interface.interface import TAGGED_DATA

from plone.supermodel.directives import Schema

class FormMetadataStorage(object):
    """Stores a value in the 'dexterity.form' metadata format.
    """

    def set(self, locals_, directive, value):
        tags = locals_.setdefault(TAGGED_DATA, {}).setdefault(u"dexterity.form", {})
        tags.setdefault(directive.key, []).extend(value)

    def get(self, directive, component, default):
        return component.queryTaggedValue(u"dexterity.form", {}).get(directive.key, default)

    def setattr(self, context, directive, value):
        tags = context.queryTaggedValue(u"dexterity.form", {})
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
        # The work's really done in the directives
        return interface.extends(Schema)

__all__ = ('omitted', 'mode', 'widget', 'fieldset', 'order_before',)