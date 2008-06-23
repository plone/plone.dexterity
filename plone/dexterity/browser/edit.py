from zope.component import getUtility

from z3c.form import form, field, button, group, subform
from plone.z3cform import base

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity import MessageFactory as _

class DefaultEditForm(form.EditForm):
    
    @property
    def fields(self):
        # TODO: Support plone.behavior-provided fields
        portal_type = self.context.portal_type
        fti = getUtility(IDexterityFTI, name=portal_type)
        schema = fti.lookup_schema()
        return field.Fields(schema)

class DefaultEditView(base.FormWrapper):
    form = DefaultEditForm
    
    @property
    def label(self):
        portal_type = self.context.portal_type
        fti = getUtility(IDexterityFTI, name=portal_type)
        type_name = fti.title
        return _(u"Edit ${name}", mapping={'name': type_name})