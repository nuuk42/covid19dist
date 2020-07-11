""" JSON Links """

import logging
from kool.jsonencoder import jsonproperty

log = logging.getLogger(__name__)


class JSONLink(object):
    """ JSON Links 
    
    Objects of this class are JSON Links according to
    the document "https://tools.ietf.org/html/draft-kelly-json-hal-08"

    Properties are:

    href (required)
    templated (optional)
    type (optional)
    deprecation (optional)
    name (optional)
    profile (optional)
    title (optional)
    hreflang (optional)
    
    """

    def __init__(self, href, templated=None, type=None, deprecation=None, name=None, profile=None, title=None, hreflang=None):
        """ Create new JSON Link object """
        log.debug('> href=%s' % href)

        self._href,self._templated,self._type,self._deprecation, self._name, self._profile, self._title, self._hreflang = (href,templated,type,deprecation,name,profile,title,hreflang)
        log.debug('<')

    @jsonproperty
    def href(self):
        return self._href
    
    @jsonproperty
    def templated(self):
        return self._templated

    @jsonproperty
    def type(self):
        return self._type

    @jsonproperty
    def title(self):
        return self._title    



