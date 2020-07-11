""" JSON HAL Document """

import logging
from kool.jsonencoder import jsonproperty, jsoncollection, jsonify
from kool import JSONLink


log = logging.getLogger(__name__)

class JSONHalDocument(object):
    """ JSON Hypertext Application Language document
    
    HAL Document with support for JSON encoding - see: 
      ttps://tools.ietf.org/html/draft-kelly-json-hal-08
    
    The class contains the JSON properties:
        * _links - contains links to methods of this resource
               Remark: _links should at least contain a "_self" link
        * _embedded - contains other documents embedded in this resource
        * _properties - a collection of other properties

    Example for "_link": 
        "next" - get the next junk from a paged resource
        "prev" - get the previous junk from a paged resource
        "last" - get the last junk from a paged resource
        "cancel" - cancel a peding order

        The "_link" elements are like the "methods" of an object

    """

    def __init__(self,link_self,**named_args):
        """ create new empty document 
	
        Parameters:
            * link_self: URL of the embedded "_self" link 
	    * embeddedDocs as positional arguments
	    * properties as named arguments
	
	"""
        log.debug('>')
        self._hal_links = {}
        self._hal_embedded = {}
        self._hal_properties = {}

        # check if we shall add a "_self" link. 
        if link_self is not None:
            # the "link_self" may contain a string (url?) or an object of type JSONLink
            if type(link_self) == JSONLink:
                self._hal_links['self']=link_self
            else:
                self._hal_links['self']=JSONLink(href=link_self)

        # check the named arguments for:
        # * JSONHalDocument --> _hal_embedded
        # * JSONLink --> _hal_links
        # others --> _hal_properties
        for object_name in named_args.keys():
            # get the object
            obj = named_args[object_name]
            # check if this is an JSONHalDocument
            if isinstance(obj, JSONHalDocument):
                # found an embedded document
                self._hal_embedded[object_name] = obj;
            else:    
                # check if this is a Link
                if isinstance(obj, JSONLink):
                    self._hal_links[object_name] = obj
                else:
                    # add a property
                    self._hal_properties[object_name] = obj

        # create properties from named arguments

        log.debug('<')

    @property
    def link_self(self):
        """ The links with the "self" """
        if '_self' in self._hal_links:
            return self._hal_links['self']
        return None
    @link_self.setter
    def link_self(self,value):
        """ Define the URL (link) that points to this document """
        # check type
        if type(value)==JSONLink:
            self._hal_links['self']=value
        else:
            # assume a string
            self._hal_links['self']=JSONLink(href=value)

    @jsonproperty
    def _links(self):
        """ Return _links to methods of the object """
        return self._hal_links

    @jsonproperty
    def _embedded(self):
        """ Return _embedded HAL documents """
        if len(self._hal_embedded)==0:
            return None
        return self._hal_embedded

    @jsoncollection
    def _prop(self):
        return self._hal_properties

    def add_link(self,name,link):
        """ add a new (link) method to this document """
        # check type
        if type(link)==JSONLink:
            self._hal_links[name]=link
        else:
            # assume a string
            self._hal_links[name]=JSONLink(href=link)

    def add_embedded(self,name,hal_document):
        """ add a new embedded document """
        self._hal_embedded[name]=hal_document

    def add_property(self,name,value):
        self._hal_properties[name]=value

# -------------------------------------------------------------------------
def jsonify_as_hal(link_self,indent=2, **named_args):
    """ Create a JSONHalDocument and serialize it to JSON """
    # add the links_self argument
    doc = JSONHalDocument(link_self, **named_args)
    return jsonify(doc,indent)
