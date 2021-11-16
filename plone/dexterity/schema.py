# -*- coding: utf-8 -*-
from .interfaces import IContentType
from .interfaces import IDexterityFTI
from .interfaces import IDexteritySchema
from .interfaces import ISchemaInvalidatedEvent
from .synchronize import synchronized
from plone.alterego import dynamic
from plone.alterego.interfaces import IDynamicObjectFactory
from plone.behavior.interfaces import IBehavior
from plone.behavior.registration import BehaviorRegistration
from plone.supermodel.parser import ISchemaPolicy
from plone.supermodel.utils import syncSchema
from Products.CMFCore.interfaces import ISiteRoot
from threading import RLock
from zope.component import adapter
from zope.component import getAllUtilitiesRegisteredFor
from zope.component import getUtility
from zope.component import queryUtility
from zope.component.hooks import getSite
from zope.dottedname.resolve import resolve
from zope.globalrequest import getRequest
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface.interface import InterfaceClass

import functools
import logging
import six
import types
import warnings


log = logging.getLogger(__name__)

# Dynamic modules
generated = dynamic.create("plone.dexterity.schema.generated")
transient = types.ModuleType("transient")

_MARKER = dict()

FTI_CACHE_KEY = "__plone_dexterity_fti_cache__"


def invalidate_cache(fti):
    fti._p_activate()
    fti.__dict__.pop("_v_schema_get", None)
    fti.__dict__.pop("_v_schema_behavior_registrations", None)
    fti.__dict__.pop("_v_schema_subtypes", None)
    fti.__dict__.pop("_v_schema_schema_interfaces", None)
    fti.__dict__.pop("_v_schema_modified", None)
    fti.__dict__.pop("_v_schema_behavior_schema_interfaces", None)
    request = getRequest()
    if request:
        setattr(request, FTI_CACHE_KEY, None)


def lookup_fti(portal_type, cache=True):
    # if its a string lookup fti
    if isinstance(portal_type, six.string_types):
        # looking up a utility is expensive, using the global request as
        # cache is twice as fast
        if cache:
            request = getRequest()
            if request:
                fti_cache = getattr(request, FTI_CACHE_KEY, None)
                if fti_cache is None:
                    fti_cache = dict()
                    setattr(request, FTI_CACHE_KEY, fti_cache)
                fti = None
                if portal_type in fti_cache:
                    fti = fti_cache[portal_type]

                if fti is None:
                    fti_cache[portal_type] = fti = queryUtility(
                        IDexterityFTI, name=portal_type
                    )
                return fti
        return queryUtility(IDexterityFTI, name=portal_type)
    if IDexterityFTI.providedBy(portal_type):
        # its already an IDexterityFTI instance
        return portal_type
    raise ValueError(
        "portal_type has to either string or IDexterityFTI instance but is "
        "{0!r}".format(portal_type)
    )


def volatile(func):
    @functools.wraps(func)
    def decorator(self, portal_type):
        """lookup fti from portal_type and cache

        input can be either a portal_type as string or as the utility instance.
        return value is always a FTI-ultiliy or None
        """
        # this function is called very often!
        # shortcut None input
        if portal_type is None:
            return func(self, None)
        fti = lookup_fti(portal_type, cache=self.cache_enabled)
        if fti is None:
            return func(self, None)
        if self.cache_enabled:
            key = "_v_schema_%s" % func.__name__
            cache = getattr(fti, key, _MARKER)
            if cache is not _MARKER:
                mtime, value = cache
                if fti._p_mtime == mtime:
                    return value

        value = func(self, fti)

        if self.cache_enabled:
            setattr(fti, key, (fti._p_mtime, value))

        return value

    return decorator


