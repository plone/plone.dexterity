# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from mock import Mock
from Products.statusmessages.interfaces import IStatusMessage
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.view import DefaultView
from plone.dexterity.content import Container
from plone.dexterity.content import Item
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import IAddBegunEvent
from plone.dexterity.interfaces import IAddCancelledEvent
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IEditBegunEvent
from plone.dexterity.interfaces import IEditCancelledEvent
from plone.dexterity.interfaces import IEditFinishedEvent
from plone.dexterity.schema import SCHEMA_CACHE
from plone.z3cform.interfaces import IDeferSecurityCheck
from z3c.form.action import Actions
from z3c.form.datamanager import AttributeField
from z3c.form.field import Fields
from z3c.form.field import FieldWidgets
from z3c.form.interfaces import IActions
from z3c.form.interfaces import IWidgets
from zope.component import adapter
from zope.component import provideAdapter
from zope.container.interfaces import INameChooser
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import provider
from zope.publisher.browser import TestRequest as TestRequestBase
from .case import MockTestCase
from zope import schema

import six


class TestRequest(TestRequestBase):
    """Zope 3's TestRequest doesn't support item assignment, but Zope 2's
    request does.
    """
    def __setitem__(self, key, value):
        pass


class ISchema(Interface):
    pass


@provider(IFormFieldProvider)
class IBehaviorOne(Interface):
    pass


@provider(IFormFieldProvider)
class IBehaviorTwo(Interface):
    pass


# intentionally no form field provider!
class IBehaviorThree(Interface):
    pass


@implementer(IBehaviorAssignable)
@adapter(Interface)
class NoBehaviorAssignable(object):
    # We will use this simple class to check that registering our own
    # IBehaviorAssignable adapter has an effect.

    def __init__(self, context):
        self.context = context

    def supports(self, behavior_interface):
        return False

    def enumerateBehaviors(self):
        return []


