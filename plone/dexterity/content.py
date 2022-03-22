# -*- coding: utf-8 -*-
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl import Permissions as acpermissions
from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import Explicit
from copy import deepcopy
from DateTime import DateTime
from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import PathReprProvider
from OFS.SimpleItem import SimpleItem
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.filerepresentation import DAVCollectionMixin
from plone.dexterity.filerepresentation import DAVResourceMixin
from plone.dexterity.interfaces import IDexterityContainer
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityItem
from plone.dexterity.schema import SCHEMA_CACHE
from plone.dexterity.utils import all_merged_tagged_values_dict
from plone.dexterity.utils import datify
from plone.dexterity.utils import iterSchemata
from plone.dexterity.utils import safe_unicode
from plone.dexterity.utils import safe_utf8
from plone.folder.ordered import CMFOrderedBTreeFolderBase
from plone.uuid.interfaces import IAttributeUUID
from plone.uuid.interfaces import IUUID
from Products.CMFCore import permissions
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.interfaces import ICatalogableDublinCore
from Products.CMFCore.interfaces import IDublinCore
from Products.CMFCore.interfaces import IMutableDublinCore
from Products.CMFCore.interfaces import ITypeInformation
from Products.CMFCore.PortalContent import PortalContent
from Products.CMFCore.PortalFolder import PortalFolderBase
from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin
from Products.CMFPlone.interfaces import IConstrainTypes
from zExceptions import Unauthorized
from zope.annotation import IAttributeAnnotatable
from zope.component import queryUtility
from zope.container.contained import Contained
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.interface.declarations import getObjectSpecification
from zope.interface.declarations import implementedBy
from zope.interface.declarations import Implements
from zope.interface.declarations import ObjectSpecificationDescriptor
from zope.interface.interface import Method
from zope.schema.interfaces import IContextAwareDefaultFactory
from zope.security.interfaces import IPermission

import six
import threading


_marker = object()
_zone = DateTime().timezone()
_recursion_detection = threading.local()
FLOOR_DATE = DateTime(1970, 0)  # always effective
CEILING_DATE = DateTime(2500, 0)  # never expires

# see comment in DexterityContent.__getattr__ method
ATTRIBUTE_NAMES_TO_IGNORE = (
    "_dav_writelocks",
    "aq_inner",
    "getCurrentSkinName",
    "getURL",
    "im_self",  # python 2 only, on python 3 it was renamed to __self__
    "plone_utils",
    "portal_membership",
    "portal_placeful_workflow",
    "portal_properties",
    "translation_service",
    "utilities",
)

ASSIGNABLE_CACHE_KEY = "__plone_dexterity_assignable_cache__"


def _default_from_schema(context, schema, fieldname):
    """helper to lookup default value of a field"""
    if schema is None:
        return _marker
    field = schema.get(fieldname, None)
    if field is None or isinstance(field, Method):
        return _marker
    default_factory = getattr(field, "defaultFactory", None)
    if (
        # check for None to avoid one expensive providedBy (called often)
        default_factory is not None
        and IContextAwareDefaultFactory.providedBy(default_factory)
    ):
        return deepcopy(field.bind(context).default)
    return deepcopy(field.default)


def get_assignable(context):
    """get the BehaviorAssignable for the context.

    Read from cache on request if needed (twice as fast as lookup)

    returns IBehaviorAssignable providing instance or None
    """
    request = getRequest()
    if not request:
        return IBehaviorAssignable(context, None)
    cache_key = getattr(context, "_p_oid", None)
    if not cache_key:
        return IBehaviorAssignable(context, None)
    assignable_cache = getattr(request, ASSIGNABLE_CACHE_KEY, _marker)
    if assignable_cache is _marker:
        assignable_cache = dict()
        setattr(request, ASSIGNABLE_CACHE_KEY, assignable_cache)
    assignable = assignable_cache.get(cache_key, _marker)
    if assignable is _marker:
        assignable_cache[cache_key] = assignable = IBehaviorAssignable(
            context,
            None,
        )
    return assignable


