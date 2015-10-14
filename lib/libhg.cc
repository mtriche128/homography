/**
 * @file   libhg.cc
 * @author Matthew Triche
 * @brief  library used for homography testing
 */

/* ------------------------------------------------------------------------- *
 * Include Header Files                                                      *
 * ------------------------------------------------------------------------- */

#include <iostream>
#include <vector>
#include <algorithm>
#include <time.h>
#include <stdio.h>
#include "opencv2/opencv_modules.hpp"
#include "opencv2/core/core.hpp"
#include "opencv2/features2d/features2d.hpp"
#include "opencv2/highgui/highgui.hpp"
#include "opencv2/gpu/gpu.hpp"
#include "opencv2/nonfree/gpu.hpp"
#include "opencv2/nonfree/nonfree.hpp"
#include "opencv2/calib3d/calib3d.hpp"


/* ------------------------------------------------------------------------- *
 * Define Namespaces                                                         *
 * ------------------------------------------------------------------------- */

using namespace std;
using namespace cv;
using namespace cv::gpu;

/* ------------------------------------------------------------------------- *
 * Define Constants                                                          *
 * ------------------------------------------------------------------------- */

// Uncomment this to enable GPU acceleration.
#define ENABLE_GPU 

/* ------------------------------------------------------------------------- *
 * Define Types                                                              *
 * ------------------------------------------------------------------------- */

typedef struct C_POINT2F_
{
	float x,y;
} c_Point2f;
	

typedef struct C_KEYPOINT_
{
	c_Point2f _pt;
	float _size;
	float _angle;
	float _response;
	int   _octave;
	int   _class_id;
} c_KeyPoint;
	
/**
 * @brief Container for results generated from the homography process.
 */

typedef struct RESULTS_
{
	c_Point2f vert[4]; // Stores the transformed vertices corresponding to the 
	                   // four corners of the object image.
	double ftime;      // The elapsed time of the feature phase. (seconds)
	double mtime;      // The elapsed time of the matching phase. (seconds)
	double htime;      // The elapsed time of the homography phase. (seconds)
} results_t;

/* ------------------------------------------------------------------------- *
 * Declare Internal Functions                                                *
 * ------------------------------------------------------------------------- */

/* ------------------------------------------------------------------------- *
 * Declare External Functions                                                *
 * ------------------------------------------------------------------------- */

extern "C" void ConfigureSURF(int);
extern "C" void LoadSceneKeypoints(c_KeyPoint*,int);
extern "C" void LoadSceneDescriptors(float*,int,int);
extern "C" bool LoadObjectImage(char *filename);
extern "C" bool LoadSceneImage(char *filename);
extern "C" void StoreOutputImage(char *filename);
extern "C" void Process(results_t*,double);
extern "C" void Release();

/* ------------------------------------------------------------------------- *
 * Define Internal Variables                                                 *
 * ------------------------------------------------------------------------- */

static Mat sceneDesc, objDesc; // object and scene descriptors
static Mat objImg, sceneImg; // object and scene images
static vector<KeyPoint> sceneKeypoints, objKeypoints;
static vector<Point2f> output_vert(4); // vertices used when storing an output image 
static vector<DMatch> matches;

#ifndef ENABLE_GPU
	static SurfFeatureDetector *detector;
	static SurfDescriptorExtractor *extractor;
#else
	static SURF_GPU *surf = NULL;
	static GpuMat sceneDescGPU, objDescGPU;
	static GpuMat objImgGPU, sceneImgGPU; 
	static GpuMat objKpGPU, sceneKpGPU;
#endif

/* ------------------------------------------------------------------------- *
 * Define Internal Functions                                                 *
 * ------------------------------------------------------------------------- */


/* ------------------------------------------------------------------------- *
 * Define External Functions                                                 *
 * ------------------------------------------------------------------------- */

/**
 * @brief Configure SURF properties. Only needed if GPU is enabled.
 * 
 * @param minHess  The minimum Hessian threshold.
 */

extern "C" void ConfigureSURF(int minHess)
{
#ifdef ENABLE_GPU
	
	/* properties set at compile-time */
	#define SURF_N_OCT        4 
	#define SURF_N_OCT_LAYERS 2 
	#define SURF_EXTENDED     false
	#define KP_RATIO          0.01

	surf = new SURF_GPU(minHess,
	                    SURF_N_OCT,
	                    SURF_N_OCT_LAYERS,
	                    SURF_EXTENDED,
	                    KP_RATIO);
#else
	
	detector = new SurfFeatureDetector(minHess);
	extractor = new SurfDescriptorExtractor();
	
#endif
	                 
}