class SchemaCache(object):
    """Simple schema cache for FTI based schema information.

    This cache will store a Python object reference to the schema, as returned
    by fti.lookupSchema(), for any number of portal types. The value will
    be cached until the server is restarted or the cache is invalidated or
    cleared.

    You should only use this if you require bare-metal speed. For almost all
    operations, it's safer and easier to do:

        >>> fti = getUtility(IDexterityFTI, name=portal_type)
        >>> schema = fti.lookupSchema()

    The lookupSchema() call is probably as fast as this cache. However, if
    you need to avoid the utility lookup, you can use the cache like so:

        >>> from plone.dexterity.schema import SCHEMA_CACHE
        >>> my_schema = SCHEMA_CACHE.get(portal_type)

    The cache uses the FTI's modification time as its invariant.
    """

    lock = RLock()

    def __init__(self, cache_enabled=True):
        self.cache_enabled = cache_enabled
        self.invalidations = 0

    @volatile
    def get(self, fti):
        """main schema

        magic! fti is passed in as a string (identifier of fti), then volatile
        decorator looks it up and passes the FTI instance in.
        """
        if fti is not None:
            try:
                return fti.lookupSchema()
            except (AttributeError, ValueError):
                pass

    @volatile
    def behavior_registrations(self, fti):
        """all behavior behavior registrations of a given fti passed in as
        portal_type string (magic see get)

        returns a tuple with instances of
        ``plone.behavior.registration.BehaviorRegistration`` instances
        for the given fti.
        """
        if fti is None:
            return tuple()
        registrations = []
        for behavior_name in filter(None, fti.behaviors):
            registration = queryUtility(IBehavior, name=behavior_name)
            if registration is None:
                # BBB - this case should be deprecated in v 3.0
                warnings.warn(
                    'No behavior registration found for behavior named "{0}"'
                    ' for factory "{1}"'
                    " - trying deprecated fallback lookup (will be removed "
                    'in 3.0)..."'.format(behavior_name, fti.getId()),
                    DeprecationWarning,
                )
                try:
                    schema_interface = resolve(behavior_name)
                except (ValueError, ImportError):
                    log.error(
                        "Error resolving behavior {0} for factory {1}".format(
                            behavior_name, fti.getId()
                        )
                    )
                    continue
                registration = BehaviorRegistration(
                    title=behavior_name,
                    description="bbb fallback lookup",
                    interface=schema_interface,
                    marker=None,
                    factory=None,
                )
            registrations.append(registration)
        return tuple(registrations)

    @volatile
    def subtypes(self, fti):
        """all registered marker interfaces of ftis behaviors

        XXX: this one does not make much sense and should be deprecated
        """
        if fti is None:
            return ()
        subtypes = []
        for behavior_registration in self.behavior_registrations(fti):
            if (
                behavior_registration is not None
                and behavior_registration.marker is not None
            ):
                subtypes.append(behavior_registration.marker)
        return tuple(subtypes)

    @volatile
    def behavior_schema_interfaces(self, fti):
        """behavior schema interfaces registered for the fti

        all schemas from behaviors
        """
        if fti is None:
            return ()
        schemas = []
        for behavior_registration in self.behavior_registrations(fti):
            if behavior_registration is not None and behavior_registration.interface:
                schemas.append(behavior_registration.interface)
        return tuple(schemas)

    @volatile
    def schema_interfaces(self, fti):
        """all schema interfaces registered for the fti

        main_schema plus schemas from behaviors
        """
        if fti is None:
            return ()
        schemas = []
        try:
            main_schema = self.get(fti)  # main schema
            schemas.append(main_schema)
        except (ValueError, AttributeError):
            pass
        for schema in self.behavior_schema_interfaces(fti):
            schemas.append(schema)
        return tuple(schemas)

    @synchronized(lock)
    def clear(self):
        for fti in getAllUtilitiesRegisteredFor(IDexterityFTI):
            self.invalidate(fti)
        request = getRequest()
        fti_cache = getattr(request, FTI_CACHE_KEY, None)
        if fti_cache is not None:
            delattr(request, FTI_CACHE_KEY)

    @synchronized(lock)
    def invalidate(self, fti):
        if fti is not None and not IDexterityFTI.providedBy(fti):
            # fti is a name, lookup
            fti = queryUtility(IDexterityFTI, name=fti)
        if fti is not None:
            invalidate_cache(fti)
            self.invalidations += 1

    @volatile
    def modified(self, fti):
        if fti:
            return fti._p_mtime


SCHEMA_CACHE = SchemaCache()


@implementer(ISchemaInvalidatedEvent)
class SchemaInvalidatedEvent(object):
    def __init__(self, portal_type):
        self.portal_type = portal_type


