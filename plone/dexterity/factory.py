from persistent import Persistent

from zope.interface import implements
from zope.interface import alsoProvides
from zope.interface.declarations import Implements

from zope.component import getUtility
from zope.component.factory import Factory

from zope.schema import getFieldsInOrder

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IDexterityFactory

from plone.dexterity.security import InstanceSecurityInfo

from plone.dexterity.utils import resolve_dotted_name

from Acquisition import aq_base

class DexterityFactory(Persistent, Factory):
    """A factory for 
    """
    
    implements(IDexterityFactory)
    
    def __init__(self, portal_type):
        self.portal_type = portal_type

    @property
    def title(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        return fti.title

    @property
    def description(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        return fti.description

    def __call__(self, *args, **kw):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        
        klass = resolve_dotted_name(fti.klass)
        if klass is None or not callable(klass):
            raise ValueError("Content class %s set for type %s is not valid" % (fti.klass, self.portal_type))
        
        try:
            obj = klass(*args, **kw)
        except TypeError, e:
            raise ValueError("Error whilst constructing content for %s using class %s: %s" % (self.portal_type, fti.klass, str(e)))
        
        # Set portal_type if not set
        if getattr(obj, 'portal_type', '') != self.portal_type:
            obj.portal_type = self.portal_type

        # Get schema interface

        schema = fti.lookup_schema()
        
        if not schema.providedBy(obj):
            alsoProvides(obj, schema)

            permission_settings = schema.queryTaggedValue(u'dexterity.security', {})
            
            # XXX: This security model does not seem to work properly
            # security = InstanceSecurityInfo()

            # Initialise fields from the schema onto the type
            for name, field in getFieldsInOrder(schema):
                if not hasattr(obj, name):
                    field = field.bind(obj)
                    field.set(obj, field.default)
                    
                    # read_permission = permission_settings.get(name, {}).get('read-permission', 'View')
                    # security.declareProtected(read_permission, name)
        
            # security.apply(aq_base(obj))
        
        return obj

    def getInterfaces(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        spec = Implements(fti.lookup_schema())
        spec.__name__ = self.portal_type
        return spec

    def __repr__(self):
        return '<%s for %s>' %(self.__class__.__name__, self.portal_type)
