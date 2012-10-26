import new
import functools

from threading import RLock
from plone.synchronize import synchronized

from zope.interface import implements, alsoProvides
from zope.interface.interface import InterfaceClass

from zope.component import adapter
from zope.component import queryUtility, getAllUtilitiesRegisteredFor

from plone.behavior.interfaces import IBehavior

from plone.supermodel.parser import ISchemaPolicy
from plone.supermodel.utils import syncSchema

from plone.alterego.interfaces import IDynamicObjectFactory

from plone.dexterity.interfaces import IContentType
from plone.dexterity.interfaces import IDexteritySchema
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import ISchemaInvalidatedEvent

from plone.dexterity import utils
from plone.alterego import dynamic

# Dynamic modules
generated = dynamic.create('plone.dexterity.schema.generated')
transient = new.module("transient")

def invalidate_cache(fti):
    fti._p_activate()
    fti.__dict__.pop('_v_schema_get', None)
    fti.__dict__.pop('_v_schema_subtypes', None)


def volatile(func):
    @functools.wraps(func)
    def decorator(self, portal_type):
        fti = queryUtility(IDexterityFTI, name=portal_type)
        if fti is not None and self.cache_enabled:
            key = '_v_schema_%s' % func.__name__
            cache = getattr(fti, key, None)
            if cache is not None:
                mtime, value = cache
                if fti._p_mtime == mtime:
                    return value

        value = func(self, fti)

        if fti is not None and value is not None and self.cache_enabled:
            setattr(fti, key, (fti._p_mtime, value))

        return value
    return decorator


class SchemaCache(object):
    """Simple schema cache. 
    
    This cache will store a Python object reference to the schema, as returned
    by fti.lookupSchema(), for any number of portal types. The value will
    be cached until the server is restarted or the cache is invalidated or
    cleared.
    
    You should only use this if you require bare-metal speed. For almost all
    operations, it's safer and easier to do:
    
        >>> fti = getUtility(IDexterityFTI, name=portal_type)
        >>> schema = fti.lookupSchema()
    
    The lookupSchema() call is probably as fast as this cache. However, if
    you need to avoid the utility lookup, you can use the cache like so:
    
        >>> from plone.dexterity.schema import SCHEMA_CACHE
        >>> my_schema = SCHEMA_CACHE.get(portal_type)
        
    The cache uses the FTI's modification time as its invariant.
    """
    
    lock = RLock()

    def __init__(self, cache_enabled=True):
        self.cache_enabled = cache_enabled

    @synchronized(lock)
    @volatile
    def get(self, fti):
        if fti is None:
            return
        try:
            return fti.lookupSchema()
        except (AttributeError, ValueError):
            pass

    @synchronized(lock)
    @volatile
    def subtypes(self, fti):
        if fti is None:
            return ()
        subtypes = []
        for behavior_name in fti.behaviors:
            behavior = queryUtility(IBehavior, name=behavior_name)
            if behavior is not None and behavior.marker is not None:
                subtypes.append(behavior.marker)
        return tuple(subtypes)

    @synchronized(lock)
    def clear(self):
        for fti in getAllUtilitiesRegisteredFor(IDexterityFTI):
            invalidate_cache(fti)


    @synchronized(lock)
    def invalidate(self, portal_type):
        fti = queryUtility(IDexterityFTI, name=portal_type)
        invalidate_cache(fti)


SCHEMA_CACHE = SchemaCache()

class SchemaInvalidatedEvent(object):
    implements(ISchemaInvalidatedEvent)
    
    def __init__(self, portal_type):
        self.portal_type = portal_type

@adapter(ISchemaInvalidatedEvent)
def invalidate_schema(event):
    if event.portal_type:
        SCHEMA_CACHE.invalidate(event.portal_type)
    else:
        SCHEMA_CACHE.clear()

# Dynamic module factory

class SchemaModuleFactory(object):
    """Create dynamic schema interfaces on the fly
    """
    
    implements(IDynamicObjectFactory)
    
    lock = RLock()
    _transient_SCHEMA_CACHE = {}
    
    @synchronized(lock)
    def __call__(self, name, module):
        """Someone tried to load a dynamic interface that has not yet been
        created yet. We will attempt to load it from the FTI if we can. If
        the FTI doesn't exist, create a temporary marker interface that we
        can fill later.
        
        The goal here is to ensure that we create exactly one interface 
        instance for each name. If we can't find an FTI, we'll cache the
        interface so that we don't get a new one with a different id later.
        This cache is global, so we synchronise the method with a thread
        lock.
        
        Once we have a properly populated interface, we set it onto the
        module using setattr(). This means that the factory will not be
        invoked again.
        """
        
        try:
            prefix, portal_type, schemaName = utils.splitSchemaName(name)
        except ValueError:
            return None
        
        if name in self._transient_SCHEMA_CACHE:
            schema = self._transient_SCHEMA_CACHE[name]
        else:
            bases = ()
            
            is_default_schema = not schemaName
            if is_default_schema:
                bases += (IDexteritySchema,)
        
            schema = InterfaceClass(name, bases, __module__=module.__name__)
        
            if is_default_schema:
                alsoProvides(schema, IContentType)
        
        fti = queryUtility(IDexterityFTI, name=portal_type)
        if fti is None and name not in self._transient_SCHEMA_CACHE:
            self._transient_SCHEMA_CACHE[name] = schema
        elif fti is not None:
            model = fti.lookupModel()            
            syncSchema(model.schemata[schemaName], schema, sync_bases=True)

            # Save this schema in the module - this factory will not be
            # called again for this name
            
            if name in self._transient_SCHEMA_CACHE:
                del self._transient_SCHEMA_CACHE[name]
                
            setattr(module, name, schema)

        return schema

class DexteritySchemaPolicy(object):
    """Determines how and where imported dynamic interfaces are created.
    Note that these schemata are never used directly. Rather, they are merged
    into a schema with a proper name and module, either dynamically or
    in code.
    """
    implements(ISchemaPolicy)
    
    def module(self, schemaName, tree):
        return 'plone.dexterity.schema.transient'
        
    def bases(self, schemaName, tree):
        return ()
        
    def name(self, schemaName, tree):
        # We use a temporary name whilst the interface is being generated;
        # when it's first used, we know the portal_type and site, and can
        # thus update it
        return '__tmp__' + schemaName

