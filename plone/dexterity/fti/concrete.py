from zope.interface import implements

from plone.dexterity.interfaces import IConcreteFTI
from plone.dexterity.fti.base import DexterityFTI, _fix_properties

from Products.GenericSetup.utils import _resolveDottedName

class ConcreteFTI(DexterityFTI):
    """A Dexterity FTI that is connected to a filesystem type
    """
    
    implements(IConcreteFTI)
    
    _properties = DexterityFTI._properties + (
        { 'id': 'schema', 
          'type': 'string',
          'mode': 'w',
          'label': 'Schema',
          'description': "Dotted name to the interface describing content type's schema"
        },
        
    )
    
    schema = u""
    
    def __init__(self, *args, **kwargs):
        super(ConcreteFTI, self).__init__(*args, **kwargs)

    def lookup_schema(self):
        schema = getattr(self, '_v_schema', None)
        if schema is not None:
            return schema
        
        schema = self._v_schema = self.lookup_model()[u'schemata'][u'']
        return schema

    def lookup_model(self):
        schema = _resolveDottedName(self.schema)
        if schema is None:
            raise ValueError(u"Schema %s set for type %s cannot be resolved" % (self.schema, self.getId()))
        return dict(schemata={u"": schema}, widgets={})

_fix_properties(ConcreteFTI)