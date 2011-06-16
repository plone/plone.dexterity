from zope.component import getUtility
from zope.event import notify

from z3c.form import form, button
from plone.z3cform import layout

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.i18n import MessageFactory as _
from plone.dexterity.events import EditBegunEvent
from plone.dexterity.events import EditCancelledEvent
from plone.dexterity.events import EditFinishedEvent

from plone.dexterity.browser.base import DexterityExtensibleForm

from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage


class DefaultEditForm(DexterityExtensibleForm, form.EditForm):
    
    @button.buttonAndHandler(_(u'Save'), name='save')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved"), "info")
        self.request.response.redirect(self.nextURL())
        notify(EditFinishedEvent(self.context))
    
    @button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Edit cancelled"), "info")
        self.request.response.redirect(self.nextURL())
        notify(EditCancelledEvent(self.context))

    def nextURL(self):
        view_url = self.context.absolute_url()
        portal_properties = getToolByName(self, 'portal_properties', None)
        if portal_properties is not None:
            site_properties = getattr(portal_properties, 'site_properties', None)
            portal_type = self.portal_type
            if site_properties is not None and portal_type is not None:
                use_view_action = site_properties.getProperty('typesUseViewActionInListings', ())
                if portal_type in use_view_action:
                    view_url = view_url + '/view'
        return view_url
    
    def update(self):
        self.portal_type = self.context.portal_type
        super(DefaultEditForm, self).update()
        
        # fire the edit begun only if no action was executed
        if len(self.actions.executedActions) == 0:
            notify(EditBegunEvent(self.context))

    def updateActions(self):
        super(DefaultEditForm, self).updateActions()
        
        if 'save' in self.actions:
            self.actions["save"].addClass("context")
        
        if 'cancel' in self.actions:
            self.actions["cancel"].addClass("standalone")

    @property
    def fti(self):
        return getUtility(IDexterityFTI, name=self.portal_type)
    
    @property
    def label(self):
        type_name = self.fti.Title()
        return _(u"Edit ${name}", mapping={'name': type_name})
        
DefaultEditView = layout.wrap_form(DefaultEditForm)
