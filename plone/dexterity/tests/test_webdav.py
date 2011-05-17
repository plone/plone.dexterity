import re
import unittest
from StringIO import StringIO
from email.Message import Message
from mocker import ANY

from plone.mocktestcase import MockTestCase

from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from zExceptions import Unauthorized, MethodNotAllowed, Forbidden

from webdav.NullResource import NullResource

from plone.dexterity.content import Item, Container
from zope.publisher.browser import TestRequest

from zope.interface import Interface
from zope.interface import implements
from zope.interface import alsoProvides

from zope.interface.interfaces import IInterface
from zope.component.interfaces import IFactory

from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.size.interfaces import ISized

from zope import schema

from zope.filerepresentation.interfaces import IRawReadFile
from zope.filerepresentation.interfaces import IRawWriteFile

from zope.filerepresentation.interfaces import IDirectoryFactory
from zope.filerepresentation.interfaces import IFileFactory

from ZPublisher.Iterators import IStreamIterator
from ZPublisher.HTTPResponse import HTTPResponse

from plone.rfc822.interfaces import IPrimaryField
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehaviorAssignable

from plone.dexterity.interfaces import DAV_FOLDER_DATA_ID
from plone.dexterity.interfaces import IDexterityFTI

from plone.dexterity.filerepresentation import FolderDataResource

from plone.dexterity.filerepresentation import DefaultDirectoryFactory
from plone.dexterity.filerepresentation import DefaultFileFactory

from plone.dexterity.filerepresentation import DefaultReadFile
from plone.dexterity.filerepresentation import DefaultWriteFile
from plone.dexterity.schema import SCHEMA_CACHE

from plone.dexterity.fti import DexterityFTI

from plone.dexterity.browser.traversal import DexterityPublishTraverse

class ITestBehavior(Interface):
    foo = schema.Int()
    bar = schema.Bytes()
alsoProvides(ITestBehavior, IFormFieldProvider)

class DAVTestRequest(TestRequest):
    
    get_header = TestRequest.getHeader
    
    def _createResponse(self):
        return HTTPResponse()


