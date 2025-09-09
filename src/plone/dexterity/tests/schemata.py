from plone.supermodel.interfaces import FILENAME_KEY
from zope import schema
from zope.interface import Interface


class ITestSchema(Interface):
    """Schema used for testing"""

    title = schema.TextLine(title="Title", description="Administrative title")

    description = schema.Text(title="Description", required=False)


class ITaggedValueSchema(Interface):
    """Schema used for testing tagged value filenames"""


ITaggedValueSchema.setTaggedValue(FILENAME_KEY, "/path/to/dummy.xml")


class IDerivedFromTaggedValueSchema(ITaggedValueSchema):
    """Schema used for testing tagged value filenames"""
