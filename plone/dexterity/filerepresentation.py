import tempfile

# capitalised for Python 2.4 compatibility
from email.Generator import Generator
from email.Parser import FeedParser

from rwproperty import getproperty, setproperty

from zope.interface import implements
from zope.component import adapts
from zope.schema import getFieldsInOrder

from zope.interface.interfaces import IInterface

from Acquisition import aq_base
from ZPublisher.Iterators import IStreamIterator
from Products.CMFCore.utils import getToolByName

from zope.filerepresentation.interfaces import IRawReadFile
from zope.filerepresentation.interfaces import IRawWriteFile

from zope.filerepresentation.interfaces import IDirectoryFactory
from zope.filerepresentation.interfaces import IFileFactory

from plone.rfc822.interfaces import IPrimaryField
from plone.rfc822 import constructMessageFromSchemata
from plone.rfc822 import initializeObjectFromSchemata

from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityContainer

from plone.dexterity.utils import iterSchemata
from plone.memoize.instance import memoize

class StringStreamIterator(object):
    """Simple stream iterator to allow efficient data streaming.
    """
    
    # Stupid workaround for the fact that on Zope < 2.12, we don't have
    # a real interface
    if IInterface.providedBy(IStreamIterator):
        implements(IStreamIterator)
    else:
        __implements__ = (IStreamIterator,)
    
    def __init__(self, data, size=None, chunk=1<<16):
        """Consume data (a str) into a temporary file and prepare streaming.
        
        size is the length of the data. If not given, the length of the data
        string is used.
        
        chunk is the chunk size for the iterator
        """
        f = tempfile.TemporaryFile(mode='w+b')
        f.write(data)
        
        if size is not None:
            assert size == f.tell(), 'Size argument does not match data length'
        else:
            size = f.tell()
        
        f.seek(0)
        
        self.file = f
        self.size = size
        self.chunk = chunk
    
    def __iter__(self):
        return self
    
    def next(self):
        data = self.file.read(self.chunk)
        if not data:
            self.file.close()
            raise StopIteration
        return data
    
    def __len__(self):
        return self.size


class DefaultDirectoryFactory(object):
    """Default directory factory, invoked when an FTP/WebDAV operation
    attempts to create a new folder via a MKCOL request.
    
    The default implementation simply calls manage_addFolder().
    """
    
    implements(IDirectoryFactory)
    adapts(IDexterityContainer)
    
    def __init__(self, context):
        self.context = context
    
    def __call__(self, name):
        self.context.manage_addFolder(name)


class DefaultFileFactory(object):
    """Default file factory, invoked when an FTP/WebDAV operation
    attempts to create a new resource via a PUT request.
    
    The default implementation uses the content_type_registry to find a
    type to add, and then creates an instance using the portal_types
    tool.
    """
    
    implements(IFileFactory)
    adapts(IDexterityContainer)
    
    def __init__(self, context):
        self.context = context
    
    def __call__(self, name, contentType, data):
        
        # Deal with Finder cruft
        if name == '.DS_Store':
            return None
        elif name.startswith('._'):
            return None
        
        registry = getToolByName(self.context, 'content_type_registry', None)
        if registry is None:
            return None
        
        typeObjectName = registry.findTypeName(name, contentType, data)
        if typeObjectName is None:
            return None
        
        self.context.invokeFactory(typeObjectName, name)
        
        # invokeFactory does too much, so the object has to be removed again
        # this is extremely lame, but old style factories have to work this
        # way. If we only had new-style factories, we could just call the
        # factory and return the result
        
        obj = aq_base(self.context._getOb(name))
        self.context._delObject(name)
        return obj