class TestAddView(MockTestCase):

    def test_addview_sets_form_portal_type(self):

        context = Container(u"container")
        request = TestRequest()
        fti = DexterityFTI(u"testtype")

        addview = DefaultAddView(context, request, fti)

        self.assertEqual(u"testtype", addview.form_instance.portal_type)

    def test_form_create(self):

        # Context and request
        context = Container(u"container")
        request = TestRequest()

        # FTI - returns dummy factory name

        fti_mock = DexterityFTI(u"testtype")
        fti_mock.factory = u'testfactory'
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # The form we're testing
        form = DefaultAddForm(context, request)
        form.portal_type = u"testtype"

        class ISchema(Interface):
            foo = schema.TextLine()
        form.fields = Fields(ISchema)

        # createObject and applyChanges

        obj_dummy = Item(id="dummy")
        alsoProvides(obj_dummy, ISchema)
        data_dummy = {u"foo": u"bar"}

        from zope.component import createObject
        self.patch_global(createObject, return_value=obj_dummy)

        provideAdapter(AttributeField)

        self.assertEqual(obj_dummy, form.create(data_dummy))
        self.assertEqual("testtype", obj_dummy.portal_type)

    def test_add(self):

        # Container, new object, and request
        container = Mock()
        obj = Mock()
        request = TestRequest()

        container._setObject = Mock(return_value=u'newid')
        container._getOb = Mock(return_value=obj)
        container.absolute_url = Mock(
            return_value="http://nohost/plone/container")

        obj.id = u"newid"
        obj.portal_type = 'testtype'

        # New object's FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.isConstructionAllowed = Mock(return_value=True)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # Container FTI
        container_fti_mock = DexterityFTI(u"containertype")
        container_fti_mock.allowType = Mock(return_value=True)
        self.mock_utility(
            container_fti_mock,
            IDexterityFTI,
            name=u"containertype"
        )

        container.getTypeInfo = Mock(return_value=container_fti_mock)

        # Name chooser
        @implementer(INameChooser)
        class NameChooser(object):

            def __init__(self, context):
                pass

            def chooseName(self, name, object):
                return u"newid"

        self.mock_adapter(NameChooser, INameChooser, (Interface,))

        form = DefaultAddForm(container, request)
        form.portal_type = u"testtype"
        form.add(obj)

    def test_add_raises_unauthorized_if_construction_not_allowed(self):
        # Container, new object, and request
        container = Mock()
        obj = Mock()
        request = TestRequest()

        # New object's FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.isConstructionAllowed = Mock(return_value=False)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # Container FTI
        container_fti_mock = DexterityFTI(u"containertype")
        self.mock_utility(
            container_fti_mock, IDexterityFTI, name=u"containertype"
        )

        container.getTypeInfo = Mock(return_value=container_fti_mock)
        obj.portal_type = 'testtype'

        form = DefaultAddForm(container, request)
        form.portal_type = u"testtype"

        self.assertRaises(Unauthorized, form.add, obj)

    def test_add_raises_value_error_if_type_not_addable(self):
        # Container, new object, and request
        container = Mock()
        obj = Mock()
        request = TestRequest()

        obj.portal_type = 'testtype'

        # New object's FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.isConstructionAllowed = Mock(return_value=True)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # Container FTI
        container_fti_mock = DexterityFTI(u"containertype")
        container_fti_mock.allowType = Mock(return_value=False)
        self.mock_utility(
            container_fti_mock,
            IDexterityFTI,
            name=u"containertype"
        )

        container.getTypeInfo = Mock(return_value=container_fti_mock)

        form = DefaultAddForm(container, request)
        form.portal_type = u"testtype"

        self.assertRaises(ValueError, form.add, obj)

    def test_label(self):

        # Add view should take its label from the FTI title

        # Context and request

        context_mock = Mock()
        request_mock = TestRequest()

        request_mock.form['disable_border'] = True

        # FTI

        fti_mock = DexterityFTI(u"testtype")
        fti_mock.Title = Mock(return_value=u'Test title')
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # Form

        addform = DefaultAddForm(context_mock, request_mock)
        addform.portal_type = u"testtype"

        label = addform.label
        self.assertEqual(u"Add ${name}", six.text_type(label))
        self.assertEqual(u"Test title", label.mapping['name'])

    def test_schema_lookup_add(self):

        # Context and request
        context_mock = self.create_dummy(portal_type=u'testtype')
        request_mock = TestRequest()

        # FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        fti_mock.behaviors = (
            IBehaviorOne.__identifier__,
            IBehaviorTwo.__identifier__,
            IBehaviorThree.__identifier__
        )
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        from plone.behavior.interfaces import IBehavior
        from plone.behavior.registration import BehaviorRegistration
        registration = BehaviorRegistration(
            title=u"Test Behavior 1",
            description=u"Provides test behavior",
            interface=IBehaviorOne,
            marker=None,
            factory=None
        )
        self.mock_utility(
            registration,
            IBehavior,
            IBehaviorOne.__identifier__
        )
        registration = BehaviorRegistration(
            title=u"Test Behavior 2",
            description=u"Provides test behavior",
            interface=IBehaviorTwo,
            marker=None,
            factory=None
        )
        self.mock_utility(
            registration,
            IBehavior,
            IBehaviorTwo.__identifier__
        )
        registration = BehaviorRegistration(
            title=u"Test Behavior 3",
            description=u"Provides test behavior",
            interface=IBehaviorThree,
            marker=None,
            factory=None
        )
        self.mock_utility(
            registration,
            IBehavior,
            IBehaviorThree.__identifier__
        )

        # Form
        view = DefaultAddForm(context_mock, request_mock)
        view.portal_type = u"testtype"

        self.assertEqual(ISchema, view.schema)

        # we expect here only formfieldprovider!
        self.assertEqual(
            (IBehaviorOne, IBehaviorTwo),
            tuple(view.additionalSchemata)
        )

        # When we register our own IBehaviorAssignable we can
        # influence what goes into the additionalSchemata. But in an Addform
        # this never grips, since its an adapter on context, and contextless
        # there is always the FTI the only valid source
        self.mock_adapter(
            NoBehaviorAssignable,
            IBehaviorAssignable,
            [Interface]
        )
        self.assertEqual(
            (IBehaviorOne, IBehaviorTwo),
            tuple(view.additionalSchemata)
        )

    def test_fires_add_begun_event(self):

        # Context and request
        context_mock = self.create_dummy(
            portal_type=u'testtype',
            allowedContentTypes=lambda: [self.create_dummy(getId=lambda: 'testtype')])
        request_mock = TestRequest()

        # FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.mock_adapter(
            FieldWidgets,
            IWidgets,
            (Interface, Interface, Interface)
        )

        self.mock_adapter(Actions, IActions, (Interface, Interface, Interface))

        # mock notify
        from zope.event import notify
        notify_mock = self.patch_global(notify)

        # Form
        view = DefaultAddForm(context_mock, request_mock)
        view.portal_type = fti_mock.getId()
        view.update()

        self.assertTrue(notify_mock.called)
        self.assertTrue(IAddBegunEvent.providedBy(notify_mock.call_args[0][0]))

    def test_update_checks_allowed_types(self):

        # Context and request
        context_mock = self.create_dummy(
            portal_type=u'testtype',
            allowedContentTypes=lambda: [])
        request_mock = TestRequest()

        # FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.mock_adapter(
            FieldWidgets,
            IWidgets,
            (Interface, Interface, Interface)
        )

        self.mock_adapter(Actions, IActions, (Interface, Interface, Interface))

        # Form
        view = DefaultAddForm(context_mock, request_mock)
        view.portal_type = fti_mock.getId()
        self.assertRaises(ValueError, view.update)

    def test_update_ignores_type_check_if_security_check_deferred(self):

        # Context and request
        context_mock = self.create_dummy(
            portal_type=u'testtype',
            allowedContentTypes=lambda: [])
        request_mock = TestRequest()
        alsoProvides(request_mock, IDeferSecurityCheck)

        # FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.mock_adapter(
            FieldWidgets,
            IWidgets,
            (Interface, Interface, Interface)
        )

        self.mock_adapter(Actions, IActions, (Interface, Interface, Interface))

        # Form
        view = DefaultAddForm(context_mock, request_mock)
        view.portal_type = fti_mock.getId()
        try:
            view.update()
        except ValueError:
            self.fail("Update raised Unauthorized with security checks "
                      "deferred")

    def test_fires_add_cancelled_event(self):

        # Context and request
        context_mock = self.create_dummy(portal_type=u'testtype')
        context_mock.absolute_url = \
            lambda *a, **kw: 'http://127.0.0.1/plone/item'
        request_mock = TestRequest()

        # mock status message
        @implementer(IStatusMessage)
        class StatusMessage(object):

            def __init__(self, request):
                pass

            def addStatusMessage(self, msg, type=''):
                pass
        self.mock_adapter(StatusMessage, IStatusMessage, (Interface,))

        # mock notify
        from zope.event import notify
        notify_mock = self.patch_global(notify)

        # Form
        view = DefaultAddForm(context_mock, request_mock)
        view.handleCancel(view, {})

        self.assertTrue(notify_mock.called)
        self.assertTrue(
            IAddCancelledEvent.providedBy(notify_mock.call_args[0][0]))


