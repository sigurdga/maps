Maps
====

Early works on a generic map application for Gnome or Ubuntu. Gnome has
an application like this in it's pipeline, in early design phase. I
just wanted to see how far I could get on my own. And then I saw this
Ubuntu application showdown a bit late.

This application uses Mapquest for search and directions search, the open API
using Openstreetmap data. Maps are standard tiles from Openstreetmap. I'm a
mapper myself, and I think there is room for an application like this.

It will also show GPX tracks if you drag them to the Ubuntu launcher or
to an open program.

When viewing results, in most cases a single click in the result
listing will highlight the result. For searches, a double click will
save the location to 'My places'. During directions search, a double
click in the results will set proper locations to be able to search for
directions.

This is only a start… localization, icons, save 'my places' and drag
and drop from 'my places' to direction search fields, are planned.

Run from source
---------------

Run it with quickly run from the project folder, having quickly installed. I
will fix a runnable main without quickly pretty soon.

Packages
--------

Ubuntu PPA: https://launchpad.net/~sigurdga/+archive/maps

APIs used
---------

* [Mapquest Open Nominatim v1](http://open.mapquestapi.com/nominatim/)
* [Mapquest Open Directions v2](http://open.mapquestapi.com/directions/)

Contributions
-------------

Contributions are very welcome.