@adapter(ISchemaInvalidatedEvent)
def invalidate_schema(event):
    if event.portal_type:
        SCHEMA_CACHE.invalidate(event.portal_type)
    else:
        SCHEMA_CACHE.clear()


# here starts the code dealing wih dynamic schemas.
class SchemaNameEncoder(object):
    """Schema name encoding"""

    key = (
        (" ", "_1_"),
        (".", "_2_"),
        ("-", "_3_"),
        ("/", "_4_"),
        ("|", "_5_"),
    )

    def encode(self, s):
        for k, v in self.key:
            s = s.replace(k, v)
        return s

    def decode(self, s):
        for k, v in self.key:
            s = s.replace(v, k)
        return s

    def join(self, *args):
        return "_0_".join([self.encode(a) for a in args if a])

    def split(self, s):
        return [self.decode(a) for a in s.split("_0_")]


def portalTypeToSchemaName(portal_type, schema=u"", prefix=None, suffix=None):
    """Return a canonical interface name for a generated schema interface."""
    if prefix is None:
        siteroot = None
        if portal_type == "Plone Site":
            fti = queryUtility(IDexterityFTI, name=portal_type)
            if fti is not None:
                siteroot = fti.__parent__
        if siteroot is None:
            siteroot = getUtility(ISiteRoot)
        prefix = "/".join(siteroot.getPhysicalPath())[1:]
    if suffix:
        prefix = "|".join([prefix, suffix])

    encoder = SchemaNameEncoder()
    return encoder.join(prefix, portal_type, schema)


def schemaNameToPortalType(schemaName):
    """Return a the portal_type part of a schema name"""
    encoder = SchemaNameEncoder()
    return encoder.split(schemaName)[1]


def splitSchemaName(schemaName):
    """Return a tuple prefix, portal_type, schemaName"""
    encoder = SchemaNameEncoder()
    items = encoder.split(schemaName)
    if len(items) == 2:
        return items[0], items[1], u""
    elif len(items) == 3:
        return items[0], items[1], items[2]
    else:
        raise ValueError("Schema name %s is invalid" % schemaName)


# Dynamic module factory
@implementer(IDynamicObjectFactory)
class SchemaModuleFactory(object):
    """Create dynamic schema interfaces on the fly"""

    lock = RLock()
    _transient_SCHEMA_CACHE = {}

    @synchronized(lock)
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
            prefix, portal_type, schemaName = splitSchemaName(name)
        except ValueError:
            return None

        if name in self._transient_SCHEMA_CACHE:
            schema = self._transient_SCHEMA_CACHE[name]
        else:
            bases = ()

            is_default_schema = not schemaName
            if is_default_schema:
                bases += (IDexteritySchema,)

            schema = InterfaceClass(name, bases, __module__=module.__name__)

            if is_default_schema:
                alsoProvides(schema, IContentType)
        if portal_type is not None:
            fti = queryUtility(IDexterityFTI, name=portal_type)
        else:
            fti = None
        if fti is None and name not in self._transient_SCHEMA_CACHE:
            self._transient_SCHEMA_CACHE[name] = schema
        elif fti is not None:
            model = fti.lookupModel()
            syncSchema(model.schemata[schemaName], schema, sync_bases=True)

            # Save this schema in the module - this factory will not be
            # called again for this name

            if name in self._transient_SCHEMA_CACHE:
                del self._transient_SCHEMA_CACHE[name]

            log.debug("Dynamic schema generated: %s", name)
            setattr(module, name, schema)

        return schema


@implementer(ISchemaPolicy)
class DexteritySchemaPolicy(object):
    """Determines how and where imported dynamic interfaces are created.
    Note that these schemata are never used directly. Rather, they are merged
    into a schema with a proper name and module, either dynamically or
    in code.
    """

    def module(self, schemaName, tree):
        return "plone.dexterity.schema.transient"

    def bases(self, schemaName, tree):
        return ()

    def name(self, schemaName, tree):
        # We use a temporary name whilst the interface is being generated;
        # when it's first used, we know the portal_type and site, and can
        # thus update it
        return "__tmp__" + schemaName
