import unittest
from plone.mocktestcase import MockTestCase

from zope.interface import implements, Interface, alsoProvides

from plone.autoform.interfaces import IFormFieldProvider

from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.view import DefaultView

from plone.dexterity.content import Item, Container
from plone.dexterity.fti import DexterityFTI

from zope.publisher.browser import TestRequest as TestRequestBase
from zope.app.container.interfaces import INameChooser

from AccessControl import Unauthorized

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
        self.expect(fti_mock.title).result(u"Test title")
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
      
        # Form
        
        self.replay()
        
        view = DefaultAddForm(context_mock, request_mock)
        view.portal_type = u"testtype"
        
        self.assertEquals(ISchema, view.schema)
        self.assertEquals([IBehaviorOne, IBehaviorTwo], list(view.additionalSchemata,))
    
class TestEditView(MockTestCase):
    
    def test_label(self):
        
        # Edit view should take its label from the FTI title
        
        # Context and request
        
        context_mock = self.create_dummy(portal_type=u'testtype')
        request_mock = TestRequest()
        
        # FTI
        
        fti_mock = self.mocker.proxy(DexterityFTI(u"testtype"))
        self.expect(fti_mock.title).result(u"Test title")
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

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
