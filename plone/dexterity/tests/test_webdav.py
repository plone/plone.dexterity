from .case import ItemDummy
from .case import MockTestCase
from email.message import Message
from io import StringIO
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.browser.traversal import DexterityPublishTraverse
from plone.dexterity.content import Container
from plone.dexterity.content import Item
from plone.dexterity.filerepresentation import DefaultDirectoryFactory
from plone.dexterity.filerepresentation import DefaultFileFactory
from plone.dexterity.filerepresentation import DefaultReadFile
from plone.dexterity.filerepresentation import DefaultWriteFile
from plone.dexterity.filerepresentation import FolderDataResource
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import DAV_FOLDER_DATA_ID
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.schema import SCHEMA_CACHE
from plone.rfc822.interfaces import IPrimaryField
from unittest.mock import Mock
from webdav.NullResource import NullResource
from zExceptions import Forbidden
from zExceptions import MethodNotAllowed
from zExceptions import Unauthorized
from zope import schema
from zope.component.interfaces import IFactory
from zope.filerepresentation.interfaces import IDirectoryFactory
from zope.filerepresentation.interfaces import IFileFactory
from zope.filerepresentation.interfaces import IRawReadFile
from zope.filerepresentation.interfaces import IRawWriteFile
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.publisher.browser import TestRequest
from zope.size.interfaces import ISized
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.Iterators import IStreamIterator

import re


XML_PROLOG = b'<?xml version="1.0" encoding="utf-8" ?>'


@provider(IFormFieldProvider)
class ITestBehavior(Interface):
    foo = schema.Int()
    bar = schema.Bytes()


class DAVTestRequest(TestRequest):

    get_header = TestRequest.getHeader

    def _createResponse(self):
        return HTTPResponse()


