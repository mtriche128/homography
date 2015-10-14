
from ctypes import *
from c_cv2 import *

class c_Results(Structure):
	_fields_ = [("vert",  c_Point2f*4),
	            ("ftime", c_double),
	            ("mtime", c_double),
	            ("htime", c_double)]

class LibHG():
	def __init__(self):
		self.lib = cdll.LoadLibrary("/home/matt/school/ind_study/code/homography/libhg.so")
		
		self.lib.ConfigureSURF.argtypes = [c_int]
		self.lib.LoadSceneKeypoints.argtypes = [POINTER(c_KeyPoint),c_int]
		self.lib.LoadSceneDescriptors.argtypes = [POINTER(c_float),c_int,c_int]
		self.lib.LoadObjectImage.argtypes = [c_char_p]
		self.lib.LoadSceneImage.argtypes = [c_char_p]
		self.lib.StoreOutputImage.argtypes = [c_char_p]
		self.lib.Process.argtypes = [POINTER(c_Results), c_double]
		
		self.lib.LoadObjectImage.restype = c_bool
		self.lib.LoadSceneImage.restype = c_bool
		
	def __del__(self):
		self.lib.Release() # ensure all memory allocated within the library is freed.
		
	def ConfigureSURF(self, minHess):
		self.lib.ConfigureSURF(minHess)
		
	def LoadObjectImage(self, filename):
		return self.lib.LoadObjectImage(filename)
	
	def LoadSceneImage(self, filename):
		return self.lib.LoadSceneImage(filename)
		
	def LoadSceneKeypoints(self, c_kp):
		ptr = cast(pointer(c_kp),POINTER(c_KeyPoint))
		return self.lib.LoadSceneKeypoints(ptr, len(c_kp))
	
	def LoadSceneDescriptors(self, c_desc,dim):
		ptr = cast(pointer(c_desc),POINTER(c_float))
		return self.lib.LoadSceneDescriptors(ptr, dim, len(c_desc) / dim)

	def StoreOutputImage(self, filename):
		self.lib.StoreOutputImage(filename)
	
	def Process(self, c_results, ratio):
		ptr = cast(pointer(c_results), POINTER(c_Results))
		self.lib.Process(ptr, ratio)
