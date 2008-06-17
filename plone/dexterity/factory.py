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

from Acquisition import aq_base
from Products.GenericSetup.utils import _resolveDottedName

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
        
        klass = _resolveDottedName(fti.klass)
        if klass is None or not callable(klass):
            raise ValueError("Content class %s set for type %s is not valid" % (fti.klass, self.portal_type))
        
        try:
            obj = klass()
        except TypeError:
            raise ValueError("Content class %s set for type %s does not have a no-args constructor" % (fti.klass, self.portal_type))
        
        # Set portal_type if not set
        if not getattr(obj, 'portal_type', None):
            obj.portal_type = self.portal_type

        # Get schema interface

        schema = fti.lookup_schema()
        
        if not schema.providedBy(obj):
            alsoProvides(obj, schema)

            model = fti.lookup_model()
            permission_settings = model['metadata'][u''].get('security', {})
            
            security = InstanceSecurityInfo()

            # Initialise fields from the schema onto the type
            for name, field in getFieldsInOrder(schema):
                if not hasattr(obj, name):
                    field = field.bind(obj)
                    field.set(obj, field.default)
                    
                    read_permission = permission_settings.get(name, {}).get('read-permission', 'View')
                    security.declareProtected(read_permission, name)
        
            security.apply(aq_base(obj))
        
        return obj

    def getInterfaces(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        spec = Implements(fti.lookup_schema())
        spec.__name__ = self.portal_type
        return spec

    def __repr__(self):
        return '<%s for %s>' %(self.__class__.__name__, self.portal_type)