class TestWebZope2DAVAPI(MockTestCase):
    def test_get_size_no_adapter(self):
        item = Item("test")

        self.assertEqual(0, item.get_size())

    def test_get_size_wrong_adapter(self):
        class SizedAdapter:
            def __init__(self, context):
                self.context = context

            def sizeForSorting(self):
                return "lines", 10

            def sizeForDisplay(self):
                "10 lines"

        self.mock_adapter(SizedAdapter, ISized, (Item,))
        item = Item("test")

        self.assertEqual(0, item.get_size())

    def test_get_size_right_adapter(self):
        class SizedAdapter:
            def __init__(self, context):
                self.context = context

            def sizeForSorting(self):
                return "bytes", 10

            def sizeForDisplay(self):
                "10 bytes"

        self.mock_adapter(SizedAdapter, ISized, (Item,))
        item = Item("test")

        self.assertEqual(10, item.get_size())

    def test_content_type_no_adapter(self):
        item = Item("test")

        self.assertEqual(None, item.content_type())
        self.assertEqual(None, item.Format())

    def test_content_type_simple_adapter(self):
        class ReadFileAdapter:
            def __init__(self, context):
                self.context = context

            mimeType = "text/foo"
            # others omitted

        self.mock_adapter(ReadFileAdapter, IRawReadFile, (Item,))
        item = Item("test")

        self.assertEqual("text/foo", item.content_type())
        self.assertEqual("text/foo", item.Format())

    def test_get_no_adapter(self):
        item = Item("test")

        self.assertEqual("", item.manage_DAVget())

    def test_get_simple_adapter(self):
        class ReadFileAdapter:
            def __init__(self, context):
                self.context = context

            mimeType = "text/foo"
            encoding = "latin1"

            def size(self):
                return 10

            def read(self, size=None):
                return "1234567890"

        self.mock_adapter(ReadFileAdapter, IRawReadFile, (Item,))

        request = DAVTestRequest()

        item = Item("item")
        item.REQUEST = request

        self.assertEqual("1234567890", item.manage_DAVget())
        self.assertEqual(
            'text/foo; charset="latin1"', request.response.getHeader("Content-Type")
        )
        self.assertEqual("10", request.response.getHeader("Content-Length"))

    def test_get_minimal_adapter(self):
        class ReadFileAdapter:
            def __init__(self, context):
                self.context = context

            mimeType = None
            encoding = None

            def size(self):
                return None

            def read(self, size=None):
                return "1234567890"

        self.mock_adapter(ReadFileAdapter, IRawReadFile, (Item,))

        request = DAVTestRequest()

        item = Item("item")
        item.REQUEST = request

        self.assertEqual("1234567890", item.manage_DAVget())
        self.assertEqual(None, request.response.getHeader("Content-Type"))
        self.assertEqual(None, request.response.getHeader("Content-Length"))

    def test_get_streaming(self):
        @implementer(IStreamIterator)
        class ReadFileAdapter:
            def __init__(self, context):
                self.context = context

            mimeType = None
            encoding = None

            def size(self):
                return 10

            def read(self, size=None):
                return "1234567890"

        adapterInstance = ReadFileAdapter(None)

        def factory(context):
            return adapterInstance

        self.mock_adapter(factory, IRawReadFile, (Item,))

        request = DAVTestRequest()

        item = Item("item")
        item.REQUEST = request

        self.assertEqual(adapterInstance, item.manage_DAVget())

    def test_put_no_adapter(self):
        request = DAVTestRequest(environ={"BODYFILE": StringIO("")})

        item = Item("item")
        item.REQUEST = request

        self.assertRaises(MethodNotAllowed, item.PUT)

    def test_put_no_body(self):
        request = DAVTestRequest()

        item = Item("item")
        item.REQUEST = request

        self.assertRaises(MethodNotAllowed, item.PUT)

    def test_put_no_content_type_header(self):
        class WriteFile:
            def __init__(self, context):
                self.context = context
                self._written = ""
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

        request = DAVTestRequest(environ={"BODYFILE": StringIO("data")})

        item = Item("item")
        item.REQUEST = request

        item.PUT()
        self.assertEqual(None, adapterInstance.mimeType)
        self.assertEqual(None, adapterInstance.encoding)
        self.assertEqual("data", adapterInstance._written)
        self.assertEqual(True, adapterInstance._closed)

    def test_put_with_content_type_header_no_charset(self):
        class WriteFile:
            def __init__(self, context):
                self.context = context
                self._written = ""
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

        request = DAVTestRequest(
            environ={"BODYFILE": StringIO("data"), "HTTP_CONTENT_TYPE": "text/foo"}
        )

        item = Item("item")
        item.REQUEST = request

        item.PUT()
        self.assertEqual("text/foo", adapterInstance.mimeType)
        self.assertEqual(None, adapterInstance.encoding)
        self.assertEqual("data", adapterInstance._written)
        self.assertEqual(True, adapterInstance._closed)
        self.assertEqual(1, len(events))

    def test_put_with_content_type_header_and_charset(self):
        class WriteFile:
            def __init__(self, context):
                self.context = context
                self._written = ""
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

        request = DAVTestRequest(
            environ={
                "BODYFILE": StringIO("data"),
                "HTTP_CONTENT_TYPE": 'text/foo; charset="latin1"',
            }
        )

        item = Item("item")
        item.REQUEST = request

        item.PUT()
        self.assertEqual("text/foo", adapterInstance.mimeType)
        self.assertEqual("latin1", adapterInstance.encoding)
        self.assertEqual("data", adapterInstance._written)
        self.assertEqual(True, adapterInstance._closed)
        self.assertEqual(1, len(events))

    def test_mkcol_no_adapter(self):
        container = Container("container")
        self.assertRaises(MethodNotAllowed, container.MKCOL_handler, "test")

    def test_mkcol_simple_adapter(self):
        created = []

        class DirectoryFactory:
            def __init__(self, context):
                self.context = context

            def __call__(self, id):
                created.append(id)

        self.mock_adapter(DirectoryFactory, IDirectoryFactory, (Container,))

        container = Container("container")
        container.MKCOL_handler("test")
        self.assertEqual(["test"], created)

    def test_put_factory_no_adapter(self):
        container = Container("container")
        self.assertEqual(None, container.PUT_factory("test", "text/foo", "body"))

    def test_put_factory_simple_adapter(self):
        instance = object()

        class FileFactory:
            def __init__(self, context):
                self.context = context

            def __call__(self, name, contentType, body):
                return instance

        self.mock_adapter(FileFactory, IFileFactory, (Container,))
        container = Container("container")
        self.assertEqual(instance, container.PUT_factory("test", "text/foo", "body"))

    def test_list_without_items(self):
        class DummyContainer(Container):
            def listFolderContents(self, filter=None):
                return []

        container = DummyContainer("container")

        objects = container.listDAVObjects()
        self.assertEqual(1, len(objects))
        self.assertTrue(isinstance(objects[0], FolderDataResource))
        self.assertEqual(DAV_FOLDER_DATA_ID, objects[0].getId())
        self.assertEqual(container, objects[0].__parent__)

    def test_list_with_items(self):
        class DummyContainer(Container):
            def listFolderContents(self, filter=None):
                return [Item("foo")]

        container = DummyContainer("container")

        objects = container.listDAVObjects()
        self.assertEqual(2, len(objects))
        self.assertTrue(isinstance(objects[0], FolderDataResource))
        self.assertEqual(DAV_FOLDER_DATA_ID, objects[0].getId())
        self.assertEqual(container, objects[0].__parent__)
        self.assertEqual("foo", objects[1].getId())


