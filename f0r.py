"""A Python3 wrapper for the Frei0r API for video effects plugins <https://frei0r.dyne.org/>.
"""
#+
# Copyright 2017 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#-

import enum
from collections import \
    namedtuple
import os
import array
import ctypes as ct
import qahirah as qah
from qahirah import \
    Colour, \
    Vector
import pixman
from pixman import \
    PIXMAN

class F0R :
    "useful definitions adapted from frei0r.h. See the more Pythonic wrappers" \
    " defined outside this class in preference to accessing low-level structures" \
    " directly."

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
                ("colour_model", ct.c_int),
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
    "the types of Frei0r plugins."
    FILTER = 0
    SOURCE = 1
    MIXER2 = 2
    MIXER3 = 3

    @property
    def nr_inputs(self) :
        "how many inputs does the plugin take."
        return \
            self._nr_inputs[self]
    #end nr_inputs

    @property
    def has_update(self) :
        "does this plugin have the update method (single input frame buffer)."
        return \
            self._has_update_methods[self][0]
    #end has_update

    @property
    def has_update2(self) :
        "does this plugin have the update2 method (up to three input frame buffers)."
        return \
            self._has_update_methods[self][1]
    #end has_update2

#end PLUGIN_TYPE
PLUGIN_TYPE._nr_inputs = \
    {
        PLUGIN_TYPE.FILTER : 1,
        PLUGIN_TYPE.SOURCE : 0,
        PLUGIN_TYPE.MIXER2 : 2,
        PLUGIN_TYPE.MIXER3 : 3,
    }
PLUGIN_TYPE._has_update_methods = \
    {
        PLUGIN_TYPE.FILTER : (True, False),
        PLUGIN_TYPE.SOURCE : (True, False),
        PLUGIN_TYPE.MIXER2 : (False, True),
        PLUGIN_TYPE.MIXER3 : (False, True),
    }

@enum.unique
class COLOUR_MODEL(enum.Enum) :
    "the various colour models that Frei0r plugins may use."
    BGRA8888 = 0
    RGBA8888 = 1
    PACKED32 = 2

    @property
    def rearrange(self) :
        "do the colour components need rearranging to agree with Cairo’s FORMAT_ARGB32."
        return \
            self == COLOUR_MODEL.RGBA8888
    #end rearrange

#end COLOUR_MODEL

@enum.unique
class PARAM(enum.Enum) :
    "the types of parameters that Frei0r plugins may accept."
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
        Colour(fc.r, fc.g, fc.b, 1)
#end from_f0r_colour
def from_f0r_position(fp) :
    return \
        Vector(fp.x, fp.y)
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
plugin_info.__doc__ = "information about a Frei0r plugin"
param_info = namedtuple("PluginParamInfo", tuple(f[0] for f in F0R.param_info_t._fields_) + ("index",))
param_info.__doc__ = "information about a parameter of a Frei0r plugin"

def decode_struct(structval, structtype, tupletype, enum_remap, extra) :
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
        tupletype(*(tuple(result) + extra))
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

def get_all(vendor = None) :
    "returns a dict of all plugin instances that can be found in the usual directories."
    return \
        dict((plugin.info.name, plugin) for plugin in find_all(vendor))
#end get_all

max_image_dimension = 2048 # width and height cannot exceed this
image_dimension_modulo = 8 # width and height must be exact multiples of this

def check_dimensions_ok(dimensions, where = None) :
    "checks that the Vector dimensions is suitable as the dimensions of an image" \
    " for Frei0r to operate on."
    width, height = Vector.from_tuple(dimensions).assert_isint()
    assert max_image_dimension >= width > 0 and max_image_dimension >= height > 0 and width % image_dimension_modulo == 0 and height % image_dimension_modulo == 0, \
        "invalid image dimensions%s" % (lambda : "", lambda : " %s" % where)[where != None]()
    return \
        Vector(width, height)
#end check_dimensions_ok

def get_frame_arg(frame) :
    "returns the integer base address of a frame buffer."
    # Not bothering to check alignment requirements!
    if isinstance(frame, ct.c_void_p) :
        baseaddr = frame.value
    elif isinstance(frame, array.array) :
        baseaddr = frame.buffer_info()[0]
    elif isinstance(frame, bytearray) :
        baseaddr = ct.addressof((ct.c_char * len(frame)).from_buffer(frame))
    elif isinstance(frame, qah.ImageSurface) :
        # Not bothering to check pixel/dimensions compatibility!
        baseaddr = frame.data
    elif frame == None :
        baseaddr = None
    else :
        raise TypeError("wrong type for frame arg")
    #end if
    return \
        baseaddr
#end get_frame_arg