class TestEditView(MockTestCase):

    def setUp(self):
        SCHEMA_CACHE.clear()

    def test_label(self):

        # Edit view should take its label from the FTI title

        # Context and request

        context_mock = self.create_dummy(portal_type=u'testtype')
        request_mock = TestRequest()

        # FTI

        fti_mock = DexterityFTI(u"testtype")
        fti_mock.Title = Mock(return_value=u'Test title')
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # Form
        editview = DefaultEditForm(context_mock, request_mock)

        # emulate update()
        editview.portal_type = u"testtype"

        label = editview.label
        self.assertEqual(u"Edit ${name}", six.text_type(label))
        self.assertEqual(u"Test title", label.mapping['name'])

    def test_schema_lookup_edit(self):

        # Context and request
        class IMarker(IDexterityContent):
            pass

        context_mock = self.create_dummy(portal_type=u'testtype')
        alsoProvides(context_mock, IMarker)
        request_mock = TestRequest()

        # FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        fti_mock.behaviors = (
            IBehaviorOne.__identifier__,
            IBehaviorTwo.__identifier__,
            IBehaviorThree.__identifier__
        )
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        from plone.behavior.interfaces import IBehavior
        from plone.behavior.registration import BehaviorRegistration
        registration = BehaviorRegistration(
            title=u"Test Behavior 1",
            description=u"Provides test behavior",
            interface=IBehaviorOne,
            marker=None,
            factory=None
        )
        self.mock_utility(
            registration,
            IBehavior,
            IBehaviorOne.__identifier__
        )
        registration = BehaviorRegistration(
            title=u"Test Behavior 2",
            description=u"Provides test behavior",
            interface=IBehaviorTwo,
            marker=None,
            factory=None
        )
        self.mock_utility(
            registration,
            IBehavior,
            IBehaviorTwo.__identifier__
        )
        registration = BehaviorRegistration(
            title=u"Test Behavior 3",
            description=u"Provides test behavior",
            interface=IBehaviorThree,
            marker=None,
            factory=None
        )
        self.mock_utility(
            registration,
            IBehavior,
            IBehaviorThree.__identifier__
        )

        # Form
        view = DefaultEditForm(context_mock, request_mock)
        view.portal_type = u"testtype"

        self.assertEqual(ISchema, view.schema)

        # we expect here only formfieldprovider!
        self.assertEqual(
            (IBehaviorOne, IBehaviorTwo),
            tuple(view.additionalSchemata)
        )

        # When we register our own IBehaviorAssignable we can
        # influence what goes into the additionalSchemata.
        self.mock_adapter(
            NoBehaviorAssignable,
            IBehaviorAssignable,
            [IMarker]
        )
        additionalSchemata = tuple(view.additionalSchemata)
        self.assertEqual(tuple(), tuple(additionalSchemata))

    def test_fires_edit_begun_event(self):

        # Context and request
        context_mock = self.create_dummy(portal_type=u'testtype')
        request_mock = TestRequest()

        # FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.mock_adapter(
            FieldWidgets,
            IWidgets,
            (Interface, Interface, Interface)
        )
        self.mock_adapter(Actions, IActions, (Interface, Interface, Interface))

        # mock notify
        from zope.event import notify
        notify_mock = self.patch_global(notify)

        # Form
        view = DefaultEditForm(context_mock, request_mock)
        view.update()

        self.assertTrue(notify_mock.called)
        self.assertTrue(
            IEditBegunEvent.providedBy(notify_mock.call_args[0][0]))

    def test_fires_edit_cancelled_event(self):

        # Context and request
        context_mock = self.create_dummy(portal_type=u'testtype', title=u'foo')
        context_mock.absolute_url = \
            lambda *a, **kw: 'http://127.0.0.1/plone/item'
        request_mock = TestRequest()

        # mock status message
        @implementer(IStatusMessage)
        class StatusMessage(object):

            def __init__(self, request):
                pass

            def addStatusMessage(self, msg, type=''):
                pass
        self.mock_adapter(StatusMessage, IStatusMessage, (Interface,))

        # mock notify
        from zope.event import notify
        notify_mock = self.patch_global(notify)

        # Form
        view = DefaultEditForm(context_mock, request_mock)
        view.handleCancel(view, {})

        self.assertTrue(notify_mock.called)
        self.assertTrue(
            IEditCancelledEvent.providedBy(notify_mock.call_args[0][0]))

    def test_fires_edit_finished_event(self):

        # Context and request
        context_mock = self.create_dummy(portal_type=u'testtype', title=u'foo')
        context_mock.absolute_url = \
            lambda *a, **kw: 'http://127.0.0.1/plone/item'
        request_mock = TestRequest()

        # mock status message
        @implementer(IStatusMessage)
        class StatusMessage(object):

            def __init__(self, request):
                pass

            def addStatusMessage(self, msg, type=''):
                pass
        self.mock_adapter(StatusMessage, IStatusMessage, (Interface,))

        # mock notify
        from zope.event import notify
        notify_mock = self.patch_global(notify)

        # Form
        view = DefaultEditForm(context_mock, request_mock)
        view.widgets = Mock()
        view.widgets.extract = Mock(return_value=({'title': u'foo'}, []))
        view.applyChanges = Mock()
        view.handleApply(view, {})

        self.assertTrue(notify_mock.called)
        self.assertTrue(
            IEditFinishedEvent.providedBy(notify_mock.call_args[0][0]))


