# file  : homography.py
# author: Matthew Triche
# brief : homography test script

# -----------------------------------------------------------------------------
# import modules

import cv2
import keypoints
import os
import json
from ctypes import *
from c_cv2 import c_KeyPoint
from _libhg import *
import argparse


# -----------------------------------------------------------------------------
# define run parameters

DESC_DIM = 64

# -----------------------------------------------------------------------------
# define utility functions

def create_c_keypoints(kpoints):
	c_kpoints = (c_KeyPoint*len(kpoints))()
	for i in range(len(kpoints)):
		c_kpoints[i]._pt.x     = kpoints[i].pt[0]
		c_kpoints[i]._pt.y     = kpoints[i].pt[1]
		c_kpoints[i]._size     = kpoints[i].size
		c_kpoints[i]._angle    = kpoints[i].angle
		c_kpoints[i]._response = kpoints[i].response
		c_kpoints[i]._octave   = kpoints[i].octave
		c_kpoints[i]._class_id = kpoints[i].class_id
	return c_kpoints

def create_c_desc(kpoints):
	total_size = DESC_DIM*len(kpoints)
	c_desc = (c_float*total_size)()
	for x in range(len(kpoints)):
		for y in range(DESC_DIM): 
			c_desc[DESC_DIM*x + y] = kpoints[x].desc[y]
	return c_desc

# -----------------------------------------------------------------------------
# define main function

def main():
	
	# ----- parse arguments -----
	
	parse = argparse.ArgumentParser(description="homography test")
	parse.add_argument("scene_keypoints", help="json file containing keypoint data for the scene")
	parse.add_argument("scene_image", help="image from which scene keypoints were taken")
	parse.add_argument("flight_image", help="filename of the flight image")
	parse.add_argument("output_data", help="filename of output data")
	parse.add_argument("-i", dest="output_image", help="(OPTIONAL) if specified, an output image will be provided")
	
	args = parse.parse_args()
	scene_keypoints = args.scene_keypoints
	scene_image     = args.scene_image
	flight_image    = args.flight_image
	output_data     = args.output_data
	output_image    = args.output_image
	

	# ----- ouput run parameters -----
	
	print("=== Homography Test ===")
	print("scene keypoints: " + str(scene_keypoints))
	print("flight image   : " + str(flight_image))
	print("output file    : " + str(output_data))
	
	# ----- read and process scene keypoints and decriptors -----
	
	if not(os.path.exists(scene_keypoints)):
		print("Error: Unable to read scene keypoints.")
		
	kpoints = keypoints.LoadJSON(scene_keypoints)
	
	# get ctypes array containing keypoint and descriptor data
	c_kpoints = create_c_keypoints(kpoints)
	c_desc    = create_c_desc(kpoints)
	
	# ----- process data -----
	
	results = c_Results()
	
	lib = LibHG() # initialize library
	lib.LoadSceneKeypoints(c_kpoints)
	lib.LoadSceneDescriptors(c_desc,64)
	lib.ConfigureSURF(400)
	
	if not(lib.LoadObjectImage(flight_image)):
		print("Could not load object image!")
		exit(1)
		
	if not(lib.LoadSceneImage(scene_image)):
		print("Could not load scene image!")
		exit(1)
	
	
	lib.Process(results, 0.6)
	
	file_out = open(output_data,"w")
	file_out.write(json.dumps(dict( [ ("vertices", [ [p.x,p.y] for p in results.vert ] ), 
	                                  ("ftime", results.ftime),
                                      ("mtime", results.mtime),
                                      ("htime", results.htime) ] )))
	file_out.close()
	
	if output_image != None:
		lib.StoreOutputImage(output_image) # if an output image file name was given, store it
	
# -----------------------------------------------------------------------------
# run script

if __name__ == '__main__':
	main()
