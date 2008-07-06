from zope.component import getUtility

from z3c.form import form, field, button, group, subform

from z3c.form.interfaces import INPUT_MODE
from z3c.form.util import expandPrefix

from plone.z3cform import base

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity import MessageFactory as _

from plone.dexterity.utils import resolve_dotted_name

from plone.supermodel.model import METADATA_KEY

from Products.statusmessages.interfaces import IStatusMessage

class DefaultEditForm(form.EditForm):
    
    @property
    def fields(self):
        
        portal_type = self.context.portal_type
        fti = getUtility(IDexterityFTI, name=portal_type)
        
        schema = fti.lookup_schema()
        
        metadata = schema.queryTaggedValue(METADATA_KEY, {})
        widget_data = metadata.get('widget', {}).copy()
        
        fields = field.Fields(schema, omitReadOnly=True)
        
        # Add fields from behaviors and record their widget hints, if any
        for behavior_name in fti.behaviors:
            behavior_interface = resolve_dotted_name(behavior_name)
            if behavior_interface is not None:
                fields += field.Fields(behavior_interface,
                                       omitReadOnly=True,
                                       prefix=behavior_name)
                behavior_metadata = behavior_interface.queryTaggedValue(METADATA_KEY, {})
                behavior_widget_data = behavior_metadata.get('widget', {})
                for field_name, widget_name in behavior_widget_data.items():
                    widget_data[expandPrefix(behavior_name) + field_name] = widget_name
        
        # Set widget factories if possible
        for field_name, widget_name in widget_data.items():
            if field_name in fields:
                widget_factory = resolve_dotted_name(widget_name)
                if widget_factory is not None:
                    fields[field_name].widgetFactory[INPUT_MODE] = widget_factory
        
        return fields

    @button.buttonAndHandler(_(u'Save'), name='save')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        changes = self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved"), "info")
        self.request.response.redirect(self.context.absolute_url())
    
    @button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Edit cancelled"), "info")
        self.request.response.redirect(self.context.absolute_url()) 

    def updateActions(self):
        super(DefaultEditForm, self).updateActions()
        self.actions["save"].addClass("context")
        self.actions["cancel"].addClass("standalone")

class DefaultEditView(base.FormWrapper):
    form = DefaultEditForm
    
    @property
    def label(self):
        portal_type = self.context.portal_type
        fti = getUtility(IDexterityFTI, name=portal_type)
        type_name = fti.title
        return _(u"Edit ${name}", mapping={'name': type_name})