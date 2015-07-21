import cherrypy
import os, os.path
import time
from datetime import datetime
import sys
import math
import simplejson
from jinja2 import Environment, FileSystemLoader

from pydblite.sqlite import Database, Table

from pymavlink import mavutil
import droneapi.lib
from droneapi.lib import VehicleMode, Location, Command

host_ip = '0.0.0.0'
host_port = 8080

cherrypy_conf = {
	'/': {
		'tools.sessions.on': False,
		'tools.staticdir.root': local_path
	},
	'/static' :{
		'tools.staticdir.on': True,
		'tools.staticdir.dir': './assets'
	}
}

configPath = 'assets/'
configFile = 'flightarea.json'

#default drone configuration

#////////////////////////////////////////////////////////////////

class StBernard(object):
	def __init__(self, sense_db_path, homecoords=None):
		self.api = local_connect()
		self.vehicle = self.api.get_vehicles()[0]
		self.commands = self.vehicle.commands
		self.homecoords = homecoords
		self.search_target = 0
		self.search_waypoints = []
		self.search_altitude = 0
		self._log("StBernard spawned")

		self.sense_db_path = sense_db_path
		sense_db = Database(self.sense_db_path)
		sense_table = Table('sensing_data', sense_db)
		sense_table.create(('timestamp', 'REAL'), ('signal', 'REAL'), ('lat','REAL'),('lon','REAL'), mode="override")
		sense_table.commit()

		#self.vehicle.add_attribute_observer('armed', self.armed_callback)
		#self.vehicle.add_attribute_observer('mode', self.mode_callback)

	def _debug(self, message):
		print "[SBDEBUG]: {0}".format(message)
	
	def _log(self, message):
		_console(message)
		print "[SB]: {0}".format(message)

	def get_location(self):
		return [self.vehicle.location.lon, self.vehicle.location.lat]

	def get_search_waypoints(self):
		return self.search_waypoints

	def get_search_altitude(self):
		return self.search_altitude

	def get_search_target(self):
		return self.search_target

	#////Flight and operation functions
	def takeoff(self, toAltitude):
		self._log('Saint-Bernard taking off')
		self.commands.takeoff(toAltitude)
		self.vehicle.flush()

	def arm(self, toggle=True):
		if toggle:
			self._log('Arming')
		else:
			self._log('Disarming')
		self.vehicle.armed = True
		self.vehicle.flush()

	def change_mode(self, mode):
		self._log("Switching to mode: {0}".format(mode))
		self.vehicle.mode = VehicleMode(mode)
		self.vehicle.flush()

	def goto(self, location, altitude, relative=None):
		self._log('Goto: {0}, {1}'.format(location, altitude))

		self.vehicle.commands.goto(
			Location(
				float(location[1]), float(location[0]),
				float(altitude),
				is_relative = relative
			)
		)
		self.vehicle.flush()

	#///Utility functions
	def wait_pt_reached(self, location, log=False):
		while self.vehicle.mode.name == 'GUIDED' and self.vehicle.armed:
			distance = self.get_distance_meters([self.vehicle.location.lon, self.vehicle.location.lat], location)
			if log:
				self._log( str(distance)+'m remaining')
			if distance < 1:
				self._log('WP reached')
				break;
			time.sleep(1)

	def get_distance_meters(self,location1, location2):

		dlat = location1[1]-location2[1]
		dlong = location1[0]-location2[0]

		return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5

	#///Mission methods
	def load_fz_waypoints(self):

		initial_wp = targetFlightZone['initial_search']
		initial_alt = targetFlightZone['initial_search_alt']
		
		self._log('Waypoints loaded for '+targetFlightZone['flname'])

		return {'waypoints' : initial_wp, 'altitude': initial_alt}

	def sense(self):
		time.sleep(1.5)
		sense_db = Database(self.sense_db_path)
		sense_table = Table('sensing_data', sense_db)
		sense_table.open()
		sense_table.insert(timestamp=time.time(), signal=0, lat=self.vehicle.location.lat, lon =self.vehicle.location.lon)
		sense_table.commit()
		return

	def initiate_search(self):
		profile = self.load_fz_waypoints()
		self.search_waypoints = profile['waypoints']
		self.search_altitude = profile['altitude']

		self._log('Taking off')
		self.change_mode('GUIDED')
		self.arm()

		while not(self.vehicle.armed):
			pass
		self.takeoff(self.search_altitude)

		self._log('Proceeding through flight plan')


		RDV_point = True
		for wp in self.search_waypoints:
			self.search_target = self.search_waypoints.index(wp)
			self.goto(wp, self.search_altitude)
			self.wait_pt_reached(wp, False)
			self.sense()

	#//////Observers and callbacks
	#// I did not get how obsevers work (or do not work in dronekit, so commented out for now)