class TestFolderDataResource(MockTestCase):
    def test_getId(self):
        container = Container("container")
        r = FolderDataResource("fdata", container)

        self.assertEqual("fdata", r.getId())
        self.assertEqual(container, r.__parent__)

    def test_HEAD(self):
        class TestContainer(Container):
            def get_size(self):
                return 10

            def content_type(self):
                return "text/foo"

        container = TestContainer("container")
        r = FolderDataResource("fdata", container).__of__(container)

        request = DAVTestRequest(environ={"URL": "http://example.org/site/container"})
        response = request.response

        self.assertEqual(response, r.HEAD(request, request.response))
        self.assertEqual(200, response.getStatus())
        self.assertTrue(response.getHeader("Content-Type").startswith("text/foo"))
        self.assertEqual("10", response.getHeader("Content-Length"))

    def test_OPTIONS(self):
        class TestContainer(Container):
            def get_size(self):
                return 10

            def content_type(self):
                return "text/foo"

        container = TestContainer("container")
        r = FolderDataResource("fdata", container).__of__(container)

        request = DAVTestRequest(environ={"URL": "http://example.org/site/container"})
        response = request.response

        self.assertEqual(response, r.OPTIONS(request, request.response))
        self.assertEqual(
            "GET, HEAD, POST, PUT, DELETE, OPTIONS, TRACE, PROPFIND, "
            "PROPPATCH, MKCOL, COPY, MOVE, LOCK, UNLOCK",
            response.getHeader("Allow"),
        )

    def test_TRACE(self):
        class TestContainer(Container):
            def get_size(self):
                return 10

            def content_type(self):
                return "text/foo"

        container = TestContainer("container")
        r = FolderDataResource("fdata", container).__of__(container)

        request = DAVTestRequest(environ={"URL": "http://example.org/site/container"})

        self.assertRaises(MethodNotAllowed, r.TRACE, request, request.response)

    def test_PROPFIND(self):
        class TestContainer(Container):
            def get_size(self):
                return 10

            def content_type(self):
                return "text/foo"

        container = TestContainer("container")
        container.manage_changeProperties(title="Container")
        r = FolderDataResource("fdata", container).__of__(container)

        request = DAVTestRequest(environ={"URL": "http://example.org/site/container"})
        response = request.response

        self.assertEqual(response, r.PROPFIND(request, response))
        self.assertEqual(
            'text/xml; charset="utf-8"', response.getHeader("Content-Type")
        )
        self.assertEqual(207, response.getStatus())

        body = (
            XML_PROLOG
            + b"""
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
        )

        result = response.getBody()
        result = re.sub(
            rb"<n:getlastmodified>.+</n:getlastmodified>",
            rb"<n:getlastmodified>...</n:getlastmodified>",
            result,
        )
        self.assertEqual(result.strip(), body.strip())

    def test_PROPPATCH(self):
        class TestContainer(Container):
            def get_size(self):
                return 10

            def content_type(self):
                return "text/foo"

        container = TestContainer("container")
        container.manage_changeProperties(title="Container")
        r = FolderDataResource("fdata", container).__of__(container)

        requestBody = """\
<?xml version="1.0" encoding="utf-8" ?>
<D:propertyupdate xmlns:D="DAV:"
                  xmlns:n="http://www.zope.org/propsets/default">
    <D:set>
        <D:prop>
            <n:title>New title</n:title>
          </D:prop>
     </D:set>
</D:propertyupdate>
"""

        request = DAVTestRequest(
            environ={
                "URL": "http://example.org/site/container",
                "BODY": requestBody,
            }
        )
        response = request.response

        self.assertEqual(response, r.PROPPATCH(request, response))

        self.assertEqual("New title", container.getProperty("title"))

        self.assertEqual(
            'text/xml; charset="utf-8"', response.getHeader("Content-Type")
        )
        self.assertEqual(207, response.getStatus())

        body = (
            XML_PROLOG
            + b"""
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
        )

        result = response.getBody()

        self.assertEqual(body.strip(), result.strip())

    def test_LOCK(self):
        # Too much WebDAV magic - just test that it delegates correctly
        class TestContainer(Container):
            def LOCK(self, request, response):
                self._locked = (
                    request,
                    response,
                )
                return response

        container = TestContainer("container")
        r = FolderDataResource("fdata", container).__of__(container)

        request = DAVTestRequest(environ={"URL": "http://example.org/site/container"})
        response = request.response

        self.assertEqual(response, r.LOCK(request, response))
        self.assertEqual((request, response), container._locked)

    def test_UNLOCK(self):
        # Too much WebDAV magic - just test that it delegates correctly
        class TestContainer(Container):
            def UNLOCK(self, request, response):
                self._unlocked = (
                    request,
                    response,
                )
                return response

        container = TestContainer("container")
        r = FolderDataResource("fdata", container).__of__(container)

        request = DAVTestRequest(environ={"URL": "http://example.org/site/container"})
        response = request.response

        self.assertEqual(response, r.UNLOCK(request, response))
        self.assertEqual((request, response), container._unlocked)

    def test_PUT(self):
        class TestContainer(Container):
            def PUT(self, request, response):
                self._put = (
                    request,
                    response,
                )
                return response

        container = TestContainer("container")
        r = FolderDataResource("fdata", container).__of__(container)

        request = DAVTestRequest(environ={"URL": "http://example.org/site/container"})
        response = request.response

        self.assertEqual(response, r.PUT(request, response))
        self.assertEqual((request, response), container._put)

    def test_MKCOL(self):
        container = Container("container")
        r = FolderDataResource("fdata", container).__of__(container)

        request = DAVTestRequest(environ={"URL": "http://example.org/site/container"})
        response = request.response

        self.assertRaises(MethodNotAllowed, r.MKCOL, request, response)

    def test_DELETE(self):
        container = Container("container")
        r = FolderDataResource("fdata", container).__of__(container)

        request = DAVTestRequest(environ={"URL": "http://example.org/site/container"})
        response = request.response

        self.assertRaises(MethodNotAllowed, r.DELETE, request, response)

    def test_COPY(self):
        container = Container("container")
        r = FolderDataResource("fdata", container).__of__(container)

        request = DAVTestRequest(environ={"URL": "http://example.org/site/container"})
        response = request.response

        self.assertRaises(MethodNotAllowed, r.COPY, request, response)

    def test_MOVE(self):
        container = Container("container")
        r = FolderDataResource("fdata", container).__of__(container)

        request = DAVTestRequest(environ={"URL": "http://example.org/site/container"})
        response = request.response

        self.assertRaises(MethodNotAllowed, r.MOVE, request, response)

    def test_manage_DAVget(self):
        class TestContainer(Container):
            def manage_DAVget(self):
                return "data"

        container = TestContainer("container")
        r = FolderDataResource("fdata", container).__of__(container)

        self.assertEqual("data", r.manage_DAVget())

    def test_manage_FTPget(self):
        class TestContainer(Container):
            def manage_FTPget(self):
                return "data"

        container = TestContainer("container")
        r = FolderDataResource("fdata", container).__of__(container)

        self.assertEqual("data", r.manage_FTPget())

    def test_listDAVObjects(self):
        container = Container("container")
        r = FolderDataResource("fdata", container).__of__(container)

        self.assertEqual([], r.listDAVObjects())


