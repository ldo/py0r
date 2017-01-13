"""A Python3 wrapper for the Frei0r API for video effects plugins <https://frei0r.dyne.org/>.
"""

import enum
from collections import \
    namedtuple, \
    OrderedDict
import os
import ctypes as ct
import qahirah as qah

class F0R :
    "useful definitions adapted from frei0r.h. You will need to use the constants," \
    " but apart from that, see the more Pythonic wrappers defined outside this" \
    " class in preference to accessing low-level structures directly."

    MAJOR_VERSION = 1
    MINOR_VERSION = 2

    PLUGIN_TYPE_FILTER = 0
    PLUGIN_TYPE_SOURCE = 1
    PLUGIN_TYPE_MIXER2 = 2
    PLUGIN_TYPE_MIXER3 = 3

    COLOR_MODEL_BGRA8888 = 0
    COLOR_MODEL_RGBA8888 = 1
    COLOR_MODEL_PACKED32 = 2
    COLOUR_MODEL_BGRA8888 = 0
    COLOUR_MODEL_RGBA8888 = 1
    COLOUR_MODEL_PACKED32 = 2

    class plugin_info_t(ct.Structure) :
        _fields_ = \
            [
                ("name", ct.c_char_p),
                ("author", ct.c_char_p),
                ("plugin_type", ct.c_int),
                ("color_model", ct.c_int),
                ("frei0r_version", ct.c_int), # version of frie0r that plugin is built for
                ("major_version", ct.c_int),
                ("minor_version", ct.c_int),
                ("num_params", ct.c_int),
                ("explanation", ct.c_char_p), # optional explanation string
            ]
    #end plugin_info_t

    # parameter type codes
    PARAM_BOOL = 0
    PARAM_DOUBLE = 1
    PARAM_COLOR = 2
    PARAM_COLOUR = 2
    PARAM_POSITION = 3
    PARAM_STRING = 4

    # parameter type definitions
    param_bool = ct.c_double # allowed range is [0, 1], 0.5 or greater is True, less is False

    param_double = ct.c_double # allowed range is [0, 1]

    class param_colour_t(ct.Structure) :
        _fields_ = \
            [
                ("r", ct.c_float),
                ("g", ct.c_float),
                ("b", ct.c_float),
            ]
    #end param_colour_t
    param_color_t = param_colour_t

    class param_position_t(ct.Structure) :
        _fields_ = \
            [
                ("x", ct.c_double),
                ("y", ct.c_double),
            ]
    #end param_position_t

    param_string = ct.c_char_p

    class param_info_t(ct.Structure) :
        _fields_ = \
            [
                ("name", ct.c_char_p),
                ("type", ct.c_int),
                ("explanation", ct.c_char_p), # optional explanation string
            ]
    #end param_info_t

    instance_t = ct.c_void_p
    param_t = ct.c_void_p

#end F0R

@enum.unique
class PLUGIN_TYPE(enum.Enum) :
    FILTER = 0
    SOURCE = 1
    MIXER2 = 2
    MIXER3 = 3
#end PLUGIN_TYPE

@enum.unique
class COLOUR_MODEL(enum.Enum) :
    BGRA8888 = 0
    RGBA8888 = 1
    PACKED32 = 2
#end COLOUR_MODEL

@enum.unique
class PARAM(enum.Enum) :
    BOOL = 0
    DOUBLE = 1
    COLOUR = 2
    POSITION = 3
    STRING = 4

    @property
    def f0r_type(self) :
        return \
            type(self)._f0r_type[self]
    #end f0r_type

    def to_f0r(self, val, c_val) :
        type(self)._to_f0r[self](val, c_val)
    #end to_f0r

    def from_f0r(self, c_val) :
        return \
            type(self)._from_f0r[self](c_val)
    #end from_f0r

#end PARAM
PARAM._f0r_type = \
    {
        PARAM.BOOL : F0R.param_bool,
        PARAM.DOUBLE : F0R.param_double,
        PARAM.COLOUR : F0R.param_colour_t,
        PARAM.POSITION : F0R.param_position_t,
        PARAM.STRING : ct.c_char_p,
    }
def to_f0r_bool(b, fb) :
    fb.value = float(b)
