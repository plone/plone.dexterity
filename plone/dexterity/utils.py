from zope.component import getUtility
from zope.dottedname.resolve import resolve

from Products.CMFCore.interfaces import ISiteRoot

# Not thread safe, but downside of a write conflict is very small
_dotted_cache = {}

def resolve_dotted_name(dotted_name):
    """Resolve a dotted name to a real object
    """
    global _dotted_cache
    if dotted_name not in _dotted_cache:
        _dotted_cache[dotted_name] = resolve(dotted_name)
    return _dotted_cache[dotted_name]

# Schema name encoding

class SchemaNameEncoder(object):

    key = (
        (' ', '_1_'),
        ('.', '_2_'),
        ('-', '_3_'),
        ('/', '_4_'),
        )

    def encode(self, s):
        for k,v in self.key:
            s = s.replace(k, v)
        return s
    
    def decode(self, s):
        for k,v in self.key:
            s = s.replace(v, k)
        return s

    def join(self, *args):
        return '_0_'.join([self.encode(a) for a in args if a])
    
    def split(self, s):
        return [self.decode(a) for a in s.split('_0_')]

def portal_type_to_schema_name(portal_type, schema=u"", prefix=None):
    """Return a canonical interface name for a generated schema interface.
    """
    if prefix is None:
        prefix = '/'.join(getUtility(ISiteRoot).getPhysicalPath())[1:]
    
    encoder = SchemaNameEncoder()
    return encoder.join(prefix, portal_type, schema)
        
def schema_name_to_portal_type(schema_name):
    """Return a the portal_type part of a schema name
    """
    encoder = SchemaNameEncoder()
    return encoder.split(schema_name)[1]

def split_schema_name(schema_name):
    """Return a tuple prefix, portal_type, schema_name
    """
    encoder = SchemaNameEncoder()
    items = encoder.split(schema_name)
    if len(items) == 2:
        return items[0], items[1], u""
    elif len(items) == 3:
        return items[0], items[1], items[2]
    else:
        raise ValueError("Schema name %s is invalid" % schema_name)

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