class Plugin :
    "wrapper class for a Frei0r plugin. Can be instantiated directly from" \
    " the pathname of a .so file; otherwise, use find_all or get_all to get these."

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
        if hasattr(lib, "f0r_update") :
            lib.f0r_update.argtypes = (F0R.instance_t, ct.c_double, ct.c_void_p, ct.c_void_p)
        #end if
        if hasattr(lib, "f0r_update2") :
            lib.f0r_update2.argtypes = (F0R.instance_t, ct.c_double, ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
        #end if
        c_info = F0R.plugin_info_t()
        lib.f0r_get_plugin_info(ct.byref(c_info))
        self.info = decode_struct(c_info, F0R.plugin_info_t, plugin_info, {"plugin_type" : PLUGIN_TYPE, "colour_model" : COLOUR_MODEL}, ())
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

    def _get_params(self) :
        if self._params == None :
            self._params = []
            self._params_by_name = {}
            c_info = F0R.param_info_t()
            for i in range(self.info.num_params) :
                self._lib.f0r_get_param_info(ct.byref(c_info), i)
                param = decode_struct(c_info, F0R.param_info_t, param_info, {"type" : PARAM}, (i,))
                self._params.append(param)
                self._params_by_name[param.name] = param
            #end for
        #end if
    #end _get_params

    @property
    def params(self) :
        "information about the parameters to this Plugin."
        self._get_params()
        return \
            self._params_by_name
    #end params

    class Instance :
        "wrapper class for a Frei0r plugin instance. Do not instantiate directly; get" \
        " from a call to Plugin.construct()."

        __slots__ = ("_instance", "_parent", "_lib", "dimensions", "rearrange")

        def __init__(self, instance, parent, dimensions, rearrange) :
            self._instance = instance
            self._parent = parent
            self._lib = parent._lib
            self.dimensions = dimensions
            self.rearrange = rearrange
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
            self._parent._get_params()
            return \
                len(self._parent._params)
        #end __len__

        def __getitem__(self, paramid) :
            "retrieves parameter value; paramid can be integer index or string name."
            self._parent._get_params()
            if isinstance(paramid, int) :
                param = self._parent._params[paramid]
            elif isinstance(paramid, str) :
                param = self._parent._params_by_name[paramid]
            else :
                raise TypeError("param must be identified by index or name")
            #end if
            c_result = param.type.f0r_type()
            self._lib.f0r_get_param_value(self._instance, ct.byref(c_result), param.index)
            return \
                param.type.from_f0r(c_result)
        #end __getitem__

        def __setitem__(self, paramid, newvalue) :
            "sets new parameter value; paramid can be integer index or string name."
            self._parent._get_params()
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

        def __iter__(self) :
            "iterating over parameter names."
            self._parent._get_params()
            for param in self._parent._params :
                yield param.name
            #end for
        #end __iter__

        @property
        def params(self) :
            "parameter settings as an updateable dict."
            result = {}
            for paramname in self :
                result[paramname] = self[paramname]
            #end for
            return \
                result
        #end params

        @params.setter
        def params(self, newparams) :
            for paramname, paramvalue in newparams.items() :
                self[paramname] = paramvalue
            #end for
        #end params

        class ChannelRearranger :
            "rearranges R and B channels as necessary to convert between RGBA8888 colour" \
            " model and Cairo’s channel ordering, which corresponds to BGRA8888."

            __slots__ = ("_parentobj", "rearrange", "src", "dst")

            def __init__(self, baseaddr, dimensions, parentobj, out, rearrange) :
                baseaddr = get_frame_arg(baseaddr)
                if baseaddr == None :
                    rearrange = False # no pixels to rearrange
                #end if
                self.rearrange = rearrange
                if rearrange :
                    orig = pixman.Image.create_bits \
                      (
                        format = PIXMAN.a8r8g8b8,
                        dimensions = dimensions,
                        bits = baseaddr,
                        stride = dimensions.x * 4 # should be correct, given constraints on dimensions
                      )
                    copy = pixman.Image.create_bits \
                      (
                        format = PIXMAN.a8b8g8r8,
                          # doesn’t really matter which of orig/copy is which format,
                          # just so long as they’re different
                        dimensions = dimensions
                      )
                    if out :
                        self.src = copy # plugin writes to copy
                        self.dst = orig
                    else :
                        self.src = orig
                        self.dst = copy # plugin reads from copy
                    #end if
                else :
                    self.src = baseaddr
                    self.dst = baseaddr
                #end if
                self._parentobj = parentobj # just to ensure it doesn’t go away prematurely
            #end __init__

            def convert(self) :
                "actually implements the channel rearrangement. Returns the output" \
                " buffer, which is handy for input conversions."
                if self.rearrange :
                    pixman.image_composite \
                      (
                        op = PIXMAN.OP_SRC,
                        src = self.src,
                        mask = None,
                        dest = self.dst,
                        src_pos = (0, 0),
                        mask_pos = None,
                        dest_pos = (0, 0),
                        dimensions = self.src.dimensions
                      )
                #end if
                return \
                    (lambda : None, lambda : (lambda : self.dst, lambda : self.dst.data)[hasattr(self.dst, "data")]())[self.dst != None]()
            #end convert

            @property
            def buf(self) :
                "returns the input buffer. Handy for output conversions."
                return \
                    (lambda : None, lambda : (lambda : self.src, lambda : self.src.data)[hasattr(self.src, "data")]())[self.src != None]()
            #end buf

        #end ChannelRearranger

        def update(self, time, inframe, outframe) :
            "invokes the plugin on the single input inframe, to produce its output in outframe." \
            " inframe and outframe can be qahirah.ImageSurface objects, pixman.Image objects," \
            " bytearray or array.array objects, or even just raw pointer addresses."
            if not hasattr(self._parent._lib, "f0r_update") :
                raise NotImplementedError("plugin has no update method")
            #end if
            inframe_r = self.ChannelRearranger \
              (
                baseaddr = inframe,
                dimensions = self.dimensions,
                parentobj = inframe,
                out = False,
                rearrange = self.rearrange
              )
            outframe_r = self.ChannelRearranger \
              (
                baseaddr = outframe,
                dimensions = self.dimensions,
                parentobj = outframe,
                out = True,
                rearrange = self.rearrange
              )
            self._parent._lib.f0r_update \
              (
                self._instance,
                time,
                inframe_r.convert(),
                outframe_r.buf
              )
            outframe_r.convert()
            if isinstance(outframe, qah.ImageSurface) :
                outframe.mark_dirty()
            #end if
        #end update

        def update2(self, time, inframe1, inframe2, inframe3, outframe) :
            "invokes the plugin on up to 3 input inframes, to produce its output in outframe." \
            " The inframes and outframe can be qahirah.ImageSurface objects, pixman.Image" \
            " objects, bytearray or array.array objects, or even just raw pointer addresses."
            if hasattr(self._parent._lib, "f0r_update2") :
                inframe1_r = self.ChannelRearranger \
                  (
                    baseaddr = inframe1,
                    dimensions = self.dimensions,
                    parentobj = inframe1,
                    out = False,
                    rearrange = self.rearrange
                  )
                inframe2_r = self.ChannelRearranger \
                  (
                    baseaddr = inframe2,
                    dimensions = self.dimensions,
                    parentobj = inframe2,
                    out = False,
                    rearrange = self.rearrange
                  )
                inframe3_r = self.ChannelRearranger \
                  (
                    baseaddr = inframe3,
                    dimensions = self.dimensions,
                    parentobj = inframe3,
                    out = False,
                    rearrange = self.rearrange
                  )
                outframe_r = self.ChannelRearranger \
                  (
                    baseaddr = outframe,
                    dimensions = self.dimensions,
                    parentobj = outframe,
                    out = True,
                    rearrange = self.rearrange
                  )
                self._parent._lib.f0r_update2 \
                  (
                    self._instance,
                    time,
                    inframe1_r.convert(),
                    inframe2_r.convert(),
                    inframe3_r.convert(),
                    outframe_r.buf
                  )
                outframe_r.convert()
            else :
                if inframe2 != None or inframe3 != None :
                    raise NotImplementedError("plugin has no update2 method")
                #end if
                if not hasattr(self._parent._lib, "f0r_update") :
                    raise NotImplementedError("plugin has no update method")
                #end if
                inframe1_r = self.ChannelRearranger \
                  (
                    baseaddr = inframe1,
                    dimensions = self.dimensions,
                    parentobj = inframe1,
                    out = False,
                    rearrange = self.rearrange
                  )
                outframe_r = self.ChannelRearranger \
                  (
                    baseaddr = outframe,
                    dimensions = self.dimensions,
                    parentobj = outframe,
                    out = True,
                    rearrange = self.rearrange
                  )
                self._parent._lib.f0r_update \
                  (
                    self._instance,
                    time,
                    inframe1_r.convert(),
                    outframe_r.buf
                  )
                outframe_r.convert()
            #end if
            if isinstance(outframe, qah.ImageSurface) :
                outframe.mark_dirty()
            #end if
        #end update2

    #end Instance

    def construct(self, dimensions, rearrange = True) :
        "constructs a new instance of this Plugin, from the given (qahirah.Vector-compatible)" \
        " dimensions. rearrange indicates whether to rearrange R and B channels as" \
        " necessary to agree with Cairo’s FORMAT_ARGB32 channel ordering."
        width, height = check_dimensions_ok(dimensions)
        instance = self._lib.f0r_construct(width, height)
        if instance == None :
            raise RuntimeError \
              (
                "failure constructing plugin instance for “%s”" % self._parent.info.name
              )
        #end if
        return \
            type(self).Instance \
              (
                instance = instance,
                parent = self,
                dimensions = Vector(width, height),
                rearrange = rearrange and self.info.colour_model.rearrange
              )
    #end construct

#end Plugin
