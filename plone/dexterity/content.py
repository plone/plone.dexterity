# Use python 2.4 import location
from email.Message import Message

from Acquisition import Explicit, aq_parent

from zope.component import queryUtility
from zope.lifecycleevent import modified

from zope.interface import implements
from zope.interface.declarations import Implements
from zope.interface.declarations import implementedBy
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import ObjectSpecificationDescriptor

from zope.security.interfaces import IPermission

from zope.annotation import IAttributeAnnotatable

from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityItem
from plone.dexterity.interfaces import IDexterityContainer

from plone.dexterity.schema import SCHEMA_CACHE

# XXX: Should move to zope.container in the future
from zope.app.container.contained import Contained

from AccessControl import getSecurityManager

from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.PortalFolder import PortalFolderBase
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware

from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin

from plone.folder.ordered import CMFOrderedBTreeFolderBase

from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.supermodel.utils import mergedTaggedValueDict

from zope.size.interfaces import ISized

from zope.filerepresentation.interfaces import IRawReadFile
from zope.filerepresentation.interfaces import IRawWriteFile

from zope.filerepresentation.interfaces import IFileFactory
from zope.filerepresentation.interfaces import IDirectoryFactory

_marker = object()

class FTIAwareSpecification(ObjectSpecificationDescriptor):
    """A __providedBy__ decorator that returns the interfaces provided by
    the object, plus the schema interface set in the FTI.
    """
    
    def __get__(self, inst, cls=None):
        
        # We're looking at a class - fall back on default
        if inst is None:
            return getObjectSpecification(cls)
        
        # Find the cached value. This calculation is expensive and called
        # hundreds of times during each request, so we require a fast cache
        cache = getattr(inst, '_v__providedBy__', None)
        
        # Find the data we need to know if our cache needs to be invalidated
        
        direct_spec = getattr(inst, '__provides__', None)
        portal_type = getattr(inst, 'portal_type', None)
        
        fti_counter = -1
        if portal_type is not None:
            fti_counter = SCHEMA_CACHE.counter(portal_type)
        
        # See if we have a valid cache. Reasons to do this include:
        # 
        #  - We don't have a portal_type yet, so we can't have found the schema
        #  - The FTI was modified, and the schema cache invalidated globally.
        #    The fti_counter will have advanced.
        #  - The instance was modified and persisted since the cache was built.
        #  - The instance now has a different __provides__, which means that someone
        #    called directlyProvides/alsoProvides on it.
        
        if cache is not None and portal_type is not None:
            cached_mtime, cached_fti_counter, cached_direct_spec, cached_spec = cache
            
            if inst._p_mtime == cached_mtime and \
                    fti_counter == cached_fti_counter and \
                    direct_spec is cached_direct_spec:
                return cached_spec
        
        # We don't have a cache, so we need to build a new spec and maybe cache it
        
        spec = direct_spec
        
        # If the instance doesn't have a __provides__ attribute, get the
        # interfaces implied by the class as a starting point.
        if spec is None:
            spec = implementedBy(cls)
        
        # Add the schema from the FTI and behavior subtypes
        
        dynamically_provided = []
        
        if portal_type is not None:
            schema = SCHEMA_CACHE.get(portal_type)
            if schema is not None:
                dynamically_provided.append(schema)
            
            subtypes = SCHEMA_CACHE.subtypes(portal_type)
            if subtypes:
                dynamically_provided.extend(subtypes)
        
        # If we have any dynamically provided interface, prepend them to the spec
        # and cache. We can't cache until we have at least the schema, because
        # it's possible that we were called before traversal and so could not
        # find the schema yet.
        
        if dynamically_provided:
            dynamically_provided.append(spec)
            spec = Implements(*dynamically_provided)
            
            inst._v__providedBy__ = inst._p_mtime, SCHEMA_CACHE.counter(portal_type), direct_spec, spec
        
        return spec

class AttributeValidator(Explicit):
    """Decide whether attributes should be accessible. This is set as the
    __allow_access_to_unprotected_subobjects__ variable in Dexterity's content
    classes.
    """
    
    def __call__(self, name, value):
        
        # Short circuit for things like views or viewlets
        if name == '':
            return 1
        
        context = aq_parent(self)
        
        schema = self._get_schema(context)
        if schema is None:
            return 1
        
        info = mergedTaggedValueDict(schema, READ_PERMISSIONS_KEY)
        
        if name not in info:
            return 1
        
        permission = queryUtility(IPermission, name=info[name])
        if permission is not None:
            return getSecurityManager().checkPermission(permission.title, context)
        
        return 0
    
    def _get_schema(self, inst):
        portal_type = getattr(inst, 'portal_type', None)
        if portal_type is not None:
            try:
                return SCHEMA_CACHE.get(portal_type)
            except (ValueError, AttributeError,):
                pass
        return None