/**
 * @brief Load scene keypoints.
 * 
 * @param buff source buffer containing pre-built c_KeyPoints
 * @param num  number of keypoints
 */

extern "C" void LoadSceneKeypoints(c_KeyPoint *buff, int num)
{
	sceneKeypoints.resize(num);
	
	for(int i = 0; i < num; i++)
	{
		sceneKeypoints[i] = KeyPoint(Point2f(buff[i]._pt.x, buff[i]._pt.y),
		                             buff[i]._size,
		                             buff[i]._angle,
		                             buff[i]._response,
		                             buff[i]._octave,
		                             buff[i]._class_id);
	}
	
#ifdef ENABLE_GPU
	surf->uploadKeypoints(sceneKeypoints, sceneKpGPU);
#endif
}

/**
 * @brief Load scene descriptors from a buffer of floats.
 * 
 * @param buff source buffer for scene descriptor data
 * @param dim  descriptor dimension
 * @param num  number of descriptors
 */

extern "C" void LoadSceneDescriptors(float *buff, int dim, int num)
{
	//sceneDesc.create(dim,num,CV_32F);
	sceneDesc.create(num,dim,CV_32F);
	
	/* there is a much faster way to do this */
	for(int c = 0; c < num; c++)
	{
		for(int r = 0; r < dim; r++)
		{
			//sceneDesc.at<float>(r,c) = *(buff++);
			sceneDesc.at<float>(c,r) = *(buff++);
		}
	}

#ifdef ENABLE_GPU
	sceneDescGPU.upload(sceneDesc);
#endif
}

/**
 * @brief Load object image.
 * 
 * @param filename string containing the path and filename of the object image
 * 
 * @return True if loaded successfully, false otherwise.
 */

extern "C" bool LoadObjectImage(char *filename)
{
    objImg = imread(filename, CV_LOAD_IMAGE_GRAYSCALE);

#ifdef ENABLE_GPU
	if(!objImg.empty())
		objImgGPU.upload(objImg);
#endif
	
    return !objImg.empty();
}

/**
 * @brief Load scene image.
 * 
 * @param filename string containing the path and filename of the scene image
 * 
 * @return True if loaded successfully, false otherwise.
 */

extern "C" bool LoadSceneImage(char *filename)
{
    sceneImg = imread(filename, CV_LOAD_IMAGE_GRAYSCALE);
    
    return !sceneImg.empty();
}

/**
 * @brief Process all data and find the homography of the object image.
 * 
 * @param dst     Destination pointer where results will be written.
 * @param minHess Minimum Hessian used when extracting onject features.
 * @param ratio   Quality ratio used when finding matches. 
 */