class DefaultReadFile(object):
    """IRawReadFile adapter for Dexterity objects.
    
    Uses RFC822 marshaler.
    
    This is also marked as an IStreamIterator, which means that it is safe
    to return it to the publisher directly. In particular, the size() method
    will return an accurate file size.
    """
    
    # Stupid workaround for the fact that on Zope < 2.12, we don't have
    # a real interface
    if IInterface.providedBy(IStreamIterator):
        implements(IRawReadFile, IStreamIterator)
    else:
        implements(IRawReadFile)
        __implements__ = (IStreamIterator,)        
    
    adapts(IDexterityContent)
    
    def __init__(self, context):
        self.context = context
        self._haveMessage = False
    
    @property
    def mimeType(self):
        if not self._haveMessage:
            single = True
            for schema in iterSchemata(self.context):
                for name, field in getFieldsInOrder(schema):
                    if IPrimaryField.providedBy(schema):
                        if single:
                            # more than one primary field
                            return 'message/rfc822'
                        else:
                            single = True
            # zero or one primary fields
            return 'text/plain'
        if not self._getMessage().is_multipart():
            return 'text/plain'
        else:
            return 'message/rfc822'
    
    @property
    def encoding(self):
        return self._getMessage().get_charset() or 'utf-8'
    
    @property
    def closed(self):
        return self._getStream().closed
    
    @property
    def name(self):
        return self._getMessage().get_filename(None)
    
    def size(self):
        # construct the stream if necessary
        self._getStream()
        return self._size
    
    def seek(self, offset, whence=None):
        self._getStream().seek(offset, whence)
    
    def tell(self):
        self._getStream().tell()
    
    def close(self):
        self._getStream().close()
    
    def read(self, size=None):
        return self._getStream().read(size)
    
    def readline(self, size=None):
        return self._getStream().readline(size)
    
    def readlines(self, sizehint=None):
        return self._getStream().readlines(sizehint)
    
    def __iter__(self):
        return self
    
    def next(self):
        return self._getStream().next()
    
    # internal helper methods
    
    @memoize
    def _getMessage(self):
        """Construct message on demand
        """
        message = constructMessageFromSchemata(self.context, iterSchemata(self.context))
        
        # Store the portal type in a header, to allow it to be identifed later
        message['Portal-Type'] = self.context.portal_type
        
        return message
    
    @memoize
    def _getStream(self):
        out = tempfile.TemporaryFile(mode='w+b')
        generator = Generator(out, mangle_from_=False)
        generator.flatten(self._getMessage())
        self._size = out.tell()
        out.seek(0)
        return out


class DefaultWriteFile(object):
    """IRawWriteFile file adapter for Dexterity objects.
    
    Uses RFC822 marshaler.
    """
    
    implements(IRawWriteFile)
    adapts(IDexterityContent)
    
    def __init__(self, context):
        self.context = context
        
        self._mimeType = None
        self._encoding = 'utf-8'
        self._closed = False
        self._name = None
        self._written = 0
        self._parser = FeedParser()
        self._message = None
    
    @getproperty
    def mimeType(self):
        if self._message is None:
            return self._mimeType
        elif not self._message.is_multipart():
            return 'text/plain'
        else:
            return 'message/rfc822'
    
    @setproperty
    def mimeType(self, value):
        self._mimeType = value
    
    @getproperty
    def encoding(self):
        if self._message is not None:
            return self._message.get_charset() or self._encoding
        return self._encoding
    
    @setproperty
    def encoding(self, value):
        self._encoding = value
    
    @property
    def closed(self):
        return self._closed
    
    @getproperty
    def name(self):
        if self._message is not None:
            return self._message.get_filename(self._name)
        return self._name
    @setproperty
    def name(self, value):
        self._name = value
    
    def seek(self, offset, whence=None):
        raise NotImplemented("Seeking is not supported")
    
    def tell(self):
        self._written
    
    def close(self):
        self._message = self._parser.close()
        self._closed = True
        initializeObjectFromSchemata(self.context, iterSchemata(self.context), self._message, self._encoding)
    
    def write(self, data):
        if self._closed:
            raise ValueError("File is closed")
        self._written += len(data)
        self._parser.feed(data)
    
    def writelines(self, sequence):
        for item in sequence:
            self.write(item)
    
    def truncate(self, size):
        if self._closed:
            raise ValueError("File is closed")
        self._parser = FeedParser()
        self._written = 0
    
    def flush(self):
        pass