class TestFileRepresentation(MockTestCase):
    def create_dummy(self, **kw):
        return ItemDummy(**kw)

    def test_directory_factory(self):
        class TestContainer(Container):
            def manage_addFolder(self, name):
                self._added = name

        container = TestContainer("container")
        factory = DefaultDirectoryFactory(container)

        factory("foo")
        self.assertEqual("foo", container._added)

    def test_file_factory_finder_cruft(self):
        container = Container("container")
        factory = DefaultFileFactory(container)

        self.assertRaises(
            Unauthorized, factory, ".DS_Store", "application/octet-stream", "xxx"
        )
        self.assertRaises(
            Unauthorized, factory, "._test", "application/octet-stream", "xxx"
        )

    def test_file_factory_no_ctr(self):
        container = Container("container")

        from Products.CMFCore.utils import getToolByName

        self.patch_global(getToolByName, return_value=None)

        factory = DefaultFileFactory(container)

        self.assertEqual(None, factory("test.html", "text/html", "<html />"))

    def test_file_factory_no_fti(self):
        container = Container("container")

        ctr_mock = Mock()
        ctr_mock.findTypeName = Mock(return_value=None)
        self.mock_tool(ctr_mock, "content_type_registry")

        factory = DefaultFileFactory(container)

        self.assertEqual(None, factory("test.html", "text/html", "<html />"))

    def test_file_factory_not_allowed(self):
        container = Container("container")
        container.portal_type = "containertype"

        child_fti_mock = Mock()
        child_fti_mock.product = None
        container_fti_mock = Mock()
        container_fti_mock.allowType = Mock(return_value=False)
        ctr_mock = Mock()
        ctr_mock.findTypeName = Mock(return_value="childtype")
        pt_mock = Mock()
        pt_mock.getTypeInfo = Mock(side_effect=[child_fti_mock, container_fti_mock])
        self.mock_tool(ctr_mock, "content_type_registry")
        self.mock_tool(pt_mock, "portal_types")

        factory = DefaultFileFactory(container)

        self.assertRaises(Unauthorized, factory, "test.html", "text/html", "<html />")

    def test_file_factory_construction_not_allowed(self):
        container = Container("container")
        container.portal_type = "containertype"

        child_fti_mock = Mock()
        child_fti_mock.product = None
        child_fti_mock.isConstructionAllowed = Mock(return_value=False)
        container_fti_mock = Mock()
        container_fti_mock.allowType = Mock(return_value=True)
        ctr_mock = Mock()
        ctr_mock.findTypeName = Mock(return_value="childtype")
        pt_mock = Mock()
        pt_mock.getTypeInfo = Mock(side_effect=[child_fti_mock, container_fti_mock])
        self.mock_tool(ctr_mock, "content_type_registry")
        self.mock_tool(pt_mock, "portal_types")

        factory = DefaultFileFactory(container)

        self.assertRaises(Unauthorized, factory, "test.html", "text/html", "<html />")

    def test_file_factory_factory_method(self):
        result_dummy = self.create_dummy()
        container_mock = Mock()
        container_mock.invokeFactory = Mock(return_value="test-1.html")
        container_mock._getOb = Mock(return_value=result_dummy)
        container_mock._delObject = Mock()
        child_fti_mock = Mock()
        child_fti_mock.product = "FooProduct"
        ctr_mock = Mock()
        ctr_mock.findTypeName = Mock(return_value="childtype")
        pt_mock = Mock()
        pt_mock.getTypeInfo = Mock(return_value=child_fti_mock)
        self.mock_tool(ctr_mock, "content_type_registry")
        self.mock_tool(pt_mock, "portal_types")

        factory = DefaultFileFactory(container_mock)

        self.assertEqual(result_dummy, factory("test.html", "text/html", "<html />"))

    def test_file_factory_factory_utility(self):
        result_dummy = self.create_dummy(id="test.html")
        container_mock = Mock()
        child_fti_mock = Mock()
        child_fti_mock.isConstructionAllowed = Mock(return_value=True)
        child_fti_mock.product = None
        child_fti_mock.factory = "childtype-factory"
        container_fti_mock = Mock()
        container_fti_mock.allowType = Mock(return_value=True)
        ctr_mock = Mock()
        ctr_mock.findTypeName = Mock(return_value="childtype")
        pt_mock = Mock()
        pt_mock.getTypeInfo = Mock(side_effect=[child_fti_mock, container_fti_mock])
        self.mock_tool(ctr_mock, "content_type_registry")
        self.mock_tool(pt_mock, "portal_types")

        def factory(*args, **kwargs):
            return result_dummy

        self.mock_utility(factory, IFactory, name="childtype-factory")

        factory = DefaultFileFactory(container_mock)

        self.assertEqual(result_dummy, factory("test.html", "text/html", "<html />"))
        self.assertEqual(result_dummy.Title(), "test.html")

    def test_file_factory_content_type_factory_utility(self):
        container_mock = Mock()
        child_fti_mock = Mock()
        child_fti_mock.isConstructionAllowed = Mock(return_value=True)
        child_fti_mock.getId = Mock(return_value="childtype")
        child_fti_mock.product = None
        child_fti_mock.factory = "childtype-factory"
        container_fti_mock = Mock()
        container_fti_mock.allowType = Mock(return_value=True)
        ctr_mock = Mock()
        ctr_mock.findTypeName = Mock(return_value="childtype")
        pt_mock = Mock()
        pt_mock.getTypeInfo = Mock(side_effect=[child_fti_mock, container_fti_mock])
        self.mock_tool(ctr_mock, "content_type_registry")
        self.mock_tool(pt_mock, "portal_types")

        def factory(*args, **kwargs):
            return Item(*args, **kwargs)

        self.mock_utility(factory, IFactory, name="childtype-factory")

        factory = DefaultFileFactory(container_mock)

        item = factory("test.html", "text/html", "<html />")

        self.assertEqual("test.html", item.id)

    def test_readfile_mimetype_no_message_no_fields(self):
        class ITest(Interface):
            pass

        SCHEMA_CACHE.clear()
        fti_mock = DexterityFTI("testtype")
        fti_mock.lookupSchema = Mock(return_value=ITest)
        fti_mock.behaviors = []

        self.mock_utility(fti_mock, IDexterityFTI, name="testtype")

        item = Item("item")
        item.portal_type = "testtype"

        readfile = DefaultReadFile(item)

        self.assertEqual("text/plain", readfile.mimeType)

    def test_readfile_mimetype_no_message_no_primary_field(self):
        class ITest(Interface):
            title = schema.TextLine()

        SCHEMA_CACHE.clear()
        fti_mock = DexterityFTI("testtype")
        fti_mock.lookupSchema = Mock(return_value=ITest)
        fti_mock.behaviors = []

        self.mock_utility(fti_mock, IDexterityFTI, name="testtype")

        item = Item("item")
        item.portal_type = "testtype"

        readfile = DefaultReadFile(item)

        self.assertEqual("text/plain", readfile.mimeType)

    def test_readfile_mimetype_no_message_single_primary_field(self):
        class ITest(Interface):
            title = schema.TextLine()
            body = schema.Text()

        alsoProvides(ITest["body"], IPrimaryField)

        SCHEMA_CACHE.clear()
        fti_mock = DexterityFTI("testtype")
        fti_mock.lookupSchema = Mock(return_value=ITest)
        fti_mock.behaviors = []

        self.mock_utility(fti_mock, IDexterityFTI, name="testtype")

        item = Item("item")
        item.portal_type = "testtype"

        readfile = DefaultReadFile(item)

        self.assertEqual("text/plain", readfile.mimeType)

    def test_readfile_mimetype_no_message_multiple_primary_fields(self):
        class ITest(Interface):
            title = schema.TextLine()
            body = schema.Text()
            stuff = schema.Bytes()

        alsoProvides(ITest["body"], IPrimaryField)
        alsoProvides(ITest["stuff"], IPrimaryField)

        SCHEMA_CACHE.clear()
        fti_mock = DexterityFTI("testtype")
        fti_mock.lookupSchema = Mock(return_value=ITest)

        self.mock_utility(fti_mock, IDexterityFTI, name="testtype")
        item = Item("item")
        item.portal_type = "testtype"

        readfile = DefaultReadFile(item)

        self.assertEqual("message/rfc822", readfile.mimeType)

    def test_readfile_mimetype_additional_schemata(self):
        # This is mostly a test that utils.iterSchemata takes
        # IBehaviorAssignable into account.

        class ITest(Interface):
            title = schema.TextLine()

        class ITestAdditional(Interface):
            # Additional behavior on an item
            body = schema.Text()
            stuff = schema.Bytes()

        alsoProvides(ITestAdditional["body"], IPrimaryField)
        alsoProvides(ITestAdditional["stuff"], IPrimaryField)
        alsoProvides(ITestAdditional, IFormFieldProvider)

        class MockBehavior:
            def __init__(self, iface):
                self.interface = iface

        class MockBehaviorAssignable:
            def __init__(self, context):
                self.context = context

            def enumerateBehaviors(self):
                yield MockBehavior(ITestAdditional)

        SCHEMA_CACHE.clear()
        fti_mock = DexterityFTI("testtype")
        fti_mock.lookupSchema = Mock(return_value=ITest)

        self.mock_adapter(MockBehaviorAssignable, IBehaviorAssignable, (Item,))
        self.mock_utility(fti_mock, IDexterityFTI, name="testtype")
        item = Item("item")
        item.portal_type = "testtype"

        readfile = DefaultReadFile(item)

        self.assertEqual("message/rfc822", readfile.mimeType)

    def test_readfile_operations(self):
        class ITest(Interface):
            title = schema.TextLine()
            body = schema.Text()

        alsoProvides(ITest["body"], IPrimaryField)

        fti_mock = DexterityFTI("testtype")
        fti_mock.lookupSchema = Mock(return_value=ITest)
        fti_mock.behaviors = [ITestBehavior.__identifier__]

        self.mock_utility(fti_mock, IDexterityFTI, name="testtype")

        item = Item("item")
        item.portal_type = "testtype"

        readfile = DefaultReadFile(item)

        message = Message()
        message["title"] = "Test title"
        message["foo"] = "10"
        message["bar"] = "xyz"
        message.set_payload("<p>body</p>")

        from plone.rfc822 import constructMessageFromSchemata

        self.patch_global(constructMessageFromSchemata, return_value=message)

        body = b"""\
title: Test title
foo: 10
bar: xyz
Portal-Type: testtype

<p>body</p>"""

        # iter
        # next

        self.assertEqual(body, readfile.read())
        self.assertEqual(69, readfile.size())
        self.assertEqual("utf-8", readfile.encoding)
        self.assertEqual(None, readfile.name)
        self.assertEqual("text/plain", readfile.mimeType)

        readfile.seek(2)
        self.assertEqual(2, readfile.tell())
        self.assertEqual(b"tl", readfile.read(2))
        self.assertEqual(4, readfile.tell())

        readfile.seek(0, 2)
        self.assertEqual(69, readfile.tell())

        readfile.seek(0)
        self.assertEqual(b"foo: 10\n", readfile.readlines()[1])

        readfile.seek(0)
        self.assertEqual(b"foo: 10\n", readfile.readlines(100)[1])

        readfile.seek(0)
        self.assertEqual(b"title: Test title\n", readfile.readline())

        readfile.seek(0)
        self.assertEqual(b"title: Test title\n", readfile.readline(100))

        readfile.seek(0)
        self.assertEqual(b"foo: 10\n", list(iter(readfile))[1])

        self.assertEqual(False, readfile.closed)
        readfile.close()

    def test_writefile_file_operations(self):
        class ITest(Interface):
            title = schema.TextLine()
            body = schema.Text()

        alsoProvides(ITest["body"], IPrimaryField)

        fti_mock = DexterityFTI("testtype")
        fti_mock.lookupSchema = Mock(return_value=ITest)
        fti_mock.behaviors = [ITestBehavior.__identifier__]

        self.mock_utility(fti_mock, IDexterityFTI, name="testtype")

        item = Item("item")
        item.portal_type = "testtype"
        item.title = "Test title"
        item.foo = 10
        item.bar = "xyz"
        item.body = "<p>body</p>"

        writefile = DefaultWriteFile(item)

        body = b"""\
title: Test title
foo: 10
bar: xyz
Portal-Type: testtype

<p>body</p>"""

        from plone.rfc822 import initializeObjectFromSchemata

        self.patch_global(initializeObjectFromSchemata)

        writefile.mimeType = "text/plain"
        self.assertEqual("text/plain", writefile.mimeType)

        writefile.encoding = "latin1"
        self.assertEqual("latin1", writefile.encoding)

        writefile.filename = "test.html"
        self.assertEqual("test.html", writefile.filename)

        self.assertEqual(False, writefile.closed)
        self.assertEqual(0, writefile.tell())

        writefile.writelines(["one\n", "two"])
        self.assertEqual(7, writefile.tell())

        self.assertRaises(NotImplementedError, writefile.truncate)

        writefile.truncate(0)
        self.assertEqual(0, writefile.tell())

        self.assertRaises(NotImplementedError, writefile.seek, 10)

        writefile.write(body[:10])
        writefile.write(body[10:])
        writefile.close()

        self.assertEqual(True, writefile.closed)
        self.assertEqual(69, writefile.tell())


