import unittest
import mocker
from plone.mocktestcase import MockTestCase

from zope.interface import implements, Interface, alsoProvides
from zope.component import adapts, provideAdapter

from z3c.form.interfaces import IWidgets
from z3c.form.interfaces import IActions
from z3c.form.action import Actions
from z3c.form.field import FieldWidgets

from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehaviorAssignable

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IEditBegunEvent
from plone.dexterity.interfaces import IAddBegunEvent
from plone.dexterity.interfaces import IEditCancelledEvent
from plone.dexterity.interfaces import IAddCancelledEvent
from plone.dexterity.interfaces import IEditFinishedEvent

from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.view import DefaultView

from plone.dexterity.content import Item, Container
from plone.dexterity.fti import DexterityFTI

from zope.publisher.browser import TestRequest as TestRequestBase
from zope.app.container.interfaces import INameChooser

from AccessControl import Unauthorized

from Products.statusmessages.interfaces import IStatusMessage

class TestRequest(TestRequestBase):
    """Zope 3's TestRequest doesn't support item assignment, but Zope 2's
    request does.
    """
    def __setitem__(self, key, value):
        pass

class ISchema(Interface):
    pass

class IBehaviorOne(Interface):
    pass
alsoProvides(IBehaviorOne, IFormFieldProvider)

class IBehaviorTwo(Interface):
    pass
alsoProvides(IBehaviorTwo, IFormFieldProvider)

class IBehaviorThree(Interface):
    pass

