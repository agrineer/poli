#!/usr/bin/bash

# very rudimentary exercises of some of the command line version of POLI

# first create a Python environment directory, eg:

#> python3 -m venv .cpoli

# activate:

#> cd .cpoli
#> source bin/activate

# you should see the terminal prompt prefixed with (.cpoli)

# get requirements:
#> pip3 install -r $POLI_HOME/misc/NOGUI_requirements.txt

# run examples:

# IMAGE EDGE DETECTION ###########################################

# using sobel operator with local data file
echo "SOBEL"
img_src -f $POLI_HOME/data/general/FlyingMerkel.jpeg | sobel | render -f SFM.jpg -c 0,1,2

# morpholoy with URL image
echo "DERIVATIVE"
img_src -f https://agrineer.org/publish/data/URLgeneral/FlyingMerkel.jpeg | derivative -d xy | dilate | render -f URLDFM.jpg -c 0,1,2

# canny edge detector
echo "CANNY"
img_src -f $POLI_HOME/data/general/FlyingMerkel.jpeg | canny | render -f CANNY_FM.jpg -c 0,1,2

# MACHINE LEARNING ############################################
echo "MSOM"
cetin_src | msom | render -f CETIN_MSOM.jpg

# repetative execution output won't be exactly the same due to random start weights, affects the assigment of class labels only

# use -t in render to pass thru numpy buffer:
echo "MSOM PASSTHRU"
cetin_src | msom | render -t -f THRU_MSOM.jpg > THRU_MSOM.npy

# use som labels to classify
echo "SOMCLASS"
cetin_src | somclass -f msom_weights.labels | render -f CETIN_SOMCLASS.jpg -l $POLI_HOME/luts/rainbow.lut 

# use npy_src on data from URL
echo "NPY_SRC"
npy_src -f  https://agrineer.org/publish/data/URLml/cetin.npy | msom | render -f URL_MSOM.jpg

# IMAGE ENHANCEMENT ###########################################
echo "EQUALHIS"
img_src -f $POLI_HOME/data/general/cuernavaca-centro.jpg | equalhis | render -f EQUALHIS.jpg -c 0,1,2

# difference
# get source image from GUI POLI
# use img_src operator to show $POLI_HOME/data/general/FlyingMerkel.jpeg
# use options button to save image as numpy file eg. FM.npy

# FM.npy in command differ:
echo "DIFFER"
img_src -f $POLI_HOME/data/general/FlyingMerkel.jpeg | blur -n 9 | differ -f $POLI_HOME/data/ml/FM.npy | render -f DIFF_FM.jpg  -c 0,1,2

# norm and cnorm where cnorm uses normalization coefficient produced by norm
echo "NORMALIZE"
img_src -f $POLI_HOME/data/general/ireland.jpg | norm -f ireland.coeff > NORM_ireland.npy

# output should be blank
echo "CNORM"
img_src -f $POLI_HOME/data/general/ireland.jpg | cnorm -f ireland.coeff | differ -f NORM_ireland.npy | render -f DIFF_ireland.jpg -c 0,1,2

# flip images
echo "FLIP"
img_src -f $POLI_HOME/data/general/ireland.jpg | flip -d y | render -f FLIP_ireland.jpg -c 0,1,2

# WRF Weather, Research and Forecast (US UCAR/NCAR ) #################
# make color image of tghree variables in WRF output:
# temperature at 2 meters, humidity, and pressure at 6:00am UTC
echo "WRF_SRC"
wrf_src -c -f https://agrineer.org/publish/data/URLwrf/wrfout_d01_2025-03-01_07-00-00.nc -b 'T2:6,Q2:6,PSFC:6' | render -f WRF_color.jpg  -c 0,1,2

# CALCULATE STANDARD EVAPORATION ###################################
# data too big for installation
#wrf_src -f https://agrineer.org/publish/data/URLwrf/wrfout_d01_2025-01-01_07-00-00 -b 'TSK:12,EMISS:12,SWDOWN:12,GLW:12,GRDFLX:12,T2:12,PSFC:12,Q2:12,U10:12,V10:12' | prep_eto | eto | render -f ETO.jpg -g 0 -l $POLI_HOME/luts/rainbow.lut

