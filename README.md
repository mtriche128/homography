# homography

## Description

This collection of software is designed to calculate the homography of flight images against satellite imagery of some pre-determined area.

## Requirements

1. g++ v4.8.2 or later (previous versions of g++ are as of yet untested with this software)
2. Python 2.7
3. OpenCV 2.4.x with python support (GPU support is optional)

## Setting Up Your System (Ubuntu)

If you're running Ubuntu, the following is a step-by-step list of directions for setting up your system to build and run this software.

### Setting Up Your Build Environment

'$ sudo apt-get install build-essential' 

Executing this under your command line will install all the nessessary tools used to compile C/C++.

$ g++ --version

This command should provide output which looks similar to the following:

g++ (Ubuntu 4.8.4-2ubuntu1~14.04) 4.8.4
Copyright (C) 2013 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

As you can see from the output above, the version of g++ is currently 4.8.4

### Installing Python

$ sudo apt-get install python

This command will install Python 2.7.x

$ python --version

After installing python, it's always a good idea to make sure you have the right version.

### Install OpenCV

A good place to start is at the following link:
http://docs.opencv.org/doc/tutorials/introduction/linux_install/linux_install.html

## Getting Started

### Install the homography software package.

$ git clone https://github.com/mtriche128/homography.git

### Build and install the library.

$ cd homography/lib
$ make
$ make install

### Veryify the library has been installed properly.

$ cd ..
$ ls libhg.so
libhg.so

### Running the Software

Before the homography script can be used, keypoints must first be generated from the satellite image. 
The generate_image_keypoints.py script can be used for this purpose. 

generate_image_keypoints.py takes three command-line arguments:

1. image_file        - This argument shall be the file-name of the image from which keypoints will be extracted.
2. keypoint_file     - This argument will specify the name of the output file (formated as a JSON) which will contain all the keypoint information.
3. hessian_threshold - The minimum Hessian threshold used when calculating keypoints will be specified by this argument.

Example:
image_file = chatfield_park_z15-0.png
keypoint_file = chatfield_park_z15-0.json
hessian_threshold = 400
$ python generate_image_keypoints.py chatfield_park_z15-0.png chatfield_park_z15-0.json 400

Once keypoints have been generated, the homography script can be run next.

homography.py takes four command-line arguments:
1. scene_keypoints - File-name of the JSON formatted data containing keypoints from the satellite image.
2. scene_image     - File-name of the satellite image.
3. flight_image    - File-name of the flight image.
4. output_data     - File-name of the JSON formatted output containing results from the homography calculation.

An optional fifth argument can be passed, which specifies an output image containing matches and vertices.
'-i OUTPUT_IMAGE'

Example:
scene_keypoints = chatfield_park_z15-0.json
scene_image = chatfield_park_z15-0.png
flight_image = chatfield_park_z16-3.png
output_data = out.json
OUTPUT_IMAGE = out.png
$ python homography.py chatfield_park_z15-0.json chatfield_park_z15-0.png chatfield_park_z16-3.png out.json -i out.png

## Enable GPU Support

To enable GPU support, uncomment the following line in lib/libhg.cc:

'//#define ENABLE_GPU' 

to

'#define ENABLE_GPU' 

Then, re-build and re-install the library:

$ make
$ make install

