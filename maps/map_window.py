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


from gi.repository import Gtk, Gdk, GdkPixbuf, Champlain

from maps.searcher import Searcher, Guide, ResultView
from maps.gpx_track import GpxTrack

class SearchLayer(Champlain.MarkerLayer):

    def __init__(self, mapview, *args, **kwargs):
        super(SearchLayer, self).__init__(*args, **kwargs)
        self.mapview = mapview

    def show(self, *args, **kwargs):
        bbox = self.get_bounding_box()
        self.mapview.ensure_visible(bbox, True)
        super(SearchLayer, self).show(*args, **kwargs)


class PlaceLayer(Champlain.MarkerLayer):
    def __init__(self, mapview, *args, **kwargs):
        super(PlaceLayer, self).__init__(*args, **kwargs)
        self.mapview = mapview

class MarkerEntry(Gtk.Entry):
    def __init__(self, *args, **kwargs):
        self.marker = None
        super(MarkerEntry, self).__init__(*args, **kwargs)

    def set_marker(self, marker):
        self.marker = marker

    def get_marker(self):
        return self.marker

    def unset_marker(self):
        self.marker = None


class MapWindow(Gtk.ApplicationWindow):

    def __init__(self, application, mapwidget):
        Gtk.Window.__init__(self, title="Maps", application=application)
        self.application = application
        self.settings = application.settings
        self.application.window = self
        self.view = mapwidget.get_view()

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.add(vbox)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(toolbar, False, False, 0)

        self.sidebartogglebutton = Gtk.ToggleButton(label="More")
        self.sidebartogglebutton.connect("toggled", self.on_sidebar_toggle, "1")
        toolbar.pack_end(self.sidebartogglebutton, False, False, 0)

        markerstogglebutton = Gtk.ToggleButton(label="Show markers")
        toolbar.pack_end(markerstogglebutton, False, False, 5)

        searchradiobutton = Gtk.ToggleButton(label="Search")
        directionsradiobutton = Gtk.ToggleButton(label="Directions")
        searchfield = Gtk.Entry()
        searchfield.set_placeholder_text("Search")
        searchbutton = Gtk.Button(label="Search")
        searchbutton.set_can_default(True)
        fromfield = MarkerEntry()
        fromfield.set_placeholder_text("From")
        tofield = MarkerEntry()
        tofield.set_placeholder_text("To")
        directionsbutton = Gtk.Button(label="Search")
        directionsbutton.set_can_default(True)

        searchradiobutton.connect("clicked", self.on_searchradiobutton_clicked, directionsradiobutton, searchfield, searchbutton, directionsbutton)
        directionsradiobutton.connect("clicked", self.on_directionsradiobutton_clicked, searchradiobutton, fromfield, tofield, directionsbutton)
        searchradiobutton.set_active(True)
        toolbar.pack_start(searchradiobutton, False, False, 0)
        toolbar.pack_start(directionsradiobutton, False, False, 0)

        searchfield.set_activates_default(True)
        toolbar.pack_start(searchfield, True, True, 0)

        toolbar.pack_start(searchbutton, False, False, 0)

        fromfield.set_activates_default(True)
        tofield.set_activates_default(True)

        toolbar.pack_start(fromfield, True, True, 0)
        toolbar.pack_start(tofield, True, True, 0)
        toolbar.pack_start(directionsbutton, False, False, 0)

        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(hpaned, True, True, 0)

        #preferences_action = Gio.SimpleAction.new("preferences", None)
        #preferences_action.connect("activate", self.preferences_cb)
        #application.add_action(preferences_action)

        # Will add locale search and other directions preferences later

        searchmarkers = SearchLayer(self.view)
        placemarkers = PlaceLayer(self.view)
        directionmarkers = SearchLayer(self.view)
        self.view.add_layer(searchmarkers)
        self.view.add_layer(placemarkers)
        self.view.add_layer(directionmarkers)
        license = self.view.get_license_actor()
        license.set_extra_text("Search and directions from Mapquest Open")
        mapwidget.set_size_request(640, 480)

        self.connect('drag-data-received', self.on_drag_data_received)

        DRAG_ACTION = Gdk.DragAction.COPY
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], DRAG_ACTION)
        self.drag_dest_add_text_targets()


        #bbox = self.path_layer.get_bounding_box()
        #self.view.ensure_visible(bbox, True)

        # stop

        vpaned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        hpaned.pack1(vpaned, True, True)

        vpaned.pack2(mapwidget)

        ########
        # Search
        ########

        searchstore = Gtk.ListStore(int, str, object)
        searchlist = Gtk.TreeView(searchstore)
        searchlist.set_headers_visible(False)
        searchselection = searchlist.get_selection()
        searchselection.connect('changed', self.on_result_clicked)
        #searchlist.connect("button-press-event", self.on_cell_clicked)

        renderer_number = Gtk.CellRendererText()
        renderer_result = Gtk.CellRendererText()
        column_number = Gtk.TreeViewColumn("#", renderer_number, text=0)
        column_result = Gtk.TreeViewColumn("Result", renderer_result, text=1)

        searchlist.append_column(column_number)
        searchlist.append_column(column_result)

        searchheader = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        searchlabel = Gtk.Label()
        searchheader.pack_start(searchlabel, True, True, 0)

        searchexit = Gtk.Button(label="Close")
        searchheader.pack_end(searchexit, False, False, 0)

        searchview = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        searchview.pack_start(searchheader, False, False, 0)

        swH_search = Gtk.ScrolledWindow() ## ADD THE SCROLLBAR
        swH_search.set_vexpand(False)
        swH_search.add(searchlist)
        searchview.pack_end(swH_search, True, True, 0)

        vpaned.pack1(searchview)

        ############
        # Directions
        ############

        directionstore = Gtk.ListStore(int, GdkPixbuf.Pixbuf, str, str, str, object)
        directionlist = Gtk.TreeView(directionstore)

        renderer_text = Gtk.CellRendererText()
        renderer_right = Gtk.CellRendererText()
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        renderer_right.set_property("xalign", 1)
        column_number = Gtk.TreeViewColumn("#", renderer_text, text=0)
        column_icon = Gtk.TreeViewColumn("", renderer_pixbuf, pixbuf=1)
        column_narrative = Gtk.TreeViewColumn("Directions", renderer_text, text=2)
        column_narrative.set_expand(True)
        column_distance = Gtk.TreeViewColumn("Distance", renderer_right, text=3)
        column_time = Gtk.TreeViewColumn("Time", renderer_right, text=4)
        column_distance.set_alignment(1)
        column_time.set_alignment(1)
        directionlist.append_column(column_number)
        directionlist.append_column(column_icon)
        directionlist.append_column(column_narrative)
        directionlist.append_column(column_time)
        directionlist.append_column(column_distance)

        swH_direction = Gtk.ScrolledWindow() ## ADD THE SCROLLBAR
        swH_direction.set_vexpand(False)
        swH_direction.add(directionlist)
        searchview.pack_end(swH_direction, True, True, 0)

        ########
        # Places
        ########

        placestore = Gtk.ListStore(str, object) # name, marker
        placelist = Gtk.TreeView(placestore)

        render_name = Gtk.CellRendererText()
        render_name.set_property("editable", True)
        render_name.connect("edited", self.on_marker_edited, placestore)
        column_name = Gtk.TreeViewColumn("Places", render_name, text=0)
        placelist.append_column(column_name)

        ########
        # Tracks
        ########

        self.trackstore = Gtk.ListStore(str, bool, object)  # name, boolean, track
        tracklist = Gtk.TreeView(self.trackstore)

        render_name = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn("Tracks", render_name, text=0)
        tracklist.append_column(column_name)

        # Other

        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        markerbutton = Gtk.Button(label="Mark place")
        self.sidebar.pack_start(markerbutton, False, False, 10)
        self.sidebar.pack_start(placelist, False, False, 0)
        self.sidebar.pack_start(tracklist, False, False, 0)

        hpaned.pack2(self.sidebar, False, False)

        resultview = ResultView(searchlabel, searchview, searchstore, searchmarkers, directionstore, directionmarkers)

        markerstogglebutton.connect("toggled", self.on_markers_toggle, "1", placemarkers)
        searchlist.connect("row-activated", self.on_row_activated, searchselection, placelist, placemarkers, resultview, directionsradiobutton, fromfield, tofield)
        searchbutton.connect("clicked", self.on_search_clicked, searchfield, resultview)
        directionsbutton.connect("clicked", self.on_directions_clicked, fromfield, tofield, resultview, directionmarkers, directionlist)
        searchexit.connect('clicked', self.on_searchexit_clicked, resultview)
        searchfield.connect("event", self.on_searchfield_clicked, resultview)
        fromfield.connect("event", self.on_searchfield_clicked, resultview)
        tofield.connect("event", self.on_searchfield_clicked, resultview)

        markerbutton.connect("clicked", self.on_add_marker_click, placemarkers, placelist, markerstogglebutton)
        #self.markersbutton.connect("clicked", self.on_test_directions, directionmarkers, resultview, directionlist)
        self.connect("delete-event", self.application.on_quit)

        ###############
        # Show and hide
        ###############

        #self.set_wmclass("Maps", "Maps")
        self.show_all()
        self.sidebar.hide()
        fromfield.hide()
        tofield.hide()
        directionsbutton.hide()
        searchview.hide()


    #def __on_entry_clicked(self, widget, event, data=None):
    #    if event.type == gtk.gdk.BUTTON_RELEASE:

    #def on_cell_toggled(self, widget, path):
        #if self.store[path][1]:
            #self.store[path][1] = False
            #self.store[path][2].hide()
        #else:
            #self.store[path][1] = True
            #self.store[path][2].show()

    def on_drag_data_received(self, window, context, x, y, data, info, time):
        g = GpxTrack(self.view, self.trackstore)
        g.import_file(data.get_text().strip())

    def on_result_clicked(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter != None:
            model[treeiter][2].animate_in()

    def on_store_changed(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter != None:
            try:
                model[treeiter][2].go_to()
            except:
                model[treeiter][2].animate_in()

    def on_row_activated(self, treeview, treeiter, path, selection, places, placemarkers, resultview, directionsradiobutton, fromfield, tofield):
        """
        On double clicking a search / directions search result, add to my
        places or to/from fields. The to/from fields does have a hidden marker
        each that is blanked out on a mouse click in the field.

        If we are searching for directions, and have both a from and to
        location (with hidden marker set), we will do the directions search.
        """

        model, treeiter = selection.get_selected()
        if treeiter != None:
            if directionsradiobutton.get_active():
                if tofield.get_text() and not tofield.get_marker():
                    tofield.set_marker(model[treeiter][2])
                    tofield.set_text(model[treeiter][1])
                else:
                    fromfield.set_marker(model[treeiter][2])
                    fromfield.set_text(model[treeiter][1])
            else:
                name = model[treeiter][1]
                name = name.split(",")[0]
                marker = model[treeiter][2]
                marker.set_text(name)
                places.get_model().prepend([name, marker])
                resultview.marker_layer.remove_marker(marker)
                placemarkers.add_marker(marker)
                self.sidebartogglebutton.set_active(True)

            resultview.clear()
            resultview.hide()
            placemarkers.show()

    #def on_cell_clicked(self, widget, event):
        #if event.button == 1 and event.type == Gdk.BUTTON_PRESS:
        #    print "Double clicked on cell"
        #print "HEI"
        #if event.type == Gdk.EventType._2BUTTON_PRESS:
            #print "DOBBEL"

    #def dialog_response(self, widget, response_id):
        #if response_id == Gtk.ResponseType.OK:
		    #print "*boom*"
        #elif response_id == Gtk.ResponseType.CANCEL:
            #print "good choice"
        #elif response_id == Gtk.ResponseType.DELETE_EVENT:
            #print "dialog closed or cancelled"
        #widget.destroy()

    #def preferences_cb(self, action, parameter):
        #messagedialog = Gtk.MessageDialog(self,
                #Gtk.DialogFlags.MODAL,
                #Gtk.MessageType.WARNING,
                #Gtk.ButtonsType.OK_CANCEL,
                #"What is this",
                #)
        #messagedialog.connect("response", self.dialog_response)
        #messagedialog.show()

    def on_sidebar_toggle(self, button, name):
        if button.get_active():
            self.sidebar.show()
        else:
            self.sidebar.hide()

    def on_searchradiobutton_clicked(self, button, otherbutton, searchfield, searchbutton, directionsbutton):
        if button.get_active():
            otherbutton.set_active(False)
            searchfield.show()
            searchbutton.show()
            self.set_default(searchbutton)
        else:
            searchfield.hide()
            searchbutton.hide()
            otherbutton.set_active(True)
            self.set_default(directionsbutton)

    def on_directionsradiobutton_clicked(self, button, otherbutton, fromfield, tofield, directionsbutton):
        if button.get_active():
            otherbutton.set_active(False)
            fromfield.show()
            tofield.show()
            directionsbutton.show()
        else:
            fromfield.hide()
            tofield.hide()
            directionsbutton.hide()
            otherbutton.set_active(True)

    def on_searchfield_clicked(self, widget, event, searchview=None):
        if searchview and event.type == Gdk.EventType.BUTTON_RELEASE:
            searchview.clear()
            searchview.hide()
            if isinstance(widget, MarkerEntry):
                widget.unset_marker()

    def on_searchexit_clicked(self, button, resultview):
        resultview.hide()
        resultview.clear()

    def on_markers_toggle(self, button, state, place_markers):
        if button.get_active():
            place_markers.show()
        else:
            place_markers.hide()

    def on_add_marker_click(self, button, marker_layer, marker_list, marker_toggle):

        name = "Marker"
        marker_toggle.set_active(True)
        marker_store = marker_list.get_model()
        marker = Champlain.Label()
        latitude = self.view.get_center_latitude()
        longitude = self.view.get_center_longitude()
        marker.set_location(latitude, longitude)
        marker.set_draggable(True)
        marker.set_selectable(True)
        marker_layer.add_marker(marker)
        marker_store.prepend([name, marker])
        marker.set_text(name)
        marker_list.set_cursor(0, column=marker_list.get_column(0), start_editing=True)

    def on_marker_edited(self, cell, path, text, model):
        if path != None and text != "":
            model[path][1].set_text(text)
            model[path][0] = text

    def on_import_clicked(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a file", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        self.add_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            track = GpxTrack(self.view, self.store)
            track.import_file(dialog.get_filename())
            track.show()
            track.go_to()
            self.sidebartogglebutton.set_active(True)

        elif response == Gtk.ResponseType.CANCEL:
            print "Cancel clicked"

        dialog.destroy()

    def on_search_clicked(self, widget, searchfield, resultview):
        marker_layer = resultview.marker_layer
        searcher = Searcher(marker_layer, resultview.liststore)
        text = searchfield.get_text()
        searcher.search(text)
        resultview.show("Results for: %s" % text, 2) ## 2 -> show search results

        marker_layer.show()

    def on_directions_clicked(self, widget, fromfield, tofield, resultview, marker_layer, directionlist):
        if fromfield.marker and tofield.marker:
            # do directions lookup
            guide = Guide(self.application, marker_layer, directionlist.get_model())
            error = guide.search(fromfield.get_marker(), tofield.get_marker())
            if not error:
                marker_layer.show()
                resultview.show("Directions", 1) ## 1 -> show directions
                directionlist.show()
            else:
                resultview.show(error, 1) ## 1 -> show directions
        else:
            marker_layer = resultview.marker_layer
            if tofield.get_text() and not tofield.get_marker():
                searcher = Searcher(marker_layer, resultview.liststore)
                text = tofield.get_text()
                searcher.search(text)
                resultview.show("Possible destination locations named: %s" % text, 2) ## 2 -> show search results
                marker_layer.show()
            elif fromfield.get_text() and not fromfield.get_marker():
                searcher = Searcher(marker_layer, resultview.liststore)
                text = fromfield.get_text()
                searcher.search(text)
                resultview.show("Possible departure locations named: %s" % text, 2) ## 2 -> show search results
                marker_layer.show()
            else:
                print "Invalid search"

    def on_test_directions(self, widget, marker_layer, resultview, directionlist):
        guide = Guide(self.application, marker_layer, directionlist.get_model())
        guide.search(1,1)
        marker_layer.show()
        resultview.show("Directions", 1) ## 1 -> show directions
        directionlist.show()

    def add_filters(self, dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name("GPX tracks")
        filter_text.add_pattern("*.gpx")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

