from zope.interface import Interface
from zope import schema

class ITestSchema(Interface):
    """Schema used for testing
    """
    
    title = schema.TextLine(title=u"Title",
                            description=u"Administrative title")
                        
    description = schema.Text(title=u"Description",
                              required=False)