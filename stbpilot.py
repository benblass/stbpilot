import cherrypy
import os
import os.path
import time
import math

from pydblite.sqlite import Database, Table

from dronekit import connect
from dronekit.lib import VehicleMode, Location

# cherrypy configuration

host_ip = '0.0.0.0'
host_port = 8080

local_path = os.path.dirname(os.path.abspath(__file__))
print local_path

cherrypy_conf = {
    '/': {
        'tools.sessions.on': False,
        'tools.staticdir.root': local_path
    },
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': './assets'
    }
}

# default drone configuration

MASTER = '10.0.2.15:14553'

# Antennas orientation compared to drone frame. Theta: in yaw, phi: in pitch
antenna_1_framephi = 0
antenna_1_frametheta = 0

antenna_2_framephi = math.pi / 2
antenna_2_frametheta = 0

# ////////////////////////////////////////////////////////////////


class StBernard(object):
    """
    Object representing the autopilot.
    """
    def __init__(self, sense_db_path, master, homecoords=None):
        self._log("Connecting")
        self.vehicle = connect(master, await_params=True)
        self.commands = self.vehicle.commands
        self.homecoords = homecoords
        self._log("StBernard spawned")

        self.sense_db_path = sense_db_path
        sense_db = Database(self.sense_db_path)
        sense_table = Table('sensing_data', sense_db)
        sense_table.create(
            ('timestamp', 'REAL'), ('signal_ant1', 'REAL'),
            ('signal_ant2', 'REAL'), ('signal_ant3', 'REAL'), ('lat', 'REAL'),
            ('lon', 'REAL'), mode="override")
        sense_table.commit()

    def _debug(self, message):
        print "[SBDEBUG]: {0}".format(message)

    def _log(self, message):
        _console(message)
        print "[SB]: {0}".format(message)

    def get_location(self):
        return [self.vehicle.location.lon, self.vehicle.location.lat]

    # ////Flight and operation functions
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
                is_relative=relative
            )
        )
        self.vehicle.flush()

    # ///Utility functions
    def wait_pt_reached(self, location, log=False):
        while self.vehicle.mode.name == 'GUIDED' and self.vehicle.armed:
            distance = self.get_distance_meters(
                [self.vehicle.location.lon, self.vehicle.location.lat],
                location)
            if log:
                self._log(str(distance)+'m remaining')
            if distance < 1:
                self._log('WP reached')
                break
            time.sleep(0.5)

    def get_distance_meters(self, location1, location2):

        dlat = location1[1]-location2[1]
        dlong = location1[0]-location2[0]

        return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5

    def get_midway_point(self, location1, location2):
        return [
            1/2. * (location1[0]+location2[0]),
            1/2. * (location1[1] + location2[1])
            ]

    # ///Mission methods
    def sense(self):
        # time.sleep(1.5)
        sense_db = Database(self.sense_db_path)
        sense_table = Table('sensing_data', sense_db)
        sense_table.open()

        start_sense_location = self.get_location()       
        frame_phi = -self.vehicle.attitude.yaw
        frame_theta = -self.vehicle.attitude.pitch

        antenna1_phi = antenna_1_framephi+frame_phi
        antenna1_theta = antenna_1_frametheta+frame_theta

        antenna2_phi = antenna_2_framephi+frame_phi
        antenna2_theta = antenna_2_frametheta+frame_theta

        # #antenna_1 = (self.vehicle.location.lon,
        #   self.vehicle.location.lat,
        #   self.vehicle.location.altitude,
        #   antenna1_theta,
        #   antenna1_phi)

        # #antenna_2 = (self.vehicle.location.lon,
        #   self.vehicle.location.lat,
        #   self.vehicle.location.altitude,
        #   antenna2_theta,
        #   antenna2_phi)

        # signal_antenna_1 = get_antenna_reading(antenna_1)
        # signal_antenna_2 = get_antenna_reading(antenna_2)

        signal_antenna_1 = 5
        signal_antenna_2 = 5

        end_sense_location = self.get_location()

        avg_sens_location = self.get_midway_point(
            start_sense_location, end_sense_location
            )
        sense_table.insert(
            timestamp=time.time(),
            signal_ant1=signal_antenna_1,
            signal_ant2=signal_antenna_2,
            signal_ant3=0,
            lat=avg_sens_location[1],
            lon=avg_sens_location[0]
            )
        sense_table.commit()
        return


class SbApp(object):
    """
        Main App. Initiates a corresponding St-Bernard,
        Serves the autopilot data through endpoints


    """
    def __init__(self, stbernard=None, flightarea=None):
        self.droid = stbernard
        self.flightarea = flightarea

    def _debug(self, message):
        print "[APPDEBUG]: {0}".format(message)

    def _log(self, message):
        _console(message)
        print "[APP]: {0}".format(message)

    def get_search_data(self):
        """
        Probably needs some optimisation since the table can become very large
        """
        sense_db = Database('sensor/flight.db')
        sense_table = Table('sensing_data', sense_db)
        sense_table.open()
        search_data = [r for r in sense_table]
        return search_data

    def get_console(self):
        return console

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def sense_status(self):
        return dict()

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def vehicle_state(self):
        return dict(position=self.droid.get_location(), console=console)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def command(self, cmd=None):
        return dict()


def _log(message):
    print "[MAINDEBUG]: {0}".format(message)


def _console(message):
    """
    Remplacer par un push
    """
    global console
    console = console + time.strftime("%c") + " : " + format(message) + '\n'
    return


# __main__

console = time.strftime("%c") + "Initating console \n"

_log('Spawning StBernard')
rex = StBernard('sensor/flight.db', MASTER)
_log('St Bernard Spawned')

cherrypy.tree.mount(SbApp(rex, flightArea), '/', config=cherrypy_conf)

cherrypy.config.update({
            'server.socket_port': host_port,
            'server.socket_host': host_ip,
            'log.screen': False,
            'server.logToScreen': False,
            'environment': 'embedded'
         })
# Supressses all cherrypy output to ease debugging
cherrypy.log.error_log.propagate = False
cherrypy.log.access_log.propagate = False

cherrypy.engine.start()
cherrypy.engine.block()
