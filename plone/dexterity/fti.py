import os.path

from zope.interface import implements

from zope.component.interfaces import IFactory
from zope.component import getUtility, queryUtility, getAllUtilitiesRegisteredFor

from zope.event import notify

from zope.security.interfaces import IPermission

from zope.lifecycleevent import modified

from zope.app.component.hooks import getSiteManager
from zope.i18nmessageid import Message

from plone.supermodel import loadString, loadFile
from plone.supermodel.model import Model
from plone.supermodel.utils import syncSchema

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IDexterityFTIModificationDescription
from plone.dexterity import utils

from plone.dexterity.factory import DexterityFactory

from Acquisition import aq_base
from AccessControl import getSecurityManager

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFDynamicViewFTI import fti as base

import plone.dexterity.schema

from plone.dexterity.schema import SchemaInvalidatedEvent

from Products.CMFCore.interfaces import IAction
from Products.CMFCore.Expression import Expression

class DexterityFTIModificationDescription(object):
    implements(IDexterityFTIModificationDescription)
    
    def __init__(self, attribute, oldValue):
        self.attribute = attribute
        self.oldValue = oldValue

# XXX: Backport from CMF 2.2 - enabled only when we are on CMF 2.1

if hasattr(base.DynamicViewTypeInformation, 'getInfoData'):
    class AddViewActionCompat(object):
        pass
