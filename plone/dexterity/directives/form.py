import zope.interface
import zope.component

import zope.interface.interface

import martian
import grokcore.security
import grokcore.view

import plone.dexterity.directives.content

from plone.z3cform import layout

from plone.dexterity.browser import add, edit

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from Products.CMFCore.interfaces import IFolderish

from Products.Five.security import protectClass
from Products.Five.browser.metaconfigure import page
from Globals import InitializeClass as initializeClass

class AddForm(add.DefaultAddForm):
    """Base class for grokked add forms
    """
    martian.baseclass()

class EditForm(edit.DefaultEditForm):
    """Base class for grokked edit forms
    """
    martian.baseclass()

class AddFormGrokker(martian.ClassGrokker):
    martian.component(AddForm)
    
    martian.directive(plone.dexterity.directives.content.portal_type)
    martian.directive(grokcore.view.layer, default=IDefaultBrowserLayer)
    martian.directive(grokcore.component.name, default=None)
    martian.directive(grokcore.security.require, name='permission', default='cmf.AddPortalContent')
    
    def execute(self, form, config, portal_type, layer, name, permission):
        
        if not portal_type:
            return False
        
        form.portal_type = portal_type
        factory = layout.wrap_form(form)
        
        if not name:
            name = "add-%s" % portal_type
        
        factory.__name__ = name
        
        page(config,
             name=name,
             permission=permission,
             for_=IFolderish,
             layer=layer,
             class_=factory)

        return True
        
class EditFormGrokker(martian.ClassGrokker):
    martian.component(EditForm)
    
    martian.directive(grokcore.component.context, default=None)
    martian.directive(grokcore.view.layer, default=IDefaultBrowserLayer)
    martian.directive(grokcore.component.name, default='edit')
    martian.directive(grokcore.security.require, name='permission', default='cmf.ModifyPortalContent')
    
    def execute(self, form, config, context, layer, name, permission):
        
        # Only grok if the context is an interface. We demand this so that the
        # form is more re-usable in case of type customisation.
        if not isinstance(context, zope.interface.interface.InterfaceClass):
            return False
        
        factory = layout.wrap_form(form)
        factory.__name__ = name
        
        page(config,
             name=name,
             permission=permission,
             for_=context,
             layer=layer,
             class_=factory)

        return True

__all__ = ('AddForm', 'EditForm',)