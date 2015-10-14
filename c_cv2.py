# file  : c_cv2_keypoint.py
# author: Matthew Triche
# brief : Implements OpenCV structures using ctypes. 

# -----------------------------------------------------------------------------
# Import Modules

from ctypes import *

# -----------------------------------------------------------------------------
# define c_Point2f structure

class c_Point2f(Structure):
	_fields_ = [ ("x", c_float), ("y", c_float) ]
	
# -----------------------------------------------------------------------------
# define c_KeyPoint structure

class c_KeyPoint(Structure):
	_fields_ = [ ("_pt",       c_Point2f), 
	             ("_size",     c_float),
	             ("_angle",    c_float),
	             ("_response", c_float),
	             ("_octave",   c_int),
	             ("_class_id", c_int) ]