#end to_f0r_bool
def to_f0r_float(f, ff) :
    ff.value = f
#end to_f0r_float
def to_f0r_colour(c, fc) :
    fc.r = c.r
    fc.g = c.g
    fc.b = c.b
#end to_f0r_colour
def to_f0r_position(p, fp) :
    fp.x = p.x
    fp.y = p.y
#end to_f0r_position
def to_f0r_string(s, fs) :
    fs.value = s.encode()
#end to_f0r_string
PARAM._to_f0r = \
    {
        PARAM.BOOL : to_f0r_bool,
        PARAM.DOUBLE : to_f0r_float,
        PARAM.COLOUR : to_f0r_colour,
        PARAM.POSITION : to_f0r_position,
        PARAM.STRING : to_f0r_string,
    }
def from_f0r_colour(fc) :
    return \
        qah.Colour(fc.r, fc.g, fc.b, 1)
#end from_f0r_colour
def from_f0r_position(fp) :
    return \
        qah.Vector(fp.x, fp.y)
#end from_f0r_position
PARAM._from_f0r = \
    {
        PARAM.BOOL : lambda f : f.value >= 0.5,
        PARAM.DOUBLE : lambda f : f.value,
        PARAM.COLOUR : from_f0r_colour,
        PARAM.POSITION : from_f0r_position,
        PARAM.STRING : lambda f : f.value.decode(),
    }
del to_f0r_bool, to_f0r_float, to_f0r_colour, to_f0r_position, to_f0r_string
del from_f0r_colour, from_f0r_position

plugin_info = namedtuple("PluginInfo", tuple(f[0] for f in F0R.plugin_info_t._fields_))
param_info = namedtuple("PluginParamInfo", tuple(f[0] for f in F0R.param_info_t._fields_) + ("index",))

def decode_struct(structval, structtype, tupletype, enum_remap) :
    result = []
    for fieldname, fieldtype in structtype._fields_ :
        attr = getattr(structval, fieldname)
        if fieldtype is ct.c_char_p :
            result.append \
              (
                (lambda : None, lambda : attr.decode())[fieldname == "name" or attr != None]()
              )
        else :
            if fieldname in enum_remap :
                attr = enum_remap[fieldname](attr)
            #end if
            result.append(attr)
        #end if
    #end for
    return \
        tupletype(*result)
#end decode_struct

subdir_name = "frei0r-1"
directories = None
  # caller can set to a list of directories to be searched for plugins
  # before invoking get_directories or find_all, to override default
  # search

# TODO: icons

def get_directories(vendor = None) :
    "returns a tuple of directories to be searched in order for plugins. In case" \
    " of a name clash, a plugin from an earlier directory takes precedence over" \
    " one from a later one."
    if directories != None :
        dirpaths = tuple(directories)
    else :
        dirpaths = os.environ.get("FREI0R_PATH")
        if dirpaths != None :
            dirpaths = dirpaths.split(":")
        else :
            dirpaths = \
                (
                    os.path.join(os.environ["HOME"], "." + subdir_name),
                    os.path.join("/usr/local/lib", subdir_name),
                    os.path.join("/usr/lib", subdir_name),
                )
            if vendor != None :
                dirpaths = tuple(os.path.join(d, vendor) for d in dirpaths)
            #end if
        #end if
    #end if
    return \
        dirpaths
#end get_directories

def find_all_in(dirs) :
    "iterates over all plugin instances that can be found in the specified directories."
    seen = set()
    for dir in dirs :
        if os.path.isdir(dir) :
            for item in os.listdir(dir) :
                if item.endswith(".so") :
                    libname = os.path.join(dir, item)
                    if os.path.isfile(libname) :
                        plugin = Plugin(libname)
                        if plugin.info.name not in seen :
                            seen.add(plugin.info.name)
                            yield plugin
                        #end if
                    #end if
                #end if
            #end for
        #end if
    #end for
#end find_all_in

def find_all(vendor = None) :
    "iterates over all plugin instances that can be found in the usual directories."
    return \
        find_all_in(get_directories(vendor))
#end find_all

