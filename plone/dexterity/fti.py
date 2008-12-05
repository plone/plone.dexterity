import os.path

from zope.interface import implements

from zope.component.interfaces import IFactory
from zope.component import getUtility, queryUtility

from zope.lifecycleevent import modified

from zope.app.component.hooks import getSiteManager

from plone.supermodel import load_string, load_file
from plone.supermodel.model import Model
from plone.supermodel.utils import sync_schema

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity import utils

from plone.dexterity.factory import DexterityFactory

from AccessControl import getSecurityManager
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFDynamicViewFTI import fti as base

import plone.dexterity.schema

from Products.CMFCore.interfaces import IAction
from Products.CMFCore.Expression import Expression

class AddViewActionCompat(object):
    """Mixin class for forward compatibility with CMF trunk, where add views
    are kept as actions in the FTI
    
    NOTE: We likely need to remove this when we move to CMF 2.2
    """
    
    implements(IAction)
    
    add_view_expr = ''
    
    #
    #   'IAction' interface methods
    #

    def getInfoData(self):
        """ Get the data needed to create an ActionInfo.
        """
        lazy_keys = ['available', 'allowed']
        lazy_map = {}

        lazy_map['id'] = self.getId()
        lazy_map['category'] = 'folder/add'
        lazy_map['title'] = self.Title()
        lazy_map['description'] = self.Description()
        if self.add_view_expr:
            lazy_map['url'] = self.add_view_expr_object
            lazy_keys.append('url')
        else:
            lazy_map['url'] = ''
        if self.content_icon:
            lazy_map['icon'] = Expression('string:${portal_url}/%s'
                                          % self.content_icon)
            lazy_keys.append('icon')
        else:
            lazy_map['icon'] = ''
        lazy_map['visible'] = True
        lazy_map['available'] = self._checkAvailable
        lazy_map['allowed'] = self._checkAllowed

        return (lazy_map, lazy_keys)

    def _setPropValue(self, id, value):
        self._wrapperCheck(value)
        if isinstance(value, list):
            value = tuple(value)
        setattr(self, id, value)
        if value and id.endswith('_expr'):
            setattr(self, '%s_object' % id, Expression(value))

    def _checkAvailable(self, ec):
        """ Check if the action is available in the current context.
        """
        return ec.contexts['folder'].getTypeInfo().allowType(self.getId())

    def _checkAllowed(self, ec):
        """ Check if the action is allowed in the current context.
        """
        return self.isConstructionAllowed(ec.contexts['folder'])

