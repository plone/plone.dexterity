# Kick dynamic module factory
import schema

#
# Convenience API
#

import zope.deferredimport

# Base class for custom schema interfaces and grok directive to specify a model
# file. For example:
#
# >>> class IMyType(dexterity.Schema)
# ...     dexterity.model('myschema.xml')

zope.deferredimport.defineFrom('plone.supermodel.directives',
    'Schema', 'model',
)

# Further directives for Schema to influence form rendering. For example:
# 
# >>> class IMyType(dexterity.Schema)
# ...     dexterity.model('myschema.xml')
# ...     dexterity.widget(body='plone.app.z3cform.wysiwyg.WysiwygFieldWidget',)
# ...     dexterity.omitted('debug_field', 'extra_info',)
# ...     dexterity.fieldset('details', label=u"Details", fields=('alpha', 'beta',))
# ...     dexterity.mode(secret_field='hidden',)
# ...     dexterity.order_before(field1='field2')
# 
# Here, the 'body' field will use a WYSIWYG widget; 'debug_field' and
# 'extra_info' will be omitted from forms; the fields 'alpha' and 'beta' will
# go into a separate fieldset 'details'; the 'secret_field' field will be
# rendered as a hidden field; and 'field1' will be guaranteed to go before 
# field2

zope.deferredimport.defineFrom('plone.dexterity.directives.schema',
    'omitted', 'mode', 'widget', 'fieldset', 'order_before',
)

# Base classes for custom content classes and directives for specifying
# the low-level add permission. This is used if also set a meta_type. If
# no meta_type is set, the type is not registered as a Zope 2 style class.
# If a portal_type is set, a factory utility will be registered (if one is
# not registered already).
# 
# >>> class MyType(dexterity.Item):
# ...     implements(IMyType)
# ...     dexterity.add_permission('My add permission')
# ...     portal_type = 'my.type'
# ...     meta_type = 'my.type'
# 
# In most cases, you can omit meta_type and add_permission(). These are only
# necessary if you want to register a Zope 2 style class that can be created
# using Zope 2's meta type factory support. This is equivalent to calling
# <five:registerClass /> in ZCML.

zope.deferredimport.defineFrom('plone.dexterity.content',
    'Item', 'Container',
)
zope.deferredimport.defineFrom('plone.dexterity.directives.content',
    'add_permission',
)

# Base classes for custom add- and edit-forms, using z3c.form. For example:
# 
# >>> class AddForm(dexterity.AddForm):
# ...     portal_type = 'my.type'
# ...     fields = field.Fields(IMyType, omitReadOnly=True)
# 
# >>> class EditForm(dexterity.EditForm):
# ...     grok.context(IFSPage)
# ...     fields = fields
# 
# See the z3c.form documentation for more details. Note that for add forms,
# we have to specify the portal type to be added. The FTI should then be
# configured (with GenericSetup) to use an add_view_expr like:
# 
#  string:${folder_url}/@@add-dexterity-content/my.type
# 
# @@add-dexterity-content is a publish traverse view that will ensure the
# add form is correctly rendered.
# 
# For edit forms, the default name is 'edit', which can be overridden with
# grok.name().

zope.deferredimport.defineFrom('plone.dexterity.directives.form',
    'AddForm', 'EditForm',
)

# Behavior interfaces can either be marked with or be adaptable to this
# interface, in order to provide fields for the standard forms. For example:
# 
# >>> class IMyBehavior(dexterity.Schema):
# ...     dexterity.order_before(enabled='description')
# ...     dexterity.fieldset('tagging', label=u"Tagging", fields=['enabled', 'tags'])
# ...     
# ...     enabled = schema.Bool(title=u"Tagging enabled", default=True)
# ...     
# ...     tags = schema.List(title=u"Tags",
# ...                        value_type=schema.Choice(values=["Tag 1", "Tag 2", "Tag 3"]))
# ... 
# >>> alsoProvides(ITagging, dexterity.IFormFieldProvider)
# 
# When this behavior (and its associated factory) is registered, any type
# where the behavior (that uses the standard Dexterity form support) is 
# enabled will have the appropriate form fields inserted.

zope.deferredimport.defineFrom('plone.dexterity.interfaces',
    'IFormFieldProvider',
)