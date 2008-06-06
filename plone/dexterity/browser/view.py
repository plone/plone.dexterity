from zope.schema import getFieldsInOrder
from zope.component import getUtility

from plone.dexterity.interfaces import IDexterityFTI

from Acquisition import aq_inner
from Products.Five.browser import BrowserView

class DefaultView(BrowserView):
    
    def fields(self, ignored=['title', 'description']):
        """Get a list of tuples of the fields and their value
        """
        
        context = aq_inner(self.context)
        
        fti = getUtility(IDexterityFTI, name=context.portal_type)
        schema = fti.lookup_schema()
        
        for name, field in getFieldsInOrder(schema):
            if name not in ignored:
                field = field.bind(context)
                yield dict(id=field.__name__, 
                           title=field.title,
                           description=field.description,
                           value=field.get(context))