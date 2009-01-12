from zope.component import getUtility
from zope.dottedname.resolve import resolve

from Products.CMFCore.interfaces import ISiteRoot

_dotted_cache = {}

# TODO: Need a better encoding algorithm here. The output needs to be
# valid Python identifiers, and unique, but this isn't terribly pretty.

key = (
    (' ', '_1_'),
    ('.', '_2_'),
    ('-', '_3_'),
    ('/', '_4_'),
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
        prefix = '/'.join(getUtility(ISiteRoot).getPhysicalPath())[1:]
    
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

def resolve_dotted_name(dotted_name):
    """Resolve a dotted name to a real object
    """
    global _dotted_cache
    if dotted_name not in _dotted_cache:
        _dotted_cache[dotted_name] = resolve(dotted_name)
    return _dotted_cache[dotted_name]

# Thread synchronisation decorator
def synchronized(lock):
    """Decorate a method with this and pass in a threading.Lock object to
    ensure that a method is synchronised over the given lock.
    """
    def wrap(f):
        def synchronized_function(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        return synchronized_function
    return wrap
