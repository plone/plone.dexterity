from Acquisition import aq_base
from Acquisition import aq_inner
from AccessControl import Unauthorized

from zope.component import getUtility, queryUtility
from zope.component import createObject

from zope.dottedname.resolve import resolve

from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityFTI

from Products.CMFCore.interfaces import ISiteRoot

# XXX: Should move to zope.container in the future
from zope.app.container.interfaces import INameChooser

# Not thread safe, but downside of a write conflict is very small
_dottedCache = {}

def resolveDottedName(dottedName):
    """Resolve a dotted name to a real object
    """
    global _dottedCache
    if dottedName not in _dottedCache:
        _dottedCache[dottedName] = resolve(dottedName)
    return _dottedCache[dottedName]

# Schema name encoding

class SchemaNameEncoder(object):

    key = (
        (' ', '_1_'),
        ('.', '_2_'),
        ('-', '_3_'),
        ('/', '_4_'),
        )

    def encode(self, s):
        for k,v in self.key:
            s = s.replace(k, v)
        return s
    
    def decode(self, s):
        for k,v in self.key:
            s = s.replace(v, k)
        return s

    def join(self, *args):
        return '_0_'.join([self.encode(a) for a in args if a])
    
    def split(self, s):
        return [self.decode(a) for a in s.split('_0_')]

def portalTypeToSchemaName(portal_type, schema=u"", prefix=None):
    """Return a canonical interface name for a generated schema interface.
    """
    if prefix is None:
        prefix = '/'.join(getUtility(ISiteRoot).getPhysicalPath())[1:]
    
    encoder = SchemaNameEncoder()
    return encoder.join(prefix, portal_type, schema)
        
def schemaNameToPortalType(schemaName):
    """Return a the portal_type part of a schema name
    """
    encoder = SchemaNameEncoder()
    return encoder.split(schemaName)[1]

def splitSchemaName(schemaName):
    """Return a tuple prefix, portal_type, schemaName
    """
    encoder = SchemaNameEncoder()
    items = encoder.split(schemaName)
    if len(items) == 2:
        return items[0], items[1], u""
    elif len(items) == 3:
        return items[0], items[1], items[2]
    else:
        raise ValueError("Schema name %s is invalid" % schemaName)

def iterSchemata(content):
    """Return an iterable containing first the object's schema, and then
    any form field schemata for any enabled behaviors.
    """
    
    fti = queryUtility(IDexterityFTI, name=content.portal_type)
    if fti is None:
        return
    
    yield fti.lookupSchema()
    
    for behavior in fti.behaviors:
        try:
            behaviorInterface = resolveDottedName(behavior)
        except ValueError:
            continue
        if behaviorInterface is not None:
            behaviorSchema = IFormFieldProvider(behaviorInterface, None)
            if behaviorSchema is not None:
                yield behaviorSchema

def createContent(portal_type, **kw):
    fti = getUtility(IDexterityFTI, name=portal_type)
    content = createObject(fti.factory)

    # Note: The factory may have done this already, but we want to be sure
    # that the created type has the right portal type. It is possible
    # to re-define a type through the web that uses the factory from an
    # existing type, but wants a unique portal_type!
    content.portal_type = fti.getId()

    for (key,value) in kw.items():
        setattr(content, key, value)

    return content


def addContentToContainer(container, object, checkConstraints=True):
    """Add an object to a container.

    The portal_type must already be set correctly. If checkConstraints
    is False no check for addable content types is done. The new object,
    wrapped in its new acquisition context, is returned.
    """
    if not hasattr(aq_base(object), "portal_type"):
        raise ValueError("object must have its portal_type set")

    container = aq_inner(container)
    if checkConstraints:
        container_fti = container.getTypeInfo()

        fti = getUtility(IDexterityFTI, name=object.portal_type)
        if not fti.isConstructionAllowed(container):
            raise Unauthorized("Cannot create %s" % object.portal_type)
        
        if container_fti is not None and not container_fti.allowType(object.portal_type):
            raise ValueError("Disallowed subobject type: %s" % object.portal_type)

    name = INameChooser(container).chooseName(None, object)
    object.id = name

    newName = container._setObject(name, object)
    return container._getOb(newName)

def createContentInContainer(container, portal_type, checkConstraints=True, **kw):
    content = createContent(portal_type, **kw)
    return addContentToContainer(container, content, checkConstraints=checkConstraints)

