# First attempt to retrieve and crop radar images over the desired AOI for extracting intense events and with ...
# ... such a mask enter the sentinel eo browser spi for retrieving images and change detection analysis

# Authors: Stefano Crema, Alessandro Sarretta, Marco Cavalli, Velio Coviello, Giorgia Macchi and Lorenzo Marchi

"""
###############################################################################
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
For a copy of the GNU-GPL v2 license please visit: http://www.gnu.org/licenses/gpl-2.0.txt
###############################################################################
"""


# imports
import os
import math
import shutil
import time
from datetime import datetime
import requests
import numpy
from osgeo import gdal

# time retrieval 5min ita geotiff (UTC + 1/2 hour back)
tempo_now = int(math.floor((time.time()) / 300.0)) * 300 - (60 * 20)  # add n min back to be sure the geotiff is present
tempo_str = (datetime.utcfromtimestamp(tempo_now).strftime('%Y-%m-%d %H:%M:%S'))
tempo_name = tempo_str[0:4] + tempo_str[5:7] + tempo_str[8:10] + "_" + tempo_str[11:13] + tempo_str[14:16] + tempo_str[
                                                                                                             17:19]

# image url parameters options here: https://www.rainviewer.com/api/legacy.html ita radar instead are here:
# https://data.rainviewer.com/images/IYCOMP2/ already in geotiff format, handy!
image_url = str("https://data.rainviewer.com/images/IYCOMP2/IYCOMP2_" + tempo_name + "_0_source.tif")
filename = "D:/Research/Thunderslide/Thunderslide/images/" + tempo_name + "_0_source.tif"

# Open the url image, set stream to True, this will return the stream content.
r = requests.get(image_url, stream=True)

# Check if the image was retrieved successfully
if r.status_code == 200:
    # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
    r.raw.decode_content = True

    # Open a local file with wb ( write binary ) permission.
    with open(filename, 'wb') as f:
        shutil.copyfileobj(r.raw, f)

    print('Image successfully Downloaded: ', filename, ' from ', image_url)
else:
    print('Image Couldn\'t be retrieved from ', image_url)

# Working with Geotiff, reducing image size removing NoData codes and values <=0
tif = gdal.Open(filename, gdal.GA_ReadOnly)

cols = tif.RasterXSize
rows = tif.RasterYSize
bands = tif.RasterCount

#
# raster as an array
tif_ar = tif.ReadAsArray()
tif_ar = tif_ar.astype(numpy.float32)
band = tif.GetRasterBand(1)  # bands retrieving, starts from 1, not zero
geoinf = tif.GetGeoTransform()  # upper left coordinates, cellsize
proj = tif.GetProjection()
tipo = tif_ar.dtype
del tif
os.remove(filename)

tif_ar[tif_ar < 0] = numpy.nan  # nan is only valid for float type, it could be worth saving as int losing the .5
# accuracy of radar intensity but also halving the space

# write back the raster
file_correct_nan = (filename[0:-12] + "out.tif")
tif_int_out = gdal.GetDriverByName('GTiff').Create(file_correct_nan, tif_ar.shape[1], tif_ar.shape[0], 1,
                                                   gdal.GDT_Float32)  # shape are rows and columns bands number  = 1
# (intensity return)
tif_int_out.SetGeoTransform(geoinf)  # coordinates and proj of input raster
tif_int_out.SetProjection(proj)
tif_int_out.GetRasterBand(1).SetNoDataValue(-9999)
tif_int_out.GetRasterBand(1).WriteArray(tif_ar, 0, 0)  # writing now after allocating memory
tif_int_out = None  # (Sometimes) I add this to ensure the file is fully deallocated
del tif_int_out

# trying to cut raster on mask of northern Italy (EPSG 4326, all the data) - shapefile in dedicated folder in GitHub
mask_shp = "D:/Research/Thunderslide/mask_N_IT/Nord_Italy.shp"
destination_raster = (filename[0:-12] + "mask_NI.tif")
print(destination_raster)

ds = gdal.Warp(destination_raster, file_correct_nan, format='GTiff', cutlineDSName=mask_shp, cutlineLayer='Nord_Italy',
               cropToCutline=True)
ds = None

os.remove(file_correct_nan)