class NoBehaviorAssignable(object):
    # We will use this simple class to check that registering our own
    # IBehaviorAssignable adapter has an effect.
    implements(IBehaviorAssignable)
    adapts(Interface)
    
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
        
        self.assertEquals(u"testtype", addview.form_instance.portal_type)
    
    def test_form_create(self):
        
        # Context and request
        context = Container(u"container")
        request = TestRequest()
        
        # FTI - returns dummy factory name
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.factory).result(u"testfactory")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        # The form we're testing
        form = DefaultAddForm(context, request)
        form.portal_type = u"testtype"
        
        # createObject and applyChanges
        
        obj_dummy = Item(id="dummy")
        data_dummy = {u"foo": u"bar"}
        
        createObject_mock = self.mocker.replace('zope.component.createObject')
        self.expect(createObject_mock(u"testfactory")).result(obj_dummy)
        
        applyChanges_mock = self.mocker.replace('z3c.form.form.applyChanges')
        self.expect(applyChanges_mock(form, obj_dummy, data_dummy))
        
        self.replay()
        
        self.assertEquals(obj_dummy, form.create(data_dummy))
        self.assertEquals("testtype", obj_dummy.portal_type)
    
    def test_add(self):
        
        # Container, new object, and request
        container = self.mocker.mock()
        obj = self.mocker.mock()
        request = TestRequest()

        self.expect(container._setObject(u"newid", obj)).result(u"newid")
        self.expect(container._getOb(u"newid")).result(obj)
        self.expect(container.absolute_url()).result("http://nohost/plone/container")
        
        obj.id = u"newid"
        
        self.expect(obj.id).result(u"newid")
        self.expect(obj.portal_type).result("testtype").count(0,None)
        
        # New object's FTI
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.isConstructionAllowed(container)).result(True)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # Container FTI
        container_fti_mock = self.mocker.proxy(DexterityFTI(u"containertype"))
        self.expect(container_fti_mock.allowType(u"testtype")).result(True)
        self.mock_utility(container_fti_mock, IDexterityFTI, name=u"containertype")
        
        self.expect(container.getTypeInfo()).result(container_fti_mock)

        # Name chooser
        class NameChooser(object):
            implements(INameChooser)
            def __init__(self, context):
                pass
            def chooseName(self, name, object):
                return u"newid"
        
        self.mock_adapter(NameChooser, INameChooser, (Interface,))

        self.replay()
        
        form = DefaultAddForm(container, request)
        form.portal_type = u"testtype"
        form.add(obj)
        
    def test_add_raises_unauthorized_if_construction_not_allowed(self):
        # Container, new object, and request
        container = self.mocker.mock()
        obj = self.mocker.mock()
        request = TestRequest()

        # New object's FTI
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.isConstructionAllowed(container)).result(False)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # Container FTI
        container_fti_mock = self.mocker.proxy(DexterityFTI(u"containertype"))
        self.mock_utility(container_fti_mock, IDexterityFTI, name=u"containertype")
        
        self.expect(container.getTypeInfo()).result(container_fti_mock)

        self.expect(obj.portal_type).result("testtype").count(0,None)

        self.replay()
        
        form = DefaultAddForm(container, request)
        form.portal_type = u"testtype"
        
        self.assertRaises(Unauthorized, form.add, obj)

    def test_add_raises_value_error_if_type_not_addable(self):
        # Container, new object, and request
        container = self.mocker.mock()
        obj = self.mocker.mock()
        request = TestRequest()

        self.expect(obj.portal_type).result("testtype").count(0,None)

        # New object's FTI
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.isConstructionAllowed(container)).result(True)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        # Container FTI
        container_fti_mock = self.mocker.proxy(DexterityFTI(u"containertype"))
        self.expect(container_fti_mock.allowType(u"testtype")).result(False)
        self.mock_utility(container_fti_mock, IDexterityFTI, name=u"containertype")
        
        self.expect(container.getTypeInfo()).result(container_fti_mock)

        self.replay()
        
        form = DefaultAddForm(container, request)
        form.portal_type = u"testtype"
        
        self.assertRaises(ValueError, form.add, obj)
           
    def test_label(self):
        
        # Add view should take its label from the FTI title
        
        # Context and request
        
        context_mock = self.mocker.mock()
        request_mock = self.mocker.proxy(TestRequest())
        
        request_mock['disable_border'] = True
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.Title()).result(u"Test title")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
      
        # Form
        
        self.replay()
        
        addform = DefaultAddForm(context_mock, request_mock)
        addform.portal_type = u"testtype"
        
        label = addform.label
        self.assertEquals(u"Add ${name}", unicode(label))
        self.assertEquals(u"Test title", label.mapping['name'])

    def test_schema_lookup(self):
        
        # Context and request
        
        context_mock = self.create_dummy(portal_type=u'testtype')
        request_mock = TestRequest()
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema)
        self.expect(fti_mock.behaviors).result((IBehaviorOne.__identifier__, 
                                                IBehaviorTwo.__identifier__, 
                                                IBehaviorThree.__identifier__))
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        self.expect(fti_mock.behaviors).result([])
      
        # Form
        
        self.replay()
        
        view = DefaultAddForm(context_mock, request_mock)
        view.portal_type = u"testtype"
        
        self.assertEquals(ISchema, view.schema)
        self.assertEquals([IBehaviorOne, IBehaviorTwo], list(view.additionalSchemata,))

        # When we register our own IBehaviorAssignable we can
        # influence what goes into the additionalSchemata:
        provideAdapter(NoBehaviorAssignable)
        self.assertEquals([], list(view.additionalSchemata,))

    def test_fires_add_begun_event(self):
        
        # Context and request
        
        context_mock = self.create_dummy(portal_type=u'testtype')
        request_mock = TestRequest()
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema)
        self.mocker.count(0, 100)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.mock_adapter(FieldWidgets, IWidgets, (Interface, Interface, Interface))

        self.mock_adapter(Actions, IActions, (Interface, Interface, Interface))
        
        # mock notify
        notify_mock = self.mocker.replace('zope.event.notify')
        self.expect(notify_mock(mocker.MATCH(
                    lambda x: IAddBegunEvent.providedBy(x)
                    )))
        
        # Form
        
        self.replay()
        
        view = DefaultAddForm(context_mock, request_mock)
        view.portal_type = fti_mock.getId()
        view.update()

    def test_fires_add_cancelled_event(self):

        # Context and request

        context_mock = self.create_dummy(portal_type=u'testtype')
        context_mock.absolute_url = lambda *a, **kw: 'http://127.0.0.1/plone/item'
        request_mock = TestRequest()

        # mock status message
        class StatusMessage(object):
            implements(IStatusMessage)
            def __init__(self, request):
                pass
            def addStatusMessage(self, msg, type=''):
                pass
        self.mock_adapter(StatusMessage, IStatusMessage, (Interface,))

        # mock notify
        notify_mock = self.mocker.replace('zope.event.notify')
        self.expect(notify_mock(mocker.MATCH(
                    lambda x: IAddCancelledEvent.providedBy(x)
                    )))

        # Form
        self.replay()

        view = DefaultAddForm(context_mock, request_mock)
        view.handleCancel(view, {})


