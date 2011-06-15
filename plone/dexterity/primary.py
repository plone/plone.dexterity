from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityFTI
from plone.rfc822.interfaces import IPrimaryField
from plone.rfc822.interfaces import IPrimaryFieldInfo
from zope.component import adapts
from zope.component import getUtility
from zope.interface import implements
from zope.schema import getFieldsInOrder


class PrimaryFieldInfo(object):
    implements(IPrimaryFieldInfo)
    adapts(IDexterityContent)

    def __init__(self, context):
        self.context = context
        fti = getUtility(IDexterityFTI, name=context.portal_type)
        self.schema = fti.lookupSchema()
        primary = [
            (name, field) for name, field in getFieldsInOrder(self.schema)
            if IPrimaryField.providedBy(field)
            ]
        if not primary:
            raise TypeError('Could not adapt', context, IPrimaryFieldInfo)
        self.fieldname, self.field = primary[0]
    
    @property
    def value(self):
        return self.field.get(self.context)
