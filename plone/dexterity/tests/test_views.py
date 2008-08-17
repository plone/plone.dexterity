import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import implements, Interface
import zope.schema

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.add import AddTraverser

from plone.dexterity.browser.edit import DefaultEditForm

from plone.dexterity.browser.view import DefaultView

from plone.dexterity.fti import DexterityFTI

from zope.publisher.browser import TestRequest as TestRequestBase
from zope.publisher.interfaces.browser import IBrowserRequest
from Products.CMFCore.interfaces import IFolderish
from zope.app.container.interfaces import INameChooser

from OFS.SimpleItem import SimpleItem
from Products.Five.browser import BrowserView
from AccessControl import Unauthorized

class TestRequest(TestRequestBase):
    """Zope 3's TestRequest doesn't support item assignment, but Zope 2's
    request does.
    """
    def __setitem__(self, key, value):
        pass

class TestAddView(MockTestCase):
    
    def test_traverser_looks_up_fti_addview(self):
        
        # Context and request
        
        class Context(SimpleItem):
            implements(IFolderish)
        
        context = Context()
        request = TestRequest()
        
        # FTI - returns dummy addview name
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.add_view_name).result(u"add-testtype")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        # Mock add view
        
        class Form(object):
            portal_type = u"dummy"
        
        class AddView(BrowserView):
            def __init__(self, context, request):
                self._form = Form()
                self.portal_type = u"foo"

        self.mock_adapter(DefaultAddView, Interface, (IFolderish, IBrowserRequest), name=u"dexterity-default-addview")
        self.mock_adapter(AddView, Interface, (IFolderish, IBrowserRequest), name=u"add-testtype")
        
        self.replay()
        
        traverser = AddTraverser(context, request)
        addview = traverser.publishTraverse(request, name="testtype")
        
        self.failUnless(isinstance(addview, AddView))
        self.assertEquals("testtype", addview._form.portal_type)
        self.assertEquals("testtype", addview.portal_type)
        
    def test_traverser_falls_back_on_default_addview(self):
        # Context and request
        
        class Context(SimpleItem):
            implements(IFolderish)
        
        context = Context()
        request = self.mocker.proxy(TestRequest())
        
        request['disable_border'] = True
        
        # FTI - returns dummy addview name
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.add_view_name).result(u"")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        # Mock add view
        
        self.mock_adapter(DefaultAddView, Interface, (IFolderish, IBrowserRequest), name=u"dexterity-default-addview")
        
        self.replay()
        
        traverser = AddTraverser(context, request)
        addview = traverser.publishTraverse(request, name="testtype")
        
        self.failUnless(isinstance(addview, DefaultAddView))
        self.assertEquals("testtype", addview._form.portal_type)

    def test_traverser_falls_back_on_default_addview_if_addview_set_but_invalid(self):
        # Context and request
        
        class Context(SimpleItem):
            implements(IFolderish)
        
        context = Context()
        request = self.mocker.proxy(TestRequest())
        
        request['disable_border'] = True
        
        # FTI - returns dummy addview name
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.add_view_name).result(u"add-non-existent")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        # Mock add view
        
        self.mock_adapter(DefaultAddView, Interface, (IFolderish, IBrowserRequest), name=u"dexterity-default-addview")
        
        self.replay()
        
        traverser = AddTraverser(context, request)
        addview = traverser.publishTraverse(request, name="testtype")
        
        self.failUnless(isinstance(addview, DefaultAddView))
        self.assertEquals("testtype", addview._form.portal_type)
    
    def test_form_create(self):
        
        # Context and request
        context = self.create_dummy()
        request = TestRequest()
        
        # FTI - returns dummy factory name
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.factory).result(u"testfactory")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        # The form we're testing
        form = DefaultAddForm(context, request, u"testtype")
        
        # createObject and applyChanges
        
        obj_dummy = self.create_dummy()
        data_dummy = {u"foo": u"bar"}
        
        createObject_mock = self.mocker.replace('zope.component.createObject')
        self.expect(createObject_mock(u"testfactory")).result(obj_dummy)
        
        applyChanges_mock = self.mocker.replace('z3c.form.form.applyChanges')
        self.expect(applyChanges_mock(form, obj_dummy, data_dummy))
        
        self.replay()
        
        self.assertEquals(obj_dummy, form.create(data_dummy))
    
    def test_add(self):
        
        # Container, new object, and request
        container = self.mocker.mock()
        obj = self.mocker.mock()
        request = TestRequest()

        self.expect(container._setObject(u"newid", obj))
        
        self.expect(obj.id).result(None)
        obj.id = u"newid"
        self.expect(obj.notifyWorkflowCreated())

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
        
        form = DefaultAddForm(container, request, u"testtype")
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

        self.replay()
        
        form = DefaultAddForm(container, request, u"testtype")
        self.assertRaises(Unauthorized, form.add, obj)

    def test_add_raises_value_error_if_type_not_addable(self):
        # Container, new object, and request
        container = self.mocker.mock()
        obj = self.mocker.mock()
        request = TestRequest()

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
        
        form = DefaultAddForm(container, request, u"testtype")
        self.assertRaises(ValueError, form.add, obj)
           
    def test_label(self):
        
        # Add view should take its label from the FTI title
        
        # Context and request
        
        context_mock = self.mocker.mock()
        request_mock = self.mocker.proxy(TestRequest())
        
        request_mock['disable_border'] = True
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.title).result(u"Test title")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
      
        # Form
        
        self.replay()
        
        addform = DefaultAddForm(context_mock, request_mock, u"testtype")
        label = addform.label
        self.assertEquals(u"Add ${name}", unicode(label))
        self.assertEquals(u"Test title", label.mapping['name'])
    
