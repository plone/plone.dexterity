from Acquisition import aq_base
from Acquisition import aq_inner
from AccessControl import Unauthorized
from zope.component import getUtility
from zope.component import createObject
from zope.app.container.interfaces import INameChooser
from zope.dottedname.resolve import resolve
from plone.dexterity.interfaces import IDexterityFTI
from Products.CMFCore.interfaces import ISiteRoot

# Not thread safe, but downside of a write conflict is very small
_dotted_cache = {}

def resolve_dotted_name(dotted_name):
    """Resolve a dotted name to a real object
    """
    global _dotted_cache
    if dotted_name not in _dotted_cache:
        _dotted_cache[dotted_name] = resolve(dotted_name)
    return _dotted_cache[dotted_name]

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

def portal_type_to_schema_name(portal_type, schema=u"", prefix=None):
    """Return a canonical interface name for a generated schema interface.
    """
    if prefix is None:
        prefix = '/'.join(getUtility(ISiteRoot).getPhysicalPath())[1:]
    
    encoder = SchemaNameEncoder()
    return encoder.join(prefix, portal_type, schema)
        
def schema_name_to_portal_type(schema_name):
    """Return a the portal_type part of a schema name
    """
    encoder = SchemaNameEncoder()
    return encoder.split(schema_name)[1]

def split_schema_name(schema_name):
    """Return a tuple prefix, portal_type, schema_name
    """
    encoder = SchemaNameEncoder()
    items = encoder.split(schema_name)
    if len(items) == 2:
        return items[0], items[1], u""
    elif len(items) == 3:
        return items[0], items[1], items[2]
    else:
        raise ValueError("Schema name %s is invalid" % schema_name)


def create_object(portal_type, **kw):
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


def add_object_to_container(container, object, check_constraints=True):
    """Add an object to a container.

    The portal_type must already be set correctly. If check_constraints
    is False no check for addable content types is done. The new object,
    wrapped in its new acquisition context, is returned.
    """
    if not hasattr(aq_base(object), "portal_type"):
        raise ValueError("object must have its portal_type set")

    container = aq_inner(container)
    if check_constraints:
        container_fti = container.getTypeInfo()

        fti = getUtility(IDexterityFTI, name=object.portal_type)
        if not fti.isConstructionAllowed(container):
            raise Unauthorized("Cannot create %s" % object.portal_type)
        
        if container_fti is not None and not container_fti.allowType(object.portal_type):
            raise ValueError("Disallowed subobject type: %s" % object.portal_type)

    name = INameChooser(container).chooseName(None, object)
    object.id = name

    new_name = container._setObject(name, object)

    # XXX: When we move to CMF 2.2, an event handler will take care of this
    wrapped_object = container._getOb(new_name)
    wrapped_object.notifyWorkflowCreated()

    return wrapped_object


def create_object_in_container(container, portal_type, check_constraints=True, **kw):
    content = create_object(portal_type, **kw)
    return add_object_to_container(container, content, check_constraints=check_constraints)

