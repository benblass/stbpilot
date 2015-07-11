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
		return [self.vehicle.location.lat, self.vehicle.location.lon]
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

	def index(self):
		self.options = self.get_options()
		return self.get_template('index')

	def map(self, params):
		self.options['vehicle_location'] = params
		self.options['flight_zone'] = 'leschaux'
		return self.get_template('map')

	def start(self, vehicle_location= None):

		#[TODO] put all this definition in a separate config file

		self.options["flight_area"] = {
			"name" : "leschaux",
			"display_options" : {
					"center_coords" : [45.7683329, 6.1365896],
					"zoom_level" : 18,
					"maxZoom" : 19,
				"minZoom": 17
				},
			"flight_zones" : [{
								"name" : "leschaux",
								"polygon": [[45.769319,6.134946],
											[45.768784,6.135258],
											[45.768565,6.134477],
											[45.768628,6.13397],
											[45.768501,6.133579],
											[45.768909,6.133249],
											[45.769319,6.134946]],
								"intial_search": []
							},
							 {
							 	"name": "laclusaz",
							 	"polygon": [[45.77,6.134946],
											[45.77879,6.135258],
											[45.77854,6.134477],
											[45.77863,6.13397],
											[45.77852,6.133579],
											[45.76891,6.133249],
											[45.76933,6.134946]],
								"intial_search": []
							 }
							]
		}

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
	def __init__(self,stbernard=None):

		self.droid = stbernard
		print '[SBDEBUG] Instantiating template'
		self.templates = Templates()
		print '[SBDEBUG] Instantiated'
	
	@cherrypy.expose
	def map(self):
		params = [self.droid.vehicle.location.lat, self.droid.vehicle.location.lon]
		return self.templates.map(params)

	@cherrypy.expose
	def start(self):
		params = [self.droid.vehicle.location.lat, self.droid.vehicle.location.lon]
		return self.templates.start(params)

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def vehicle(self):
		return dict(position=self.droid.get_location())
#--SbApp-----------------------------------------------------

class Sensor(multiprocessing.Process):
	def run(self):
		while True:
			#print 'Worker running'
			#sys.stdout.flush()
			time.sleep(1)
		return


#__main__
print '[SBDEBUG] Spawning StBernard'
Rex = StBernard()
print '[SBDEBUG] Spawned'

sensoring = Sensor()
sensoring.daemon = True
sensoring.start()


cherrypy.tree.mount(SbApp(Rex), '/', config=cherrypy_conf)

cherrypy.config.update({
            'server.socket_port': host_port,
            'server.socket_host': host_ip,
            'log.screen': False
         })

cherrypy.engine.start()
cherrypy.engine.block()