class TestEditView(MockTestCase):
    
    # TODO: Add tests for field/widget setup code
    
    def test_label(self):
        
        # Edit view should take its label from the FTI title
        
        # Context and request
        
        context_mock = self.create_dummy(portal_type=u'testtype')
        request_mock = self.create_dummy()
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.title).result(u"Test title")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
      
        # Form
        
        self.replay()
        
        editview = DefaultEditForm(context_mock, request_mock)
        label = editview.label
        self.assertEquals(u"Edit ${name}", unicode(label))
        self.assertEquals(u"Test title", label.mapping['name'])
    
class TestDefaultView(MockTestCase):
    
    def test_fields(self):
        
        # Context and request
        
        context_dummy = self.create_dummy(portal_type=u"testtype", 
                                          field1=u"Field one",
                                          field2=u"Field two")
        request_mock = self.mocker.mock()
        
        # Schema
        schema_dummy = self.create_dummy()

        # Fields
        field1_mock = self.mocker.proxy(zope.schema.TextLine(__name__="field1", title=u"Field 1"))
        self.expect(field1_mock.bind(context_dummy)).result(field1_mock)
        
        field2_mock = self.mocker.proxy(zope.schema.TextLine(__name__="field2", title=u"Field 2"))
        self.expect(field2_mock.bind(context_dummy)).result(field2_mock)
        
        # Field enumeration
        getFieldsInOrder_mock = self.mocker.replace('zope.schema.getFieldsInOrder')
        self.expect(getFieldsInOrder_mock(schema_dummy)).result([('field1', field1_mock,), ('field2', field2_mock,)])
        
        
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookup_schema()).result(schema_dummy)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        view = DefaultView(context_dummy, request_mock)
        
        fields = list(view.fields(ignored=[]))
        
        self.assertEquals(
        [{'title': u'Field 1', 'id': 'field1', 'value': u"Field one", 'description': u''},
         {'title': u'Field 2', 'id': 'field2', 'value': u"Field two", 'description': u''}], fields)
        
    def test_ignored(self):
        
        # Context and request
        
        context_dummy = self.create_dummy(portal_type=u"testtype", 
                                          field1=u"Field one",
                                          field2=u"Field two")
        request_mock = self.mocker.mock()
        
        # Schema
        schema_dummy = self.create_dummy()

        # Fields
        field1_mock = self.mocker.proxy(zope.schema.TextLine(__name__="field1", title=u"Field 1"))
        
        field2_mock = self.mocker.proxy(zope.schema.TextLine(__name__="field2", title=u"Field 2"))
        self.expect(field2_mock.bind(context_dummy)).result(field2_mock)
        
        # Field enumeration
        getFieldsInOrder_mock = self.mocker.replace('zope.schema.getFieldsInOrder')
        self.expect(getFieldsInOrder_mock(schema_dummy)).result([('field1', field1_mock,), ('field2', field2_mock,)])
        
        
        # FTI
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookup_schema()).result(schema_dummy)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        view = DefaultView(context_dummy, request_mock)
        
        fields = list(view.fields(ignored=['field1']))
        
        self.assertEquals(
        [{'title': u'Field 2', 'id': 'field2', 'value': u"Field two", 'description': u''}], fields)
    
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAddView))
    suite.addTest(unittest.makeSuite(TestEditView))
    suite.addTest(unittest.makeSuite(TestDefaultView))
    return suite