class TestEditView(MockTestCase):
    
    def test_label(self):
        
        # Edit view should take its label from the FTI title
        
        # Context and request
        
        context_mock = self.create_dummy(portal_type=u'testtype')
        request_mock = TestRequest()
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.Title()).result(u"Test title")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
      
        # Form
        
        self.replay()
        
        editview = DefaultEditForm(context_mock, request_mock)
        
        # emulate update()
        editview.portal_type = u"testtype"
        
        label = editview.label
        self.assertEquals(u"Edit ${name}", unicode(label))
        self.assertEquals(u"Test title", label.mapping['name'])

    def test_schema_lookup(self):
        
        # Context and request
        
        context_mock = self.create_dummy(portal_type=u'testtype')
        request_mock = TestRequest()
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema)
        self.expect(fti_mock.behaviors).result((IBehaviorOne.__identifier__, 
                                                IBehaviorTwo.__identifier__, 
                                                IBehaviorThree.__identifier__))
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
      
        # Form
        
        self.replay()
        
        view = DefaultEditForm(context_mock, request_mock)
        
        # emulate update()
        view.portal_type = u"testtype"
        
        self.assertEquals(ISchema, view.schema)
        self.assertEquals([IBehaviorOne, IBehaviorTwo], list(view.additionalSchemata,))

        # When we register our own IBehaviorAssignable we can
        # influence what goes into the additionalSchemata:
        provideAdapter(NoBehaviorAssignable)
        self.assertEquals([], list(view.additionalSchemata,))

    def test_fires_edit_begun_event(self):
        
        # Context and request
        
        context_mock = self.create_dummy(portal_type=u'testtype')
        request_mock = TestRequest()
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema)
        self.mocker.count(0, 100)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")

        self.mock_adapter(FieldWidgets, IWidgets, (Interface, Interface, Interface))
        self.mock_adapter(Actions, IActions, (Interface, Interface, Interface))
        
        # mock notify
        notify_mock = self.mocker.replace('zope.event.notify')
        self.expect(notify_mock(mocker.MATCH(
                    lambda x: IEditBegunEvent.providedBy(x)
                    )))
        
        # Form
        
        view = DefaultEditForm(context_mock, request_mock)
        
        self.replay()
        
        view.update()

    def test_fires_edit_cancelled_event(self):

        # Context and request

        context_mock = self.create_dummy(portal_type=u'testtype', title=u'foo')
        context_mock.absolute_url = lambda *a, **kw: 'http://127.0.0.1/plone/item'
        request_mock = TestRequest()

        # mock status message
        class StatusMessage(object):
            implements(IStatusMessage)
            def __init__(self, request):
                pass
            def addStatusMessage(self, msg, type=''):
                pass
        self.mock_adapter(StatusMessage, IStatusMessage, (Interface,))

        # mock notify
        notify_mock = self.mocker.replace('zope.event.notify')
        self.expect(notify_mock(mocker.MATCH(
                    lambda x: IEditCancelledEvent.providedBy(x)
                    )))

        # Form
        self.replay()

        view = DefaultEditForm(context_mock, request_mock)
        view.handleCancel(view, {})

    def test_fires_edit_finished_event(self):

        # Context and request

        context_mock = self.create_dummy(portal_type=u'testtype', title=u'foo')
        context_mock.absolute_url = lambda *a, **kw: 'http://127.0.0.1/plone/item'
        request_mock = TestRequest()

        # mock status message
        class StatusMessage(object):
            implements(IStatusMessage)
            def __init__(self, request):
                pass
            def addStatusMessage(self, msg, type=''):
                pass
        self.mock_adapter(StatusMessage, IStatusMessage, (Interface,))

        # mock notify
        notify_mock = self.mocker.replace('zope.event.notify')
        self.expect(notify_mock(mocker.MATCH(
                    lambda x: IEditFinishedEvent.providedBy(x)
                    )))

        # Form
        view = DefaultEditForm(context_mock, request_mock)
        view.widgets = self.create_dummy()
        view.widgets.extract = lambda *a, **kw: ({'title': u'foo'}, [])
        self.replay()

        view.handleApply(view, {})
        


class TestDefaultView(MockTestCase):
    
    def test_schema_lookup(self):
        
        # Context and request
        
        context_mock = self.create_dummy(portal_type=u'testtype')
        request_mock = self.create_dummy()
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.lookupSchema()).result(ISchema)
        self.expect(fti_mock.behaviors).result((IBehaviorOne.__identifier__, 
                                                IBehaviorTwo.__identifier__, 
                                                IBehaviorThree.__identifier__))
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
      
        # Form
        
        self.replay()
        
        view = DefaultView(context_mock, request_mock)
        
        self.assertEquals(ISchema, view.schema)
        self.assertEquals([IBehaviorOne, IBehaviorTwo], list(view.additionalSchemata,))

        # When we register our own IBehaviorAssignable we can
        # influence what goes into the additionalSchemata:
        provideAdapter(NoBehaviorAssignable)
        self.assertEquals([], list(view.additionalSchemata,))


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
