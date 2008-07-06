from persistent import Persistent
from zope.interface import implements
from zope.component import adapts, getUtility, createObject

from zope.app.container.interfaces import IAdding

from zope.publisher.interfaces.browser import IBrowserView
from zope.publisher.interfaces.browser import IBrowserRequest

from z3c.form import form, field, button, group, subform, adding
from plone.z3cform import base

from z3c.form.interfaces import INPUT_MODE

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity import MessageFactory as _
from plone.dexterity.utils import resolve_dotted_name

from plone.supermodel.model import METADATA_KEY

from Acquisition import aq_inner, aq_parent
from AccessControl import Unauthorized

from Products.statusmessages.interfaces import IStatusMessage

class AddViewFactory(Persistent):
    """Factory for add views - will be registered as a local adapter factory
    """
    
    implements(IBrowserView)
    adapts(IAdding, IBrowserRequest)
    
    def __init__(self, portal_type):
        self.portal_type = portal_type
        
    def __call__(self, context, request):
        return DefaultAddView(context, request, self.portal_type)
        
class DefaultAddForm(adding.AddForm):
    
    def __init__(self, context, request, portal_type):
        super(DefaultAddForm, self).__init__(context, request)
        self.portal_type = portal_type
    
    @property
    def fields(self):
        
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        
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
    
    def create(self, data):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        content = createObject(fti.factory)
        form.applyChanges(self, content, data)
        return content
        
    @button.buttonAndHandler(_('Save'), name='save')
    def handleAdd(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        obj = self.createAndAdd(data)
        if obj is not None:
            # mark only as finished if we get the new object
            self._finishedAdd = True
    
    @button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Add New Item operation cancelled"), "info")
        adding = aq_inner(self.context)
        container = aq_parent(adding)
        self.request.response.redirect(container.absolute_url()) 

    def updateActions(self):
        super(DefaultAddForm, self).updateActions()
        self.actions["save"].addClass("context")
        self.actions["cancel"].addClass("standalone")

class DefaultAddView(base.FormWrapper):
    
    def __init__(self, context, request, portal_type, form=None):
        super(DefaultAddView, self).__init__(context, request)
        
        fti = getUtility(IDexterityFTI, name=portal_type)
        self.__name__ = fti.factory
        
        if form is None:
            form = DefaultAddForm
        
        self.form = form
        self.portal_type = portal_type
        
        self.request['disable_border'] = True
    
    def __call__(self):
        context = aq_inner(self.context)
        container = aq_inner(context.context)
        
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        if not fti.isConstructionAllowed(container):
            raise Unauthorized("You are not allowed to access the add view for %s because you lack the permission %s" % (self.portal_type, fti.add_permission))

        return super(DefaultAddView, self).__call__()
    
    def render_form(self):
        return self.form(self.context.aq_inner, self.request, self.portal_type)()
    
    @property
    def label(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        type_name = fti.title
        return _(u"Add ${name}", mapping={'name': type_name})