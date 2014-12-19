#    Copyright (C) 2014 Imperial College London.

#    This file is part of Firedrake-Fluids.
#
#    Firedrake-Fluids is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Firedrake-Fluids is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Firedrake-Fluids.  If not, see <http://www.gnu.org/licenses/>.

from firedrake import *
import libspud

from firedrake_fluids import LOG
      
class TurbineArray:

   def __init__(self, base_option_path, mesh):
      """ Create an array of turbines. """
      
      fs = FunctionSpace(mesh, "CG", 2)
   
      turbine_type = libspud.get_option(base_option_path + "/turbine_type/name")
      turbine_coords = eval(libspud.get_option(base_option_path + "/turbine_coordinates"))
      turbine_radius = eval(libspud.get_option(base_option_path + "/turbine_radius"))
      K = libspud.get_option(base_option_path + "/scalar_field::TurbineDragCoefficient/value/constant")
      
      self.turbine_drag = Function(fs).interpolate(Expression("0"))
      for coords in turbine_coords:
         # For each coordinate tuple in the list, create a new turbine.
         # FIXME: This assumes that all turbines are of the same type.
         try:
            if(turbine_type == "bump"):
               turbine = BumpTurbine(K=K, coords=coords, r=turbine_radius)
            elif(turbine_type == "tophat"):
               turbine = TopHatTurbine(K=K, coords=coords, r=turbine_radius)
            else:
               raise ValueError
         except ValueError:
            LOG.error("Unknown turbine type '%s'." % turbine_type)
            sys.exit(1)

         self.turbine_drag += Function(fs).interpolate(turbine)
         LOG.info("Added %s turbine at %s..." % (turbine_type, coords))

      return
      
   def write_turbine_drag(self, options):
      """ Write the turbine drag field to a file for visualisation. """
      
      LOG.debug("Integral of the turbine drag field: %.2f" % (assemble(self.turbine_drag*dx)))
      LOG.debug("Writing turbine drag field to file...")
      f = File("%s_%s.pvd" % (options["simulation_name"], "TurbineDrag"))
      f << self.turbine_drag
      return
    
class TopHatTurbine(Expression):

   def eval(self, value, X, K=None, coords=None, r=None):
      px = sqrt((X[0]-coords[0])**2)
      py = sqrt((X[1]-coords[1])**2)
      
      if(px <= r[0] and py <= r[1]):
         value[0] = K
      else:
         value[0] = 0
      
class BumpTurbine(Expression):

   def eval(self, value, X, K=None, coords=None, r=None):
      value[0] = K
      for i in range(2):
         p = sqrt(((X[i]-coords[i])/r[i])**2)
         if(p < 1.0):
            value[0] *= exp( 1.0 - 1.0/(1.0 - p**2) )
         else:
            value[0] *= 0

