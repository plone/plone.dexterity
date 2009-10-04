from zope.component import adapts

from zope.publisher.interfaces.browser import IBrowserRequest
from plone.dexterity.interfaces import IDexterityContent

try:
    from repoze.zope2.publishtraverse import DefaultPublishTraverse
except ImportError:
    from ZPublisher.BaseRequest import DefaultPublishTraverse


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

    def browserDefault(self, request):
        
        # If this is not a WebDAV request, we don't want to give a 
        # default view. The ZPublisher's WebDAV implementation doesn't
        # deal well with default views.
        
        if (getattr(request, 'maybe_webdav_client', False) and
            request.get('REQUEST_METHOD', 'GET') not in ('GET', 'POST',)
        ):
            return self.context, ()
        
        return super(DexterityPublishTraverse, self).browserDefault(request)
