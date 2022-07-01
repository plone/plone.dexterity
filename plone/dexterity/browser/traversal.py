from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition.interfaces import IAcquirer
from plone.dexterity.filerepresentation import FolderDataResource
from plone.dexterity.interfaces import DAV_FOLDER_DATA_ID
from plone.dexterity.interfaces import IDexterityContent
from webdav.NullResource import NullResource
from zope.component import adapter
from zope.publisher.interfaces.browser import IBrowserRequest


try:
    from repoze.zope2.publishtraverse import DefaultPublishTraverse
except ImportError:
    from ZPublisher.BaseRequest import DefaultPublishTraverse


@adapter(IDexterityContent, IBrowserRequest)
class DexterityPublishTraverse(DefaultPublishTraverse):
    """Override the default browser publisher to make WebDAV work for
    Dexterity objects.

    In part, this works around certain problems with the ZPublisher that make
    DAV requests difficult, and in part it adds support for the '_data'
    pseudo-resource that is shown for folderish content items.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def publishTraverse(self, request, name):

        context = aq_inner(self.context)

        # If we are trying to traverse to the folder "body" pseudo-object
        # returned by listDAVObjects(), return that immediately

        if (
            getattr(request, "maybe_webdav_client", False)
            and name == DAV_FOLDER_DATA_ID
        ):
            return FolderDataResource(DAV_FOLDER_DATA_ID, context).__of__(context)

        defaultTraversal = super().publishTraverse(request, name)

        # If this is a WebDAV PUT/PROPFIND/PROPPATCH request, don't acquire
        # things. If we did, we couldn't create a new object with PUT, for
        # example, because the acquired object would shadow the NullResource

        if (
            getattr(request, "maybe_webdav_client", False)
            and request.get("REQUEST_METHOD", "GET")
            not in (
                "GET",
                "POST",
            )
            and IAcquirer.providedBy(defaultTraversal)
        ):
            parent = aq_parent(aq_inner(defaultTraversal))
            if parent is not None and parent is not context:
                return NullResource(self.context, name, request).__of__(self.context)

        return defaultTraversal

    def browserDefault(self, request):

        # If this is not a WebDAV request, we don't want to give a
        # default view. The ZPublisher's WebDAV implementation doesn't
        # deal well with default views.

        if getattr(request, "maybe_webdav_client", False) and request.get(
            "REQUEST_METHOD", "GET"
        ) not in (
            "GET",
            "POST",
        ):
            return self.context, ()

        return super().browserDefault(request)
