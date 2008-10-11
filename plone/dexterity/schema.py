import new
from threading import Lock

from zope.interface import implements, alsoProvides
from zope.interface.interface import InterfaceClass

from zope.component import queryUtility

from zope.app.content.interfaces import IContentType

from plone.supermodel.parser import ISchemaPolicy
from plone.supermodel.parser import IFieldMetadataHandler

from plone.supermodel.utils import ns, sync_schema

from plone.alterego.interfaces import IDynamicObjectFactory

from plone.dexterity.interfaces import IDexteritySchema
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
        
            if is_default_schema:
                alsoProvides(schema, IContentType)
        
        fti = queryUtility(IDexterityFTI, name=portal_type)
        if fti is None and name not in self._transient_schema_cache:
            self._transient_schema_cache[name] = schema
        elif fti is not None:
            try:
                model = fti.lookup_model()
            except Exception, e:
                self._lock.release()
                raise
            
            sync_schema(model.schemata[schema_name], schema, sync_bases=True)

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
        return ()
        
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
    
    def read(self, field_node, schema, field):
        name = field.__name__
        
        read_permission = field_node.get(ns('read-permission', self.namespace))
        write_permission = field_node.get(ns('write-permission', self.namespace))
        
        permissions = schema.queryTaggedValue(u'dexterity.security', {})
        
        if read_permission:
            permissions.setdefault(name, {})['read-permission'] = read_permission
        if write_permission:
            permissions.setdefault(name, {})['write-permission'] = write_permission
            
        if permissions:
            schema.setTaggedValue(u'dexterity.security', permissions)

    def write(self, field_node, schema, field):
        name = field.__name__
        
        permissions = schema.queryTaggedValue(u'dexterity.security', {})
        
        read_permission = permissions.get(name, {}).get('read-permission', None)
        write_permission = permissions.get(name, {}).get('write-permission', None)
        
        if read_permission:
            field_node.set(ns('read-permission', self.namespace), read_permission)
        if write_permission:
            field_node.set(ns('write-permission', self.namespace), write_permission)

class FormSchema(object):
    """Support the form: namespace in model definitions.
    """
    implements(IFieldMetadataHandler)
    
    namespace = 'http://namespaces.plone.org/dexterity/form'
    prefix = 'form'
    
    def read(self, field_node, schema, field):
        name = field.__name__
        
        widget = field_node.get(ns('widget', self.namespace))
        mode = field_node.get(ns('mode', self.namespace))
        omitted = field_node.get(ns('omitted', self.namespace))
        before = field_node.get(ns('before', self.namespace))
        
        settings = schema.queryTaggedValue(u'dexterity.form', {})
        updated = False
        
        if widget:
            settings.setdefault('widgets', []).append((name, widget))
            updated = True
        if mode:
            settings.setdefault('modes', []).append((name, mode))
            updated = True
        if omitted:
            settings.setdefault('omitted', []).append((name, omitted))
            updated = True
        if before:
            settings.setdefault('before', []).append((name, before))
            updated = True
            
        if updated:
            schema.setTaggedValue(u'dexterity.form', settings)

    def write(self, field_node, schema, field):
        name = field.__name__
        
        settings = schema.queryTaggedValue(u'dexterity.form', {})
        
        widget = [v for n,v in settings.get('widgets', []) if n == name]
        mode = [v for n,v in settings.get('modes', []) if n == name]
        omitted = [v for n,v in settings.get('omitted', []) if n == name]
        before = [v for n,v in settings.get('before', []) if n == name]
        
        if widget:
            field_node.set(ns('widget', self.namespace), widget[0])
        if mode:
            field_node.set(ns('mode', self.namespace), mode[0])
        if omitted:
            field_node.set(ns('omitted', self.namespace), omitted[0])
        if before:
            field_node.set(ns('before', self.namespace), before[0])