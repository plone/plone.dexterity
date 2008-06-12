from zope.interface import implements
from zope.lifecycleevent import modified

from plone.dexterity.interfaces import IDexterityFTI

from AccessControl import getSecurityManager
from Products.CMFDynamicViewFTI import fti

class DexterityFTI(fti.DynamicViewTypeInformation):
    """A Dexterity FTI
    """
    
    implements(IDexterityFTI)
    meta_type = "Dexterity FTI"
    
    _properties = fti.DynamicViewTypeInformation._properties + (
        { 'id': 'add_permission', 
          'type': 'selection',
          'select_variable': 'possible_permissions',
          'mode': 'w',
          'label': 'Add permission',
          'description': 'Permission needed to be able to add content of this type'
        },
        { 'id': 'klass', 
          'type': 'string',
          'mode': 'w',
          'label': 'Content type class',
          'description': 'Dotted name to the class that contains the content type'
        },
        { 'id': 'behaviors', 
          'type': 'lines',
          'mode': 'w',
          'label': 'Behaviors',
          'description': 'Named of enabled behaviors type'
        },
    )
    
    default_aliases = {'(Default)': '(selected layout)',
                       'view': '@@view',
                       'edit': '@@edit',
                       'sharing': '@@sharing',}
    
    default_actions = [{'id': 'view', 
                        'title': 'View', 
                        'action': 'string:${object_url}',
                        'permissions': ('View',)},
                       {'id': 'edit', 
                        'title': 'Edit', 
                        'action': 'string:${object_url}/edit',
                        'permissions': ('Modify portal content',)},
                        ]
    
    immediate_view = 'edit'
    default_view = 'view'
    view_methods = ('view',)
    add_permission = 'Add portal content'
    behaviors = []
    klass = 'plone.dexterity.content.Item'
    
    def __init__(self, *args, **kwargs):
        super(DexterityFTI, self).__init__(*args, **kwargs)
        
        if 'aliases' not in kwargs:
            self.setMethodAliases(self.default_aliases)
            
        if 'actions' not in kwargs:
            for action in self.default_actions:
                self.addAction(id=action['id'],
                               name=action['title'],
                               action=action['action'],
                               condition=action.get('condition'),
                               permission=action.get( 'permissions', ()),
                               category=action.get('category', 'object'),
                               visible=action.get('visible', True))
    
    # Tie the factory to the portal_type name - one less thing to have to set
    @property
    def factory(self):
        return self.getId()
    
    def lookup_schema(self):
        raise NotImplemented
    
    def lookup_model(self):
        raise NotImplemented
    
    # Make sure we get an event when the FTI is modifieid
    
    def manage_editProperties(self, REQUEST=None):
        """Gotta love Zope 2
        """
        page = super(DexterityFTI, self).manage_editProperties(REQUEST)
        modified(self)
        return page
    
    def manage_changeProperties(self, REQUEST=None, **kw):
        """Gotta love Zope 2
        """
        page = super(DexterityFTI, self).manage_changeProperties(REQUEST, **kw)
        modified(self)
        return page
        
    # Allow us to specify a particular add permission rather than rely on ones
    # stored in meta types that we don't have anyway
    
    def isConstructionAllowed(self, container):
        if not self.add_permission:
            return False
        return getSecurityManager().checkPermission(self.add_permission, container)
        

def _fix_properties(class_, ignored=['product', 'content_meta_type', 'factory']):
    """Remove properties with the given ids, and ensure that later properties
    override earlier ones with the same id
    """
    properties = []
    processed = set()
    
    for item in reversed(class_._properties):
        item = item.copy()
        
        if item['id'] in processed:
            continue
        
        # Ignore some fields
        if item['id'] in ignored:
            continue
        
        properties.append(item)
        processed.add('id')
    
    class_._properties = tuple(reversed(properties))
    
_fix_properties(DexterityFTI)