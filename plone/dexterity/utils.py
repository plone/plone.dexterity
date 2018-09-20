# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from Acquisition import aq_base
from Acquisition import aq_inner
from DateTime import DateTime
from plone.app.uuid.utils import uuidToObject
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.schema import SCHEMA_CACHE
from plone.dexterity.schema import SchemaNameEncoder  # noqa bbb
from plone.dexterity.schema import portalTypeToSchemaName  # noqa bbb
from plone.dexterity.schema import schemaNameToPortalType  # noqa bbb
from plone.dexterity.schema import splitSchemaName  # noqa bbb
from plone.supermodel.utils import mergedTaggedValueDict
from plone.uuid.interfaces import IUUID
from zope import deprecation
from zope.component import createObject
from zope.component import getUtility
from zope.container.interfaces import INameChooser
from zope.dottedname.resolve import resolve
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent

import datetime
import logging
import six


deprecation.deprecated(
    'SchemaNameEncoder',
    'moved to plone.dexterity.schema')
deprecation.deprecated(
    'portalTypeToSchemaName',
    'moved to plone.dexterity.schema')
deprecation.deprecated(
    'schemaNameToPortalType',
    'moved to plone.dexterity.schema')
deprecation.deprecated(
    'splitSchemaName',
    'moved to plone.dexterity.schema')

log = logging.getLogger(__name__)

# Not thread safe, but downside of a write conflict is very small
_dottedCache = {}


def resolveDottedName(dottedName):
    """Resolve a dotted name to a real object
    """
    global _dottedCache
    if dottedName not in _dottedCache:
        _dottedCache[dottedName] = resolve(dottedName)
    return _dottedCache[dottedName]


def iterSchemataForType(portal_type):
    """XXX: came from plone.app.deco.utils, very similar to iterSchemata

    Not fully merged codewise with iterSchemata as that breaks
    test_webdav.test_readline_mimetype_additional_schemata.
    """
    main_schema = SCHEMA_CACHE.get(portal_type)
    if main_schema:
        yield main_schema
    for schema in getAdditionalSchemata(portal_type=portal_type):
        yield schema


def iterSchemata(context):
    """Return an iterable containing first the object's schema, and then
    any form field schemata for any enabled behaviors.
    """
    main_schema = SCHEMA_CACHE.get(context.portal_type)
    if main_schema:
        yield main_schema
    for schema in getAdditionalSchemata(context=context):
        yield schema


def getAdditionalSchemata(context=None, portal_type=None):
    """Get additional schemata for this context or this portal_type.

    Additional form field schemata can be defined in behaviors.

    Usually either context or portal_type should be set, not both.
    The idea is that for edit forms or views you pass in a context
    (and we get the portal_type from there) and for add forms you pass
    in a portal_type (and the context is irrelevant then).  If both
    are set, the portal_type might get ignored, depending on which
    code path is taken.
    """
    log.debug("getAdditionalSchemata with context %r and portal_type %s",
              context, portal_type)
    if context is None and portal_type is None:
        return
    if context:
        behavior_assignable = IBehaviorAssignable(context, None)
    else:
        behavior_assignable = None
    if behavior_assignable is None:
        log.debug("No behavior assignable found, only checking fti.")
        # Usually an add-form.
        if portal_type is None:
            portal_type = context.portal_type
        for schema_interface in SCHEMA_CACHE.behavior_schema_interfaces(
            portal_type
        ):
            form_schema = IFormFieldProvider(schema_interface, None)
            if form_schema is not None:
                yield form_schema
    else:
        log.debug("Behavior assignable found for context.")
        for behavior_reg in behavior_assignable.enumerateBehaviors():
            form_schema = IFormFieldProvider(behavior_reg.interface, None)
            if form_schema is not None:
                yield form_schema


def createContent(portal_type, **kw):
    fti = getUtility(IDexterityFTI, name=portal_type)
    content = createObject(fti.factory)

    # Note: The factory may have done this already, but we want to be sure
    # that the created type has the right portal type. It is possible
    # to re-define a type through the web that uses the factory from an
    # existing type, but wants a unique portal_type!
    content.portal_type = fti.getId()
    fields = dict(kw)
    done = []

    for schema in iterSchemataForType(portal_type):
        # schema.names() doesn't return attributes from superclasses in derived
        # schemas. therefore we have to iterate over all items from the passed
        # keywords arguments and set it, if the behavior has the questioned
        # attribute.
        behavior = schema(content)
        for name, value in fields.items():
            if name in done:
                # already set
                continue
            try:
                # hasattr swallows exceptions.
                getattr(behavior, name)
            except AttributeError:
                # fieldname not available
                continue
            setattr(behavior, name, value)
            done.append(name)

    for (key, value) in fields.items():
        if key in done:
            continue
        setattr(content, key, value)

    notify(ObjectCreatedEvent(content))
    return content


def addContentToContainer(container, object, checkConstraints=True):
    """Add an object to a container.

    The portal_type must already be set correctly. If checkConstraints
    is False no check for addable content types is done. The new object,
    wrapped in its new acquisition context, is returned.
    """
    if not hasattr(aq_base(object), "portal_type"):
        raise ValueError("object must have its portal_type set")

    container = aq_inner(container)
    if checkConstraints:
        container_fti = container.getTypeInfo()

        fti = getUtility(IDexterityFTI, name=object.portal_type)
        if not fti.isConstructionAllowed(container):
            raise Unauthorized("Cannot create %s" % object.portal_type)

        if container_fti is not None \
           and not container_fti.allowType(object.portal_type):
            raise ValueError(
                "Disallowed subobject type: %s" % object.portal_type
            )

    name = getattr(aq_base(object), 'id', None)
    name = INameChooser(container).chooseName(name, object)
    object.id = name

    newName = container._setObject(name, object)
    try:
        return container._getOb(newName)
    except AttributeError:
        uuid = IUUID(object)
        return uuidToObject(uuid)


def createContentInContainer(container, portal_type, checkConstraints=True,
                             **kw):
    content = createContent(portal_type, **kw)
    return addContentToContainer(
        container,
        content,
        checkConstraints=checkConstraints
    )


def safe_utf8(st):
    if isinstance(st, six.text_type):
        st = st.encode('utf8')
    return st


def safe_unicode(st):
    if isinstance(st, six.binary_type):
        st = st.decode('utf8')
    return st


def datify(in_date):
    """Get a DateTime object from a string (or anything parsable by DateTime,
       a datetime.date, a datetime.datetime
    """
    if isinstance(in_date, DateTime):
        return in_date
    if in_date == 'None':
        in_date = None
    elif isinstance(in_date, datetime.datetime):
        in_date = DateTime(in_date)
    elif isinstance(in_date, datetime.date):
        in_date = DateTime(in_date.year, in_date.month, in_date.day)
    elif in_date is not None:
        in_date = DateTime(in_date)
    return in_date


def all_merged_tagged_values_dict(ifaces, key):
    """mergedTaggedValueDict of all interfaces for a given key

    usally interfaces is a list of schemas
    """
    info = dict()
    for iface in ifaces:
        info.update(mergedTaggedValueDict(iface, key))
    return info
