# -*- coding: utf-8 -*-
import zope.deferredimport


zope.deferredimport.initialize()


HAS_WEBDAV = True
try:
    import webdav as _  # noqa: F401
except ImportError:
    HAS_WEBDAV = False


zope.deferredimport.deprecated(
    "Import HAS_WEBDAV instead.", HAS_ZSERVER="plone.dexterity:bbb.HAS_WEBDAV"
)


NullResource = None


class Resource(object):
    def dav__init(self, request, response):
        pass

    def dav__validate(self, object, methodname, REQUEST):
        pass

    def dav__simpleifhandler(
        self, request, response, method="PUT", col=0, url=None, refresh=0
    ):
        pass
