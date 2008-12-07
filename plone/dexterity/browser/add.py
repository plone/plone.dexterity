from zope.interface import implements
from zope.component import getUtility, queryMultiAdapter, createObject

from z3c.form import form, button
from plone.z3cform import layout

from zope.app.container.interfaces import INameChooser
from zope.publisher.interfaces import IPublishTraverse

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.i18n import MessageFactory as _

from plone.dexterity.browser.base import DexterityExtensibleForm

from zExceptions import NotFound
from Acquisition import aq_inner, aq_base
from Acquisition.interfaces import IAcquirer
from AccessControl import Unauthorized

from Products.Five.browser import BrowserView

from Products.statusmessages.interfaces import IStatusMessage

class DefaultAddForm(DexterityExtensibleForm, form.AddForm):
    """Standard add form. This is capable of rendering the fields of
    any Dexterity type. It needs to know the portal_type, which can be set
    as a class variable, in the constructor or by the view. The standard
    pattern is to use the @@add-dexterity-content traverser - see below.
    """
    
    portal_type = None
    obj_url = None
    
    def __init__(self, context, request, portal_type=None):
        super(DefaultAddForm, self).__init__(context, request)
        
        if portal_type is not None:
            self.portal_type = portal_type
            
        self.request['disable_border'] = True
    
    # API
    
    def create(self, data):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        
        container = aq_inner(self.context)
        content = createObject(fti.factory)
        
        # acquisition wrap to satisfy things like vocabularies depending on tools
        if IAcquirer.providedBy(content):
            content = content.__of__(container)

        form.applyChanges(self, content, data)
        for group in self.groups:
            form.applyChanges(group, content, data)

        return aq_base(content)

    def add(self, object):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        
        container = aq_inner(self.context)
        container_fti = container.getTypeInfo()
        
        # Validate that the object is addable
        
        if not fti.isConstructionAllowed(container):
            raise Unauthorized('Cannot create %s' % self.portal_type)

        if container_fti is not None and not container_fti.allowType(self.portal_type):
            raise ValueError('Disallowed subobject type: %s' % self.portal_type)

        name = INameChooser(container).chooseName(None, object)
        object.id = name
        
        # XXX: When we move to CMF 2.2, an event handler will take care of this
        object.notifyWorkflowCreated()
        container._setObject(name, object)
        
        self.obj_url = container.absolute_url() + '/' + name

    def nextURL(self):
        if self.obj_url is not None:
            return self.obj_url
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

DefaultAddView = layout.wrap_form(DefaultAddForm)

class AddTraverser(BrowserView):
    """A traverser that can locate and initialise add forms that need to be
    aware of the portal type they are adding.
    
    This is registered as @@add-dexterity-content.
    
    The idea is that when we traverse to e.g.
    
        http://example.com/some/folder/@@add-dexterity-content/my.type
        
    the traverser looks up the FTI for my.type. If this has an 'add_view_name'
    property set, then it will attempt to look up the view with this name.
    If it does not, it will attempt to look up an add view called
    @@add-my.type, which is the default name when registering custom add 
    forms. If this is not found, it will fall back on the default add form,
    @@dexterity-default-addview.
    
    If the obtained view has an attribute 'portal_type', it is set to
    'my.type'; if it has an attribute 'form' which in turn has an attribute
    'portal_type', then view.form.portal_type is set to 'my.type'.
    
    This way, the add view or a form that it wraps will be able to know
    which portal type to add.
    """
    implements(IPublishTraverse)
    
    def publishTraverse(self, request, name):
        context = aq_inner(self.context)
        
        fti = getUtility(IDexterityFTI, name=name)
        add_view_name = fti.add_view_name or "add-%s" % name
        
        if add_view_name.startswith('@@'):
            add_view_name = add_view_name[2:]
        
        view = queryMultiAdapter((context, request), name=add_view_name)
        if view is None:
            view = queryMultiAdapter((context, request), name=u"dexterity-default-addview")

        if view is None:
            raise NotFound(u"Cannot find add view for %s" % name)
        
        # XXX: This is depending on plone.z3cform internals too much
        if hasattr(view, 'form_instance') and hasattr(view.form_instance, 'portal_type'):
            view.form_instance.portal_type = name
        
        if hasattr(view, 'portal_type'):
            view.portal_type = name

        return view.__of__(context)