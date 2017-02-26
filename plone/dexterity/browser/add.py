# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition.interfaces import IAcquirer
from Products.statusmessages.interfaces import IStatusMessage
from plone.dexterity.browser.base import DexterityExtensibleForm
from plone.dexterity.events import AddBegunEvent
from plone.dexterity.events import AddCancelledEvent
from plone.dexterity.i18n import MessageFactory as _
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import addContentToContainer
from plone.dexterity.utils import getAdditionalSchemata
from plone.z3cform import layout
from plone.z3cform.interfaces import IDeferSecurityCheck
from z3c.form import button
from z3c.form import form
from z3c.form.interfaces import IDataManager
from z3c.form.interfaces import NOT_CHANGED
from z3c.form.util import changedField
from zope.component import createObject
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.event import notify
from zope.publisher.browser import BrowserPage


class DefaultAddForm(DexterityExtensibleForm, form.AddForm):
    """Standard add form, which is wrapped by DefaultAddView (see below).

    This form is capable of rendering the fields of any Dexterity schema,
    including behaviours. To do that, needs to know the portal_type, which
    can be set as a class variable (in a subclass), or on a created instance.

    By default, the DefaultAddView (see below) will set the portal_type based
    on the FTI.
    """

    portal_type = None
    immediate_view = None
    success_message = _(u"Item created")

    def __init__(self, context, request, ti=None):
        super(DefaultAddForm, self).__init__(context, request)
        if ti is not None:
            self.ti = ti
            self.portal_type = ti.getId()
        self.request.form['disable_border'] = True

    @property
    def additionalSchemata(self):
        return getAdditionalSchemata(portal_type=self.portal_type)

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

        _applyChanges(self, content, data, force=True)
        for group in self.groups:
            _applyChanges(group, content, data, force=True)

        return aq_base(content)

    def add(self, object):

        fti = getUtility(IDexterityFTI, name=self.portal_type)
        container = aq_inner(self.context)
        new_object = addContentToContainer(container, object)

        if fti.immediate_view:
            self.immediate_view = "/".join(
                [container.absolute_url(), new_object.id, fti.immediate_view]
            )
        else:
            self.immediate_view = "/".join(
                [container.absolute_url(), new_object.id]
            )

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
            IStatusMessage(self.request).addStatusMessage(
                self.success_message, "info"
            )

    @button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(
            _(u"Add New Item operation cancelled"), "info"
        )
        self.request.response.redirect(self.nextURL())
        notify(AddCancelledEvent(self.context))

    def update(self):
        if not IDeferSecurityCheck.providedBy(self.request):
            allowed_ids = [fti.getId() for fti in
                           self.context.allowedContentTypes()]
            if self.portal_type not in allowed_ids:
                raise ValueError(
                    'Subobject type disallowed by IConstrainTypes adapter: %s'
                    % self.portal_type
                )
        super(DefaultAddForm, self).update()
        # fire the edit begun only if no action was executed
        if len(self.actions.executedActions) == 0:
            notify(AddBegunEvent(self.context))

    def updateActions(self):
        super(DefaultAddForm, self).updateActions()
        if 'save' in self.actions:
            self.actions["save"].addClass("context")

        if 'cancel' in self.actions:
            self.actions["cancel"].addClass("standalone")

    @property
    def label(self):
        portal_type = self.portal_type
        fti = getUtility(IDexterityFTI, name=portal_type)
        type_name = fti.Title()
        return _(u"Add ${name}", mapping={'name': type_name})


class DefaultAddView(layout.FormWrapper, BrowserPage):
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
        if self.form_instance is not None \
           and not getattr(self.form_instance, 'portal_type', None):
            self.form_instance.portal_type = ti.getId()


def _applyChanges(form, content, data, force=False):
    # This is copied from z3c.form, but modified to add
    # an option to always set values even if already set.
    changes = {}
    for name, field in form.fields.items():
        # If the field is not in the data, then go on to the next one
        try:
            newValue = data[name]
        except KeyError:
            continue
        # If the value is NOT_CHANGED, ignore it, since the widget/converter
        # sent a strong message not to do so.
        if newValue is NOT_CHANGED:
            continue
        if force or changedField(field.field, newValue, context=content):
            # Only update the data, if it is different
            dm = getMultiAdapter((content, field.field), IDataManager)
            dm.set(newValue)
            # Record the change using information required later
            changes.setdefault(dm.field.interface, []).append(name)
    return changes
