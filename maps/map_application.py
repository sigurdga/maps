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

from gi.repository import Gtk, Gio, GtkClutter, Clutter
GtkClutter.init([])
from gi.repository import Champlain, GtkChamplain

import os
import tempfile

import locale
from locale import gettext as _
locale.textdomain('maps')

from maps_lib import get_version
from maps.map_window import MapWindow
from maps.gpx_track import GpxTrack


class MapApplication(Gtk.Application):

    BASE_KEY = "net.launchpad.maps"

    def __init__(self, files):
        Gtk.Application.__init__(self, application_id=self.BASE_KEY,
                flags=Gio.ApplicationFlags.HANDLES_OPEN)

        self.settings = Gio.Settings.new(self.BASE_KEY)
        self.latitude = self.settings.get_double("latitude")
        self.longitude = self.settings.get_double("longitude")
        self.zoom = self.settings.get_int("zoom")

        self.embed = GtkChamplain.Embed()
        self.view = self.embed.get_view()
        self.view.set_kinetic_mode(True)
        self.view.set_zoom_level(self.zoom)
        self.view.center_on(self.latitude, self.longitude)
        scale = Champlain.Scale()
        scale.connect_view(self.view)
        self.view.bin_layout_add(scale, Clutter.BinAlignment.START,
                Clutter.BinAlignment.END)

        self.files = files
        tempdir = tempfile.gettempdir()
        self.icon_cache = os.path.join(tempdir, "maps-icon-cache")
        if not os.path.exists(self.icon_cache):
            os.makedirs(self.icon_cache)

        #######
        # About
        #######

        self.about = Gtk.AboutDialog()
        self.about.set_program_name(_("Maps"))
        self.about.set_title(_("About Maps"))
        self.about.set_authors(["Sigurd Gartmann <sigurdga-ubuntu@sigurdga.no>"])
        self.about.set_copyright(_("Copyright © 2012 Sigurd Gartmann <sigurdga-ubuntu@sigurdga.no>"))
        self.about.set_wrap_license(True)
        self.about.set_comments(_(
        "Early works on a generic map application for Gnome or Ubuntu.\n\n"

        "This application uses Mapquest Open for search and directions search,"
        "and standard tiles from Openstreetmap. I'm a mapper myself, and I think"
        "there is room for an application like this.\n\n"

        "It will also show GPX tracks if you drag them to the Ubuntu launcher or"
        "to an open program.\n\n"

        "When viewing results, in most cases a single click in the result"
        "listing will highlight the result. For searches, a double click will"
        "save the location to 'My places'. During directions search, a double"
        "click in the results will set proper locations to be able to search for"
        "directions."
        ))
        #self.about.set_license("GPL 3+")
        self.about.set_version(get_version())

        self.about.connect("response", self.dialog_response)

    def dialog_response(self, widget, response_id):
        widget.hide()

    def on_about(self, action, parameter):
        self.about.show()

    def do_startup(self):
        Gtk.Application.do_startup(self)

        open_action = Gio.SimpleAction.new("open", None)
        about_action = Gio.SimpleAction.new("about", None)
        quit_action = Gio.SimpleAction.new("quit", None)
        open_action.connect("activate", self.on_open)
        about_action.connect("activate", self.on_about)
        quit_action.connect("activate", self.on_quit)
        self.add_action(open_action)
        self.add_action(about_action)
        self.add_action(quit_action)
        menu = Gio.Menu()
        menu.append(_("Open track"), "app.open")
        menu.append(_("About Maps"), "app.about")
        menu.append(_("Quit"), "app.quit")
        self.set_app_menu(menu)

    def do_activate(self):
        self.window = MapWindow(self, self.embed)

    def do_open(self, file_list, file_count, hint):
        self.window = MapWindow(self, self.embed)

        # FIXME: file_list is empty, why?
        # Fetching files from constructor
        for gpx_file in self.files[-file_count:]:
            try:
                g = GpxTrack(self.window.view, self.window.store)
                g.import_file(gpx_file)
            except:
                print("ERROR: %s was not a functional GPX file")

    def on_quit(self, action, parameter):
        self.save()
        self.quit()

    def on_open(self, action, parameter):
        if hasattr(self.window, "on_import_clicked"):
            self.window.on_import_clicked(action)


    #def do_startup(self):
        #Gtk.Application.do_startup(self)

    def save(self):
        self.settings.set_double("latitude",
                self.view.get_center_latitude())
        self.settings.set_double("longitude",
                self.view.get_center_longitude())
        self.settings.set_int("zoom", self.view.get_zoom_level())

def main():

    import sys

    # FIXME: Needs sys.argv two places, as do_open is not able to get the file
    # list
    application = MapApplication(sys.argv)
    exit_status = application.run(sys.argv)
    sys.exit(exit_status)

if __name__ == "__main__":
    main()
