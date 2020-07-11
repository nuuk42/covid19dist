# service utilities
import os
import logging
import json
import re
from collections import namedtuple

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
def _collection_to_object(item):
    """
    Convert a dictionary or a list into an object (recursive).
    """
    def convert(item): 
        if isinstance(item, dict):
            # try to create a new namedtuple class. It will fail, if the dict contains names like "a.b" or "__name"
            try:
                TupleClass = namedtuple('config', [k for k in item])
                return TupleClass( *[convert(v) for v in item.values()] )
            except ValueError:
                # we cant create a named tuple - so: return a dict but convert all contains elements
                log.info('Cant create TupleClass - using dict')
                return {k:convert(v) for k,v in item.items()} 

        if isinstance(item, list):
            # list: return a list; convert all elements in the list
            def yield_convert(item):
                for index, value in enumerate(item):
                    yield convert(value)
            return list(yield_convert(item))
        return item

    return convert(item)

# ---------------------------------------------------------------------------
def _split_json_path(json_path):
    """ Split a string into tokens that we can use to read as properties """
    return list(filter(lambda tok: len(tok)>0,re.split('\.|\]|\[',json_path)))
# ---------------------------------------------------------------------------
def _get_expression(index_str):
    c = re.compile('@([^=]+)\W*={0,1}\W*([^""]+){0,1}\W*')
    x = c.match(index_str)
    # check. We must have one or two matches...
    if x is None:
        raise IndexError('Invalid expression in array index:%s' % index_str)
    return (x.groups()[0],x.groups()[1])

# ---------------------------------------------------------------------------
def _get_json_attribute_from_object(o,json_path):
    """ Read a value from a JSON string or a JSON object.

    The function support an XPath-like access to a JSON object.
    Example:

    _get_json_attribute('{"name":"Kalle","adr":{"city":"Worms","street":"Main"}}, "adr.street")
    ...will return "Main"
    """
    # split the json_path
    tokens = _split_json_path(json_path)
    # setup the "current" element we are checking against
    current = o
    # loop all tokens
    for tok in tokens:
        # case 1: the current element is a list: check index
        if isinstance(current,list):
            # check index agains current token. Must be 
            # - a number
            # - an expression to access a attribute value. Example: @name="Kalle"
            # - an expression to check if an attribute exits. Example: @name.firstname
            if tok.isdigit()==False:
                # get the expression: attrname,attrvalue
                attrname,attrvalue = _get_expression(tok)
                # loop the list to find the first matching element
                current = _filter_key_value(current, attrname, attrvalue)
                if current is None:
                    # no element with given index expression in list
                    raise IndexError('No matching element for expression:%s' % tok)
            else:
                list_index = int(tok)
                # check position
                if (list_index<0) or (list_index>len(current)):
                    raise IndexError('Invalid index:%s' % tok)
                # the element at the given index becomes the next "current"
                current=current[list_index]
        elif isinstance(current,dict):
            # the JSON did contain elements (like "my-age":42) that can not be converted into attributes of a named-tuple.
            # so, we had to use a dict here...
            current = current.get(tok)
            if current is None:
                raise KeyError('Invalid key for dict:%s' % tok)
        else:
            # case 2: the current element is a dict: check element name
            # check if the dict contains the element with the name "tok"
            if hasattr(current,tok)==False:
                raise KeyError('Invalid key:%s' % tok)
            # get the value at the given key - it becomes the next "current"
            current = getattr(current,tok)
    return current
# ---------------------------------------------------------------------------
def _filter_key_value(json_object_list,key,value=None):
    """ Find an element with a matching attribute within a collection 
    """
    for json_object in json_object_list:
        # if the "key" does not exist in the current "json_object", the function _get_json_attribute_from_object will
        # throw an exception. 
        try:
            json_attr = _get_json_attribute_from_object(json_object,key)
            # if a value has been specified, we need to check it. Otherwise we are done
            if value is not None:
                if json_attr == value:
                    # found
                    return json_object
            else:
                # accepted without value check
                return json_object
        except IndexError as ixErr:
            pass
        except KeyError as kErr:
            pass
    return None
# ---------------------------------------------------------------------------
def get_json_attribute(obj_or_string, json_path=None):
    """ Get one element from a JSON document
    
    Access elements within a JSON document using "dotted" syntax.
    
    Example:
    
    get_json_attribute({"adr":{"city":"Worms", "street":"Bondstreet","number":42}}, 
                       'adr.street')

    ...will return "42"

    More examples for "json_path":

    person.name[1] -->    access a JSON array; index starts at 0
    person.name[0].firstname --> access an object inside an array
    person.name[@firstname] --> access an object inside an array which has a attribute "firstname"
    person.name[@firstname="Kalle"] --> access an object inside an array by property value

    """
    # check type
    if isinstance(obj_or_string,str):
        json_as_object = json_to_object(obj_or_string)
        # check for an access path; if no path is given, return the entier object
        if json_path is None:
            return json_as_object
        return _get_json_attribute_from_object(json_as_object,json_path)
    else:
        return _get_json_attribute_from_object(obj_or_string, json_path)

# ---------------------------------------------------------------------------
def json_to_object(json_string):
    """ Convert a JSON string to an object
    """
    return _collection_to_object(json.loads(json_string))

