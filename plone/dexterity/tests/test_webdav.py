import unittest
from StringIO import StringIO
from plone.mocktestcase import MockTestCase

from zExceptions import MethodNotAllowed

from plone.dexterity.content import Item, Container
from zope.publisher.browser import TestRequest

from zope.interface import implements
from zope.interface.interfaces import IInterface
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.size.interfaces import ISized

from zope.filerepresentation.interfaces import IRawReadFile
from zope.filerepresentation.interfaces import IRawWriteFile

from zope.filerepresentation.interfaces import IDirectoryFactory
from zope.filerepresentation.interfaces import IFileFactory

from ZPublisher.Iterators import IStreamIterator

from plone.dexterity.interfaces import DAV_FOLDER_DATA_ID
from plone.dexterity.filerepresentation import FolderDataResource

class DAVTestRequest(TestRequest):
    
    get_header = TestRequest.getHeader

class TestWebDAV(MockTestCase):
    
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
    
    pass
    
class TestFileRepresentation(MockTestCase):
    
    pass

class TestDAVTraversal(MockTestCase):
    
    pass

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
