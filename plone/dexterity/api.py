# Convenience imports for users of the Dexterity system

# Base class for custom schema interfaces and grok directive to specify a
# model file.
from plone.supermodel.directives import Schema
from plone.supermodel.directives import model

# Base classes for custom content classes
from plone.dexterity.content import Item, Container

# Directives for specifying a meta type and add permission if registering
# custom classes
from plone.dexterity.directives import add_permission, meta_type

# Standard WYSIWYG widget for zope.schema.Text fields
from plone.z3cform.wysiwyg.widget import WysiwygFieldWidget as WysiwygWidget