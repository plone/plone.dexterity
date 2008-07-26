from persistent import Persistent
from zope.interface import implements
from zope.component import adapts, getUtility, createObject

from zope.app.container.interfaces import IAdding

from zope.publisher.interfaces.browser import IBrowserView
from zope.publisher.interfaces.browser import IBrowserRequest

from z3c.form import form, button, adding
from plone.z3cform import layout

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity import MessageFactory as _

from plone.dexterity.browser.base import DexterityExtensibleForm

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
        
class DefaultAddForm(DexterityExtensibleForm, adding.AddForm):
    
    def __init__(self, context, request, portal_type=None):
        super(DefaultAddForm, self).__init__(context, request)
        
        if portal_type is not None:
            self.portal_type = portal_type
    
    def create(self, data):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        content = createObject(fti.factory)
        form.applyChanges(self, content, data)
        for group in self.groups:
            form.applyChanges(group, content, data)
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

class DefaultAddView(layout.FormWrapper):
    form = DefaultAddForm
    
    def __init__(self, context, request, portal_type=None):
        super(DefaultAddView, self).__init__(context, request)
        
        # We allow subclasses to sepcify a form where the portal_type is
        # set on the form rather than passed in as an argument
        if portal_type is None:
            portal_type = getattr(self.form, 'portal_type', None)
            
        if portal_type is None:
            raise ValueError("An add view must either be passed a portal_type, or have a form that specifies a portal_type") 

        fti = getUtility(IDexterityFTI, name=portal_type)
        self.__name__ = fti.factory
        self.portal_type = portal_type
    
    def __call__(self):
        self.request['disable_border'] = True
        
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