class TestWebZope2DAVAPI(MockTestCase):
    
    def test_get_size_no_adapter(self):
        item = Item('test')
        
        self.replay()
        
        self.assertEquals(0, item.get_size())
    
    def test_get_size_wrong_adapter(self):
        class SizedAdapter(object):
            def __init__(self, context):
                self.context = context
            def sizeForSorting(self):
                return 'lines', 10
            def sizeForDisplay(self):
                '10 lines'
        self.mock_adapter(SizedAdapter, ISized, (Item,))
        item = Item('test')
        
        self.replay()
        
        self.assertEquals(0, item.get_size())
    
    def test_get_size_right_adapter(self):
        class SizedAdapter(object):
            def __init__(self, context):
                self.context = context
            def sizeForSorting(self):
                return 'bytes', 10
            def sizeForDisplay(self):
                '10 bytes'
        self.mock_adapter(SizedAdapter, ISized, (Item,))
        item = Item('test')
        
        self.replay()
        
        self.assertEquals(10, item.get_size())
    
    def test_content_type_no_adapter(self):
        item = Item('test')
        
        self.replay()
        
        self.assertEquals(None, item.content_type())
        self.assertEquals(None, item.Format())
    
    def test_content_type_simple_adapter(self):
        class ReadFileAdapter(object):
            def __init__(self, context):
                self.context = context
            mimeType = 'text/foo'
            # others omitted
        self.mock_adapter(ReadFileAdapter, IRawReadFile, (Item,))
        item = Item('test')
        
        self.replay()
        
        self.assertEquals('text/foo', item.content_type())
        self.assertEquals('text/foo', item.Format())
    
    def test_get_no_adapter(self):
        item = Item('test')
        
        self.replay()
        
        self.assertEquals('', item.manage_DAVget())
    
    def test_get_simple_adapter(self):
        class ReadFileAdapter(object):
            def __init__(self, context):
                self.context = context
            mimeType = 'text/foo'
            encoding = 'latin1'
            def size(self):
                return 10
            def read(self, size=None):
                return '1234567890'
        self.mock_adapter(ReadFileAdapter, IRawReadFile, (Item,))
        
        request = DAVTestRequest()
        
        item = Item('item')
        item.REQUEST = request
        
        self.replay()
        
        self.assertEquals('1234567890', item.manage_DAVget())
        self.assertEquals('text/foo; charset="latin1"', request.response.getHeader('Content-Type'))
        self.assertEquals('10', request.response.getHeader('Content-Length'))
        
    def test_get_minimal_adapter(self):
        class ReadFileAdapter(object):
            def __init__(self, context):
                self.context = context
            mimeType = None
            encoding = None
            def size(self):
                return None
            def read(self, size=None):
                return '1234567890'
        self.mock_adapter(ReadFileAdapter, IRawReadFile, (Item,))
        
        request = DAVTestRequest()
        
        item = Item('item')
        item.REQUEST = request
        
        self.replay()
        
        self.assertEquals('1234567890', item.manage_DAVget())
        self.assertEquals(None, request.response.getHeader('Content-Type'))
        self.assertEquals(None, request.response.getHeader('Content-Length'))
    
    def test_get_streaming(self):
        class ReadFileAdapter(object):
            if IInterface.providedBy(IStreamIterator):
                implements(IStreamIterator)
            else:
                __implements__ = (IStreamIterator,)
            def __init__(self, context):
                self.context = context
            mimeType = None
            encoding = None
            def size(self):
                return 10
            def read(self, size=None):
                return '1234567890'
        
        adapterInstance = ReadFileAdapter(None)
        def factory(context):
            return adapterInstance
        self.mock_adapter(factory, IRawReadFile, (Item,))
        
        request = DAVTestRequest()
        
        item = Item('item')
        item.REQUEST = request
        
        self.replay()
        
        self.assertEquals(adapterInstance, item.manage_DAVget())
    
    def test_put_no_adapter(self):
        request = DAVTestRequest(environ={'BODYFILE': StringIO('')})
        
        item = Item('item')
        item.REQUEST = request
        
        self.replay()
        
        self.assertRaises(MethodNotAllowed, item.PUT)
    
    def test_put_no_body(self):
        request = DAVTestRequest()
        
        item = Item('item')
        item.REQUEST = request
        
        self.replay()
        
        self.assertRaises(MethodNotAllowed, item.PUT)
    
    def test_put_no_content_type_header(self):
        class WriteFile(object):
            def __init__(self, context):
                self.context = context
                self._written = ''
                self._closed = False
            mimeType = None
            encoding = None
            def write(self, data):
                self._written += data
            def close(self):
                self._closed = True
        
        adapterInstance = WriteFile(None)
        def factory(context):
            return adapterInstance
        
        self.mock_adapter(factory, IRawWriteFile, (Item,))
        
        request = DAVTestRequest(environ={'BODYFILE': StringIO('data')})
        
        item = Item('item')
        item.REQUEST = request
        
        self.replay()
        
        item.PUT()
        self.assertEquals(None, adapterInstance.mimeType)
        self.assertEquals(None, adapterInstance.encoding)
        self.assertEquals('data', adapterInstance._written)
        self.assertEquals(True, adapterInstance._closed)
    
    def test_put_with_content_type_header_no_charset(self):
        class WriteFile(object):
            def __init__(self, context):
                self.context = context
                self._written = ''
                self._closed = False
            mimeType = None
            encoding = None
            def write(self, data):
                self._written += data
            def close(self):
                self._closed = True
        
        adapterInstance = WriteFile(None)
        def factory(context):
            return adapterInstance
        
        events = []
        def handler(event):
            events.append(event)
        
        self.mock_adapter(factory, IRawWriteFile, (Item,))
        self.mock_handler(handler, (IObjectModifiedEvent,))
        
        request = DAVTestRequest(environ={'BODYFILE': StringIO('data'), 'HTTP_CONTENT_TYPE': 'text/foo'})
        
        item = Item('item')
        item.REQUEST = request
        
        self.replay()
        
        item.PUT()
        self.assertEquals('text/foo', adapterInstance.mimeType)
        self.assertEquals(None, adapterInstance.encoding)
        self.assertEquals('data', adapterInstance._written)
        self.assertEquals(True, adapterInstance._closed)
        self.assertEquals(1, len(events))
    
    def test_put_with_content_type_header_and_charset(self):
        class WriteFile(object):
            def __init__(self, context):
                self.context = context
                self._written = ''
                self._closed = False
            mimeType = None
            encoding = None
            def write(self, data):
                self._written += data
            def close(self):
                self._closed = True
        
        adapterInstance = WriteFile(None)
        def factory(context):
            return adapterInstance
        
        events = []
        def handler(event):
            events.append(event)
        
        self.mock_adapter(factory, IRawWriteFile, (Item,))
        self.mock_handler(handler, (IObjectModifiedEvent,))
        
        request = DAVTestRequest(environ={'BODYFILE': StringIO('data'), 'HTTP_CONTENT_TYPE': 'text/foo; charset="latin1"'})
        
        item = Item('item')
        item.REQUEST = request
        
        self.replay()
        
        item.PUT()
        self.assertEquals('text/foo', adapterInstance.mimeType)
        self.assertEquals('latin1', adapterInstance.encoding)
        self.assertEquals('data', adapterInstance._written)
        self.assertEquals(True, adapterInstance._closed)
        self.assertEquals(1, len(events))
    
    def test_mkcol_no_adapter(self):
        container = Container('container')
        self.replay()
        self.assertRaises(MethodNotAllowed, container.MKCOL_handler, 'test')
    
    def test_mkcol_simple_adapter(self):
        created = []
        class DirectoryFactory(object):
            def __init__(self, context):
                self.context = context
            def __call__(self, id):
                created.append(id)
        self.mock_adapter(DirectoryFactory, IDirectoryFactory, (Container,))
        
        container = Container('container')
        self.replay()
        container.MKCOL_handler('test')
        self.assertEquals(['test'], created)
    
    def test_put_factory_no_adapter(self):
        container = Container('container')
        self.replay()
        self.assertEquals(None, container.PUT_factory('test', 'text/foo', 'body'))
    
    def test_put_factory_simple_adapter(self):
        instance = object()
        class FileFactory(object):
            def __init__(self, context):
                self.context = context
            def __call__(self, name, contentType, body):
                return instance
        self.mock_adapter(FileFactory, IFileFactory, (Container,))
        container = Container('container')
        self.replay()
        self.assertEquals(instance, container.PUT_factory('test', 'text/foo', 'body'))
    
    def test_list_without_items(self):
        
        class DummyContainer(Container):
            
            def listFolderContents(self, filter=None):
                return []
        
        container = DummyContainer('container')
        self.replay()
        
        objects = container.listDAVObjects()
        self.assertEquals(1, len(objects))
        self.failUnless(isinstance(objects[0], FolderDataResource))
        self.assertEquals(DAV_FOLDER_DATA_ID, objects[0].getId())
        self.assertEquals(container, objects[0].__parent__)
    
    def test_list_with_items(self):
        
        class DummyContainer(Container):
            
            def listFolderContents(self, filter=None):
                return [Item('foo')]
        
        container = DummyContainer('container')
        self.replay()
        
        objects = container.listDAVObjects()
        self.assertEquals(2, len(objects))
        self.failUnless(isinstance(objects[0], FolderDataResource))
        self.assertEquals(DAV_FOLDER_DATA_ID, objects[0].getId())
        self.assertEquals(container, objects[0].__parent__)
        self.assertEquals('foo', objects[1].getId())


