import logging

from Acquisition import aq_base
from Acquisition import aq_inner
from AccessControl import Unauthorized

from zope.component import getUtility, queryUtility
from zope.component import createObject

from zope.dottedname.resolve import resolve
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent

from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.interfaces import IDexterityFTI

from Products.CMFCore.interfaces import ISiteRoot

# XXX: Should move to zope.container in the future
from zope.app.container.interfaces import INameChooser

try:
    from plone.uuid.interfaces import IUUID
    from plone.app.uuid.utils import uuidToObject
    HAS_UUID = True
except ImportError:
    HAS_UUID = False

log = logging.getLogger(__name__)

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
    for schema in getAdditionalSchemata(context=content):
        yield schema


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

    notify(ObjectCreatedEvent(content))
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
    try:
        return container._getOb(newName)
    except AttributeError:
        if HAS_UUID:
            # work around edge case where a content rule may have moved the item
            uuid = IUUID(object)
            return uuidToObject(uuid)
        else:
            # no way to know where it is
            raise


def createContentInContainer(container, portal_type, checkConstraints=True, **kw):
    content = createContent(portal_type, **kw)
    return addContentToContainer(container, content, checkConstraints=checkConstraints)


def getAdditionalSchemata(context=None, portal_type=None):
    """Get additional schemata for this context or this portal_type.

    Additional schemata can be defined in behaviors.

    Usually either context or portal_type should be set, not both.
    The idea is that for edit forms or views you pass in a context
    (and we get the portal_type from there) and for add forms you pass
    in a portal_type (and the context is irrelevant then).  If both
    are set, the portal_type might get ignored, depending on which
    code path is taken.
    """
    log.debug("getAdditionalSchemata with context %r and portal_type %s",
              context, portal_type)
    if context is None and portal_type is None:
        return
    if context:
        behavior_assignable = IBehaviorAssignable(context, None)
    else:
        behavior_assignable = None
    if behavior_assignable is None:
        log.debug("No behavior assignable found, only checking fti.")
        # Usually an add-form.
        if portal_type is None:
            portal_type = context.portal_type
        fti = getUtility(IDexterityFTI, name=portal_type)
        for behavior_name in fti.behaviors:
            try:
                behavior_interface = resolveDottedName(behavior_name)
            except (ValueError, ImportError):
                log.warning("Error resolving behaviour %s", behavior_name)
                continue
            if behavior_interface is not None:
                behavior_schema = IFormFieldProvider(behavior_interface, None)
                if behavior_schema is not None:
                    yield behavior_schema
    else:
        log.debug("Behavior assignable found for context.")
        for behavior_reg in behavior_assignable.enumerateBehaviors():
            behavior_schema = IFormFieldProvider(behavior_reg.interface, None)
            if behavior_schema is not None:
                yield behavior_schema
