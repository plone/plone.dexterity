# -*- coding: utf-8 -*-
import pkg_resources

HAS_ZSERVER = True
try:
    dist = pkg_resources.get_distribution('ZServer')
except pkg_resources.DistributionNotFound:
    HAS_ZSERVER = False

NullResource = None


class Resource(object):
    def dav__init(self, request, response):
        pass

    def dav__validate(self, object, methodname, REQUEST):
        pass

    def dav__simpleifhandler(self, request, response, method='PUT',
                             col=0, url=None, refresh=0):
        pass
