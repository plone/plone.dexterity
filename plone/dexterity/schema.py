import new

from zope.interface import implements, Interface, alsoProvides
from zope.interface.interface import InterfaceClass

from plone.supermodel.parser import ISchemaPolicy

from plone.alterego.interfaces import IDynamicObjectFactory

from plone.dexterity.interfaces import IDexteritySchema

from plone.dexterity.interfaces import ITemporarySchema
from plone.dexterity.interfaces import ITransientSchema
from plone.dexterity import utils

from plone.alterego import dynamic

# Dynamic modules
generated = dynamic.create('plone.dexterity.schema.generated')
transient = new.module("transient")

class SchemaModuleFactory(object):
    """Create dynamic schema interfaces on the fly
    """
    
    implements(IDynamicObjectFactory)
    
    def __call__(self, name, module):
        """Someone tried to load a dynamic interface that has not yet been
        created yet. We will attempt to load it from the FTI if we can. If
        the FTI doesn't exist, create a temporary marker interface that we
        can fill later.
        """
        
        bases = (Interface,)
        
        try:
            prefix, portal_type, schema_name = utils.split_schema_name(name)
        except ValueError:
            return None
        
        is_default_schema = not schema_name
        if is_default_schema:
            bases += (IDexteritySchema,)
        
        klass = InterfaceClass(name, bases, __module__=module.__name__)
        alsoProvides(klass, ITemporarySchema)
        return klass

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