else:
    class AddViewActionCompat(object):
        """Mixin class for forward compatibility with CMF 2.2, where add views
        are kept as actions in the FTI.
        """
    
        implements(IAction)
    
        add_view_expr = ''
    
        #
        #   'IAction' interface methods
    
        # BBB support for action interface export
        def getMapping(self):
            """ Get a mapping of this object's data. Used for export/import.
            """
        
            permissions = ()
            permission = queryUtility(IPermission, name=self.add_permission)
            if permission:
                permissions = (permission.title,)
        
            return { 'id': self.getId(),
                     'title': self.Title(),
                     'description': self.Description(),
                     'category': 'folder/add',
                     'condition': getattr(self, 'condition', None) and self.condition.text or '',
                     'permissions': permissions,
                     'visible': True,
                     'action': self.add_view_expr }

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
          'select_variable': 'possiblePermissionIds',
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
    
    default_aliases = {'(Default)': '(dynamic view)',
                       'view': '(selected layout)',
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
    
    immediate_view = 'view'
    default_view = 'view'
    view_methods = ('view',)
    add_permission = 'cmf.AddPortalContent'
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
                               permission=action.get('permissions', ()),
                               category=action.get('category', 'object'),
                               visible=action.get('visible', True))
        
        # Default factory name to be the FTI name
        if not self.factory:
            self.factory = self.getId()
        
        # In CMF (2.2+, but we've backported it) the property add_view_expr is
        # used to construct an action in the 'folder/add' category. The
        # portal_types tool loops over all FTIs and lets them provide such
        # actions.
        # 
        # By convention, the expression is string:${folder_url}/++add++my.type
        # 
        # The ++add++ traverser will find the FTI with name my.type, and then
        # looks up an adapter for (context, request, fti) with a name equal
        # to fti.factory, falling back on an unnamed adapter. The result is
        # assumed to be an add view.
        # 
        # Dexterity provides a default (unnamed) adapter for any IFolderish
        # context, request and IDexterityFTI that can construct an add view
        # for any Dexterity schema.
        
        if not self.add_view_expr:
            add_view_expr = kwargs.get('add_view_expr', "string:${folder_url}/++add++%s" % self.getId())
            self._setPropValue('add_view_expr', add_view_expr)
        
        # Set the content_meta_type from the klass
        
        klass = utils.resolveDottedName(self.klass)
        if klass is not None:
            self.content_meta_type = getattr(klass, 'meta_type', None)
    
    def Title(self):
        if self.title and self.i18n_domain:
            return Message(self.title.decode('utf8'), self.i18n_domain)
        else:
            return self.title or self.getId()

    def Description(self):
        if self.description and self.i18n_domain:
            return Message(self.description.decode('utf8'), self.i18n_domain)
        else:
            return self.description
    
    def Metatype(self):
        if self.content_meta_type:
            return self.content_meta_type
        # BBB - this didn't use to be set
        klass = utils.resolveDottedName(self.klass)
        if klass is not None:
            self.content_meta_type = getattr(klass, 'meta_type', None)
        return self.content_meta_type
    
    @property
    def hasDynamicSchema(self):
        return not(self.schema)
    
    def lookupSchema(self):
        
        # If a specific schema is given, use it
        if self.schema:
            schema = utils.resolveDottedName(self.schema)
            if schema is None:
                raise ValueError(u"Schema %s set for type %s cannot be resolved" % (self.schema, self.getId()))
            return schema
        
        # Otherwise, look up a dynamic schema. This will query the model for
        # an unnamed schema if it is the first time it is looked up. 
        # See schema.py

        schemaName = utils.portalTypeToSchemaName(self.getId())
        return getattr(plone.dexterity.schema.generated, schemaName)
    
    def lookupModel(self):
        
        if self.model_source:
            return loadString(self.model_source, policy=u"dexterity")
        
        elif self.model_file:
            model_file = self._absModelFile()
            return loadFile(model_file, reload=True, policy=u"dexterity")
        
        elif self.schema:
            schema = self.lookupSchema()
            return Model({u"": schema})
        
        raise ValueError("Neither model source, nor model file, nor schema is specified in FTI %s" % self.getId())
    
    #
    # Base class overrides
    # 
    
    # Make sure we get an event when the FTI is modified
    
    def _updateProperty(self, id, value):
        """Allow property to be updated, and fire a modified event. We do this
        on a per-property basis and invalidate selectively based on the id of
        the property that was changed.
        """
        
        oldValue = getattr(self, id, None)
        super(DexterityFTI, self)._updateProperty(id, value)
        new_value = getattr(self, id, None)
        
        if oldValue != new_value:
            modified(self, DexterityFTIModificationDescription(id, oldValue))
            
            # Update meta_type from klass
            if id == 'klass':
                klass = utils.resolveDottedName(new_value)
                if klass is not None:
                    self.content_meta_type = getattr(klass, 'meta_type', None)
    
    # Allow us to specify a particular add permission rather than rely on ones
    # stored in meta types that we don't have anyway
    
    def isConstructionAllowed(self, container):
        if not self.add_permission:
            return False
        
        permission = queryUtility(IPermission, name=self.add_permission)
        if permission is None:
            return False
        
        return getSecurityManager().checkPermission(permission.title, container)
        
    #
    # Helper methods
    # 

    def possiblePermissionIds(self):
        """Get a vocabulary of Zope 3 permission ids
        """
        permission_names = set()
        for permission in getAllUtilitiesRegisteredFor(IPermission):
            permission_names.add(permission.id)
        return sorted(permission_names)

    def _absModelFile(self):
        colons = self.model_file.count(':')
        model_file = self.model_file
        
        # We have a package and not an absolute Windows path
        if colons == 1 and self.model_file[1:3] != ':\\':
            package, filename = self.model_file.split(':')
            mod = utils.resolveDottedName(package)
             # let / work as path separator on all platforms
            filename = filename.replace('/', os.path.sep)
            model_file = os.path.join(os.path.split(mod.__file__)[0], filename)
        else:
            if not os.path.isabs(model_file):
                raise ValueError(u"Model file name %s is not an absolute path and does not contain a package name in %s" % (model_file, self.getId(),))
        
        if not os.path.isfile(model_file):
            raise ValueError(u"Model file %s in %s cannot be found" % (model_file, self.getId(),))
        
        return model_file

def _fixProperties(class_, ignored=['product', 'content_meta_type']):
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
_fixProperties(DexterityFTI)

# Event handlers