"""
	def armed_callback(self, armed):
		self._log("Armed !")
		self.vehicle.remove_attribute_observer('armed', self.armed_callback)
		self.vehicle.add_attribute_observer('disarmed', self.disarmed_callback)

	def disarmed_callback(self, disarmed):
		self._log('Disarmed !')
		self.vehicle.remove_attribute_observer('disarmed', self.armed_callback)
		self.vehicle.add_attribute_observer('armed', self.armed_callback)

	def mode_callback(self, mode):
		self._log("Now in mode {0}".format(self.vehicle.mode))
"""
#--StBernard-----------------------------------------------------

#////////////////////////////////////////////////////////////////
class Templates:
	def __init__(self, home_coords = None):
		self.home_coords = home_coords
		self.options = self.get_options()
		self.environment = Environment(loader=FileSystemLoader( local_path + '/html/'))

	def get_options(self):
			return {
					'vehicle_location': [],
					'flight_area': {}
			}
	def _log(self, message):
		print("[TMPDEBUG]: {0}".format(message))

	def index(self):
		self.options = self.get_options()
		return self.get_template('index')

	def map(self, params):
		self.options['vehicle_location'] = params
		self.options['flight_zone'] = 'leschaux'
		return self.get_template('map')

	def start(self, flight_area = None, vehicle_location= None):
		#[TODO] put all this definition in a separate config file
		self.options['flight_area'] = flight_area
		self.options['vehicle_location'] = vehicle_location
		return self.get_template('start')

	def get_template(self, filename):
		template = self.environment.get_template(filename + '.html')
		return template.render(options = self.options)
#--Templates-----------------------------------------------------

#////////////////////////////////////////////////////////////////
class SbApp(object):
	""" 
		Main Appp. Initiates a corresponding St-Bernard, Initiates the templates and serves the application URLs

	"""
	def __init__(self,stbernard=None,flightarea=None):

		self.droid = stbernard
		self.flightarea = flightarea
		self._debug('Instantiating template')
		self.templates = Templates()
		self._debug('Instantiated')

	def _debug(self, message):
		print "[APPDEBUG]: {0}".format(message)

	def _log(self, message):
		_console(message)
		print "[APP]: {0}".format(message)

	def get_search_data(self):
		sense_db = Database('sensor/flight.db')
		sense_table = Table('sensing_data', sense_db)
		sense_table.open()
		search_data = [r for r in sense_table]
		return search_data

	@cherrypy.expose
	def start(self):
		params = [self.droid.vehicle.location.lon, self.droid.vehicle.location.lat]
		return self.templates.start(self.flightarea,params)

	@cherrypy.expose
	def initial_search(self,flindex):
		global targetFlightZone
		targetFlightZone = flightArea['flight_zones']['features'][int(flindex)]['properties']
		self._log('Initial Search started to ' + targetFlightZone['flname'])
		self.droid.initiate_search()
		return

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def search_data(self):
		return dict(data = self.get_search_data())

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def search_status(self):
		return dict(waypoints = self.droid.get_search_waypoints(), target = self.droid.get_search_target(), altitude = self.droid.get_search_altitude(), search_data = self.get_search_data())

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def vehicle(self):
		return dict(position=self.droid.get_location(), console = console)
#--SbApp-----------------------------------------------------


#--/////////////////////////////////////////////////////////

def _log(message):
	print "[MAINDEBUG]: {0}".format(message)

def loadFlightArea(filename = ''):
	json_data = open(filename).read()
	return simplejson.loads(json_data)

def _console(message):
	global console
	console = console + time.strftime("%c") + " : " + format(message) +'\n'
	return


#__main__

console = time.strftime("%c") + "Initating console \n"

_log('Spawning StBernard')
rex = StBernard('sensor/flight.db')
_log('St Bernard Spawned')

_log('Loading flight area')
flightArea = loadFlightArea(configPath + configFile)
_log(' loaded flight area')

cherrypy.tree.mount(SbApp(rex, flightArea), '/', config=cherrypy_conf)

cherrypy.config.update({
            'server.socket_port': host_port,
            'server.socket_host': host_ip,
            'log.screen': False,
            'server.logToScreen': False,
            'environment': 'embedded'
         })
#Supressses all cherrypy output to ease debugging
cherrypy.log.error_log.propagate = False
cherrypy.log.access_log.propagate = False

cherrypy.engine.start()
cherrypy.engine.block()

