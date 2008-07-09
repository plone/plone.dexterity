import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import Interface
import zope.schema

from z3c.form.field import Fields

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.browser.add import AddViewFactory
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView

from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.edit import DefaultEditView

from plone.dexterity.browser.view import DefaultView

from plone.dexterity.fti import DexterityFTI

from AccessControl import Unauthorized

class TestAddView(MockTestCase):
    
    def test_factory(self):
        
        # Factory should create the add view, which should look up
        # basic properties (__name__, portal_type) from FTI and
        # set the disable_border flag.
        
        # Context and request
        context_mock = self.mocker.mock()
        request_mock = self.mocker.mock()
    
        # Expect factory to disable editable border
        request_mock['disable_border'] = True
        
        # Mock FTI to return factory
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        self.replay()
        
        factory = AddViewFactory(u"testtype")
        addview = factory(context_mock, request_mock)
        
        self.failUnless(isinstance(addview, DefaultAddView))
        self.assertEquals(u"testtype", addview.__name__)
        self.assertEquals(u"testtype", addview.portal_type)
    
    # TODO: Add tests for field/widget setup code

    def test_form_create(self):
        
        # When asked to create an object, the form should look up the
        # factory from the FTI, and then all createObject() with this factory
        # to invoke the factory and then applyChanges() with the form, the
        # object and the data dict to set data
    
        # Context and request
        context_mock = self.mocker.mock()
        request_mock = self.mocker.mock()
        
        # FTI - returns dummy factory name
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.factory).result(u"testfactory")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        # The form we're testing
        form = DefaultAddForm(context_mock, request_mock, u"testtype")
        
        # createObject and applyChanges
        
        obj_dummy = self.create_dummy()
        data_dummy = {u"foo": u"bar"}
        
        createObject_mock = self.mocker.replace('zope.component.createObject')
        self.expect(createObject_mock(u"testfactory")).result(obj_dummy)
        
        applyChanges_mock = self.mocker.replace('z3c.form.form.applyChanges')
        self.expect(applyChanges_mock(form, obj_dummy, data_dummy))
        
        self.replay()
        
        self.assertEquals(obj_dummy, form.create(data_dummy))
    
    def test_call_checks_fti_is_allowed(self):
        
        # When calling the add view, we need to ensure that construction
        # is allowed
        
        # Container, context and request
        
        container_mock = self.mocker.mock()
        context_mock = self.mocker.mock()
        request_mock = self.mocker.mock()
        
        self.expect(context_mock.context).result(container_mock)
        
        request_mock['disable_border'] = True
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.isConstructionAllowed(container_mock)).result(True)
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
      
        # Form
        
        form_mock = self.mocker.mock()
      
        # Override base view's __call__ 
      
        # XXX: This should be doable with mocker
        import plone.z3cform.base
        old_call = plone.z3cform.base.FormWrapper.__call__
        plone.z3cform.base.FormWrapper.__call__ = lambda self: ''
          
        self.replay()
      
        addview = DefaultAddView(context_mock, request_mock, u"testtype", form=form_mock)
        addview()
        
        # XXX: Clean up
        plone.z3cform.base.FormWrapper.__call__ = old_call
        
    def test_call_raises_unauthorized_if_not_allowed(self):
        
        # When calling the add view, we need to ensure that construction
        # is allowed and raise Unauthorized if it is not
        
        # Container, context and request
        
        container_mock = self.mocker.mock()
        context_mock = self.mocker.mock()
        request_mock = self.mocker.mock()
        
        self.expect(context_mock.context).result(container_mock)
        
        request_mock['disable_border'] = True
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.isConstructionAllowed(container_mock)).result(False) # -> Unauthorized
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
      
        # Form
        
        form_mock = self.mocker.mock()
        
        self.replay()
        
        addview = DefaultAddView(context_mock, request_mock, u"testtype", form=form_mock)
        self.assertRaises(Unauthorized, addview)
       
    def test_label(self):
        
        # Add view should take its label from the FTI title
        
        # Context and request
        
        context_mock = self.mocker.mock()
        request_mock = self.mocker.mock()
        
        request_mock['disable_border'] = True
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.title).result(u"Test title")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
      
        # Form
        
        form_mock = self.mocker.mock()
        
        self.replay()
        
        addview = DefaultAddView(context_mock, request_mock, u"testtype", form=form_mock)
        label = addview.label
        self.assertEquals(u"Add ${name}", unicode(label))
        self.assertEquals(u"Test title", label.mapping['name'])
    
class TestEditView(MockTestCase):
    
    # TODO: Add tests for field/widget setup code
    
    def test_label(self):
        
        # Edit view should take its label from the FTI title
        
        # Context and request
        
        context_mock = self.mocker.mock()
        request_mock = self.mocker.mock()
        
        self.expect(context_mock.portal_type).result(u"testtype")
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.title).result(u"Test title")
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
      
        # Form
        
        self.replay()
        
        editview = DefaultEditView(context_mock, request_mock)
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
