from plone.dexterity.browser.base import DexterityExtensibleForm
from plone.dexterity.events import EditBegunEvent
from plone.dexterity.events import EditCancelledEvent
from plone.dexterity.events import EditFinishedEvent
from plone.dexterity.i18n import MessageFactory as _
from plone.dexterity.interfaces import IDexterityEditForm
from plone.dexterity.interfaces import IDexterityFTI
from plone.registry.interfaces import IRegistry
from plone.z3cform import layout
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import form
from zope.component import getUtility
from zope.event import notify
from zope.interface import classImplements


class DefaultEditForm(DexterityExtensibleForm, form.EditForm):

    success_message = _("Changes saved")

    @button.buttonAndHandler(_("Save"), name="save")
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(self.success_message, "info")
        self.request.response.redirect(self.nextURL())
        notify(EditFinishedEvent(self.context))

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_("Edit cancelled"), "info")
        self.request.response.redirect(self.nextURL())
        notify(EditCancelledEvent(self.context))

    def nextURL(self):
        view_url = self.context.absolute_url()
        portal_type = getattr(self, "portal_type", None)
        if portal_type is not None:
            registry = getUtility(IRegistry)
            use_view_action = registry.get(
                "plone.types_use_view_action_in_listings", []
            )
            if portal_type in use_view_action:
                view_url = view_url + "/view"
        return view_url

    def update(self):
        self.portal_type = self.context.portal_type
        super().update()

        # fire the edit begun only if no action was executed
        if len(self.actions.executedActions) == 0:
            notify(EditBegunEvent(self.context))

    def updateActions(self):
        super().updateActions()

        if "save" in self.actions:
            self.actions["save"].addClass("success")

        if "cancel" in self.actions:
            self.actions["cancel"].addClass("secondary")

    @property
    def fti(self):
        return getUtility(IDexterityFTI, name=self.portal_type)

    @property
    def label(self):
        type_name = self.fti.Title()
        return _("Edit ${name}", mapping={"name": type_name})


DefaultEditView = layout.wrap_form(DefaultEditForm)
classImplements(DefaultEditView, IDexterityEditForm)