class Plugin :
    "wrapper class for a Frei0r plugin. Can be instantiated directly from" \
    " the pathname of a .so file; otherwise, use the find_all method."

    __slots__ = ("_lib", "info", "_params", "_params_by_name")

    def __init__(self, libname) :
        self._lib = None # in case of error
        lib = ct.CDLL(libname)
        lib.f0r_init()
        self._lib = lib
        lib.f0r_get_plugin_info.argtypes = (ct.POINTER(F0R.plugin_info_t),)
        lib.f0r_get_param_info.argtypes = (ct.POINTER(F0R.param_info_t), ct.c_int)
        lib.f0r_construct.argtypes = (ct.c_uint, ct.c_uint)
        lib.f0r_construct.restype = F0R.instance_t
        lib.f0r_destruct.argtypes = (F0R.instance_t,)
        lib.f0r_set_param_value.argtypes = (F0R.instance_t, F0R.param_t, ct.c_int)
        lib.f0r_get_param_value.argtypes = (F0R.instance_t, F0R.param_t, ct.c_int)
        c_info = F0R.plugin_info_t()
        lib.f0r_get_plugin_info(ct.byref(c_info))
        self.info = decode_struct(c_info, F0R.plugin_info_t, plugin_info, {"plugin_type" : PLUGIN_TYPE})
        # defer filling in of params info until it’s actually needed
        self._params = None
        self._params_by_name = None
    #end __init__

    def __repr__(self) :
        return \
            "<frei0r_plugin “%s”>" % self.info.name
    #end __repr__

    def __del__(self) :
        if self._lib != None :
            self._lib.f0r_deinit()
            self._lib = None
        #end if
    #end __del__

    @property
    def params(self) :
        if self._params == None :
            params = OrderedDict()
            c_info = F0R.param_info_t()
            for i in range(self.info.num_params) :
                self._lib.f0r_get_param_info(ct.byref(c_info), i)
                param = decode_struct(c_info, F0R.param_info_t, param_info, {"type" : PARAM})
                param.index = i
                params[param.name] = param
            #end for
            self._params = tuple(params.values())
            self._params_by_name = params
        #end if
        return \
            self._params
    #end params

    class Instance :
        "wrapper class for a Frei0r plugin instance. Do not instantiate directly; get" \
        " from a call to Plugin.construct()."

        __slots__ = ("_instance", "_parent", "_lib")

        def __init__(self, instance, parent) :
            self._instance = instance
            self._parent = parent
            self._lib = parent._lib
        #end __init__

        def __repr__(self) :
            return \
                "<frei0r_plugin_instance “%s”>" % self._parent.info.name
        #end __repr__

        def __del__(self) :
            if self._parent != None and self._parent._lib != None and self._instance != None :
                self._parent._lib.f0r_destruct(self._instance)
                self._instance = None
            #end if
        #end __del__

        def __len__(self) :
            "the number of parameters."
            return \
                len(self._parent._params)
        #end __len__

        def __getitem__(self, paramid) :
            "retrieves parameter value; paramid can be integer index or string name."
            if isinstance(paramid, int) :
                param = self._parent._params[paramid]
            elif isinstance(paramid, str) :
                param = self._parent._params_by_name[paramid]
            else :
                raise TypeError("param must be identified by index or name")
            #end if
            c_result = param.type.f0r_type()
            self._lib.f0r_get_param_value.argtypes(self._instance, ct.byref(c_result), param.index)
            return \
                param.type.from_f0r(c_result)
        #end __getitem__

        def __setitem__(self, paramid, newvalue) :
            "sets new parameter value; paramid can be integer index or string name."
            if isinstance(paramid, int) :
                param = self._parent._params[paramid]
            elif isinstance(paramid, str) :
                param = self._parent._params_by_name[paramid]
            else :
                raise TypeError("param must be identified by index or name")
            #end if
            c_value = param.type.f0r_type()
            param.type.to_f0r(newvalue, c_value)
            self._lib.f0r_set_param_value(self._instance, ct.byref(c_value), param.index)
        #end __setitem__

        # TBD update, update2

    #end Instance

    def construct(self, width, height) :
        "constructs a new instance of this Plugin."
        return \
            type(self).Instance(self._lib.f0r_construct(width, height), self)
    #end construct

#end Plugin