class FTIAwareSpecification(ObjectSpecificationDescriptor):
    """A __providedBy__ decorator that returns the interfaces provided by
    the object, plus the schema interface set in the FTI.
    """

    def __get__(self, inst, cls=None):
        # We're looking at a class - fall back on default
        if inst is None:
            return getObjectSpecification(cls)

        # get direct specification
        spec = getattr(inst, "__provides__", None)

        # avoid recursion - fall back on default
        if getattr(_recursion_detection, "blocked", False):
            return spec

        # If the instance doesn't have a __provides__ attribute, get the
        # interfaces implied by the class as a starting point.
        if spec is None:
            spec = implementedBy(cls)

        # Find the data we need to know if our cache needs to be invalidated
        portal_type = getattr(inst, "portal_type", None)

        # If the instance has no portal type, then we're done.
        if portal_type is None:
            return spec

        # Find the cached value. This calculation is expensive and called
        # hundreds of times during each request, so we require a fast cache
        cache = getattr(inst, "_v__providedBy__", None)
        updated = ()
        dynamically_provided = []

        # block recursion
        setattr(_recursion_detection, "blocked", True)
        try:
            # See if we have a current cache. Reasons to do this include:
            #
            #  - The FTI was modified.
            #  - The instance was modified and persisted since the cache was built.
            #  - The instance has a different direct specification.
            updated = (
                inst._p_mtime,
                SCHEMA_CACHE.modified(portal_type),
                SCHEMA_CACHE.invalidations,
                hash(spec),
            )
            if cache is not None and cache[:-1] == updated:
                setattr(_recursion_detection, "blocked", False)
                if cache[-1] is not None:
                    return cache[-1]
                return spec

            main_schema = SCHEMA_CACHE.get(portal_type)
            if main_schema:
                dynamically_provided = [main_schema]
            else:
                dynamically_provided = []

            assignable = get_assignable(inst)
            if assignable is not None:
                for behavior_registration in assignable.enumerateBehaviors():
                    if behavior_registration.marker:
                        dynamically_provided.append(behavior_registration.marker)
        finally:
            setattr(_recursion_detection, "blocked", False)

        if not dynamically_provided:
            # rare case if no schema nor behaviors with markers are set
            inst._v__providedBy__ = updated + (None,)
            return spec

        dynamically_provided.append(spec)
        all_spec = Implements(*dynamically_provided)
        inst._v__providedBy__ = updated + (all_spec,)

        return all_spec


class AttributeValidator(Explicit):
    """Decide whether attributes should be accessible. This is set as the
    __allow_access_to_unprotected_subobjects__ variable in Dexterity's content
    classes.
    """

    def __call__(self, name, value):
        # Short circuit for things like views or viewlets
        if name == "":
            return 1

        context = aq_parent(self)

        # we may want to cache this based on the combined mod-times
        # of fti and context, but even this is not save in the case someone
        # decides to have behaviors bound on something different than context
        # or fti, i.e. schemas for subtrees.
        protection_dict = all_merged_tagged_values_dict(
            iterSchemata(context), READ_PERMISSIONS_KEY
        )

        if name not in protection_dict:
            return 1

        permission = queryUtility(IPermission, name=protection_dict[name])
        if permission is not None:
            return getSecurityManager().checkPermission(permission.title, context)

        return 0


class PasteBehaviourMixin(object):
    def _notifyOfCopyTo(self, container, op=0):
        """Keep Archetypes' reference info internally when op == 1 (move)
        because in those cases we need to keep Archetypes' refeferences.

        This is only required to support legacy Archetypes' references related
        to content within Dexterity container objects.
        """
        # AT BaseObject does this to prevent removing AT refs on object move
        # See: Products.Archetypes.Referenceable.Referenceable._notifyOfCopyTo

        # This isn't really safe for concurrent usage, but the
        # worse case is not that bad and could be fixed with a reindex
        # on the archetype tool:
        if op == 1:
            self._v_cp_refs = 1
            self._v_is_cp = 0
        if op == 0:
            self._v_cp_refs = 0
            self._v_is_cp = 1

        # AT BaseFolderMixin does this to propagate the notify to its children
        # See: Products.Archetypes.BaseFolder.BaseFolderMixin._notifyOfCopyTo

        if isinstance(self, PortalFolderBase):
            for child in self.objectValues():
                try:
                    child._notifyOfCopyTo(self, op)
                except AttributeError:
                    pass

    def _verifyObjectPaste(self, obj, validate_src=True):
        # Extend the paste checks from OFS.CopySupport.CopyContainer
        # (permission checks) and
        # Products.CMFCore.PortalFolder.PortalFolderBase (permission checks and
        # allowed content types) to also ask the FTI if construction is
        # allowed.
        super(PasteBehaviourMixin, self)._verifyObjectPaste(obj, validate_src)
        if validate_src:
            portal_type = getattr(aq_base(obj), "portal_type", None)
            if portal_type:
                fti = queryUtility(ITypeInformation, name=portal_type)
                if fti is not None and not fti.isConstructionAllowed(self):
                    raise ValueError("You can not add the copied content here.")

    def _getCopy(self, container):
        # Copy the _v_is_cp and _v_cp_refs flags from the original
        # object (self) to the new copy.
        # This has impact on how children will be handled.
        # When the flags are missing, an Archetypes child object will not have
        # the UID updated in some situations.
        # Copied from Products.Archetypes.Referenceable.Referenceable._getCopy
        is_cp_flag = getattr(self, "_v_is_cp", None)
        cp_refs_flag = getattr(self, "_v_cp_refs", None)
        ob = super(PasteBehaviourMixin, self)._getCopy(container)
        if is_cp_flag:
            setattr(ob, "_v_is_cp", is_cp_flag)
        if cp_refs_flag:
            setattr(ob, "_v_cp_refs", cp_refs_flag)
        return ob


