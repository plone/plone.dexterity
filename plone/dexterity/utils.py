from zope.schema import getFieldsInOrder
from zope.component import getUtility
from Products.CMFCore.interfaces import ISiteRoot

# TODO: Need a better encoding algorithm here. The output needs to be
# valid Python identifiers.

key = (
    (' ', '_1_'),
    ('.', '_2_'),
    ('-', '_3_'),
    )

def encode(s):
    for k,v in key:
        s = s.replace(k, v)
    return s
    
def decode(s):
    for k,v in key:
        s = s.replace(v, k)
    return s

def join(*args):
    return '_0_'.join([encode(a) for a in args if a])
    
def split(s):
    return [decode(a) for a in s.split('_0_')]

def portal_type_to_schema_name(portal_type, schema=u"", prefix=None):
    """Return a canonical interface name for a generated schema interface.
    """
    if prefix is None:
        prefix = getUtility(ISiteRoot).getId()
    
    return join(prefix, portal_type, schema)
        
def schema_name_to_portal_type(schema_name):
    """Return a the portal_type part of a schema name
    """
    return split(schema_name)[1]

def split_schema_name(schema_name):
    """Return a tuple prefix, portal_type, schema_name
    """
    items = split(schema_name) 
    if len(items) == 2:
        return items[0], items[1], u""
    elif len(items) == 3:
        return items[0], items[1], items[2]
    else:
        raise ValueError("Schema name %s is invalid" % schema_name)

def sync_schema(source, dest, overwrite=False):
    """Copy attributes from the source to the destination. If overwrite is
    False, do not overwrite attributes that already exist or delete ones
    that don't exist in source.
    """
    
    if overwrite:    
        to_delete = set()
    
        # Delete fields in dest, but not in source
        for name, field in getFieldsInOrder(dest):
            if name not in source:
                to_delete.add(name)
    
        for name in to_delete:
            # delattr(dest, name)
            del dest._InterfaceClass__attrs[name]
            if hasattr(dest, '_v_attrs'):
                del dest._v_attrs[name]

    # Add fields that are in source, but not in dest
    
    for name, field in getFieldsInOrder(source):
        if overwrite or name not in dest:
            
            clone = field.__class__.__new__(field.__class__)
            clone.__dict__.update(field.__dict__)
            clone.interface = dest
            clone.__name__ = name
            
            # setattr(dest, name, clone)
            dest._InterfaceClass__attrs[name] = clone
            if hasattr(dest, '_v_attrs'):
                dest._v_attrs[name] = clone