class TestFolderDataResource(MockTestCase):
    
    def test_getId(self):
        container = Container('container')
        r = FolderDataResource('fdata', container)
        
        self.replay()
        
        self.assertEquals('fdata', r.getId())
        self.assertEquals(container, r.__parent__)
    
    def test_HEAD(self):
        
        class TestContainer(Container):
            
            def get_size(self):
                return 10
            
            def content_type(self):
                return 'text/foo'
        
        container = TestContainer('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container'})
        response = request.response
        
        self.replay()
        
        self.assertEquals(response, r.HEAD(request, request.response))
        self.assertEquals(200, response.getStatus())
        self.assertEquals('close', response.getHeader('Connection', literal=True))
        self.assertEquals('text/foo', response.getHeader('Content-Type'))
        self.assertEquals('10', response.getHeader('Content-Length'))
    
    def test_OPTIONS(self):
        class TestContainer(Container):
            
            def get_size(self):
                return 10
            
            def content_type(self):
                return 'text/foo'
        
        container = TestContainer('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container'})
        response = request.response
        
        self.replay()
    
        self.assertEquals(response, r.OPTIONS(request, request.response))
        self.assertEquals('close', response.getHeader('Connection', literal=True))
        self.assertEquals('GET, HEAD, POST, PUT, DELETE, OPTIONS, TRACE, PROPFIND, PROPPATCH, MKCOL, COPY, MOVE, LOCK, UNLOCK', response.getHeader('Allow'))
    
    def test_TRACE(self):
        class TestContainer(Container):
            
            def get_size(self):
                return 10
            
            def content_type(self):
                return 'text/foo'
        
        container = TestContainer('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container'})
        
        self.replay()
    
        self.assertRaises(MethodNotAllowed, r.TRACE, request, request.response)
    
    def test_PROPFIND(self):
        class TestContainer(Container):
            
            def get_size(self):
                return 10
            
            def content_type(self):
                return 'text/foo'
        
        container = TestContainer('container')
        container.manage_changeProperties(title="Container")
        r = FolderDataResource('fdata', container).__of__(container)
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container'})
        response = request.response
        
        self.replay()
        
        self.assertEquals(response, r.PROPFIND(request, response))
        
        self.assertEquals('close', response.getHeader('connection', literal=True))
        self.assertEquals('text/xml; charset="utf-8"', response.getHeader('Content-Type'))
        self.assertEquals(207, response.getStatus())
        
        body = """\
<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:">
<d:response>
<d:href>/site/container</d:href>
<d:propstat xmlns:n="http://www.zope.org/propsets/default">
  <d:prop>
  <n:title>Container</n:title>
  </d:prop>
  <d:status>HTTP/1.1 200 OK</d:status>
</d:propstat>
<d:propstat xmlns:n="DAV:">
  <d:prop>
  <n:creationdate>1970-01-01T12:00:00Z</n:creationdate>
  <n:displayname>Container</n:displayname>
  <n:resourcetype></n:resourcetype>
  <n:getcontenttype>text/foo</n:getcontenttype>
  <n:getcontentlength>10</n:getcontentlength>
  <n:source></n:source>
  <n:supportedlock>
  <n:lockentry>
  <d:lockscope><d:exclusive/></d:lockscope>
  <d:locktype><d:write/></d:locktype>
  </n:lockentry>
  </n:supportedlock>
  <n:lockdiscovery>

</n:lockdiscovery>
  <n:getlastmodified>...</n:getlastmodified>
  </d:prop>
  <d:status>HTTP/1.1 200 OK</d:status>
</d:propstat>
</d:response>
</d:multistatus>
"""
        
        result = response.getBody()
        result = re.sub(r'<n:getlastmodified>.+</n:getlastmodified>', '<n:getlastmodified>...</n:getlastmodified>', result)
        
        self.assertEquals(result.strip(), body.strip())
    
    def test_PROPPATCH(self):
        class TestContainer(Container):
            
            def get_size(self):
                return 10
            
            def content_type(self):
                return 'text/foo'
        
        container = TestContainer('container')
        container.manage_changeProperties(title="Container")
        r = FolderDataResource('fdata', container).__of__(container)
        
        requestBody = """\
<?xml version="1.0" encoding="utf-8" ?>
<D:propertyupdate xmlns:D="DAV:" xmlns:n="http://www.zope.org/propsets/default">
    <D:set>
        <D:prop>
            <n:title>New title</n:title>
          </D:prop>
     </D:set>
</D:propertyupdate>
"""
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container', 'BODY': requestBody})
        response = request.response
        
        self.replay()
        
        self.assertEquals(response, r.PROPPATCH(request, response))
        
        self.assertEquals('New title', container.getProperty('title'))
        
        self.assertEquals('close', response.getHeader('connection', literal=True))
        self.assertEquals('text/xml; charset="utf-8"', response.getHeader('Content-Type'))
        self.assertEquals(207, response.getStatus())
        
        body = """\
<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:">
<d:response>
<d:href>http%3A//example.org/site/container</d:href>
<d:propstat xmlns:n="http://www.zope.org/propsets/default">
  <d:prop>
  <n:title/>
  </d:prop>
  <d:status>HTTP/1.1 200 OK</d:status>
</d:propstat>
<d:responsedescription>
The operation succeded.
</d:responsedescription>
</d:response>
</d:multistatus>
"""
        
        result = response.getBody()
        self.assertEquals(body.strip(), result.strip())

    def test_LOCK(self):
        # Too much WebDAV magic - just test that it delegates correctly
        class TestContainer(Container):
            
            def LOCK(self, request, response):
                self._locked = (request, response,)
                return response
        
        container = TestContainer('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container'})
        response = request.response
        
        self.replay()
        
        self.assertEquals(response, r.LOCK(request, response))
        self.assertEquals((request, response), container._locked)
    
    def test_UNLOCK(self):
        # Too much WebDAV magic - just test that it delegates correctly
        class TestContainer(Container):
            
            def UNLOCK(self, request, response):
                self._unlocked = (request, response,)
                return response
        
        container = TestContainer('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container'})
        response = request.response
        
        self.replay()
        
        self.assertEquals(response, r.UNLOCK(request, response))
        self.assertEquals((request, response), container._unlocked)
    
    def test_PUT(self):
        class TestContainer(Container):
            
            def PUT(self, request, response):
                self._put = (request, response,)
                return response
        
        container = TestContainer('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container'})
        response = request.response
        
        self.replay()
        
        self.assertEquals(response, r.PUT(request, response))
        self.assertEquals((request, response), container._put)
    
    def test_MKCOL(self):
        container = Container('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        self.replay()
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container'})
        response = request.response
        
        self.assertRaises(MethodNotAllowed, r.MKCOL, request, response)
    
    def test_DELETE(self):
        container = Container('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        self.replay()
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container'})
        response = request.response
        
        self.assertRaises(MethodNotAllowed, r.DELETE, request, response)
    
    def test_COPY(self):
        container = Container('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        self.replay()
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container'})
        response = request.response
        
        self.assertRaises(MethodNotAllowed, r.COPY, request, response)
    
    def test_MOVE(self):
        container = Container('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        self.replay()
        
        request = DAVTestRequest(environ={'URL': 'http://example.org/site/container'})
        response = request.response
        
        self.assertRaises(MethodNotAllowed, r.MOVE, request, response)
    
    def test_manage_DAVget(self):
        class TestContainer(Container):
            
            def manage_DAVget(self):
                return 'data'
        
        container = TestContainer('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        self.replay()
        
        self.assertEquals('data', r.manage_DAVget())
    
    def test_manage_FTPget(self):
        class TestContainer(Container):
            
            def manage_FTPget(self):
                return 'data'
        
        container = TestContainer('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        self.replay()
        
        self.assertEquals('data', r.manage_FTPget())
    
    def test_listDAVObjects(self):
        container = Container('container')
        r = FolderDataResource('fdata', container).__of__(container)
        
        self.replay()
        
        self.assertEquals([], r.listDAVObjects())
    
class TestFileRepresentation(MockTestCase):
    
    def test_directory_factory(self):
        class TestContainer(Container):
            
            def manage_addFolder(self, name):
                self._added = name
        
        container = TestContainer('container')
        factory = DefaultDirectoryFactory(container)
        
        self.replay()
        
        factory('foo')
        self.assertEquals('foo', container._added)
    
    def test_file_factory_finder_cruft(self):
        container = Container('container')
        factory = DefaultFileFactory(container)
        
        self.replay()
        
        self.assertRaises(Unauthorized, factory, '.DS_Store', 'application/octet-stream', 'xxx')
        self.assertRaises(Unauthorized, factory, '._test', 'application/octet-stream', 'xxx')
    
    
    def test_file_factory_no_ctr(self):
        container = Container('container')
        
        getToolByName_mock = self.mocker.replace('Products.CMFCore.utils.getToolByName')
        self.expect(getToolByName_mock(container, 'content_type_registry', None)).result(None)
        
        factory = DefaultFileFactory(container)
        
        self.replay()
        
        self.assertEquals(None, factory('test.html', 'text/html', '<html />'))
    
    def test_file_factory_no_fti(self):
        container = Container('container')
        
        ctr_mock = self.mocker.mock()
        getToolByName_mock = self.mocker.replace('Products.CMFCore.utils.getToolByName')
        
        self.expect(getToolByName_mock(container, 'content_type_registry', None)).result(ctr_mock)
        self.expect(ctr_mock.findTypeName('test.html', 'text/html', '<html />')).result(None)
        
        factory = DefaultFileFactory(container)
        
        self.replay()
        
        self.assertEquals(None, factory('test.html', 'text/html', '<html />'))    
    
    def test_file_factory_not_allowed(self):
        container = Container('container')
        container.portal_type = 'containertype'
        
        child_fti_mock = self.mocker.mock()
        container_fti_mock = self.mocker.mock()
        ctr_mock = self.mocker.mock()
        pt_mock = self.mocker.mock()
        getToolByName_mock = self.mocker.replace('Products.CMFCore.utils.getToolByName')
        
        self.expect(getToolByName_mock(container, 'content_type_registry', None)).result(ctr_mock)
        self.expect(getToolByName_mock(container, 'portal_types')).result(pt_mock)
        
        self.expect(ctr_mock.findTypeName('test.html', 'text/html', '<html />')).result('childtype')
        
        self.expect(pt_mock.getTypeInfo('childtype')).result(child_fti_mock)
        self.expect(pt_mock.getTypeInfo(container)).result(container_fti_mock)
        
        self.expect(child_fti_mock.product).result(None)
        
        self.expect(container_fti_mock.allowType('childtype')).result(False)
        
        factory = DefaultFileFactory(container)
        
        self.replay()
        
        self.assertRaises(Unauthorized, factory, 'test.html', 'text/html', '<html />')
    
    def test_file_factory_construction_not_allowed(self):
        container = Container('container')
        container.portal_type = 'containertype'
        
        child_fti_mock = self.mocker.mock()
        container_fti_mock = self.mocker.mock()
        ctr_mock = self.mocker.mock()
        pt_mock = self.mocker.mock()
        getToolByName_mock = self.mocker.replace('Products.CMFCore.utils.getToolByName')
        
        self.expect(getToolByName_mock(container, 'content_type_registry', None)).result(ctr_mock)
        self.expect(getToolByName_mock(container, 'portal_types')).result(pt_mock)
        
        self.expect(ctr_mock.findTypeName('test.html', 'text/html', '<html />')).result('childtype')
        
        self.expect(pt_mock.getTypeInfo('childtype')).result(child_fti_mock)
        self.expect(pt_mock.getTypeInfo(container)).result(container_fti_mock)
        
        self.expect(child_fti_mock.product).result(None)
        
        self.expect(container_fti_mock.allowType('childtype')).result(True)
        self.expect(child_fti_mock.isConstructionAllowed(container)).result(False)
        
        factory = DefaultFileFactory(container)
        
        self.replay()
        
        self.assertRaises(Unauthorized, factory, 'test.html', 'text/html', '<html />')
    
    def test_file_factory_factory_method(self):
        
        container_mock = self.mocker.mock()
        child_fti_mock = self.mocker.mock()
        ctr_mock = self.mocker.mock()
        pt_mock = self.mocker.mock()
        
        result_dummy = self.create_dummy()
        
        getToolByName_mock = self.mocker.replace('Products.CMFCore.utils.getToolByName')
        
        self.expect(getToolByName_mock(container_mock, 'content_type_registry', None)).result(ctr_mock)
        self.expect(getToolByName_mock(container_mock, 'portal_types')).result(pt_mock)
        
        self.expect(ctr_mock.findTypeName('test.html', 'text/html', '<html />')).result('childtype')
        
        self.expect(pt_mock.getTypeInfo('childtype')).result(child_fti_mock)
        
        self.expect(child_fti_mock.product).result('FooProduct')
        self.expect(container_mock.invokeFactory('childtype', 'test.html')).result('test-1.html')
        
        self.expect(container_mock._getOb('test-1.html')).result(result_dummy)
        self.expect(container_mock._delObject('test-1.html'))

        factory = DefaultFileFactory(container_mock)
        
        self.replay()
        
        self.assertEquals(result_dummy, factory('test.html', 'text/html', '<html />'))
    
    def test_file_factory_factory_utility(self):
        container_mock = self.mocker.mock()
        child_fti_mock = self.mocker.mock()
        container_fti_mock = self.mocker.mock()
        ctr_mock = self.mocker.mock()
        pt_mock = self.mocker.mock()
        
        result_dummy = self.create_dummy()
        
        getToolByName_mock = self.mocker.replace('Products.CMFCore.utils.getToolByName')
        
        self.expect(getToolByName_mock(container_mock, 'content_type_registry', None)).result(ctr_mock)
        self.expect(getToolByName_mock(container_mock, 'portal_types')).result(pt_mock)
        
        self.expect(ctr_mock.findTypeName('test.html', 'text/html', '<html />')).result('childtype')
        
        self.expect(pt_mock.getTypeInfo('childtype')).result(child_fti_mock)
        self.expect(pt_mock.getTypeInfo(container_mock)).result(container_fti_mock)
        
        self.expect(container_fti_mock.allowType('childtype')).result(True)
        self.expect(child_fti_mock.isConstructionAllowed(container_mock)).result(True)
        
        self.expect(child_fti_mock.product).result(None)
        self.expect(child_fti_mock.factory).result('childtype-factory')
        
        def factory(*args, **kwargs):
            return result_dummy
        self.mock_utility(factory, IFactory, name=u'childtype-factory')

        factory = DefaultFileFactory(container_mock)
        
        self.replay()
        
        self.assertEquals(result_dummy, factory('test.html', 'text/html', '<html />'))
    
    def test_readfile_mimetype_no_message_no_fields(self):
        
        class ITest(Interface):
            pass
        
        fti_mock = self.mocker.mock(DexterityFTI)
        SCHEMA_CACHE.clear()
        self.expect(fti_mock.lookupSchema()).result(ITest)
        self.expect(fti_mock.lookupSchema()).result(ITest)
        self.expect(fti_mock.behaviors).result([])
        self.expect(fti_mock.behaviors).result([])
        
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        item = Item('item')
        item.portal_type = 'testtype'
        
        readfile = DefaultReadFile(item)
        
        self.replay()
        
        self.assertEquals('text/plain', readfile.mimeType)
    
    def test_readfile_mimetype_no_message_no_primary_field(self):
        
        class ITest(Interface):
            title = schema.TextLine()
        
        SCHEMA_CACHE.clear()
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(ITest)
        self.expect(fti_mock.lookupSchema()).result(ITest)
        self.expect(fti_mock.behaviors).result([])
        self.expect(fti_mock.behaviors).result([])
        
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        item = Item('item')
        item.portal_type = 'testtype'
        
        readfile = DefaultReadFile(item)
        
        self.replay()
        
        self.assertEquals('text/plain', readfile.mimeType)

    def test_readfile_mimetype_no_message_single_primary_field(self):
        
        class ITest(Interface):
            title = schema.TextLine()
            body = schema.Text()
        alsoProvides(ITest['body'], IPrimaryField)
            
        SCHEMA_CACHE.clear()
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(ITest)
        self.expect(fti_mock.lookupSchema()).result(ITest)
        self.expect(fti_mock.behaviors).result([])
        self.expect(fti_mock.behaviors).result([])
        
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        item = Item('item')
        item.portal_type = 'testtype'
        
        readfile = DefaultReadFile(item)
        
        self.replay()
        
        self.assertEquals('text/plain', readfile.mimeType)

    def test_readfile_mimetype_no_message_multiple_primary_fields(self):
        
        class ITest(Interface):
            title = schema.TextLine()
            body = schema.Text()
            stuff = schema.Bytes()
        alsoProvides(ITest['body'], IPrimaryField)
        alsoProvides(ITest['stuff'], IPrimaryField)
            
        SCHEMA_CACHE.clear()
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(ITest)
        
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        item = Item('item')
        item.portal_type = 'testtype'
        
        readfile = DefaultReadFile(item)
        
        self.replay()
        
        self.assertEquals('message/rfc822', readfile.mimeType)
    
    def test_readfile_mimetype_additional_schemata(self):
        # This is mostly a test that utils.iterSchemata takes
        # IBehaviorAssignable into account.
        
        class ITest(Interface):
            title = schema.TextLine()
        class ITestAdditional(Interface):
            # Additional behavior on an item
            body = schema.Text()
            stuff = schema.Bytes()
        alsoProvides(ITestAdditional['body'], IPrimaryField)
        alsoProvides(ITestAdditional['stuff'], IPrimaryField)
        alsoProvides(ITestAdditional, IFormFieldProvider)
        class MockBehavior(object):
            def __init__(self, iface):
                self.interface = iface
        class MockBehaviorAssignable(object):
            def __init__(self, context):
                self.context = context
            def enumerateBehaviors(self):
                yield MockBehavior(ITestAdditional)
        SCHEMA_CACHE.clear()
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(ITest)
        self.expect(fti_mock.lookupSchema()).result(ITest)

        self.mock_adapter(MockBehaviorAssignable, IBehaviorAssignable,
                          (Item, ))
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        item = Item('item')
        item.portal_type = 'testtype'
        
        readfile = DefaultReadFile(item)
        
        self.replay()
        
        self.assertEquals('message/rfc822', readfile.mimeType)
    
    def test_readfile_operations(self):
        
        class ITest(Interface):
            title = schema.TextLine()
            body = schema.Text()
        alsoProvides(ITest['body'], IPrimaryField)
        
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(ITest).count(0, None)
        self.expect(fti_mock.behaviors).result([ITestBehavior.__identifier__]).count(0, None)
        
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        item = Item('item')
        item.portal_type = 'testtype'
        
        readfile = DefaultReadFile(item)
        
        message = Message()
        message['title'] = 'Test title'
        message['foo'] = '10'
        message['bar'] = 'xyz'
        message.set_payload('<p>body</p>')
        
        constructMessageFromSchemata_mock = self.mocker.replace('plone.rfc822.constructMessageFromSchemata')
        self.expect(constructMessageFromSchemata_mock(item, ANY)).result(message)
        
        self.replay()
        
        body = """\
title: Test title
foo: 10
bar: xyz
Portal-Type: testtype

<p>body</p>"""
        
        # iter
        # next
        
        self.assertEquals(body, readfile.read())
        self.assertEquals(69L, readfile.size())
        self.assertEquals('utf-8', readfile.encoding)
        self.assertEquals(None, readfile.name)
        self.assertEquals('text/plain', readfile.mimeType)
        
        readfile.seek(2)
        self.assertEquals(2, readfile.tell())
        self.assertEquals('tl', readfile.read(2))
        self.assertEquals(4, readfile.tell())
        
        readfile.seek(0,2)
        self.assertEquals(69, readfile.tell())
        
        readfile.seek(0)
        self.assertEquals('foo: 10\n', readfile.readlines()[1])
        
        readfile.seek(0)
        self.assertEquals('foo: 10\n', readfile.readlines(100)[1])
        
        readfile.seek(0)
        self.assertEquals('title: Test title\n', readfile.readline())
        
        readfile.seek(0)
        self.assertEquals('title: Test title\n', readfile.readline(100))
        
        readfile.seek(0)
        self.assertEquals('foo: 10\n', list(iter(readfile))[1])
        
        self.assertEquals(False, readfile.closed)
        readfile.close()
    
    def test_writefile_file_operations(self):
        
        class ITest(Interface):
            title = schema.TextLine()
            body = schema.Text()
        alsoProvides(ITest['body'], IPrimaryField)
        
        fti_mock = self.mocker.mock(DexterityFTI)
        self.expect(fti_mock.lookupSchema()).result(ITest).count(0, None)
        self.expect(fti_mock.behaviors).result([ITestBehavior.__identifier__]).count(0, None)
        
        self.mock_utility(fti_mock, IDexterityFTI, name=u"testtype")
        
        item = Item('item')
        item.portal_type = 'testtype'
        item.title = u"Test title"
        item.foo = 10
        item.bar = 'xyz'
        item.body = u"<p>body</p>"
        
        writefile = DefaultWriteFile(item)
        
        body = """\
title: Test title
foo: 10
bar: xyz
Portal-Type: testtype

<p>body</p>"""
        
        initializeObjectFromSchemata_mock = self.mocker.replace('plone.rfc822.initializeObjectFromSchemata')
        self.expect(initializeObjectFromSchemata_mock(item, ANY, self.match_type(Message), 'latin1'))
        
        self.replay()
        
        writefile.mimeType = 'text/plain'
        self.assertEquals('text/plain', writefile.mimeType)
        
        writefile.encoding = 'latin1'
        self.assertEquals('latin1', writefile.encoding)
        
        writefile.filename = 'test.html'
        self.assertEquals('test.html', writefile.filename)
        
        self.assertEquals(False, writefile.closed)
        self.assertEquals(0, writefile.tell())
        
        writefile.writelines(['one\n', 'two'])
        self.assertEquals(7, writefile.tell())
        
        self.assertRaises(NotImplementedError, writefile.truncate)
        
        writefile.truncate(0)
        self.assertEquals(0, writefile.tell())
        
        self.assertRaises(NotImplementedError, writefile.seek, 10)
        
        writefile.write(body[:10])
        writefile.write(body[10:])
        writefile.close()
        
        self.assertEquals(True, writefile.closed)
        self.assertEquals(69, writefile.tell())
        

class TestDAVTraversal(MockTestCase):
    
    def test_no_acquire_dav(self):
        container = Container('container')
        
        outer = Folder('outer')
        outer._setOb('item', SimpleItem('item'))
        outer._setOb('container', container)
        
        request = DAVTestRequest(environ={'URL': 'http://site/test', 'REQUEST_METHOD': 'PUT'})
        request.maybe_webdav_client = True
        
        traversal = DexterityPublishTraverse(container.__of__(outer), request)
        
        self.replay()
        
        r = traversal.publishTraverse(request, 'item')
        
        self.failUnless(isinstance(r, NullResource))
        self.assertEquals(container, r.aq_parent)
    
    def test_acquire_without_dav(self):
        container = Container('container')
        
        outer = Folder('outer')
        outer._setOb('item', SimpleItem('item'))
        outer._setOb('container', container)
        
        request = DAVTestRequest(environ={'URL': 'http://site/test', 'REQUEST_METHOD': 'GET'})
        request.maybe_webdav_client = False
        
        traversal = DexterityPublishTraverse(container.__of__(outer), request)
        
        self.replay()
        
        r = traversal.publishTraverse(request, 'item')
        
        self.assertEquals(r.aq_base, outer['item'].aq_base)
        self.assertEquals(container, r.aq_parent)
    
    def test_folder_data_traversal_dav(self):
        container = Container('test')
        request = DAVTestRequest(environ={'URL': 'http://site/test'})
        request.maybe_webdav_client = True
        
        traversal = DexterityPublishTraverse(container, request)
        
        self.replay()
        
        r = traversal.publishTraverse(request, DAV_FOLDER_DATA_ID)
        
        self.assertEquals(DAV_FOLDER_DATA_ID, r.__name__)
        self.assertEquals(container, r.__parent__)
        self.assertEquals(container, r.aq_parent)
        
    
    def test_folder_data_traversal_without_dav(self):
        container = Container('test')
        request = DAVTestRequest(environ={'URL': 'http://site/test'})
        request.maybe_webdav_client = False
        
        traversal = DexterityPublishTraverse(container, request)
        
        self.replay()
        
        self.assertRaises(Forbidden, traversal.publishTraverse, request, DAV_FOLDER_DATA_ID)
    
    def test_browser_default_dav(self):
        class TestContainer(Container):
            
            def __browser_default__(self, request):
                return self, ('foo',)
        
        container = TestContainer('container')
        request = DAVTestRequest(environ={'URL': 'http://site/test', 'REQUEST_METHOD': 'PROPFIND'})
        request.maybe_webdav_client = True
        
        traversal = DexterityPublishTraverse(container, request)
        
        self.replay()
        
        self.assertEquals((container, (),), traversal.browserDefault(request))
    
    def test_browser_default_dav_get(self):
        class TestContainer(Container):
            
            def __browser_default__(self, request):
                return self, ('foo',)
        
        container = TestContainer('container')
        request = DAVTestRequest(environ={'URL': 'http://site/test', 'REQUEST_METHOD': 'GET'})
        request.maybe_webdav_client = True
        
        traversal = DexterityPublishTraverse(container, request)
        
        self.replay()
        
        self.assertEquals((container, ('foo',),), traversal.browserDefault(request))
    
    def test_browser_default_without_dav(self):
        class TestContainer(Container):
            
            def __browser_default__(self, request):
                return self, ('foo',)
        
        container = TestContainer('container')
        request = DAVTestRequest(environ={'URL': 'http://site/test', 'REQUEST_METHOD': 'PROPFIND'})
        request.maybe_webdav_client = False
        
        traversal = DexterityPublishTraverse(container, request)
        
        self.replay()
        
        self.assertEquals((container, ('foo',),), traversal.browserDefault(request))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
