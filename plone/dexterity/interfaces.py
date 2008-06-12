from zope.interface import Interface, alsoProvides
from zope import schema

from zope.component.interfaces import IFactory
from zope.app.content.interfaces import IContentType

class IDexterityFTI(Interface):
    """The Factory Type Information for Dexterity content objects
    """

    def lookup_schema():
        """Return an InterfaceClass that represents the schema of this type.
        Raises a ValueError if it cannot be found.
        """

    def lookup_model():
        """Return the 'spec' dict for the model. See plone.supermodel for
        more information about the format of this.
        """

    behaviors = schema.List(title=u"Behaviors",
                            description=u"A list of behaviors that are enabled for this type. "
                                        u"See plone.behavior for more details.",
                            value_type=schema.DottedName(title=u"Behavior name"))

class IDynamicFTI(IDexterityFTI):
    """Web/TTW-specific features of the FTI
    """
    
    model_file = schema.Text(title=u"Model file",
                        description=u"A file that contains an XML model")
    
    model_source = schema.Text(title=u"Model text",
                        description=u"XML representation of the model for this type")
    
class IConcreteFTI(IDexterityFTI):
    """Filesystem-specific features of the FTI
    """

    schema = schema.DottedName(title=u"Schema interface",
                                description=u"Dotted name to an interface describing the type")
    
class IDexterityFactory(IFactory):
    """A factory that can create Dexterity objects
    """
    
    portal_type = schema.TextLine(title=u"Portal type name",
                                  description=u"The portal type this is an FTI for")

# Schema

class IDexteritySchema(Interface):
    """Base class for Dexterity schemata
    """
    
alsoProvides(IDexteritySchema, IContentType)

class ITransientSchema(Interface):
    """Marker interface for transient schemata
    """

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