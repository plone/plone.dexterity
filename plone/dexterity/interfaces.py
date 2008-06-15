from zope.interface import Interface, alsoProvides
import zope.schema

from zope.component.interfaces import IFactory
from zope.app.content.interfaces import IContentType

class IDexterityFTI(Interface):
    """The Factory Type Information for Dexterity content objects
    """

    def lookup_schema():
        """Return an InterfaceClass that represents the schema of this type.
        Raises a ValueError if it cannot be found.
        
        If a schema interface is specified, return this. Otherwise, look up
        the model from either the TTW model source string or a specified
        model XML file, and return the unnamed schema from this.
        """

    def lookup_model():
        """Return the model dict specified in either the model_source or
        model_file (the former takes precedence). See plone.supermodel for
        more information about the format of this.
        
        If neither a model_dict or a model_file is given, but a schema is
        given, return a faux model that contains just this schema.
        """

    behaviors = zope.schema.List(title=u"Behaviors",
                                 description=u"A list of behaviors that are enabled for this type. "
                                             u"See plone.behavior for more details.",
                                 value_type=zope.schema.DottedName(title=u"Behavior name"))

    schema = zope.schema.DottedName(title=u"Schema interface",
                                    description=u"Dotted name to an interface describing the type. "
                                                u"This is not required if there is a model file or a "
                                                u"model source string containing an unnamed schema.")

    model_source = zope.schema.Text(title=u"Model text",
                                    description=u"XML representation of the model for this type. " +
                                                u"If this is given, it will override any model_file.")

    model_file = zope.schema.Text(title=u"Model file",
                                  description=u"A file that contains an XML model. " 
                                              u"This may be an absolute path, or one relative to a " 
                                              u"package, e.g. my.package:model.xml")
    
    has_dynamic_schema = zope.schema.Bool(title=u"Whether or not the FTI uses a dynamic schema.",
                                          readonly=True)
    
class IDexterityFactory(IFactory):
    """A factory that can create Dexterity objects
    """
    
    portal_type = zope.schema.TextLine(title=u"Portal type name",
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