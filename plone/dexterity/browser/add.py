from zope.component import getUtility, createObject

from z3c.form import form, button
from plone.z3cform import layout

from zope.app.container.interfaces import INameChooser

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.i18n import MessageFactory as _

from plone.dexterity.browser.base import DexterityExtensibleForm

from Acquisition import aq_inner, aq_base
from Acquisition.interfaces import IAcquirer
from AccessControl import Unauthorized

from Products.statusmessages.interfaces import IStatusMessage

class DefaultAddForm(DexterityExtensibleForm, form.AddForm):
    """Standard add form, which is warpped by DefaultAddView (see below).
    
    This form is capable of rendering the fields of any Dexterity schema,
    including behaviours. To do that, needs to know the portal_type, which
    can be set as a class variable (in a subclass), or on a created instance.
    
    By default, the DefaultAddView (see below) will set the portal_type based
    on the FTI.
    """
    
    portal_type = None
    immediate_view = None
    
    def __init__(self, context, request):
        super(DefaultAddForm, self).__init__(context, request)
        self.request['disable_border'] = True
    
    # API
    
    def create(self, data):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        
        container = aq_inner(self.context)
        content = createObject(fti.factory)
        
        # Note: The factory may have done this already, but we want to be sure
        # that the created type has the right portal type. It is possible
        # to re-define a type through the web that uses the factory from an
        # existing type, but wants a unique portal_type!

        if hasattr(content, '_setPortalTypeName'):
            content._setPortalTypeName(fti.getId())
        
        # Acquisition wrap temporarily to satisfy things like vocabularies
        # depending on tools
        if IAcquirer.providedBy(content):
            content = content.__of__(container)

        form.applyChanges(self, content, data)
        for group in self.groups:
            form.applyChanges(group, content, data)

        return aq_base(content)

    def chooseName(self, container, object):
        return INameChooser(container).chooseName(None, object)

    def add(self, object):
        
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        
        container = aq_inner(self.context)
        container_fti = container.getTypeInfo()
        
        # Validate that the object is addable
        
        if not fti.isConstructionAllowed(container):
            raise Unauthorized('Cannot create %s' % self.portal_type)

        if container_fti is not None and not container_fti.allowType(self.portal_type):
            raise ValueError('Disallowed subobject type: %s' % self.portal_type)

        name = self.chooseName(container, object)
        object.id = name
        
        new_name = container._setObject(name, object)
        
        # XXX: When we move to CMF 2.2, an event handler will take care of this
        wrapped_object = container._getOb(new_name)
        wrapped_object.notifyWorkflowCreated()
        
        immediate_view = fti.immediate_view or 'view'
        self.immediate_view = "%s/%s/%s" % (container.absolute_url(), new_name, immediate_view,)

    def nextURL(self):
        if self.immediate_view is not None:
            return self.immediate_view
        else:
            return self.context.absolute_url()
    
    # Buttons
    
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
            IStatusMessage(self.request).addStatusMessage(_(u"Changes saved"), "info")
    
    @button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Add New Item operation cancelled"), "info")
        container = aq_inner(self.context)
        self.request.response.redirect(self.nextURL()) 

    def updateActions(self):
        super(DefaultAddForm, self).updateActions()
        self.actions["save"].addClass("context")
        self.actions["cancel"].addClass("standalone")

    @property
    def label(self):
        portal_type = self.portal_type
        fti = getUtility(IDexterityFTI, name=portal_type)
        type_name = fti.title
        return _(u"Add ${name}", mapping={'name': type_name})

class DefaultAddView(layout.FormWrapper):
    """This is the default add view as looked up by the ++add++ traversal
    namespace adapter in CMF. It is an unnamed adapter on 
    (context, request, fti).
    
    Note that this is registered in ZCML as a simple <adapter />, but we
    also use the <class /> directive to set up security.
    """
    
    form = DefaultAddForm
    
    def __init__(self, context, request, ti):
        super(DefaultAddView, self).__init__(context, request)
        self.ti = ti

        # Set portal_type name on newly created form instance
        if self.form_instance is not None and not getattr(self.form_instance, 'portal_type', None): 
            self.form_instance.portal_type = ti.getId()
