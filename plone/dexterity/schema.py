import new
from threading import Lock

from zope.interface import implements
from zope.interface.interface import InterfaceClass

from zope.component import queryUtility

from plone.supermodel.parser import ISchemaPolicy
from plone.supermodel.parser import IFieldMetadataHandler

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
        elif fti is not None:
            try:
                model = fti.lookup_model()
            except Exception, e:
                self._lock.release()
                raise
            
            utils.sync_schema(model.schemata[schema_name].schema, schema)
        
            # Save this schema in the module - this factory will not be
            # called again for this name
            
            if name in self._transient_schema_cache:
                del self._transient_schema_cache[name]
                
            setattr(module, name, schema)
            
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
        
class SecuritySchema(object):
    """Support the security: namespace in model definitions.
    """
    implements(IFieldMetadataHandler)
    
    namespace = 'http://namespaces.plone.org/dexterity/security'
    prefix = 'security'
    
    def read(self, field_node, field, schema_metadata):
        name = field.__name__
        
        read_permission = field_node.get('{%s}read-permission' % self.namespace)
        write_permission = field_node.get('{%s}write-permission' % self.namespace)
        
        if read_permission:
            schema_metadata.setdefault(name, {})['read-permission'] = read_permission
        if write_permission:
            schema_metadata.setdefault(name, {})['write-permission'] = write_permission

    def write(self, field_node, schema, schema_metadata):
        name = field.__name__
        read_permission = schema_metadata.get(name, {}).get('read-permission', None)
        write_permission = schema_metadata.get(name, {}).get('read-permission', None)
        
        if read_permission:
            field_node.set('{%s}read-permission' % self.namespace, read_permission)
        if write_permission:
            field_node.set('{%s}write-permission' % self.namespace, write_permission)

class WidgetSchema(object):
    """Support the widget: namespace in model definitions.
    """
    implements(IFieldMetadataHandler)
    
    namespace = 'http://namespaces.plone.org/dexterity/widget'
    prefix = 'widget'
    
    def read(self, field_node, field, schema_metadata):
        # TODO: Read widget hints
        pass

    def write(self, field_node, field, schema_metadata):
        # TODO: Write widget hints
        pass