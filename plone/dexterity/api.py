from plone.supermodel import xml_schema as xml_schema_
from plone.dexterity.content import Item, Container

def xml_schema(filename, schema=u"", policy=u"dexterity", _frame=2):
    return xml_schema_(filename, schema, policy, _frame=_frame+1)
    
__all__ = ('xml_schema', 'Item', 'Container', )