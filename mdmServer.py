#!/usr/bin/python
import cherrypy
from cherrypy.process.plugins import PIDFile
import ConfigParser
import M2Crypto

import discovery
import enrollment
import pushSender
import omaDM

import sys

class HealthCheck():
	@cherrypy.expose
	def index(self, **kwargs):
		return "ok"

class NotFound():
	@cherrypy.expose
	def index(self, **kwargs):
		return "<html><body><h3>SafeKiddo MDM Server - Page not found (404)</h3><p>Sorry, that page does not exist!</p></body></html>"

def caseInsensitive(string):
	return '{dummy:(?i)'+string+'}'

def runServer(config):
	PIDFile(cherrypy.engine, config.get('Server', 'PIDFile')).subscribe()
	configCherryPyDict = {}
	stderrFile = config.get('Logs', 'stderr')
	configCherryPyDict['log.error_file'] = stderrFile
	configCherryPyDict['log.screen'] = False
	
	stdoutFile = config.get('Logs', 'stdout')
	configCherryPyDict['log.access_file'] = stdoutFile
	configCherryPyDict['log.screen'] = False

	#Check if KeyPair is installed
	try:
		keyPair = M2Crypto.RSA.load_key(config.get("SSL", "KeyPair"))
	except:
		raise AssertionError("Copy KeyPair.pem to MDM directory")
	
	mapper = cherrypy.dispatch.RoutesDispatcher()
	mapper.connect('wp', caseInsensitive("/wp"),controller=discovery.Discovery(config), action='index')
	mapper.connect('healthCheck', caseInsensitive("/healthCheck"),controller=HealthCheck(), action='index')
	mapper.connect('discovery', caseInsensitive("/EnrollmentServer/Discovery.svc"),controller=discovery.Discovery(config), action='index')
	mapper.connect('enrollment', caseInsensitive("/EnrollmentServer/Enrollment.svc"),controller=enrollment.Enrollment(config), action='index')
	mapper.connect('omadm', caseInsensitive("/omadm/WindowsPhone.ashx"),controller=omaDM.OMADM(config), action='index')
	mapper.connect('pushSender', caseInsensitive("/push"), controller=pushSender.PushSender(config), action='index')
	mapper.connect('notFound', '{dummy:/(.*)}', NotFound(), action='index')
	
	configCherryPyDict['server.socket_host'] = config.get("Server", "Host") 
	configCherryPyDict['server.socket_port'] = config.getint("Server", "Port")
	configCherryPyDict['server.thread_pool'] = config.getint("Server", "ThreadPool")
	if config.getboolean("SSL", "TurnedOn"):
		configCherryPyDict['server.ssl_module'] = 'pyopenssl'
		configCherryPyDict['server.ssl_certificate'] = config.get("SSL", "Certificate")
		configCherryPyDict['server.ssl_private_key'] = config.get("SSL", "Key")
		configCherryPyDict['server.ssl_certificate_chain'] = config.get("SSL", "CertificateChain")
	cherrypy.config.update(configCherryPyDict)

	config = {"/": {"request.dispatch": mapper}}
	cherrypy.quickstart(None, config=config)
	
if __name__ == '__main__':
	config = ConfigParser.ConfigParser()
	config.readfp(open('configs/mdmServer.cfg'))
	runServer(config)