class DexterityFTI(AddViewActionCompat, base.DynamicViewTypeInformation):
    """A Dexterity FTI
    """
    
    implements(IDexterityFTI)

    meta_type = "Dexterity FTI"
    
    _properties = base.DynamicViewTypeInformation._properties + (
        { 'id': 'add_permission', 
          'type': 'selection',
          'select_variable': 'possible_permissions',
          'mode': 'w',
          'label': 'Add permission',
          'description': 'Permission needed to be able to add content of this type'
        },
        {'id': 'add_view_name',
         'type': 'string', 
         'mode': 'w',
         'label': 'Name of the add form view',
         'description': 'Used to construct the URL to the add form. ' +
                        'Defaults to "@@add-<typename>" if not set. ' +
                        'There is a fallback default add view as well.'
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
        { 'id': 'schema', 
          'type': 'string',
          'mode': 'w',
          'label': 'Schema',
          'description': "Dotted name to the interface describing content type's schema. " +
                         "This does not need to be given if model_source or model_file are given, " +
                         "and either contains an unnamed (default) schema."
        },
        { 'id': 'model_source', 
          'type': 'text',
          'mode': 'w',
          'label': 'Model source',
          'description': "XML source for the type's model. Note that this takes " +
                         "precedence over any model file."
        },
        { 'id': 'model_file', 
          'type': 'string',
          'mode': 'w',
          'label': 'Model file',
          'description': "Path to file containing the schema model. This can be " +
                         "relative to a package, e.g. 'my.package:myschema.xml'."
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
    
    add_view_name = ''
    immediate_view = 'edit'
    default_view = 'view'
    view_methods = ('view',)
    add_permission = 'Add portal content'
    behaviors = []
    klass = 'plone.dexterity.content.Item'
    model_source = """\
<model xmlns="http://namespaces.plone.org/supermodel/schema">
    <schema>
        <field name="title" type="zope.schema.TextLine">
            <title>Title</title>
            <required>True</required>
        </field>
        <field name="description" type="zope.schema.Text">
            <title>Description</title>
            <required>False</required>
        </field>
    </schema>
</model>
"""
    model_file = u""
    schema = u""
    
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
        
        # CMF (2.2+, but we've backported it) the property add_view_expr is
        # used to construct an action in the 'folder/add' category. The
        # portal_types tool loops over all FTIs and lets them provide such
        # actions.
        # 
        # For Dexterity, we use a standard pattern where an add view is
        # registered, e.g. 'add-my.type'. The action URL for an FTI with id
        # 'my.type' is always
        # 
        #   string:${folder_url}/@@add-dexterity-content/my.type
        # 
        # The @@add-dexterity-content view is a publish traverse view that
        # looks up the FTI with name my.type to locate the type's add view.
        # 
        # We store the type's add view in a property called 'add_view_name'. 
        # By default, this is empty. In this case, the traverser will attempt
        # to look up a view called @@add-my.type, falling back on a default
        # view (@@dexterity-default-addview) that introspects the FTI if a 
        # specific view is not registered.
        # 
        # The point if this whole dance is that it is possible to customise a
        # type and re-use its add view. Add views are registered for
        # IFolderish, and should have a 'form' attribute (a form class).
        # The traverser will set addview.form_instance.portal_type to be the
        # traversed-to type name. This the add form is aware of what type to
        # add without this having to be hardcoded.
        
        if not self.add_view_expr:
            self._setPropValue('add_view_expr', "string:${folder_url}/@@add-dexterity-content/%s" % self.getId())

    @property
    def factory(self):
        """Tie the factory to the portal_type name - one less thing to have to set
        """
        return self.getId()
    
    @property
    def has_dynamic_schema(self):
        return not bool(self.schema)
    
    def lookup_schema(self):
        
        # If a specific schema is given, use it
        if self.schema:
            schema = utils.resolve_dotted_name(self.schema)
            if schema is None:
                raise ValueError(u"Schema %s set for type %s cannot be resolved" % (self.schema, self.getId()))
            return schema
        
        # Otherwise, look up a dynamic schema. This will query the model for
        # an unnamed schema if it is the first time it is looked up. 
        # See schema.py

        schema_name = utils.portal_type_to_schema_name(self.getId())
        return getattr(plone.dexterity.schema.generated, schema_name)
    
    def lookup_model(self):
        
        if self.model_source:
            return load_string(self.model_source, policy=u"dexterity")
        
        elif self.model_file:
            model_file = self._abs_model_file()
            return load_file(model_file, reload=True, policy=u"dexterity")
        
        elif self.schema:
            schema = self.lookup_schema()
            return Model({u"": schema})
        
        raise ValueError("Neither model source, nor model file, nor schema is specified in FTI %s" % self.getId())
    
    #
    # Base class overrides
    # 
    
    # Make sure we get an event when the FTI is modifieid
    
    def manage_editProperties(self, REQUEST=None):
        """Gotta love Zope 2
        """
        page = super(DexterityFTI, self).manage_editProperties(REQUEST)
        modified(self)
        return page
    
    def manage_changeProperties(self, **kw):
        """Gotta love Zope 2
        """
        super(DexterityFTI, self).manage_changeProperties(**kw)
        modified(self)
        
    # Allow us to specify a particular add permission rather than rely on ones
    # stored in meta types that we don't have anyway
    
    def isConstructionAllowed(self, container):
        if not self.add_permission:
            return False
        return getSecurityManager().checkPermission(self.add_permission, container)
        
    #
    # Helper methods
    # 

    def _abs_model_file(self):
        colons = self.model_file.count(':')
        model_file = self.model_file
        
        # We have a package and not an absolute Windows path
        if colons == 1 and self.model_file[1:3] != ':\\':
            package, filename = self.model_file.split(':')
            mod = utils.resolve_dotted_name(package)
             # let / work as path separator on all platforms
            filename = filename.replace('/', os.path.sep)
            model_file = os.path.join(os.path.split(mod.__file__)[0], filename)
        else:
            if not os.path.isabs(model_file):
                raise ValueError(u"Model file name %s is not an absolute path and does not contain a package name in %s" % (model_file, self.getId(),))
        
        if not os.path.isfile(model_file):
            raise ValueError(u"Model file %s in %s cannot be found" % (model_file, self.getId(),))
        
        return model_file

def _fix_properties(class_, ignored=['product', 'content_meta_type', 'factory', 'add_view_expr']):
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

# Event handlers

def register(fti):
    """Helper method to:
    
         - register an FTI as a local utility
         - register a local factory utility
         - register an add view
    """
    
    site = getUtility(ISiteRoot)
    site_manager = getSiteManager(site)
    
    portal_type = fti.getId()
    
    fti_utility = queryUtility(IDexterityFTI, name=portal_type)
    if fti_utility is None:
        site_manager.registerUtility(fti, IDexterityFTI, portal_type)
        
    factory_utility = queryUtility(IFactory, name=fti.factory)
    if factory_utility is None:
        site_manager.registerUtility(DexterityFactory(portal_type), IFactory, fti.factory)

def unregister(fti):
    """Helper method to:
    
        - unregister the FTI local utility
        - unregister any local factory utility associated with the FTI
        - unregister any local add view associated with the FTI
    """
    site = queryUtility(ISiteRoot)
    if site is None:
        return
    
    site_manager = getSiteManager(site)
    
    portal_type = fti.getId()
    
    site_manager.unregisterUtility(provided=IDexterityFTI, name=portal_type)
    site_manager.unregisterUtility(provided=IFactory, name=fti.factory)
        
def fti_added(object, event):
    """When the FTI is created, install local components
    """
    
    if not IDexterityFTI.providedBy(event.object):
        return
    
    register(event.object)
    
def fti_removed(object, event):
    """When the FTI is removed, uninstall local coponents
    """
    
    if not IDexterityFTI.providedBy(event.object):
        return
            
    unregister(event.object)

def fti_renamed(object, event):
    """When the FTI is modified, ensure local components are still valid
    """
    
    if not IDexterityFTI.providedBy(event.object):
        return
    
    if event.oldParent is None or event.newParent is None or event.oldName == event.newName:
        return
    
    unregister(event.object)
    register(event.object)

    # Ensure that the add view URL is in sync
    event.object._setPropValue('add_view_expr', "string:${folder_url}/@@add-dexterity-content/%s" % event.newName)
    
    # TODO: We will either need to keep a trace of the old FTI, or 
    # we'll need to migrate all objects using this FTI, because instances 
    # with the old schema name will no longer be able to find their FTI

def fti_modified(object, event):
    """When an FTI is modified, re-sync the schema, if any
    """
    
    if not IDexterityFTI.providedBy(event.object):
        return    
    
    fti = event.object
    
    if fti.has_dynamic_schema:    
        schema_name = utils.portal_type_to_schema_name(fti.getId())
        schema = getattr(plone.dexterity.schema.generated, schema_name)
    
        model = fti.lookup_model()
        sync_schema(model.schema, schema, overwrite=True)