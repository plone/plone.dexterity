from zope.component import getUtility
from zope.schema import getFieldsInOrder

from z3c.form import field
from z3c.form.util import expandPrefix
from z3c.form.interfaces import INPUT_MODE

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IFormFieldProvider

from plone.dexterity.utils import resolve_dotted_name

from plone.z3cform.fieldsets.extensible import ExtensibleForm
from plone.z3cform.fieldsets.group import GroupFactory

from plone.z3cform.fieldsets.utils import move

def process_fields(form, schema, prefix=None):
    """Add the fields from the schema to the from, taking into account
    the hints in the dexterity.form tagged value.
    """
    
    def _fn(field_name):
        if prefix:
            return expandPrefix(prefix) + field_name
        else:
            return field_name
    
    form_data = schema.queryTaggedValue(u'dexterity.form', {})
    
    # Get metadata
    
    omitted = frozenset([_fn(field_name) 
                    for field_name, value in form_data.get('omitted', [])])
    modes = dict([(_fn(field_name), value)
                    for field_name, value in form_data.get('modes', [])])
    widgets = dict([(_fn(field_name), value)
                    for field_name, value in form_data.get('widgets', [])])
    moves = dict([(_fn(field_name), value)
                    for field_name, value in form_data.get('moves', [])])
    
    fieldsets = {}
    fieldset_fields = set()
    for field_name, fieldset in form_data.get('fieldsets', []):
        if field_name not in omitted:
            fieldsets.setdefault(fieldset, []).append(_fn(field_name))
            fieldset_fields.add(_fn(field_name))
    
    default_fieldset_fields = [_fn(f) for f, value in getFieldsInOrder(schema) 
                                if not value.readonly and 
                                    _fn(f) not in fieldset_fields and 
                                    _fn(f) not in omitted]

    groups_by_label = dict([(g.label, g) for g in form.groups])
    
    if prefix:
        all_fields = field.Fields(schema, prefix=prefix, omitReadOnly=True)
    else:
        all_fields = field.Fields(schema, omitReadOnly=True)
    
    # Set up the default fields, widget factories and widget modes
    
    new_fields = all_fields.select(*default_fieldset_fields)
    
    def process_widgets(new_fields):
        for field_name in new_fields:
            widget_name = widgets.get(field_name, None)
            if widget_name is not None:
                widget_factory = resolve_dotted_name(widget_name)
                if widget_factory is not None:
                    new_fields[field_name].widgetFactory[INPUT_MODE] = widget_factory
            if field_name in modes:
                new_fields[field_name].mode = modes[field_name]
    
    process_widgets(new_fields)
    
    if form.fields is None:
        form.fields = new_fields
    else:
        form.fields += new_fields
    
    # Set up fields for fieldsets
    
    for fieldset, field_names in fieldsets.items():
        
        new_fields = all_fields.select(*field_names)
        process_widgets(new_fields)
        
        if fieldset not in groups_by_label:
            form.groups.append(GroupFactory(fieldset, new_fields))
        else:
            groups_by_label[fieldset].fields += new_fields
    
    # Process moves
    for field_name, before in moves.items():
        try:
            move(form, field_name, before=before)
        except KeyError:
            pass

class DexterityExtensibleForm(ExtensibleForm):
    """Mixin class for Dexterity forms that support updatable fields
    """
    
    def updateFields(self):
    
        self.fields = None
        self.groups = []
        
        # Set up fields from the FTI
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        
        schema = fti.lookup_schema()
        process_fields(self, schema)
        
        # Set up fields from behaviors
        for behavior_name in fti.behaviors:
            behavior_interface = resolve_dotted_name(behavior_name)
            if behavior_interface is not None:
                behavior_schema = IFormFieldProvider(behavior_interface, None)
                if behavior_schema is not None:
                    process_fields(self, behavior_schema, prefix=behavior_schema.__identifier__)
                
        # Allow the regular adapters to update the fields
        super(DexterityExtensibleForm, self).updateFields()
        
    @property
    def description(self):
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        return fti.description