@implementer(
    IDexterityContent,
    IAttributeAnnotatable,
    IAttributeUUID,
    IDublinCore,
    ICatalogableDublinCore,
    IMutableDublinCore,
)
class DexterityContent(DAVResourceMixin, PortalContent, PropertyManager, Contained):
    """Base class for Dexterity content"""

    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()

    security = ClassSecurityInfo()

    # portal_type is set by the add view and/or factory
    portal_type = None

    title = u""
    description = u""
    subject = ()
    creators = ()
    contributors = ()
    effective_date = None
    expiration_date = None
    format = "text/html"
    language = ""
    rights = ""

    def __init__(
        self,
        id=None,
        title=_marker,
        subject=_marker,
        description=_marker,
        contributors=_marker,
        effective_date=_marker,
        expiration_date=_marker,
        format=_marker,
        language=_marker,
        rights=_marker,
        **kwargs
    ):

        if id is not None:
            self.id = id
        now = DateTime()
        self.creation_date = now
        self.modification_date = now

        if title is not _marker:
            self.setTitle(title)
        if subject is not _marker:
            self.setSubject(subject)
        if description is not _marker:
            self.setDescription(description)
        if contributors is not _marker:
            self.setContributors(contributors)
        if effective_date is not _marker:
            self.setEffectiveDate(effective_date)
        if expiration_date is not _marker:
            self.setExpirationDate(expiration_date)
        if format is not _marker:
            self.setFormat(format)
        if language is not _marker:
            self.setLanguage(language)
        if rights is not _marker:
            self.setRights(rights)

        for (k, v) in kwargs.items():
            setattr(self, k, v)

    def __getattr__(self, name):
        # python basics:  __getattr__ is only invoked if the attribute wasn't
        # found by __getattribute__
        #
        # optimization: sometimes we're asked for special attributes
        # such as __conform__ that we can disregard (because we
        # wouldn't be in here if the class had such an attribute
        # defined).
        # also handle special dynamic providedBy cache here.
        # Ignore also some other well known names like
        # Permission, Acquisition and AccessControl related ones.
        if (
            name.startswith("__")
            or name.startswith("_v")
            or name.endswith("_Permission")
            or name in ATTRIBUTE_NAMES_TO_IGNORE
        ):
            raise AttributeError(name)

        # attribute was not found; try to look it up in the schema and return
        # a default
        value = _default_from_schema(self, SCHEMA_CACHE.get(self.portal_type), name)
        if value is not _marker:
            return value

        # do the same for each behavior
        assignable = get_assignable(self)
        if assignable is not None:
            for behavior_registration in assignable.enumerateBehaviors():
                if behavior_registration.interface:
                    value = _default_from_schema(
                        self, behavior_registration.interface, name
                    )
                    if value is not _marker:
                        return value

        raise AttributeError(name)

    # Let __name__ and id be identical. Note that id must be ASCII in Zope 2,
    # but __name__ should be unicode. Note that setting the name to something
    # that can't be encoded to ASCII will throw a UnicodeEncodeError

    def _get__name__(self):
        if six.PY2:
            return safe_unicode(self.id)
        return self.id

    def _set__name__(self, value):
        if six.PY2 and isinstance(value, six.text_type):
            value = str(value)  # may throw, but id must be ASCII in py2
        self.id = value

    __name__ = property(_get__name__, _set__name__)

    def UID(self):
        # Returns the item's globally unique id.
        return IUUID(self)

    @security.private
    def notifyModified(self):
        # Update creators and modification_date.
        # This is called from CMFCatalogAware.reindexObject.
        self.addCreator()
        self.setModificationDate()

    @security.protected(permissions.ModifyPortalContent)
    def addCreator(self, creator=None):
        # Add creator to Dublin Core creators.

        if len(self.creators) > 0:
            # do not add creator if one is already set
            return

        if creator is None:
            user = getSecurityManager().getUser()
            creator = user and user.getId()

        # call self.listCreators() to make sure self.creators exists
        if creator and creator not in self.listCreators():
            self.creators = self.creators + (creator,)

    @security.protected(permissions.ModifyPortalContent)
    def setModificationDate(self, modification_date=None):
        # Set the date when the resource was last modified.
        # When called without an argument, sets the date to now.
        if modification_date is None:
            self.modification_date = DateTime()
        else:
            self.modification_date = datify(modification_date)

    # IMinimalDublinCore

    @security.protected(permissions.View)
    def Title(self):
        # this is a CMF accessor, so should return utf8-encoded
        if six.PY2 and isinstance(self.title, six.text_type):
            return self.title.encode("utf-8")
        return self.title or ""

    @security.protected(permissions.View)
    def Description(self):
        value = self.description or ""

        # If description is containing linefeeds the HTML
        # validation can break.
        # See http://bo.geekworld.dk/diazo-bug-on-html5-validation-errors/
        # Remember: \r\n - Windows, \r - OS X, \n - Linux/Unix
        value = value.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")  # noqa

        # this is a CMF accessor, so should return utf8-encoded
        if six.PY2 and isinstance(value, six.text_type):
            value = value.encode("utf-8")

        return value

    @security.protected(permissions.View)
    def Type(self):
        ti = self.getTypeInfo()
        return ti is not None and ti.Title() or "Unknown"

    # IDublinCore

    @security.protected(permissions.View)
    def listCreators(self):
        # List Dublin Core Creator elements - resource authors.
        if self.creators is None:
            return ()
        if six.PY2:
            return tuple(safe_utf8(c) for c in self.creators)
        return self.creators

    @security.protected(permissions.View)
    def Creator(self):
        # Dublin Core Creator element - resource author.
        creators = self.listCreators()
        return creators and creators[0] or ""

    @security.protected(permissions.View)
    def Subject(self):
        # Dublin Core Subject element - resource keywords.
        if self.subject is None:
            return ()
        if six.PY2:
            return tuple(safe_utf8(s) for s in self.subject)
        return tuple(self.subject)

    @security.protected(permissions.View)
    def Publisher(self):
        # Dublin Core Publisher element - resource publisher.
        return "No publisher"

    @security.protected(permissions.View)
    def listContributors(self):
        # Dublin Core Contributor elements - resource collaborators.
        if six.PY2:
            return tuple(safe_utf8(c) for c in self.contributors)
        return tuple(self.contributors)

    @security.protected(permissions.View)
    def Contributors(self):
        # Deprecated alias of listContributors.
        return self.listContributors()

    @security.protected(permissions.View)
    def Date(self, zone=None):
        # Dublin Core Date element - default date.
        if zone is None:
            zone = _zone
        # Return effective_date if set, modification date otherwise
        date = getattr(self, "effective_date", None)
        if date is None:
            date = self.modified()

        date = datify(date)
        return date.toZone(zone).ISO()

    @security.protected(permissions.View)
    def CreationDate(self, zone=None):
        # Dublin Core Date element - date resource created.
        if zone is None:
            zone = _zone
        # return unknown if never set properly
        if self.creation_date:
            date = datify(self.creation_date)
            return date.toZone(zone).ISO()
        else:
            return "Unknown"

    @security.protected(permissions.View)
    def EffectiveDate(self, zone=None):
        # Dublin Core Date element - date resource becomes effective.
        if zone is None:
            zone = _zone
        ed = getattr(self, "effective_date", None)
        ed = datify(ed)
        return ed and ed.toZone(zone).ISO() or "None"

    @security.protected(permissions.View)
    def ExpirationDate(self, zone=None):
        # Dublin Core Date element - date resource expires.
        if zone is None:
            zone = _zone
        ed = getattr(self, "expiration_date", None)
        ed = datify(ed)
        return ed and ed.toZone(zone).ISO() or "None"

    @security.protected(permissions.View)
    def ModificationDate(self, zone=None):
        # Dublin Core Date element - date resource last modified.
        if zone is None:
            zone = _zone
        date = datify(self.modified())
        return date.toZone(zone).ISO()

    @security.protected(permissions.View)
    def Identifier(self):
        # Dublin Core Identifier element - resource ID.
        return self.absolute_url()

    @security.protected(permissions.View)
    def Language(self):
        # Dublin Core Language element - resource language.
        return self.language

    @security.protected(permissions.View)
    def Rights(self):
        # Dublin Core Rights element - resource copyright.
        if six.PY2:
            return safe_utf8(self.rights)
        return self.rights

    # ICatalogableDublinCore

    @security.protected(permissions.View)
    def created(self):
        # Dublin Core Date element - date resource created.
        # allow for non-existent creation_date, existed always
        date = getattr(self, "creation_date", None)
        date = datify(date)
        return date is None and FLOOR_DATE or date

    @security.protected(permissions.View)
    def effective(self):
        # Dublin Core Date element - date resource becomes effective.
        date = getattr(self, "effective_date", _marker)
        if date is _marker:
            date = getattr(self, "creation_date", None)
        date = datify(date)
        return date is None and FLOOR_DATE or date

    @security.protected(permissions.View)
    def expires(self):
        # Dublin Core Date element - date resource expires.
        date = getattr(self, "expiration_date", None)
        date = datify(date)
        return date is None and CEILING_DATE or date

    @security.protected(permissions.View)
    def modified(self):
        # Dublin Core Date element - date resource last modified.
        date = self.modification_date
        if date is None:
            # Upgrade.
            date = DateTime(self._p_mtime)
            self.modification_date = date
        date = datify(date)
        return date

    @security.protected(permissions.View)
    def isEffective(self, date):
        # Is the date within the resource's effective range?
        pastEffective = self.effective_date is None or self.effective_date <= date
        beforeExpiration = self.expiration_date is None or self.expiration_date >= date
        return pastEffective and beforeExpiration

    # IMutableDublinCore

    @security.protected(permissions.ModifyPortalContent)
    def setTitle(self, title):
        # Set Dublin Core Title element - resource name.
        self.title = safe_unicode(title)

    @security.protected(permissions.ModifyPortalContent)
    def setDescription(self, description):
        # Set Dublin Core Description element - resource summary.
        self.description = safe_unicode(description)

    @security.protected(permissions.ModifyPortalContent)
    def setCreators(self, creators):
        # Set Dublin Core Creator elements - resource authors.
        if isinstance(creators, six.string_types):
            creators = [creators]
        self.creators = tuple(safe_unicode(c.strip()) for c in creators)

    @security.protected(permissions.ModifyPortalContent)
    def setSubject(self, subject):
        # Set Dublin Core Subject element - resource keywords.
        if isinstance(subject, six.string_types):
            subject = [subject]
        self.subject = tuple(safe_unicode(s.strip()) for s in subject)

    @security.protected(permissions.ModifyPortalContent)
    def setContributors(self, contributors):
        # Set Dublin Core Contributor elements - resource collaborators.
        if isinstance(contributors, six.string_types):
            contributors = contributors.split(";")
        self.contributors = tuple(safe_unicode(c.strip()) for c in contributors)

    @security.protected(permissions.ModifyPortalContent)
    def setEffectiveDate(self, effective_date):
        # Set Dublin Core Date element - date resource becomes effective.
        self.effective_date = datify(effective_date)

    @security.protected(permissions.ModifyPortalContent)
    def setExpirationDate(self, expiration_date):
        # Set Dublin Core Date element - date resource expires.
        self.expiration_date = datify(expiration_date)

    @security.protected(permissions.ModifyPortalContent)
    def setFormat(self, format):
        # Set Dublin Core Format element - resource format.
        self.format = format

    @security.protected(permissions.ModifyPortalContent)
    def setLanguage(self, language):
        # Set Dublin Core Language element - resource language.
        self.language = language

    @security.protected(permissions.ModifyPortalContent)
    def setRights(self, rights):
        # Set Dublin Core Rights element - resource copyright.
        self.rights = safe_unicode(rights)


