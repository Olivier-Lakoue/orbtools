################################################################################
#
# Orbital toolbox: Payloads, delta-v and propellant calculations
#
# Equations:
#
# - dv           = ve * ln(mtot/payload)
# - dv / ve      =      ln(mtot/payload)
# - exp(dv / ve) =         mtot/payload
#
# - ve = dv / ln(mtot/payload)
#
# 2) mtot = payload + mfuel
#
# R = ratio of masses = Mtot / Mpayload
#
################################################################################

from orbtools import *

#-------------------------------------------------------------------------------
#
#-------------------------------------------------------------------------------

def solve_rocket_eq(M0, M1, dv, ve):

	def Rv(dv, ve): return exp(float(dv)/ve)
	def Rm(M0, M1): return log(float(M0)/M1)
	
	if M0 == None:
		return M1 * Rv(dv, ve)
	elif M1 == None:
		return M0 / Rv(dv, ve)
	elif dv == None:
		return ve * Rm(M0, M1)
	else:
		return dv / Rm(M0, M1)

#-------------------------------------------------------------------------------
#
#-------------------------------------------------------------------------------

class Engine(object):
	def __init__(self, u):
		self.u = float(u)

	def R(self, dv):
		return exp(float(dv)/self.u)

	def dvR(self, R):
		return self.u*log(R)
	
	def dv(self, m0, m1):
		return self.dvR(m0/m1)

class Payload(object):

	def __init__(self, name, mass):
		self.name = name
		self.mass = float(mass)
		self.dv   = 0
		self.engine = None

	@property
	def payload(self): return self.mass
	
	@property
	def fuel(self):    return 0

	def printOut(self):
		print "Payload"
		print "   ", "Mass: %.2f kg" % self.mass

class Stage(object):

	#--------------------------------------------------------------------------
	# mass = payload + fuel
	#
	# - payload = mass / R <=> mass = R * payload
	#
	# - payload = mass / R
	#   mass - fuel = mass / R
	#   - fuel = mass / R - mass
	#   fuel = mass - mass / R
	#   fuel = mass * (1 - 1/R)
	#   fuel/(1-1/R) = mass
	#   
	# R = (payload + fuel) / payload = mass / payload
	#
	#--------------------------------------------------------------------------

	@property
	def payload(self):
		return self.mass / self.R
	
	@property
	def fuel(self):
		return self.mass - self.payload

	#--------------------------------------------------------------------------
	# mass (tot), payload, mf (fuel mass), dv:
	# - Give two of them, and others None to solve the rest
	# - Engine u is always known
	#--------------------------------------------------------------------------

	def __init__(self, name, engine, mass = None, payload = None, fuel = None, dv = None, mission = None):
		self.name = name
		self.engine = engine
		self.mission = mission
		
		# If delta-v is given, use it to solve masses
		if dv != None:
			self.dv = dv
			self.R  = engine.R(dv)
			if mass != None:
				self.mass = float(mass)
			elif payload != None:
				self.mass = self.R * float(payload)
			else:
				self.mass = fuel/(1 - 1.0/self.R)
		# If not, use masses to solve dv        	
		else:
			if mass != None:
				self.mass = float(mass)
				if payload != None:
					self.dv = self.engine.dv(self.mass, float(payload))
				else:
					self.dv = self.engine.dv(self.mass, self.mass - fuel)
			else:
				self.mass = float(payload + fuel)
				self.dv = self.engine.dv(self.mass, float(payload))
			self.R = self.engine.R(self.dv)

	def printOut(self):
		print self.name
		print "   ", "Mass.......: %.2f kg" % self.mass, "(%.2f / %.2f)" % (self.payload, self.fuel)
		print "   ", "DV.........: %.2f m/s" % self.dv
		if self.mission != None:
			phase = self.mission
			print "   ", "Mission DV.: %.2f m/s" % phase.dv
			print "   ", "DV diff....: %.2f m/s" % (self.dv - phase.dv)
			
################################################################################

class Rocket(object):

	#---------------------------------------------------------------------------
	# Staged rocket: we create it from top to bottom, creating new objects
	# to include masses of upper stages.
	def __init__(self, name, *stages, **kw):
		self.name = name
		self.stages = []
		if "mission" in kw:
			self.mission = kw["mission"]
		else:
			self.mission = None
		
		totmass = 0
		for stage in stages:
			if stage.engine:
				solvedstage = Stage(
					stage.name,
					stage.engine,
					None,
					stage.payload + totmass,
					stage.fuel,
					mission = stage.mission
				)
			else:
				solvedstage = Payload(
					stage.name,
					stage.mass
				)
			self.stages.append(solvedstage)
			totmass = totmass + stage.mass
	
	@property
	def payload(self):
		return self.stages[0].payload

	@property
	def dv(self):
		return sum(map(lambda s: s.dv, self.stages))

	@property
	def mass(self):
		return self.stages[-1].mass

	@property
	def fuel(self):
		return sum(map(lambda s: s.fuel, self.stages))

	def printOut(self):
		print "Rocket:", self.name
		print "- Payload........: %.2f kg"  % self.payload
		print "- Tot. mass......: %.2f kg"  % self.mass
		print "- Tot. propellant: %.2f kg"  % self.fuel
		print "- Tot. DV........: %.2f m/s" % self.dv
		if self.mission != None:
			phase = self.mission
			print "- Mission DV.....: %.2f m/s" % phase.dv
			print "- DV diff........: %.2f m/s" % (self.dv - phase.dv)
		print "Stages:"
		for stage in self.stages:
			stage.printOut()

