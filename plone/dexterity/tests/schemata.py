from zope.interface import Interface
from zope import schema

class ITestSchema(Interface):
    """Schema used for testing
    """
    
    title = schema.TextLine(title=u"Title",
                            description=u"Administrative title")
                        
    description = schema.Text(title=u"Description",
                              required=False)

class ITaggedValueSchema(Interface):
    """Schema used for testing tagged value filenames
    """
    
ITaggedValueSchema.setTaggedValue('plone.supermodel.filename', '/path/to/dummy.xml')

class IDerivedFromTaggedValueSchema(ITaggedValueSchema):
    """Schema used for testing tagged value filenames
    """