class TestDefaultView(MockTestCase):

    def test_schema_lookup_default_view(self):

        # Context and request
        class IMarker(IDexterityContent):
            pass

        context_mock = self.create_dummy(portal_type=u'testtype')
        alsoProvides(context_mock, IMarker)
        request_mock = TestRequest()

        # FTI
        fti_mock = DexterityFTI(u"testtype")
        fti_mock.lookupSchema = Mock(return_value=ISchema)
        fti_mock.behaviors = (
            IBehaviorOne.__identifier__,
            IBehaviorTwo.__identifier__,
            IBehaviorThree.__identifier__
        )
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        from plone.behavior.interfaces import IBehavior
        from plone.behavior.registration import BehaviorRegistration
        registration = BehaviorRegistration(
            title=u"Test Behavior 1",
            description=u"Provides test behavior",
            interface=IBehaviorOne,
            marker=None,
            factory=None
        )
        self.mock_utility(
            registration,
            IBehavior,
            IBehaviorOne.__identifier__
        )
        registration = BehaviorRegistration(
            title=u"Test Behavior 2",
            description=u"Provides test behavior",
            interface=IBehaviorTwo,
            marker=None,
            factory=None
        )
        self.mock_utility(
            registration,
            IBehavior,
            IBehaviorTwo.__identifier__
        )
        registration = BehaviorRegistration(
            title=u"Test Behavior 3",
            description=u"Provides test behavior",
            interface=IBehaviorThree,
            marker=None,
            factory=None
        )
        self.mock_utility(
            registration,
            IBehavior,
            IBehaviorThree.__identifier__
        )

        # Form
        view = DefaultView(context_mock, request_mock)
        view.portal_type = u"testtype"

        self.assertEqual(ISchema, view.schema)

        # we expect here only formfieldprovider!
        self.assertEqual(
            (IBehaviorOne, IBehaviorTwo),
            tuple(view.additionalSchemata)
        )

        # When we register our own IBehaviorAssignable we can
        # influence what goes into the additionalSchemata.
        self.mock_adapter(
            NoBehaviorAssignable,
            IBehaviorAssignable,
            [IMarker]
        )
        additionalSchemata = tuple(view.additionalSchemata)
        self.assertEqual(tuple(), tuple(additionalSchemata))
