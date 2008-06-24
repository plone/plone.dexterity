# integration with plone.app.schemaeditor

from zope.component import queryUtility

from plone.dexterity.interfaces import IDexteritySchema, IDexterityFTI
from plone.dexterity.utils import split_schema_name, sync_schema
from plone.supermodel import serialize_model

def serialize_schema(field_view, event):
    # XXX should batch so we don't do this multiple times if multiple
    # fields were modified.  but for that, we need to annotate the request or something?
    
    schema = field_view.schema
    
    # determine portal_type
    try:
        prefix, portal_type, schema_name = split_schema_name(schema.__name__)
    except ValueError:
        # not a dexterity schema
        return

    # find the FTI and model
    # (XXX Proof of concept.  Need to think through full use cases involving things
    # like customizing through the web following filesystem customization, need for
    # merging, etc.)
    fti = queryUtility(IDexterityFTI, name=portal_type)
    
    if fti.has_dynamic_schema:
        try:
            model = fti.lookup_model()
        except Exception, e:
            raise
            
        # synchronize changes to the model
        sync_schema(schema, model.schemata[schema_name].schema, overwrite=True)
        fti.model_source = serialize_model(model)
    else:
        raise "Changes to non-dynamic schemata not yet supported."
