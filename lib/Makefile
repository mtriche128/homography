INSTALL_DIR=../

all: libhg.cc
	g++ -o libhg.so -I/usr/local/include/opencv -I/usr/local/include -L/usr/local/lib /usr/local/lib/libopencv_ts.a -lrt -lpthread -lm -shared -fPIC libhg.cc -lopencv_core -lopencv_calib3d -lopencv_contrib -lopencv_features2d -lopencv_flann -lopencv_gpu -lopencv_highgui -lopencv_imgproc -lopencv_legacy -lopencv_ml -lopencv_nonfree -lopencv_objdetect -lopencv_ocl -lopencv_photo -lopencv_stitching -lopencv_superres -lopencv_video -lopencv_videostab

install:
	cp libhg.so ${INSTALL_DIR}

clean:
	rm *.so
