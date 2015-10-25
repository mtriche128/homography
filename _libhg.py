# file  : _libhg.py
# brief : This module contains a class used to use and manage libhg.so
# author: Matthew Triche

from ctypes import *
from c_cv2 import *
import os

# -----------------------------------------------------------------------------
# class c_Results
# 
# This class serves a structure used to obtain results from libhg.so

class c_Results(Structure):
	_fields_ = [("vert",  c_Point2f*4),
	            ("ftime", c_double),
	            ("mtime", c_double),
	            ("htime", c_double),
	            ("m_num", c_int),
	            ("f_num", c_int)]

# -----------------------------------------------------------------------------
# class LibHG
# 
# This class is used to interface with and manage libhg.so

class LibHG():
  
	# ---------------------------------------------------------------------
	# __init__
	#
	# This is the class constructor. When an instance is created, a handle 
	# to libhg.so will be generated using the ctypes module. 
	
	def __init__(self):
		lib_filename = os.getcwd() + "/libhg.so"
		self.lib = cdll.LoadLibrary(lib_filename) # create handle to libhg.so
		
		# define how arguments are passed to external functions within libhg.so
		self.lib.ConfigureSURF.argtypes = [c_int]
		self.lib.LoadSceneKeypoints.argtypes = [POINTER(c_KeyPoint),c_int]
		self.lib.LoadSceneDescriptors.argtypes = [POINTER(c_float),c_int,c_int]
		self.lib.LoadObjectImage.argtypes = [c_char_p]
		self.lib.LoadSceneImage.argtypes = [c_char_p]
		self.lib.StoreOutputImage.argtypes = [c_char_p]
		self.lib.Process.argtypes = [POINTER(c_Results), c_double]
		
		# define how return values are handled when external functions within libhg.so are called
		self.lib.LoadObjectImage.restype = c_bool
		self.lib.LoadSceneImage.restype = c_bool
	
	# ---------------------------------------------------------------------
	# __del__
	#
	# This is the class destructor. It's called when an instance is garbage
	# collected by python. Before this instance is destroyed, all memory 
	# allocated within libhg.so must be freed.
	# 
	# NOTE: This is part of managing the life-cycle of shared objects.
	
	def __del__(self):
		self.lib.Release() # ensure all memory allocated within the library is freed.
	
	# ---------------------------------------------------------------------
	# define calls to each external function within libhg.so
	
	def ConfigureSURF(self, minHess):
		self.lib.ConfigureSURF(minHess)
		
	def LoadObjectImage(self, filename):
		return self.lib.LoadObjectImage(filename)
	
	def LoadSceneImage(self, filename):
		return self.lib.LoadSceneImage(filename)
		
	def LoadSceneKeypoints(self, c_kp):
		ptr = cast(pointer(c_kp),POINTER(c_KeyPoint)) # aquire a pointer to the array of keypoints
		return self.lib.LoadSceneKeypoints(ptr, len(c_kp))
	
	def LoadSceneDescriptors(self, c_desc,dim):
		ptr = cast(pointer(c_desc),POINTER(c_float)) # aquire a pointer to the array of descriptors
		return self.lib.LoadSceneDescriptors(ptr, dim, len(c_desc) / dim)

	def StoreOutputImage(self, filename):
		self.lib.StoreOutputImage(filename)
	
	def SceneSURF(self):
		self.lib.SceneSURF()
		
	def Process(self, c_results, ratio):
		ptr = cast(pointer(c_results), POINTER(c_Results)) # aquire a pointer to the structure where results will be stored
		self.lib.Process(ptr, ratio)
