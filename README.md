#Saint-Bernard Pilot

Python script based on dronekit api
Necessitates cherrypy, jinja2


Run in a mavproxy console (connected to a working vehicle):
api start stbpilot.py


|--html
|  |-start.html //main page
|  |-scripts.html //includes external js and css
|  |-tiles.html //renders the map
| 
|--assets
|  |-img
|  |-css
|  |-js //local storage of jQuery and leaflet
|  |-maptiles //tiles for the areas to be rendered localy
|  |-flightarea.json //json file containing the definition of the flight area and included filezones, with the necessary options for leaflet to display properly
| 
|-stbpilot.py //main code
|-README.md //this file


As of V0.1:
Will start serving on 127.0.0.1:8080/start : a map of the flight area considered, with the drone on the map and gps coordinates values, updated every 0.5s


