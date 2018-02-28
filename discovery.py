import cherrypy
from xmlDoc import XmlDoc
import xml.etree.ElementTree as ET
import globalFunctions

NAMESPACE_S = "http://www.w3.org/2003/05/soap-envelope"
NAMESPACE_A = "http://www.w3.org/2005/08/addressing"

CONTENT_TYPE_SOAP = 'application/soap+xml; charset=utf-8'

class Discovery():
	
	def __init__(self, config):
		self.config = config
	
	def addResponseHeader(self, xmlDoc, envelope, messageId):
		header = xmlDoc.subElement(envelope, 'Header', 's')
		
		action = xmlDoc.subElement(header, 'Action', 'a')
		xmlDoc.addAttribute(action, "mustUnderstand", '1', 's')
		xmlDoc.addText(action, "http://schemas.microsoft.com/windows/management/2012/01/enrollment/IDiscoveryService/DiscoverResponse")
		
		xmlDoc.subElementWithText(header, 'ActivityId', globalFunctions.makeGuid())
		xmlDoc.subElementWithText(header, 'RelatesTo', messageId, 'a')
		
	def addResponseBody(self, xmlDoc, envelope):
		body = xmlDoc.subElement(envelope, 'Body', 's')
		xmlDoc.addSchemaXsi(body)
		xmlDoc.addSchemaXsd(body)
		
		discoverResponse = xmlDoc.subElement(body, 'DiscoverResponse')
		xmlDoc.addDefaultNamespaceToElement(discoverResponse, 'http://schemas.microsoft.com/windows/management/2012/01/enrollment')
		
		discoverResult = xmlDoc.subElement(discoverResponse, "DiscoverResult")
		xmlDoc.subElementWithText(discoverResult, "AuthPolicy", "OnPremise")
		xmlDoc.subElementWithText(discoverResult, "EnrollmentServiceUrl", self.config.get("Discovery", "EnrollmentServiceUrl"))
	
	def makeResponse(self, messageId):
		xmlDoc= XmlDoc()
		xmlDoc.addNamespace('s', NAMESPACE_S )
		xmlDoc.addNamespace('a', NAMESPACE_A)
		
		envelope = xmlDoc.element('Envelope', 's')
		self.addResponseHeader(xmlDoc, envelope, messageId)
		self.addResponseBody(xmlDoc, envelope)
		
		return xmlDoc.elementToString(envelope)	
	
	@cherrypy.expose
	def index(self, **kwargs):
		if 'Content-Type' not in cherrypy.request.headers:
			return "Error, no content type"
		
		if cherrypy.request.method == "GET":
			return ""
		
		if cherrypy.request.headers['Content-Type'] == CONTENT_TYPE_SOAP:
			cherrypy.response.headers['Content-Type'] = CONTENT_TYPE_SOAP
			requestBody = cherrypy.request.body.read()
			globalFunctions.printDebugLog(self.config, "DISCOVERY REQUEST", requestBody)
			tree = ET.fromstring(requestBody)
			messageId = tree.find("./{%s}Header/{%s}MessageID/."% (NAMESPACE_S, NAMESPACE_A)).text
			toReturn = self.makeResponse(messageId)
			globalFunctions.printDebugLog(self.config, "DISCOVERY RESPONSE", toReturn)
			return toReturn
		
		return "unsupported request" 
		