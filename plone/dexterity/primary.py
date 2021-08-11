# -*- coding: utf-8 -*-
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import iterSchemata
from plone.rfc822.interfaces import IPrimaryField
from plone.rfc822.interfaces import IPrimaryFieldInfo
from zope.component import adapter
from zope.interface import implementer
from zope.schema import getFieldsInOrder


@implementer(IPrimaryFieldInfo)
@adapter(IDexterityContent)
class PrimaryFieldInfo(object):
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
            raise TypeError("Could not adapt", context, IPrimaryFieldInfo)
        self.fieldname, self.field = primary

    @property
    def value(self):
        return self.field.get(self.context)
