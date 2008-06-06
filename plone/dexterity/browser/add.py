from persistent import Persistent
from zope.interface import implements
from zope.component import adapts, getUtility, createObject

from zope.app.container.interfaces import IAdding

from zope.publisher.interfaces.browser import IBrowserView
from zope.publisher.interfaces.browser import IBrowserRequest

from z3c.form import form, field, button, group, subform, adding
from plone.z3cform import base

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity import MessageFactory as _

from Acquisition import aq_inner
from AccessControl import Unauthorized
from AccessControl import getSecurityManager

# TODO: Add view needs to be protected by fti.add_permission dynamically

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
        # TODO: Support plone.behavior-provided fields
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        schema = fti.lookup_schema()        
        return field.Fields(schema)    
    
    def create(self, data):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        content = createObject(fti.factory)
        form.applyChanges(self, content, data)
        return content

class DefaultAddView(base.FormWrapper):
    
    def __init__(self, context, request, portal_type, form=None):
        super(DefaultAddView, self).__init__(context, request)
        
        fti = getUtility(IDexterityFTI, name=portal_type)
        self.__name__ = fti.factory
        
        if form is None:
            form = DefaultAddForm
        
        self.form = form
        self.portal_type = portal_type
    
    def render_form(self):
        return self.form(self.context.aq_inner, self.request, self.portal_type)()
    
    @property
    def label(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        type_name = fti.title
        return _(u"Add ${name}", mapping={'name': type_name})