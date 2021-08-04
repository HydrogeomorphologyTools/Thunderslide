# First attempt to retrieve and crop radar images over the desired AOI for extracting intense events and with ...
# ... such a mask enter the sentinel eo browser spi for retrieving images and change detection analysis

# Authors: Stefano Crema, Alessandro Sarretta, Marco Cavalli, Velio Coviello, Giorgia Macchi and Lorenzo Marchi
# July 2021

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

# create radar animation with basemap for ThunderSlide

from __future__ import print_function
import os
import time
import folium
import webbrowser
from osgeo import gdal
import numpy
from datetime import datetime
import datetime as dt
import matplotlib.cm
from PIL import Image
from desktopmagic.screengrab_win32 import (getRectAsImage)

# originally the desktopmagik import was: from desktopmagic.screengrab_win32 import (
#     getDisplayRects, saveScreenToBmp, saveRectToBmp, getScreenAsImage,
#     getRectAsImage, getDisplaysAsImages)
# unused import are removed

# setting start and end time and create a gif
start_dt = "2021/07/31 17:40:00"
end_dt = "2021/07/31 18:00:00"

# to datetime format
start_datetime = datetime.strptime(start_dt, "%Y/%m/%d %H:%M:%S")
end_datetime = datetime.strptime(end_dt, "%Y/%m/%d %H:%M:%S")

# markers for locations and maps
location_map = [45.9, 11.4]
# location_map = [45.12, 11.62] # location map Casa Crema
# text_marker = [45.33, 10.99] # for location map Casa Crema 45.12, 11.62, with zoom 11

# for zoom level = 9 text marker upper left
text_marker = [46.8, 9.0]
cancia_marker = [46.447, 12.248]

# initialization
images_gif = []

# list of images every 5 minutes
listOfDates = [date for date in numpy.arange(start_datetime, end_datetime, dt.timedelta(minutes=5))]
for i in range(len(listOfDates)):
    fn_tmp = str(listOfDates[i])
    filename = "D:/Research/Thunderslide/Thunderslide/images/" + \
               fn_tmp[0:4] + fn_tmp[5:7] + fn_tmp[8:10] + "_" + fn_tmp[11:13] + \
               fn_tmp[14:16] + fn_tmp[17:19] + "_mask_NI.tif"
    del fn_tmp
    # filename = "D:/Research/Thunderslide/Thunderslide/images/20210702_002000_mask_NI.tif"

    tif = gdal.Open(filename, gdal.GA_ReadOnly)

    # raster as an array
    tif_ar = tif.ReadAsArray()
    tif_ar = tif_ar.astype(numpy.float32)
    tif_ar[tif_ar <= 0] = numpy.nan
    del tif

    # normed_data = (tif_ar - numpy.nanmin(tif_ar)) / (numpy.nanmax(tif_ar) - numpy.nanmin(tif_ar))
    normed_data = (tif_ar - numpy.nanmin(tif_ar)) / (60 - numpy.nanmin(tif_ar))  # guessing a max value around 60-70 for
    # the original geotiff
    cm = matplotlib.cm.get_cmap('seismic')
    colored_data = cm(normed_data)
    del tif_ar

    m = folium.Map(location=location_map, zoom_start=9, tiles="Stamen Terrain")
    # e.g., Antelao = [46.45, 12.24]

    # Add marker popup over Cancia triggering area
    tooltip = "Cancia!"

    folium.Marker(
        cancia_marker, popup="<i>Cancia</i>", tooltip=tooltip
    ).add_to(m)

    # As bounding box the limits of the geotiff retrieved by rasterio (inverted lat lon order) boundingbox and then
    # cancelled
    # general Northeastern Italy bounding box from shapefile = [[43.402017091252105, 6.264951031762513], [47.63896794552554, 14.427680384636325]]
    # needs to be exactly the BB of the shapefile
    # Antelao-Dolomites area = [[46.37, 12,17], [46.41, 12.34]]
    folium.raster_layers.ImageOverlay(colored_data,
                                      [[43.39866, 6.26438], [47.63939, 14.43821]],
                                      opacity=0.6).add_to(m)

    # add marker with text reporting datetime of the frame
    folium.Marker(location=text_marker,
                  popup=filename[-27:-12],
                  icon=folium.DivIcon(
                      html=f"""<div style="font-size: 48pt; font-weight: bold; font-family: courier new; color: white">
                        {filename[-27:-12]}</div>""")).add_to(m)

    fileout = ("D:/Research/Thunderslide/animation/map_" + filename[-27:-12] + ".html")
    fileout_png = ("D:/Research/Thunderslide/animation/map_" + filename[-27:-12] + ".png")

    m.save(fileout)
    webbrowser.open(fileout)
    time.sleep(0.8)  # wait for html open, tune on your machine performance

    # Capture an arbitrary rectangle of the virtual screen: (left, top, right, bottom)
    capture = getRectAsImage((1920, 100, 3840, 1040))
    capture.save(fileout_png, format='png')

    # os.system(fileout_png)
    im_temp = Image.open(fileout_png)
    images_gif.append(im_temp)
    del im_temp

animation_out = "D:/Research/Thunderslide/animation/test_animation.gif"
images_gif[0].save(animation_out, save_all=True, append_images=images_gif[1:], optimize=True, duration=500, loop=0)
# duration is millisec per frame

os.system(animation_out)
