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

import urllib2
import json
import os

from gi.repository import Champlain, GdkPixbuf

class IconDownloader(object):

    def __init__(self, icon_cache, *args, **kwargs):
        self.icon_cache = icon_cache
        super(IconDownloader, self).__init__(*args, **kwargs)

    def download(self, url):
        encoded_url = url.replace("/", "_")  # urllib2.quote(url.encode("utf-8"))
        file_location = os.path.join(self.icon_cache, encoded_url)
        if not os.path.exists(file_location):
            try:
                headers = { 'User-Agent' : 'StrekmannMapSearch/0.1' }
                request = urllib2.Request(url, headers=headers)
                response = urllib2.urlopen(request).read()
                icon_file = open(file_location, "wb")
                icon_file.write(response)
                icon_file.close()
            except:
                return None

        return file_location


class ResultView(object):

    def __init__(self, label, widget, liststore, marker_layer, directionstore, directionmarkers):
        self.label = label
        self.widget = widget
        self.liststore = liststore
        self.marker_layer = marker_layer
        self.directionstore = directionstore
        self.directionmarkers = directionmarkers

    def show(self, text="", widget=1):
        self.label.set_text(text)
        self.widget.show()
        self.widget.get_children()[widget].show()
        self.widget.get_children()[3-widget].hide()
        self.marker_layer.show()
        self.directionmarkers.show()

    def hide(self):
        self.label.set_text("")
        self.widget.hide()
        self.marker_layer.hide()
        self.directionmarkers.hide()

    def clear(self):
        self.liststore.clear()
        self.marker_layer.remove_all()
        self.directionstore.clear()
        self.directionmarkers.remove_all()

class Way(object):

    def __init__(self, *args, **kwargs):
        self.direction = None
        self.lat = None
        self.lon = None
        self.narrative = None
        self.icon_url = None
        self.distance = None
        self.time = None

class Guide(object):

    def __init__(self, application, marker_layer, resultstore):
        super(Guide, self).__init__()
        self.store = resultstore
        self.marker_layer = marker_layer
        self.icon_downloader = IconDownloader(application.icon_cache)

    def search(self, marker_position1, marker_position2):
        headers = { 'User-Agent' : 'StrekmannMapSearch/0.1' }
        request = urllib2.Request(
                'http://open.mapquestapi.com/directions/v1/route?outFormat=json&from=%F,%F&to=%F,%F' % (
                    marker_position1.get_latitude(), marker_position1.get_longitude(),
                    marker_position2.get_latitude(), marker_position2.get_longitude(),
                    ),
                headers=headers,
                )
        response = urllib2.urlopen(request).read()
        data = json.loads(response)
        #print data
        #data = json.load(open("/home/sigurdga/route.json"))

        def format_time(seconds):
            hours = seconds / 3600
            rest = seconds % 3600
            minutes = rest / 60
            seconds = seconds % 60
            return "%d:%02d:%02d" % (hours, minutes, seconds)

        if data['info']['statuscode'] == 0:
            ways = []

            for leg in data['route']['legs']:
                for maneuver in leg['maneuvers']:
                    way = Way()
                    way.direction = maneuver['directionName']
                    way.lat = maneuver['startPoint']['lat']
                    way.lon = maneuver['startPoint']['lng']
                    way.narrative = maneuver['narrative']
                    way.icon_url = maneuver['iconUrl']
                    way.distance = "%.02f" % maneuver['distance']
                    way.time = format_time(maneuver['time'])
                    ways.append(way)

            for i, way in enumerate(ways):
                icon_filename = self.icon_downloader.download(way.icon_url)
                icon = GdkPixbuf.Pixbuf.new_from_file(icon_filename)
                marker = Champlain.Label.new_from_file(icon_filename)
                number = i + 1
                #marker.set_text("%d: %s" % (number, way.direction))
                marker.set_location(way.lat, way.lon)
                self.marker_layer.add_marker(marker)
                self.store.append([number, icon, way.narrative, way.distance, way.time, marker])

        else:
            return ", ".join(data['info']['messages'])



class Searcher(object):

    def __init__(self, marker_layer, resultstore):
        super(Searcher, self).__init__()
        self.store = resultstore
        self.marker_layer = marker_layer
        #self.mapwidget.add_layer(self.marker_layer)

    def search(self, query, limit=6):
        headers = { 'User-Agent' : 'StrekmannMapSearch/0.1' }
        req = urllib2.Request(
                'http://open.mapquestapi.com/nominatim/v1/search?format=json&q=%s&limit=%d' % (urllib2.quote(query), limit),
                headers=headers,
                )
        response = urllib2.urlopen(req).read()

        data = json.loads(response)
        #data = json.load(open("search_results.json"))

        if len(data):
            #searchiter = self.store.append(["Search %s" % query, True, self])
            for i, result in enumerate(data):
                marker = Champlain.Label()
                number = i + 1
                marker.set_text(str(number))
                lat = float(result['lat'])
                lon = float(result['lon'])
                marker.set_location(lat, lon)
                name = result['display_name']
                #_class = result['class']
                self.store.append([number, name, marker])
                self.marker_layer.add_marker(marker)
