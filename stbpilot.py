import cherrypy
import os, os.path
import time
import sys
import simplejson
from jinja2 import Environment, FileSystemLoader

import multiprocessing

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
	def __init__(self, homecoords=None):
		self.api = local_connect()
		self.vehicle = self.api.get_vehicles()[0]
		self.commands = self.vehicle.commands
		self.homecoords = homecoords
		self._log("StBernard spawned")

	def _log(self, message):
		print "[SBDEBUG]: {0}".format(message)

	def get_location(self):
		return [self.vehicle.location.lon, self.vehicle.location.lat]
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
		self._log('Instantiating template')
		self.templates = Templates()
		self._log('Instantiated')

	def _log(self, message):
		print "[APPDEBUG]: {0}".format(message)

	@cherrypy.expose
	def start(self):
		params = [self.droid.vehicle.location.lon, self.droid.vehicle.location.lat]
		return self.templates.start(self.flightarea,params)

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def vehicle(self):
		position = self.droid.get_location()
		self._log(position)
		return dict(position=self.droid.get_location())
#--SbApp-----------------------------------------------------

class Sensor(multiprocessing.Process):
	def run(self):
		while True:
			#print 'Worker running'
			#sys.stdout.flush()
			time.sleep(1)
		return

def _log(message):
	print "[MAINDEBUG]: {0}".format(message)

def loadFlightArea(filename = ''):
	json_data = open(filename).read()
	return simplejson.loads(json_data)

#__main__
_log('Spawning StBernard')
rex = StBernard()
_log('St Bernard Spawned')

_log('Loading flight area')
flightArea = loadFlightArea(configPath + configFile)
_log(' loaded : ' + str(flightArea))

sensoring = Sensor()
sensoring.daemon = True
sensoring.start()


cherrypy.tree.mount(SbApp(rex, flightArea), '/', config=cherrypy_conf)

cherrypy.config.update({
            'server.socket_port': host_port,
            'server.socket_host': host_ip,
            'log.screen': False
         })

cherrypy.engine.start()
cherrypy.engine.block()

