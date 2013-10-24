# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012 Sigurd Gartmann sigurdga-ubuntu@sigurdga.no
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import os
from lxml import etree


from gi.repository import Champlain, Clutter

class GpxTrack(object):

    def __init__(self, mapwidget, resultstore, *args, **kwargs):
        super(GpxTrack, self).__init__(*args, **kwargs)
        self.mapwidget = mapwidget
        self.store = resultstore
        self.path_layer = Champlain.PathLayer()
        self.marker_layer = Champlain.MarkerLayer()
        self.mapwidget.add_layer(self.path_layer)
        self.mapwidget.add_layer(self.marker_layer)
        self.name = "No name"
        self._id = None

    def show(self):
        self.path_layer.show()
        self.marker_layer.show()

    def hide(self):
        self.path_layer.hide()
        self.marker_layer.hide()

    def go_to(self):
        bbox = self.path_layer.get_bounding_box()
        self.mapwidget.ensure_visible(bbox, True)

    def import_file(self, filename):
        self._id = filename
        basename = os.path.basename(filename)
        self.name = os.path.splitext(basename)[0]
        tree = etree.parse(filename)
        locations = tree.xpath("//*[local-name()='trkpt']")
        waypoints = tree.xpath("//*[local-name()='wpt']")

        self.store.append([self.name, True, self])

        for location in locations:
            lat = float(location.attrib['lat'])
            lon = float(location.attrib['lon'])
            self.path_layer.add_node(Champlain.Coordinate.new_full(lat, lon))

        for waypoint in waypoints:
            lat = float(waypoint.attrib['lat'])
            lon = float(waypoint.attrib['lon'])
            text = waypoint.find("{http://www.topografix.com/GPX/1/1}name").text
            linktag = waypoint.find("{http://www.topografix.com/GPX/1/1}link")
            marker = Champlain.Label()
            if linktag is not None:
                url = linktag.attrib['href']
                if url.endswith('jpg') or url.endswith('JPG'):
                    if os.path.exists(url):
                        image = Clutter.Texture.new_from_file(url)
                        image.set_keep_aspect_ratio(True)
                        image.set_width(60)
                        marker.set_image(image)
                    else:
                        marker = None

            if marker:
                if text:
                    marker.set_text(text)
                marker.set_location(lat, lon)
                self.store.append([text, True, marker])
                self.marker_layer.add_marker(marker)
