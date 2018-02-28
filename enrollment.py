import cherrypy
from xmlDoc import XmlDoc
import xml.etree.ElementTree as ET
import datetime
import M2Crypto
import textwrap
import email
import time
import globalFunctions

NAMESPACE_S = "http://www.w3.org/2003/05/soap-envelope"
NAMESPACE_A = "http://www.w3.org/2005/08/addressing"
NAMESPACE_U = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
NAMESPACE_WST = "http://docs.oasis-open.org/ws-sx/ws-trust/200512"
NAMESPACE_WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"

SUBJECT = "*.safekiddo.com"
SUBJECT2 = "3db250987a-a46e-4e2d-94cd-2245d095c9d8"
DUMMY = "dummy"

CONTENT_TYPE_SOAP = 'application/soap+xml; charset=utf-8'

class Enrollment():
	
	def __init__(self, config):
		self.config = config
	
	def addResponseHeader(self, xmlDoc, envelope, messageId):
		header = xmlDoc.subElement(envelope, 'Header', 's')
		
		action = xmlDoc.subElement(header, 'Action')
		xmlDoc.addAttribute(action, "mustUnderstand", '1', 's')
		xmlDoc.addText(action, "http://schemas.microsoft.com/windows/pki/2009/01/enrollment/RSTRC/wstep")
		
		relatesTo = xmlDoc.subElement(header, 'RelatesTo', 'a')
		xmlDoc.addText(relatesTo, messageId)
		
		security = xmlDoc.subElementWithNamespace(header, "Security", 'o', "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd")
		xmlDoc.addAttribute(security, "mustUnderstand", '1', 's')
		
		timestamp = xmlDoc.subElement(security, 'Timestamp', 'u')
		xmlDoc.addAttribute(timestamp, "Id", '_0', 'u')
		
		created = xmlDoc.subElement(timestamp, 'Created', 'u')
		xmlDoc.addText(created, datetime.datetime.now().isoformat())
		
		expires = xmlDoc.subElement(timestamp, 'Expires', 'u')
		xmlDoc.addText(expires, (datetime.datetime.now() + datetime.timedelta(0, int(self.config.get("Enrollment", "CertificateLength")))).isoformat())
		
	def tokenBase64Convert(self, token):
		return email.base64MIME.encode(token)
	
	def addResponseBody(self, xmlDoc, envelope, tokenRequest, deviceId):
		body = xmlDoc.subElement(envelope, 'Body', 's')
		
		requestSecurityTokenResponseCollection = xmlDoc.subElement(body, 'RequestSecurityTokenResponseCollection')
		xmlDoc.addDefaultNamespaceToElement(requestSecurityTokenResponseCollection, "http://docs.oasis-open.org/ws-sx/ws-trust/200512")
		
		requestSecurityTokenResponse = xmlDoc.subElement(requestSecurityTokenResponseCollection, 'RequestSecurityTokenResponse')
		
		tokenType = xmlDoc.subElement(requestSecurityTokenResponse, "TokenType")
		xmlDoc.addText(tokenType, "http://schemas.microsoft.com/5.0.0.0/ConfigurationManager/Enrollment/DeviceEnrollmentToken")
		
		requestedSecurityToken = xmlDoc.subElement(requestSecurityTokenResponse, "RequestedSecurityToken")
		binarySecurityToken = xmlDoc.subElement(requestedSecurityToken, "BinarySecurityToken")
		xmlDoc.addAttribute(binarySecurityToken, "ValueType", 'http://schemas.microsoft.com/5.0.0.0/ConfigurationManager/Enrollment/DeviceEnrollmentProvisionDoc')
		xmlDoc.addAttribute(binarySecurityToken, "EncodingType", 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd#base64binary')
		xmlDoc.addDefaultNamespaceToElement(binarySecurityToken, "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd")
		
		xmlDoc.addText(binarySecurityToken, self.tokenBase64Convert(self.createProvisioningXML(tokenRequest, deviceId)))
		
	def makeResponse(self, messageId, tokenRequest, deviceId):
		xmlDoc= XmlDoc()
		xmlDoc.addNamespace('s', NAMESPACE_S)
		xmlDoc.addNamespace('a', NAMESPACE_A)
		xmlDoc.addNamespace('u', NAMESPACE_U)
		
		envelope = xmlDoc.element('Envelope', 's')
		self.addResponseHeader(xmlDoc, envelope, messageId)
		self.addResponseBody(xmlDoc, envelope, tokenRequest, deviceId)
		
		return xmlDoc.elementToString(envelope)	
	
	def reformatRequestToken(self, token):
		token = textwrap.fill(token, 64)
		token = "-----BEGIN CERTIFICATE REQUEST-----\n" + token
		token = token + "\n-----END CERTIFICATE REQUEST-----\n"
		return token
	
	def makeCharacteristicNode(self, xmlDoc, parent, type):
		characteristic = xmlDoc.subElement(parent, 'characteristic')
		xmlDoc.addAttribute(characteristic, "type", type)
		return characteristic

	def reformatCertificate(self, string):
		#remove -----BEGIN...
		string = string[string.find('\n'):]		
		#remove empty line
		string = string[:string.rfind('\n')]
		#remove -----END...
		string = string[:string.rfind('\n')]
		string = string.replace("\n", "")
		return string	
		
	def makeParmNode(self, xmlDoc, parent, name, value=None, datatype=None):
		parm = xmlDoc.subElement(parent, 'parm')
		xmlDoc.addAttribute(parm, "name", name)
		if value is not None:
			xmlDoc.addAttribute(parm, "value", value)
		if datatype is not None:
			xmlDoc.addAttribute(parm, "datatype", datatype)
		return parm
	
	def rootPublicKey(self):
		keyPair = M2Crypto.RSA.load_key(self.config.get("SSL", "KeyPair"))
		publicKey = M2Crypto.EVP.PKey(md='sha1')
		publicKey.assign_rsa(keyPair)
		return publicKey
	
	def createCertificate(self, publicKey, signKey, subjectCN=SUBJECT):
		certificate = M2Crypto.X509.X509()
		certificate.set_version(1)
		issuer = M2Crypto.X509.X509_Name()
		issuer.CN = SUBJECT
		certificate.set_issuer(issuer)
		ASN1 = M2Crypto.ASN1.ASN1_UTCTIME()
		ASN1.set_time(int(time.time()))
		certificate.set_not_before(ASN1)
		ASN1 = M2Crypto.ASN1.ASN1_UTCTIME ()
		ASN1.set_time (int(time.time()) + int(self.config.get("Enrollment", "CertificateLength")))
		certificate.set_not_after(ASN1)
		certificate.set_pubkey(pkey=publicKey)
		subject = M2Crypto.X509.X509_Name()
		subject.CN = subjectCN
		certificate.set_subject_name(subject)
		certificate.sign(signKey,'sha1')
		
		return certificate
	
	def createRootCertificate(self):
		return M2Crypto.X509.load_cert("GeoTrust_Global_CA.cer")
	
	def createClientCertificate(self, tokenRequest):
		publicKey = tokenRequest.get_pubkey()
		certificate = self.createCertificate(publicKey, self.rootPublicKey(), SUBJECT2)
		certificate.add_ext(M2Crypto.X509.new_extension('extendedKeyUsage', 'TLS Web Client Authentication', 1))
		certificate.add_ext(M2Crypto.X509.new_extension('basicConstraints', 'CA:FALSE', 1))
		certificate.set_serial_number(2)
		return certificate
	
	def createProvisioningXML(self, tokenRequest, deviceId):
		xmlDoc = XmlDoc()
		wapProvisioningDoc = xmlDoc.element('wap-provisioningdoc')
		xmlDoc.addAttribute(wapProvisioningDoc, "version", '1.1')
		
		characteristicCertificateStore = self.makeCharacteristicNode(xmlDoc, wapProvisioningDoc, 'CertificateStore')
		characteristicRoot = self.makeCharacteristicNode(xmlDoc, characteristicCertificateStore, 'Root')
		characteristicSystem = self.makeCharacteristicNode(xmlDoc, characteristicRoot, 'System')
		rootCertificate = self.createRootCertificate()
		characteristicNumSystem = self.makeCharacteristicNode(xmlDoc, characteristicSystem, rootCertificate.get_fingerprint('sha1'))
		self.makeParmNode(xmlDoc, characteristicNumSystem, "EncodedCertificate",  self.reformatCertificate(rootCertificate.as_pem()))
		
		characteristicMy = self.makeCharacteristicNode(xmlDoc, characteristicCertificateStore, 'My')
		characteristicUser = self.makeCharacteristicNode(xmlDoc, characteristicMy, 'User')
		clientCertificate = self.createClientCertificate(tokenRequest)	
		characteristicNumUser = self.makeCharacteristicNode(xmlDoc, characteristicUser, clientCertificate.get_fingerprint('sha1'))
		self.makeParmNode(xmlDoc, characteristicNumUser, "EncodedCertificate", self.reformatCertificate(clientCertificate.as_pem()))
		characteristicPrivateKeyContainer = self.makeCharacteristicNode(xmlDoc, characteristicNumUser, 'PrivateKeyContainer')
		
		characteristicWSTEP = self.makeCharacteristicNode(xmlDoc, characteristicMy, 'WSTEP')
		characteristicRenew = self.makeCharacteristicNode(xmlDoc, characteristicWSTEP, 'Renew')
		self.makeParmNode(xmlDoc, characteristicRenew, "ROBOSupport", "true", "boolean")
		self.makeParmNode(xmlDoc, characteristicRenew, "RenewPeriod", self.config.get("Enrollment", "ROBORenewPeriod"), "integer")
		self.makeParmNode(xmlDoc, characteristicRenew, "RetryInterval", self.config.get("Enrollment", "ROBORetryInterval"), "integer")
		
		characteristicApplication = self.makeCharacteristicNode(xmlDoc, wapProvisioningDoc, 'APPLICATION')
		self.makeParmNode(xmlDoc, characteristicApplication, "APPID", "w7")
		self.makeParmNode(xmlDoc, characteristicApplication, "PROVIDER-ID", self.config.get("Enrollment", "ProviderId"))
		self.makeParmNode(xmlDoc, characteristicApplication, "NAME", self.config.get("Enrollment", "Name"))
		self.makeParmNode(xmlDoc, characteristicApplication, "ADDR", self.config.get("Enrollment", "MDMServerUrl"))
		self.makeParmNode(xmlDoc, characteristicApplication, "INIT", "")
		
		characteristicAPPAUTH = self.makeCharacteristicNode(xmlDoc, characteristicApplication, 'APPAUTH')
		self.makeParmNode(xmlDoc, characteristicAPPAUTH, "AAUTHLEVEL", "CLIENT")
		self.makeParmNode(xmlDoc, characteristicAPPAUTH, "AAUTHSECRET", DUMMY)
		self.makeParmNode(xmlDoc, characteristicAPPAUTH, "AAUTHDATA", DUMMY)
		
		characteristicAPPAUTH = self.makeCharacteristicNode(xmlDoc, characteristicApplication, 'APPAUTH')
		self.makeParmNode(xmlDoc, characteristicAPPAUTH, "AAUTHLEVEL", "APPSRV")
		self.makeParmNode(xmlDoc, characteristicAPPAUTH, "AAUTHNAME", deviceId)
		self.makeParmNode(xmlDoc, characteristicAPPAUTH, "AAUTHSECRET", DUMMY)
		
		characteristicDMClient = self.makeCharacteristicNode(xmlDoc, wapProvisioningDoc, 'DMClient')
		characteristicProvider = self.makeCharacteristicNode(xmlDoc, characteristicDMClient, 'Provider')
		characteristicTestMDMServer = self.makeCharacteristicNode(xmlDoc, characteristicProvider, self.config.get("Enrollment", "ProviderId"))
		characteristicPoll = self.makeCharacteristicNode(xmlDoc, characteristicTestMDMServer, 'Poll')
		
		self.makeParmNode(xmlDoc, characteristicPoll, "NumberOfFirstRetries", "8", "integer")
		self.makeParmNode(xmlDoc, characteristicPoll, "IntervalForFirstSetOfRetries", "15", "integer")
		self.makeParmNode(xmlDoc, characteristicPoll, "NumberOfSecondRetries", "5", "integer")
		self.makeParmNode(xmlDoc, characteristicPoll, "IntervalForSecondSetOfRetries", "3", "integer")
		self.makeParmNode(xmlDoc, characteristicPoll, "NumberOfRemainingScheduledRetries", "0", "integer")
		
		self.makeParmNode(xmlDoc, characteristicPoll, "IntervalForRemainingScheduledRetries", self.config.get("Enrollment", "SynchInterval"), "integer")
		
		toReturn = xmlDoc.elementToString(wapProvisioningDoc, False)
		globalFunctions.printDebugLog(self.config, "ENROLLMENT WAP PROVINSIONING FILE", toReturn)
		return toReturn
	
	@cherrypy.expose
	def index(self, **kwargs):
		if 'Content-Type' not in cherrypy.request.headers:
			return "Error, no content type"
		
		if cherrypy.request.headers['Content-Type'] == CONTENT_TYPE_SOAP:
			cherrypy.response.headers['Content-Type'] = CONTENT_TYPE_SOAP
			requestBody = cherrypy.request.body.read()
			globalFunctions.printDebugLog(self.config, "ENROLLMENT REQUEST", requestBody)
			tree = ET.fromstring(requestBody)
			xmlDoc = XmlDoc()
			messageId = tree.find("./{%s}Header/{%s}MessageID/." % (NAMESPACE_S, NAMESPACE_A)).text
			binarySecurityTokenPem = tree.find("./{%s}Body/{%s}RequestSecurityToken/{%s}BinarySecurityToken/." % (NAMESPACE_S, NAMESPACE_WST, NAMESPACE_WSSE)).text
			binarySecurityToken = M2Crypto.X509.load_request_string(self.reformatRequestToken(binarySecurityTokenPem))
			
			usernameToken = tree.find("./{%s}Header/{%s}Security/{%s}UsernameToken/." % (NAMESPACE_S, NAMESPACE_WSSE, NAMESPACE_WSSE))
			#username is enrollment token
			username = usernameToken.find("./{%s}Username/." % NAMESPACE_WSSE).text
			#password is parent pid
			password = usernameToken.find("./{%s}Password/." % NAMESPACE_WSSE).text
			
			result = globalFunctions.queryApi(self.config, {'token': username, 'pin': password}, self.config.get("API", "CheckTokenUrl"))
			if result["success"] != True:
				globalFunctions.printDebugLog(self.config, "cannot verify username and token", "")
				return
			
			deviceId = str(result["device_id"])
			
			toReturn = self.makeResponse(messageId, binarySecurityToken, deviceId)
			globalFunctions.printDebugLog(self.config, "ENROLLMENT RESPONSE", toReturn)
			return toReturn
		
		return "unsupported request" 
		