## AVHRR (noaa satellites) ################################

# detect dust
echo "AVHRR and DUST"
ag_src -c -f https://agrineer.org/publish/data/URLsat/noaa-19_2021_0710_1420_scrb.hdf  | adust | render -f ADUST.jpg -g 0 -l $POLI_HOME/luts/rainbow.lut

# calculate albedo
echo "ALBEDO"
ag_src -c -f  https://agrineer.org/publish/data/URLsat/noaa-19_2021_0710_1420_scrb.hdf | albedo | render -g 0 -l $POLI_HOME/luts/rainbow.lut -f ALBEDO.jpg

# calculate land surface temperature
echo "LST"
ag_src -c -f  https://agrineer.org/publish/data/URLsat/noaa-19_2021_0710_1420_scrb.hdf | lst -m singh | render -g 0 -l $POLI_HOME/luts/sixteenthbow.lut -f LST.jpg

# MODIS (aqua and terra satellites) ###################################
echo "PROJMOD"
projmod_src -c -f https://agrineer.org/publish/data/URLsat/SCRB_MODIS_1km.hdf -b 1,2,3,4,26,31,32 | mdust -u | render -f MDUST.jpg -c 0,1,2

echo "MOD02"
mod02_src -c -f https://agrineer.org/publish/data/URLsat/MOD02_1KM.A2010095.1745.005.2010096020843.hdf -b 1,2,3,5 | render -f MOD2.jpg -l $POLI_HOME/luts/ramp.lut -g 3

## IMAGE THRESHOLDING #######################################
echo "NOTCH"
img_src -f $POLI_HOME/data/general/wedge.tiff | thrsh_notch -b -l 64 -u 192 | render -f THRESH_wedge.tiff -g 0 -l $POLI_HOME/luts/ramp.lut

echo "LOCAL"
img_src -f $POLI_HOME/data/general/tree.jpg | thrsh_local -b | render -f TREE_LOCAL.jpg -l $POLI_HOME/luts/ramp.lut -g 0

# show merged binary buffers as color; POLI GUI can show individual buffers as binary
echo "MEAN"
img_src -f $POLI_HOME/data/general/tree.jpg | thrsh_mean -b | render -f TREE_MEAN.jpg -c 0,1,2

echo "MIN"
img_src -f $POLI_HOME/data/general/tree.jpg | thrsh_min -b -m 5000 | render -f TREE_MIN.jpg -c 0,1,2

echo "MOTSU"
img_src -f $POLI_HOME/data/general/tree.jpg | thrsh_motsu -n 5 | render -f TREE_MOTSU.jpg -c 0,1,2

echo "NIBLACK"
img_src -f $POLI_HOME/data/general/tree.jpg | thrsh_niblack -w 15 | render -f TREE_NIBLACK.jpg -c 0,1,2

echo "OTSU"
img_src -f $POLI_HOME/data/general/tree.jpg | thrsh_otsu | render -f TREE_OTSU.jpg -c 0,1,2

echo "SAUVOLA"
img_src -f $POLI_HOME/data/general/tree.jpg | thrsh_sauvola -k 0.2 -b | render -f TREE_SAUVOLA.jpg -c 0,1,2

echo "TRIANGLE"
img_src -f $POLI_HOME/data/general/tree.jpg | thrsh_tri -b | render -f TREE_TRIANGLE.jpg -c 0,1,2

echo "LI"
img_src -f $POLI_HOME/data/general/tree.jpg | thrsh_li -b | render -f TREE_LI.jpg -c 0,1,2

echo "YEN"
img_src -f $POLI_HOME/data/general/tree.jpg | thrsh_yen -b | render -f TREE_YEN.jpg -c 0,1,2

echo "ISO"
img_src -f $POLI_HOME/data/general/tree.jpg | thrsh_iso -b | render -f TREE_ISO.jpg -c 0,1,2

echo "ETO"
prep_eto -c -w https://agrineer.org/publish/data/ANDES03 -d 3 -r 20250302 | eto | render -f ETO_20250302.jpg -l $POLI_HOME/luts/ramp.lut

##################################################
# example batch implementation
echo "RUNNING BATCH EXAMPLE"
$POLI_HOME/misc/cetin_batch.py
