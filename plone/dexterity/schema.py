import new
from threading import Lock

from zope.interface import implements, Interface
from zope.interface.interface import InterfaceClass

from zope.component import queryUtility

from plone.supermodel.parser import ISchemaPolicy

from plone.alterego.interfaces import IDynamicObjectFactory

from plone.dexterity.interfaces import IDexteritySchema
from plone.dexterity.interfaces import ITransientSchema
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity import utils

from plone.alterego import dynamic

# Dynamic modules
generated = dynamic.create('plone.dexterity.schema.generated')
transient = new.module("transient")

class SchemaModuleFactory(object):
    """Create dynamic schema interfaces on the fly
    """
    
    implements(IDynamicObjectFactory)
    
    _lock = Lock()
    _transient_schema_cache = {}
    
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
            prefix, portal_type, schema_name = utils.split_schema_name(name)
        except ValueError:
            return None
        
        self._lock.acquire()
        
        if name in self._transient_schema_cache:
            schema = self._transient_schema_cache[name]
        else:
            bases = ()
            
            is_default_schema = not schema_name
            if is_default_schema:
                bases += (IDexteritySchema,)
        
            schema = InterfaceClass(name, bases, __module__=module.__name__)
        
        fti = queryUtility(IDexterityFTI, name=portal_type)
        if fti is None and name not in self._transient_schema_cache:
            self._transient_schema_cache[name] = schema
        else:
            try:
                model = fti.lookup_model()
            except Exception, e:
                self._lock.release()
                raise ValueError(u"Error loading model for %s: %s" % (fti.getId(), str(e)))
            
            utils.sync_schema(model['schemata'][schema_name], schema)
        
            # Save this schema in the module - this factory will not be
            # called again for this name
            
            setattr(module, name, schema)
            if name in self._transient_schema_cache:
                del self._transient_schema_cache[name]

        self._lock.release()
        return schema


class DexteritySchemaPolicy(object):
    """Determines how and where imported dynamic interfaces are created.
    Note that these schemata are never used directly. Rather, they are merged
    into a schema with a proper name and module, either dynamically or
    in code.
    """
    implements(ISchemaPolicy)
    
    def module(self, schema_name, tree):
        return 'plone.dexterity.schema.transient'
        
    def bases(self, schema_name, tree):
        return (ITransientSchema,)
        
    def name(self, schema_name, tree):
        # We use a temporary name whilst the interface is being generated;
        # when it's first used, we know the portal_type and site, and can
        # thus update it
        return '__tmp__' + schema_name