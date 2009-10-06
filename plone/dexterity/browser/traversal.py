from zope.component import adapts

from zope.publisher.interfaces.browser import IBrowserRequest
from plone.dexterity.interfaces import IDexterityContent

try:
    from repoze.zope2.publishtraverse import DefaultPublishTraverse
except ImportError:
    from ZPublisher.BaseRequest import DefaultPublishTraverse

from Acquisition import aq_inner, aq_parent
from Acquisition.interfaces import IAcquirer
from webdav.NullResource import NullResource
from plone.dexterity.filerepresentation import FolderDataResource

class DexterityPublishTraverse(DefaultPublishTraverse):
    """Override the default browser publisher to make WebDAV work for
    Dexterity objects.
    
    This may become superfluous if http://bugs.launchpad.net/zope2/+bug/180155
    is fixed in Zope 2.
    """
    
    adapts(IDexterityContent, IBrowserRequest)
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    def publishTraverse(self, request, name):
        
        context = aq_inner(self.context)
        
        # If we are trying to traverse to the folder "body" pseudo-object 
        # returned by listDAVObjects(), return that immediately

        if name == '__folder_data__':
            return FolderDataResource('__folder_data__', context).__of__(context)
        
        defaultTraversal = super(DexterityPublishTraverse, self).publishTraverse(request, name)
        
        # If this is a WebDAV PUT/PROPFIND/PROPPATCH request, don't acquire
        # things. If we did, we couldn't create a new object with PUT, for
        # example, because the acquired object would shadow the NullResource
        
        if (getattr(request, 'maybe_webdav_client', False)               and
            request.get('REQUEST_METHOD', 'GET') not in ('GET', 'POST',) and
            IAcquirer.providedBy(defaultTraversal)
        ):
            parent = aq_parent(aq_inner(defaultTraversal))
            if parent is not None and parent is not context:
                return NullResource(self.context, name, request).__of__(self.context)
        
        return defaultTraversal
    
    def browserDefault(self, request):
        
        # If this is not a WebDAV request, we don't want to give a 
        # default view. The ZPublisher's WebDAV implementation doesn't
        # deal well with default views.
        
        if (getattr(request, 'maybe_webdav_client', False) and
            request.get('REQUEST_METHOD', 'GET') not in ('GET', 'POST',)
        ):
            return self.context, ()
        
        return super(DexterityPublishTraverse, self).browserDefault(request)