class TestDAVTraversal(MockTestCase):
    def test_no_acquire_dav(self):
        container = Container("container")

        outer = Folder("outer")
        outer._setOb("item", SimpleItem("item"))
        outer._setOb("container", container)

        request = DAVTestRequest(
            environ={"URL": "http://site/test", "REQUEST_METHOD": "PUT"}
        )
        request.maybe_webdav_client = True

        traversal = DexterityPublishTraverse(container.__of__(outer), request)

        r = traversal.publishTraverse(request, "item")

        self.assertTrue(isinstance(r, NullResource))
        self.assertEqual(container, r.aq_parent)

    def test_acquire_without_dav(self):
        container = Container("container")

        outer = Folder("outer")
        outer._setObject("item", SimpleItem("item"))
        outer._setOb("container", container)

        request = DAVTestRequest(
            environ={"URL": "http://site/test", "REQUEST_METHOD": "GET"}
        )
        request.maybe_webdav_client = False

        traversal = DexterityPublishTraverse(container.__of__(outer), request)

        r = traversal.publishTraverse(request, "item")

        self.assertEqual(r.aq_base, outer["item"].aq_base)
        self.assertEqual(container, r.aq_parent)

    def test_folder_data_traversal_dav(self):
        container = Container("test")
        request = DAVTestRequest(environ={"URL": "http://site/test"})
        request.maybe_webdav_client = True

        traversal = DexterityPublishTraverse(container, request)

        r = traversal.publishTraverse(request, DAV_FOLDER_DATA_ID)

        self.assertEqual(DAV_FOLDER_DATA_ID, r.__name__)
        self.assertEqual(container, r.__parent__)
        self.assertEqual(container, r.aq_parent)

    def test_folder_data_traversal_without_dav(self):
        container = Container("test")
        request = DAVTestRequest(environ={"URL": "http://site/test"})
        request.maybe_webdav_client = False

        traversal = DexterityPublishTraverse(container, request)

        self.assertRaises(
            Forbidden, traversal.publishTraverse, request, DAV_FOLDER_DATA_ID
        )

    def test_browser_default_dav(self):
        class TestContainer(Container):
            def __browser_default__(self, request):
                return self, ("foo",)

        container = TestContainer("container")
        request = DAVTestRequest(
            environ={"URL": "http://site/test", "REQUEST_METHOD": "PROPFIND"}
        )
        request.maybe_webdav_client = True

        traversal = DexterityPublishTraverse(container, request)

        self.assertEqual(
            (
                container,
                (),
            ),
            traversal.browserDefault(request),
        )

    def test_browser_default_dav_get(self):
        class TestContainer(Container):
            def __browser_default__(self, request):
                return self, ("foo",)

        container = TestContainer("container")
        request = DAVTestRequest(
            environ={"URL": "http://site/test", "REQUEST_METHOD": "GET"}
        )
        request.maybe_webdav_client = True

        traversal = DexterityPublishTraverse(container, request)

        self.assertEqual(
            (
                container,
                ("foo",),
            ),
            traversal.browserDefault(request),
        )

    def test_browser_default_without_dav(self):
        class TestContainer(Container):
            def __browser_default__(self, request):
                return self, ("foo",)

        container = TestContainer("container")
        request = DAVTestRequest(
            environ={"URL": "http://site/test", "REQUEST_METHOD": "PROPFIND"}
        )
        request.maybe_webdav_client = False

        traversal = DexterityPublishTraverse(container, request)

        self.assertEqual(
            (
                container,
                ("foo",),
            ),
            traversal.browserDefault(request),
        )