def register(fti):
    """Helper method to:
    
         - register an FTI as a local utility
         - register a local factory utility
         - register an add view
    """

    fti = aq_base(fti) # remove acquisition wrapper
    site = getUtility(ISiteRoot)
    site_manager = getSiteManager(site)
    
    portal_type = fti.getId()
    
    fti_utility = queryUtility(IDexterityFTI, name=portal_type)
    if fti_utility is None:
        site_manager.registerUtility(fti, IDexterityFTI, portal_type, info='plone.dexterity.dynamic')
        
    factory_utility = queryUtility(IFactory, name=fti.factory)
    if factory_utility is None:
        site_manager.registerUtility(DexterityFactory(portal_type), IFactory, fti.factory, info='plone.dexterity.dynamic')

def unregister(fti, old_name=None):
    """Helper method to:
    
        - unregister the FTI local utility
        - unregister any local factory utility associated with the FTI
        - unregister any local add view associated with the FTI
    """
    site = queryUtility(ISiteRoot)
    if site is None:
        return
    
    site_manager = getSiteManager(site)
    
    portal_type = old_name or fti.getId()
    
    site_manager.unregisterUtility(provided=IDexterityFTI, name=portal_type)
    unregister_factory(fti.factory, site_manager)
    
    notify(SchemaInvalidatedEvent(portal_type))

def unregister_factory(factory_name, site_manager):
    """Helper method to unregister factories when unused by any dexterity
    type
    """
    utilities = list(site_manager.registeredUtilities())
    # Do nothing if an FTI is still using it
    if factory_name in [f.component.factory for f in utilities
                        if (f.provided, f.info) == (IDexterityFTI, 'plone.dexterity.dynamic')]:
        return
    
    # If a factory with a matching name exists, remove it
    if [f for f in utilities
        if (f.provided, f.name, f.info) == (IFactory, factory_name, 'plone.dexterity.dynamic')]:
        site_manager.unregisterUtility(provided=IFactory, name=factory_name)

def ftiAdded(object, event):
    """When the FTI is created, install local components
    """
    
    if not IDexterityFTI.providedBy(event.object):
        return
    
    register(event.object)
    
def ftiRemoved(object, event):
    """When the FTI is removed, uninstall local coponents
    """
    
    if not IDexterityFTI.providedBy(event.object):
        return
            
    unregister(event.object)

def ftiRenamed(object, event):
    """When the FTI is modified, ensure local components are still valid
    """
    
    if not IDexterityFTI.providedBy(event.object):
        return
    
    if event.oldParent is None or event.newParent is None or event.oldName == event.newName:
        return
    
    unregister(event.object, event.oldName)
    register(event.object)

def ftiModified(object, event):
    """When an FTI is modified, re-sync and invalidate the schema, if 
    necessary.
    """
    
    if not IDexterityFTI.providedBy(event.object):
        return
    
    # TODO: Make sure that we don't get orphan factory utilities if
    # the 'factory' property is changed.
    
    fti = event.object
    portal_type = fti.getId()
    
    mod = {}
    for desc in event.descriptions:
        if IDexterityFTIModificationDescription.providedBy(desc):
            mod[desc.attribute] = desc.oldValue
    
    # If the factory utility name was modified, we may get an orphan if one 
    # was registered as a local utility to begin with. If so, remove the
    # orphan.
    
    if 'factory' in mod:
        old_factory = mod['factory']
        
        site = getUtility(ISiteRoot)
        site_manager = getSiteManager(site)
        
        # Remove previously registered factory, if no other type uses it.
        unregister_factory(old_factory, site_manager)
        
        # Register a new local factory if one doesn't exist already
        new_factory_utility = queryUtility(IFactory, name=fti.factory)
        if new_factory_utility is None:
            site_manager.registerUtility(DexterityFactory(portal_type), IFactory, fti.factory, info='plone.dexterity.dynamic')
        
    # Determine if we need to invalidate the schema at all
    if 'behaviors' in mod or 'schema' in mod or 'model_source' in mod or 'model_file' in mod:
        
        # Determine if we need to re-sync a dynamic schema
        if (fti.model_source or fti.model_file) and ('model_source' in mod or 'model_file' in mod):
            
            schemaName = utils.portalTypeToSchemaName(portal_type)
            schema = getattr(plone.dexterity.schema.generated, schemaName)
    
            model = fti.lookupModel()
            syncSchema(model.schema, schema, overwrite=True)
        
        notify(SchemaInvalidatedEvent(portal_type))