# -*- coding: utf-8 -*-
from plone.autoform.view import WidgetsView
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import getAdditionalSchemata
from zope.component import getUtility
from plone.dexterity.utils import default_from_schema
from z3c.form.interfaces import IValue
from zope.component import adapter
from zope.interface import implementer

import os

_marker = object()


class DefaultView(WidgetsView):
    """The default view for Dexterity content. This uses a WidgetsView and
    renders all widgets in display mode.
    """

    if os.environ.get('DEXTERITY_WITHOUT_GETATTR'):
        def getContent(self):
            return self.context.aq_explicit

    @property
    def schema(self):
        fti = getUtility(IDexterityFTI, name=self.context.portal_type)
        return fti.lookupSchema()

    @property
    def additionalSchemata(self):
        return getAdditionalSchemata(context=self.context)


@implementer(IValue)
@adapter(None, None, DefaultView, None, None)
class DefaultViewDefaultValueAdapter(object):
    def __init__(self, context, request, form, field, widget):
        self.context = context
        self.request = request
        self.form = form
        self.field = field
        self.widget = widget

    def get(self):
        context = self.context
        schema = self.field.interface
        fieldname = self.field.__name__

        value = default_from_schema(context, schema, fieldname, default=_marker)  # noqa
        if value is _marker:
            return None
        else:
            return value
