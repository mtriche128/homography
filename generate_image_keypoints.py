# file    : generate_image_keypoints.py
# citation: This scrpt was created in support of projects at UC Denver.
# brief   : This script is designed to extract features from an image using SURF.

import cv2 
import numpy as np 
import cPickle as pickle 
import json
import argparse

def pickle_keypoints(keypoints, descriptors): 
   temp_array = [] 
   for index, point in enumerate(keypoints): 
      temp = (point.pt, point.size, point.angle, point.response, point.octave, point.class_id, descriptors[index]) 
      print index, temp
      temp_array.append(temp) 
   return temp_array

def unpickle_keypoints(array): 
   keypoints = [] 
   descriptors = [] 
   for point in array: 
      temp_feature = cv2.KeyPoint(x=point[0][0],y=point[0][1],_size=point[1], _angle=point[2], 
           _response=point[3], _octave=point[4], _class_id=point[5]) 
      temp_descriptor = point[6] 
      keypoints.append(temp_feature) 
      descriptors.append(temp_descriptor) 
   return keypoints, np.array(descriptors) 

class NumpyAwareJSONEncoder(json.JSONEncoder):
   def default(self, obj):
       if isinstance(obj, np.ndarray) and obj.ndim == 1:
           return obj.tolist()
       return json.JSONEncoder.default(self, obj)

def write_json_keypoints(keypoint_file, kp, desc):
   data = dict ((index, (point.pt, point.size, point.angle, point.response, point.octave, point.class_id, desc[index])) for index, point in enumerate(kp))

   with open(keypoint_file, "w") as fo:
      fo.write(json.dumps(data, cls=NumpyAwareJSONEncoder) + "\n")

def read_json_keypoints(keypoints_file):
   with open(keypoints_file, "r") as fi:
      data = json.load(fi)
   return data

def generate_keypoint_image(image_file, hessian_threshold=400, feature_type="SURF"):
   # Load the images 
   img =cv2.imread(image_file) 

   # Convert them to greyscale 
   grey_img =cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) 

   # Algo to run
   detector = cv2.FeatureDetector_create(feature_type)
   descriptor = cv2.DescriptorExtractor_create(feature_type)
   
   # set Hessian threshold
   detector.setInt("hessianThreshold",hessian_threshold)
   descriptor.setInt("hessianThreshold",hessian_threshold)

   #print "Detecting keypoints"
   kp = detector.detect(grey_img)
   #print "Generating descriptors"
   kp, desc = descriptor.compute(grey_img, kp)

   return kp, desc

def main():
   # Setup argument parser
   parser = argparse.ArgumentParser(description='Parsing')
   parser.add_argument('image_file', help="requires an image file")
   parser.add_argument('keypoint_file', help="requires a keypoint file")
   parser.add_argument('hessian_threshold', help="requires a hessian theshold")

   # Parse arguments
   args = parser.parse_args()
   image_file = args.image_file
   keypoint_file = args.keypoint_file
   hessian_threshold = int(args.hessian_threshold)

   # Generate keypoints
   kp, desc = generate_keypoint_image(image_file, hessian_threshold)
   write_json_keypoints(keypoint_file, kp, desc)

#base http://www.programcreek.com/python/example/70407/cv2.FeatureDetector_create
 

if __name__ == '__main__':
    main()

