from zope.component import getUtility

from z3c.form import form, field, button, group, subform
from plone.z3cform import base

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity import MessageFactory as _

from plone.dexterity.utils import resolve_dotted_name

class DefaultEditForm(form.EditForm):
    
    @property
    def fields(self):
        # TODO: Support plone.behavior-provided fields and custom widgets

        portal_type = self.context.portal_type
        fti = getUtility(IDexterityFTI, name=portal_type)
        
        model = fti.lookup_model()
        
        schema = model.schema
        metadata = model.metadata
        
        fields = field.Fields(schema, omitReadOnly=True)
        
        widget_data = metadata.get('widget', {})
        for field_name, widget_name in widget_data.items():
            if field_name in fields:
                widget_factory = resolve_dotted_name(widget_name)
                if widget_factory is not None:
                    fields[field_name].widgetFactory = widget_factory
        
        return fields

class DefaultEditView(base.FormWrapper):
    form = DefaultEditForm
    
    @property
    def label(self):
        portal_type = self.context.portal_type
        fti = getUtility(IDexterityFTI, name=portal_type)
        type_name = fti.title
        return _(u"Edit ${name}", mapping={'name': type_name})