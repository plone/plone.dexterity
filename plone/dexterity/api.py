# Convenience imports for users of the Dexterity system

# Base class for custom schema interfaces and grok directive to specify a
# model file.
from plone.supermodel.directives import Schema
from plone.supermodel.directives import model

# Further directives for Schema to influence form rendering
from plone.dexterity.directives.form import omitted, mode, widget, fieldset, order_before

# Base classes for custom content classes
from plone.dexterity.content import Item, Container

# Directives for specifying a meta type and add permission if registering
# custom classes
from plone.dexterity.directives.content import add_permission, meta_type, portal_type

# Behavior interfaces can either be marked with or be adaptable to this
# interface, in order to provide fields for the standard forms.
from plone.dexterity.interfaces import IFormFieldProvider
