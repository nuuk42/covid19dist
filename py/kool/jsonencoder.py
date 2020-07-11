""" JSON tools """
import json
import logging
import inspect

log = logging.getLogger(__name__)

class jsonproperty(property):
    """ Marker-Class for properties that are serialized into a JSON document """
    pass

class jsoncollection(property):
    """ Marker-Class for a collection of properties to be serialized into a JSON document """
    pass

class JSONEncoder(json.JSONEncoder):
    """ Override default() function
    
    This JSON Encoder >>works much better :) then the original<< 

    In addition to all classes supported json.JSONEncoder we support
    any class
    * that has one or more "jsonproperty". 
    * that has a "jsoncollection" 

    Example:
    --------
    class A:
        def __init__(self,counter):
            self.counter=counter
        @jsonproperty 
        def name(self):
            return self._name
        @name.setter
        def name(self,value):
            self._name=value

    a=A(42)
    a.name="Kalle"
    jsonify(a)

    This will be encoded to:
    {"name":"Kalle"}

    Example:
    --------
    class B:
        def __init__(self,city):
            self._city=city
            self._json_coll={'name':'Kalle','age':42}
        @jsoncollection
        def props(self):
            return self._json_coll
        @jsonproperty
        def city(self):
            return self._city

    jsonify( B() )

    This will be encoded to:
    {"name":"Kalle", "age":42, city:"Worms"}

    """

    def __init__(self, include_none_values=False,indent=2):
        json.JSONEncoder.__init__(self, indent=indent)
        self._include_none_values = include_none_values

    def _get_property_names(self,o,marker_class):
        """ get the names of all properties of the object "o" """
        log.debug('>')
        property_names = []

        # loop all classes of "o" and receive the property names
        for cls in inspect.getmro(o.__class__):
            log.debug('cls=%s' % cls.__name__)
            # loop everything the class contains
            for cls_key in cls.__dict__.keys():
                # check the class of the object we found. If the
                # class is "jsonproperty" store the name
                if cls.__dict__[cls_key].__class__ == marker_class:
                    log.debug('Found property: %s' % cls_key)
                    # check for duplicated names
                    if not cls_key in property_names:
                        # new one found - store it
                        property_names.append(cls_key)
        log.debug('<')
        return property_names;

    def _get_dynamic_properties(self,o):
        """ get all collections marked with "jsoncollection" """
        log.debug('>')
        # create an empty result
        result = {}

        # first get the names of all collections marked as "jsoncollection"
        # now read each of the found properties. They must contain a "dict"
        for collection_name in self._get_property_names(o,jsoncollection):
            current_dict = o.__getattribute__(collection_name)
            # join the keys into the result
            for key in current_dict.keys():
                # check, if the key exist in the collection
                if key not in result:
                    result[key] = current_dict[key]
        log.debug('<')
        return result
    
    def default(self, o):
        """ Override default from base class 
        
        We return a "dict" filled with the names:value pairs 
        of all properties from "o"
        """
        log.debug('>default')

        # check for properties; start with an empty dict; add dynamic an static @jsonproperty objects to the dict
        property_dict = dict()

        # create a dict from the dynamic properties; check for date+time
        dyn =self._get_dynamic_properties(o)
        for name in dyn.keys():
            value = dyn[name]
            if hasattr(value,'isoformat'):
                property_dict[name] = value.isoformat()
            else:
                property_dict[name] = value

        for property_name in self._get_property_names(o,jsonproperty):
            # get the value of the property; if it's value is None, we do no
            # only include the property, if the flag "include_none" has been
            # set in the constructor of the encode class.
            value = o.__getattribute__(property_name)
            log.debug('getting value for property:%s value=%s' % (property_name,value) )
            if (self._include_none_values == True) or (value != None):
                # date + time objects     
                if hasattr(value, 'isoformat'):
                    property_dict[property_name] = value.isoformat()
                else:    
                    property_dict[property_name] = value

        # now read properties from jsoncollection
        log.debug('< default')
        return property_dict

# ----------------------------------------------------------------------------
def jsonify(source,indent=None):
    """ Create json from given object """
    if source is None:
        return None
    encoder = JSONEncoder(indent=indent)
    return encoder.encode(source)

