# -*- coding: utf-8 -*-
from Products.CMFCore.interfaces import ITypeInformation
from zope.component.interfaces import IFactory
from zope.component.interfaces import IObjectEvent
from zope.interface import Interface, Attribute
from zope.lifecycleevent.interfaces import IModificationDescription
import zope.schema

try:
    from zope.app.content import IContentType
except ImportError:
    class IContentType(Interface):
        pass

# id for pseudo-resource used to expose data for folderish items over WebDAV
DAV_FOLDER_DATA_ID = '_data'


class IDexterityFTI(ITypeInformation):
    """The Factory Type Information for Dexterity content objects
    """

    def lookupSchema():
        """Return an InterfaceClass that represents the schema of this type.
        Raises a ValueError if it cannot be found.

        If a schema interface is specified, return this. Otherwise, look up
        the model from either the TTW model source string or a specified
        model XML file, and build a schema from the unnamed schema
        specified in this model.
        """

    def lookupModel():
        """Return the IModel specified in either the model_source or
        model_file (the former takes precedence). See plone.supermodel for
        more information about this type.

        If neither a model_source or a model_file is given, but a schema is
        given, return a faux model that contains just this schema.

        Note that model.schema is not necessarily going to be the same as
        the schema returned by lookupSchema().
        """

    add_permission = zope.schema.DottedName(
        title=u"Add permission",
        description=u"Zope 3 permission name for the permission required to "
                    u"construct this content",
    )

    behaviors = zope.schema.List(
        title=u"Behaviors",
        description=u"A list of behaviors that are enabled for this type. "
                    u"See plone.behavior for more details.",
        value_type=zope.schema.DottedName(title=u"Behavior name")
    )

    schema = zope.schema.DottedName(
        title=u"Schema interface",
        description=u"Dotted name to an interface describing the type. "
                    u"This is not required if there is a model file or a "
                    u"model source string containing an unnamed schema."
    )

    model_source = zope.schema.Text(
        title=u"Model text",
        description=u"XML representation of the model for this type. " +
                    u"If this is given, it will override any model_file."
    )

    model_file = zope.schema.Text(
        title=u"Model file",
        description=u"A file that contains an XML model. "
                    u"This may be an absolute path, or one relative to a "
                    u"package, e.g. my.package:model.xml"
    )

    hasDynamicSchema = zope.schema.Bool(
        title=u"Whether or not the FTI uses a dynamic schema.",
        readonly=True
    )


class IDexterityFTIModificationDescription(IModificationDescription):
    """Descriptor passed with an IObjectModifiedEvent for a Dexterity FTI.
    """

    attribute = zope.schema.ASCII(
        title=u"Name of the attribute that was modified"
    )
    oldValue = Attribute("Old value")


class IDexterityFactory(IFactory):
    """A factory that can create Dexterity objects.

    This factory will create an object by looking up the klass property of
    the FTI with the given portal type. It will also set the portal_type
    on the instance and mark the instance as providing the schema interface
    if it does not do so already.
    """

    portal_type = zope.schema.TextLine(
        title=u"Portal type name",
        description=u"The portal type this is an FTI for"
    )


# Schema
class IDexteritySchema(Interface):
    """Base class for Dexterity schemata
    """


# Schema cache
class ISchemaInvalidatedEvent(Interface):
    """Event fired when the schema cache should be invalidated.

    If the portal_type is not given, all schemata will be cleared from the
    cache.
    """

    portal_type = zope.schema.TextLine(title=u"FTI name", required=False)


# Content
class IDexterityContent(Interface):
    """Marker interface for dexterity-managed content objects
    """


class IDexterityItem(IDexterityContent):
    """Marker interface applied to dexterity-managed non-folderish objects
    """


class IDexterityContainer(IDexterityContent):
    """Marker interface applied to dexterity-managed folderish objects
    """


# Events
class IBegunEvent(IObjectEvent):
    """Base begun event
    """


class IEditBegunEvent(IBegunEvent):
    """An edit operation was begun
    """


class IAddBegunEvent(IBegunEvent):
    """An add operation was begun. The event context is the folder,
    since the object does not exist yet.
    """


class ICancelledEvent(IObjectEvent):
    """Base cancel event
    """


class IEditCancelledEvent(ICancelledEvent):
    """An edit operation was cancelled
    """


class IAddCancelledEvent(ICancelledEvent):
    """An add operation was cancelled. The event context is the folder,
    since the object does not exist yet.
    """


class IEditFinishedEvent(IObjectEvent):
    """Edit was finished and contents are saved. This event is fired
    even when no changes happen (and no modified event is fired.)
    """


# Views
class IDexterityEditForm(Interface):
    """The edit form for a Dexterity content type."""