class DexterityContent(PortalContent, DefaultDublinCoreImpl, Contained):
    """Base class for Dexterity content
    """
    implements(IDexterityContent, IAttributeAnnotatable)
    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()
    
    # portal_type is set by the add view and/or factory
    portal_type = None
    
    def __getattr__(self, name):
        
        # attribute was not found; try to look it up in the schema and return
        # a default
        
        schema = SCHEMA_CACHE.get(self.portal_type)
        if schema is not None:
            field = schema.get(name, None)
            if field is not None:
                return field.default
        
        raise AttributeError(name)
    
    # Let __name__ and id be identical. Note that id must be ASCII in Zope 2,
    # but __name__ should be unicode. Note that setting the name to something
    # that can't be encoded to ASCII will throw a UnicodeEncodeError

    def _get__name__(self):
        return unicode(self.id)
    def _set__name__(self, value):
        if isinstance(value, unicode):
            value = str(value) # may throw, but that's OK - id must be ASCII
        self.id = value
    __name__ = property(_get__name__, _set__name__)
    
    # WebDAV/FTP support
    
    def get_size(self):
        sized = ISized(self, None)
        if sized is None:
            return None
        unit, size = sized.sizeForSorting()
        if unit == 'bytes':
            return size
        return None
    
    def content_type(self):
        """Return the content type of the tiem
        """
        return self.Format()
    
    def Format(self):
        """Return the content type of the item
        """
        readFile = IRawReadFile(self, None)
        if readFile is None:
            return None
        return readFile.mimeType

    def manage_DAVget(self):
        """Get the body of the content item in a WebDAV response
        """
        return self.manage_FTPget()
    
    def manage_FTPget(self, REQUEST=None, RESPONSE=None):
        """Return the body of the content item in an FTP response
        """
        
        reader = IRawReadFile(self, None)
        if reader is None:
            return ''
        
        request = REQUEST is not None and REQUEST or self.REQUEST
        response = RESPONSE is not None and RESPONSE or request.response
        
        mimeType = reader.mimeType
        encoding = reader.encoding
        
        if mimeType is not None:
            if encoding is not None:
                response.setHeader('Content-Type', '%s; charset="%s"' % (mimeType, encoding,))
            else:
                response.setHeader('Content-Type', mimeType)
        
        size = reader.size()
        if size is not None:
            response.setHeader('Content-Length', size)
        
        # the reader is an iterator
        return reader
    
    def PUT(self, REQUEST=None, RESPONSE=None):
        """WebDAV method to replace self with a new resource.
        """
        
        request = REQUEST is not None and REQUEST or self.REQUEST
        response = RESPONSE is not None and RESPONSE or request.response
        
        self.dav__init(request, response)
        self.dav__simpleifhandler(request, response, refresh=1)
        
        infile = request.get('BODYFILE', None)
        if infile is None:
            raise KeyError("No BODYFILE in request")
        
        writer = IRawWriteFile(self)
        contentTypeHeader = request.get_header('content-type', None)
        
        if contentTypeHeader is not None:
            msg = Message()
            msg['Content-Type'] = contentTypeHeader
            
            mimeType = msg.get_content_type()
            if mimeType is not None:
                writer.mimeType = mimeType
            
            charset = msg.get_param('charset')
            if charset is not None:
                writer.encoding = charset
        
        try:
            for chunk in infile:
                writer.write(chunk)
        finally:
            writer.close()
        
        # TODO: detect if object was just created, and if so fire an object
        # created event instead
        modified(self)

# XXX: It'd be nice to reduce the number of base classes here

class Item(BrowserDefaultMixin, DexterityContent):
    """A non-containerish, CMFish item
    """
    
    implements(IDexterityItem)
    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()
    
    isPrincipiaFolderish = 0
    
    def __init__(self, id=None, **kwargs):
        PortalContent.__init__(self, id, **kwargs)
        DefaultDublinCoreImpl.__init__(self, **kwargs)
        
        if id is not None:
            self.id = id
    
    # Be explicit about which __getattr__ to use
    __getattr__ = DexterityContent.__getattr__

class Container(BrowserDefaultMixin, CMFCatalogAware, CMFOrderedBTreeFolderBase, DexterityContent):
    """Base class for folderish items
    """
    
    implements(IDexterityContainer)
    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()
    
    isPrincipiaFolderish = 1
    
    # make sure CMFCatalogAware's manage_options don't take precedence
    manage_options = PortalFolderBase.manage_options

    def __init__(self, id=None, **kwargs):
        CMFOrderedBTreeFolderBase.__init__(self, id, **kwargs)
        DefaultDublinCoreImpl.__init__(self, **kwargs)
        
        if id is not None:
            self.id = id
    
    def __getattr__(self, name):
        
        # attribute was not found; try to look it up in the schema and return
        # a default
        
        schema = SCHEMA_CACHE.get(self.portal_type)
        if schema is not None:
            field = schema.get(name, None)
            if field is not None:
                return field.default
        
        # Be specific about the implementation we use
        return CMFOrderedBTreeFolderBase.__getattr__(self, name)
    
    # WebDAV/FTP support
    
    def MKCOL_handler(self, id, REQUEST=None, RESPONSE=None):
        """Handle "make collection" by delegating to an IDirectoryFactory
        adapter.
        """
        factory = IDirectoryFactory(self)
        factory(id)
    
    def PUT_factory(self, name, contentType, body):
        """Handle constructing a new object upon a PUT request by delegating
        to an IFileFactory adapter
        """
        factory = IFileFactory(self)
        return factory(name, contentType, body)
    
def reindexOnModify(content, event):
    """When an object is modified, re-index it in the catalog
    """
    
    if event.object is not content:
        return
    
    # NOTE: We are not using event.descriptions because the field names may
    # not match index names.
    
    content.reindexObject()
