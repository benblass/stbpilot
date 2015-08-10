from numpy import *
from numpy.linalg import inv
import scipy.io as sio

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

 
def mag_field_local_cart(sp_local_coords):
  Xx = sp_local_coords.item(0)
  Yy = sp_local_coords.item(1)
  Zz = sp_local_coords.item(2)

  r = sqrt(Xx*Xx+Yy*Yy+Zz*Zz)

  
  if r<0.5*meters_scaling:
    return [[0],[0],[0]]


  B_x = scaling * 3 * Xx*Zz / (r*r*r*r*r)
  B_y = scaling * 3 * Yy*Zz / (r*r*r*r*r)
  B_z = scaling * (3 * Zz*Zz - r*r) / (r*r*r*r*r)

  return array([[B_x],[B_y],[B_z]])


def mag_field_at_global_cartesian(x,y,z):
#Translates the target point in the global referential to its coordinates in the cartesian referential
#of the transmitter (transmitter antenna along z axis)
  M_global_to_local_Ctransmitter = array([[cos(transmitter_theta)*cos(transmitter_phi), cos(transmitter_theta)*sin(transmitter_phi), -sin(transmitter_theta) ],
                                          [-sin(transmitter_phi),                     cos(transmitter_phi),                     0],
                                          [sin(transmitter_theta)*cos(transmitter_phi), sin(transmitter_theta)*sin(transmitter_phi), cos(transmitter_theta)]])
 
  transmitter_pos0_global = array([[transmitter_x0],[transmitter_y0],[transmitter_z0]])

  target = array([[x],[y],[z]])

  local_cartesian_target_coords = M_global_to_local_Ctransmitter.dot(target-transmitter_pos0_global)

  cartesian_field_local = mag_field_local_cart(local_cartesian_target_coords)
    
  cartesian_field_global = inv(M_global_to_local_Ctransmitter).dot(cartesian_field_local)
    
  return cartesian_field_global

def spherical_to_cart(r,theta,phi): #theta colatitude, phi longitude

  sp_r = cart_sp.item(0)
  sp_theta = cart_sp.item(1)
  sp_phi = cart_sp.item(2)

  sp_x = sp_r * sin(sp_theta)*cos(sp_phi)
  sp_y = sp_r * sin(sp_theta)*sin(sp_phi)
  sp_z = sp_r * cos(sp_theta)
  return array([[x],[y],[z]])


#Initiate position of the transmitter 
#theta : angle of the antenna from the vertical, phi: angle of the antenna from the north (trigo rotation direction-wise)

vsim_scaling = 1E-6
vsim_meters_scaling = 1/1.113195 * 1E-5

transmitter_x0 = 6.1333293
transmitter_y0 = 45.7684287
transmitter_z0 = 0

transmitter_theta = 0
transmitter_phi = 0

def get_antenna_reading(antenna):
#antenna: x,y,z,theta,phi ferrite rod (theta colatitude, phi longitude)
  ant_x = antenna(0)
  ant_y = antenna(1)
  ant_z = antenna(2)
  ant_theta = antenna(3)
  ant_phi = antenna(4)
  
  field = mag_field_at_global_cartesian(ant_x,ant_y,ant_z)

  v_antenna = spherical_to_cart(1,ant_theta, ant_phi)

  return abs(dot(field,v_antenna))