@implementer(IDexterityItem)
class Item(PasteBehaviourMixin, BrowserDefaultMixin, DexterityContent):
    """A non-containerish, CMFish item"""

    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()

    isPrincipiaFolderish = 0

    manage_options = (
        PropertyManager.manage_options
        + (
            {
                "label": "View",
                "action": "view",
            },
        )
        + CMFCatalogAware.manage_options
        + SimpleItem.manage_options
    )

    # Be explicit about which __getattr__ to use
    __getattr__ = DexterityContent.__getattr__


@implementer(IDexterityContainer)
class Container(
    PathReprProvider,
    PasteBehaviourMixin,
    DAVCollectionMixin,
    BrowserDefaultMixin,
    CMFCatalogAware,
    CMFOrderedBTreeFolderBase,
    DexterityContent,
):
    """Base class for folderish items"""

    __providedBy__ = FTIAwareSpecification()
    __allow_access_to_unprotected_subobjects__ = AttributeValidator()

    security = ClassSecurityInfo()
    security.declareProtected(acpermissions.copy_or_move, "manage_copyObjects")
    security.declareProtected(permissions.ModifyPortalContent, "manage_cutObjects")
    security.declareProtected(permissions.ModifyPortalContent, "manage_pasteObjects")
    security.declareProtected(permissions.ModifyPortalContent, "manage_renameObject")
    security.declareProtected(permissions.ModifyPortalContent, "manage_renameObjects")

    isPrincipiaFolderish = 1

    # make sure CMFCatalogAware's manage_options don't take precedence
    manage_options = PortalFolderBase.manage_options

    # Make sure PortalFolder's accessors and mutators don't take precedence
    Title = DexterityContent.Title
    setTitle = DexterityContent.setTitle
    Description = DexterityContent.Description
    setDescription = DexterityContent.setDescription

    def __init__(self, id=None, **kwargs):
        CMFOrderedBTreeFolderBase.__init__(self, id)
        DexterityContent.__init__(self, id, **kwargs)

    def __getattr__(self, name):
        try:
            return DexterityContent.__getattr__(self, name)
        except AttributeError:
            pass

        # Be specific about the implementation we use
        if self._tree is not None:
            return CMFOrderedBTreeFolderBase.__getattr__(self, name)

        raise AttributeError(name)

    @security.protected(permissions.DeleteObjects)
    def manage_delObjects(self, ids=None, REQUEST=None):
        """Delete the contained objects with the specified ids.

        If the current user does not have permission to delete one of the
        objects, an Unauthorized exception will be raised.
        """
        if ids is None:
            ids = []
        if isinstance(ids, six.string_types):
            ids = [ids]
        for id in ids:
            item = self._getOb(id)
            if not getSecurityManager().checkPermission(
                permissions.DeleteObjects, item
            ):
                raise Unauthorized("Do not have permissions to remove this object")
        return super(Container, self).manage_delObjects(ids, REQUEST=REQUEST)

    # override PortalFolder's allowedContentTypes to respect IConstrainTypes
    # adapters
    def allowedContentTypes(self, context=None):
        if not context:
            context = self

        constrains = IConstrainTypes(context, None)
        if not constrains:
            return super(Container, self).allowedContentTypes()

        return constrains.allowedContentTypes()

    # override PortalFolder's invokeFactory to respect IConstrainTypes
    # adapters
    def invokeFactory(self, type_name, id, RESPONSE=None, *args, **kw):
        # Invokes the portal_types tool.
        constrains = IConstrainTypes(self, None)

        if constrains:
            # Do permission check before constrain checking so we'll get
            # an Unauthorized over a ValueError.
            fti = queryUtility(ITypeInformation, name=type_name)
            if fti is not None and not fti.isConstructionAllowed(self):
                raise Unauthorized("Cannot create %s" % fti.getId())

            allowed_ids = [i.getId() for i in constrains.allowedContentTypes()]
            if type_name not in allowed_ids:
                raise ValueError(
                    "Subobject type disallowed by IConstrainTypes adapter: %s"
                    % type_name
                )

        return super(Container, self).invokeFactory(
            type_name, id, RESPONSE, *args, **kw
        )


def reindexOnModify(content, event):
    """When an object is modified, re-index it in the catalog"""

    if event.object is not content:
        return

    # NOTE: We are not using event.descriptions because the field names may
    # not match index names.

    content.reindexObject()