extern "C" void Process(results_t *dst, double ratio)
{
	int tstart, tend;
	
	cout << "Processing Data... " << endl;
	
	// --------------------------------------
	// detect object features
	
	cout << "  (1) extracting object features" << endl;
	
#ifdef ENABLE_GPU

	tstart = clock();
	(*surf)(objImgGPU, GpuMat(), objKpGPU, objDescGPU);
	tend = clock();
	dst->ftime = (double)(tend - tstart)/(double)CLOCKS_PER_SEC;
	
	surf->downloadKeypoints(objKpGPU, objKeypoints);
	
#else
	
	tstart = clock();
	detector->detect(objImg, objKeypoints);
	extractor->compute(objImg, objKeypoints, objDesc);
	tend = clock();
	dst->ftime = (double)(tend - tstart)/(double)CLOCKS_PER_SEC;
	
#endif
	
	// --------------------------------------
	// find matches
	
	cout << "  (2) finding matches" << endl;
	
	vector< vector<DMatch> > init_matches;
	
#ifdef ENABLE_GPU
	
	BFMatcher_GPU matcher(NORM_L2);
	
	tstart = clock();
	matcher.knnMatch(objDescGPU, sceneDescGPU, init_matches, 2);
	
	matches.clear();
	
	for (int i = 0; i < init_matches.size(); i++)
	{
		if(init_matches[i][0].distance <= (ratio*init_matches[i][1].distance))
		{
			matches.push_back(init_matches[i][0]);
		}
	}
	
	tend = clock();
	dst->mtime = (double)(tend - tstart)/(double)CLOCKS_PER_SEC;

#else

	Mat descriptors1, descriptors2;  	 
	FlannBasedMatcher flann_matcher;
	
	tstart = clock();
	flann_matcher.knnMatch(objDesc, sceneDesc, init_matches, 2);
	matches.clear();
	for (int i = 0; i < init_matches.size(); i++)
	{
		if(init_matches[i][0].distance <= (ratio*init_matches[i][1].distance))
		{
			matches.push_back(init_matches[i][0]);
		}
	}
	tend = clock();
	dst->mtime = (double)(tend - tstart)/(double)CLOCKS_PER_SEC;	

#endif

	// --------------------------------------
	// calculate homography
	
	cout << "  (3) calculating homography" << endl;
	
	vector<Point2f> objKeypointsHg;
	vector<Point2f> sceneKeypointsHg;
	
	tstart = clock();
	
	for(int i = 0; i < matches.size(); i++)
	{
			objKeypointsHg.push_back(objKeypoints[matches[i].queryIdx].pt);
			sceneKeypointsHg.push_back(sceneKeypoints[matches[i].trainIdx].pt);
	}
	
	Mat H = findHomography(objKeypointsHg, sceneKeypointsHg, CV_RANSAC );
	
    vector<Point2f> obj_corners(4); // stores object image corners
    obj_corners[0] = cvPoint(0,0);
    obj_corners[1] = cvPoint(objImg.cols, 0);
    obj_corners[2] = cvPoint(objImg.cols, objImg.rows);
    obj_corners[3] = cvPoint(0, objImg.rows);

    perspectiveTransform(obj_corners, output_vert, H);
	
	tend = clock();
	dst->htime = (double)(tend - tstart)/(double)CLOCKS_PER_SEC;
	
	// --------------------------------------
	// write vertex results
	
	cout << "  (4) writing vertex results" << endl;

	dst->vert[0].x = output_vert[0].x;
	dst->vert[1].x = output_vert[1].x;
	dst->vert[2].x = output_vert[2].x;
	dst->vert[3].x = output_vert[3].x;
	
	dst->vert[0].y = output_vert[0].y;
	dst->vert[1].y = output_vert[1].y;
	dst->vert[2].y = output_vert[2].y;
	dst->vert[3].y = output_vert[3].y;

	cout << "DONE" << endl;
}

/**
 * @brief Store an output image with matches and homography visualized.
 *
 * @param filename Filename of the output image.
 */

extern "C" void StoreOutputImage(char *filename)
{
	Mat img_matches;

	drawMatches(Mat(objImg), objKeypoints, Mat(sceneImg), sceneKeypoints, matches, img_matches, 
		        Scalar::all(-1), Scalar::all(-1), vector<char>(),
		        DrawMatchesFlags::NOT_DRAW_SINGLE_POINTS);
	
	line( img_matches, output_vert[0] + Point2f( objImg.cols, 0), output_vert[1] + Point2f( objImg.cols, 0), Scalar(0, 255, 0), 4 );
    line( img_matches, output_vert[1] + Point2f( objImg.cols, 0), output_vert[2] + Point2f( objImg.cols, 0), Scalar( 0, 255, 0), 4 );
    line( img_matches, output_vert[2] + Point2f( objImg.cols, 0), output_vert[3] + Point2f( objImg.cols, 0), Scalar( 0, 255, 0), 4 );
    line( img_matches, output_vert[3] + Point2f( objImg.cols, 0), output_vert[0] + Point2f( objImg.cols, 0), Scalar( 0, 255, 0), 4 );
	
	imwrite(filename, img_matches);
}

/**
 * @brief Free allocated memory.
 */

extern "C" void Release()
{
	sceneDesc.release();
	objDesc.release();	
	objImg.release();
	sceneImg.release();
	
	sceneKeypoints.clear();
	objKeypoints.clear();
	output_vert.clear();  
	matches.clear();
	
#ifdef ENABLE_GPU
	sceneDescGPU.release();
	objDescGPU.release();
	objImgGPU.release();
	sceneImgGPU.release(); 
	objKpGPU.release();
	sceneKpGPU.release();
	
	surf->releaseMemory();
	delete surf;
#else
	delete detector;
	delete extractor;
#endif
}
