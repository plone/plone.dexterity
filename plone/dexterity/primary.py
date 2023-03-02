from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import iterSchemata
from plone.rfc822.interfaces import IPrimaryField
from plone.rfc822.interfaces import IPrimaryFieldInfo
from zope.component import adapter
from zope.interface import implementer
from zope.schema import getFieldsInOrder


@implementer(IPrimaryFieldInfo)
@adapter(IDexterityContent)
class PrimaryFieldInfo:
    def __init__(self, context):
        self.context = context
        primary = None
        for i in iterSchemata(context):
            fields = getFieldsInOrder(i)
            for name, field in fields:
                if IPrimaryField.providedBy(field):
                    primary = (name, field)
                    break
        if not primary:
            self.fieldname, self.field = None, None
        else:
            self.fieldname, self.field = primary

    @property
    def value(self):
        if self.field is None:
            return None
        return self.field.get(self.context)
