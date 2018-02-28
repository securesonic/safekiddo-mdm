import cherrypy
from xmlDoc import XmlDoc
import xml.etree.ElementTree as ET
import urllib
import configs.blockedBrowsers as blockedBrowsers
import globalFunctions
import base64

CONTENT_TYPE_SYNCML = "application/vnd.syncml.dm+xml"
NAMESPACE_1_1 = "SYNCML:SYNCML1.1"
NAMESPACE_1_2 = "SYNCML:SYNCML1.2"

DATA_OK_CODE = 200
DATA_EXISTS_CODE = 418

CMD_ADD = "Add"
CMD_DELETE = "Delete"
CMD_GET = "Get"
CMD_REPLACE = "Replace"
CMD_EXEC = "Exec"

TOKEN_URI= "./Vendor/MSFT/DMClient/Provider/%s/Push/ChannelURI"
UNENROLLMENT_CODE = 1226
DEVICE_HARDWARE_ID_PREFIX = "urn:uuid:"

class OMADM():
	
	def __init__(self, config):
		self.config = config

	def makePushNotificationCommand(self, xmlDoc, syncBody, cmdId, type, path = ""):
		replace = xmlDoc.subElement(syncBody, type)
		xmlDoc.subElementWithText(replace, "CmdID", cmdId)
		item = xmlDoc.subElement(replace, "Item")
		target = xmlDoc.subElement(item, "Target")
		xmlDoc.subElementWithText(target, "LocURI", "./Vendor/MSFT/DMClient/Provider/"+urllib.quote(self.config.get("Enrollment", "ProviderId"))+"/Push" + path)
		
		if type == CMD_ADD and path == "":
			meta = xmlDoc.subElement(item, "Meta")
			format = xmlDoc.subElementWithText(meta, "Format", 'node')
			xmlDoc.addDefaultNamespaceToElement(format, "syncml:metinf")
		
		if type == CMD_REPLACE and path == "/PFN":
			xmlDoc.subElementWithText(item, "Data", self.config.get("OMADM", "PFN"))

	def addBlockAddPFN(self, xmlDoc, syncBody, cmdId):
		# /<Provider>/Push don't support replace, so we have to delete old and add new
		self.makePushNotificationCommand(xmlDoc, syncBody, cmdId, CMD_DELETE)
		cmdId += 1
		self.makePushNotificationCommand(xmlDoc, syncBody, cmdId, CMD_ADD)
		cmdId += 1
		self.makePushNotificationCommand(xmlDoc, syncBody, cmdId, CMD_REPLACE, "/PFN")
		return 3
					
	def addBlockGetChannelURI(self, xmlDoc, syncBody, cmdId):
		self.makePushNotificationCommand(xmlDoc, syncBody, cmdId, CMD_GET, "/ChannelURI")
		cmdId = cmdId + 1
		self.makePushNotificationCommand(xmlDoc, syncBody, cmdId, CMD_GET, "/Status")
		return 2
	
	def addBlockGetUserCertificate(self, xmlDoc, syncBody, cmdId):
		replace = xmlDoc.subElement(syncBody, CMD_GET)
		xmlDoc.subElementWithText(replace, "CmdID", cmdId)
		item = xmlDoc.subElement(replace, "Item")
		target = xmlDoc.subElement(item, "Target")
		xmlDoc.subElementWithText(target, "LocURI", "./Vendor/MSFT/CertificateStore/Root/System")
		
	def changeAppAccess(self, xmlDoc, syncBody, cmdId, path, value):
		replace = xmlDoc.subElement(syncBody, CMD_REPLACE)
		xmlDoc.subElementWithText(replace, "CmdID", cmdId)
		item = xmlDoc.subElement(replace, "Item")
		target = xmlDoc.subElement(item, "Target")
		xmlDoc.subElementWithText(target, "LocURI", path)
		meta = xmlDoc.subElement(item, "Meta")
		type = xmlDoc.subElementWithText(meta, "Type", 'text/plain')
		xmlDoc.addDefaultNamespaceToElement(type, "syncml:metinf")
		format = xmlDoc.subElementWithText(meta, "Format", 'int')
		xmlDoc.addDefaultNamespaceToElement(format, "syncml:metinf")
		xmlDoc.subElementWithText(item, "Data", value)

	def blockApp(self, xmlDoc, syncBody, cmdId, path):
		self.changeAppAccess(xmlDoc, syncBody, cmdId, path, 0)
	
	def addBlockIeSection(self, xmlDoc, syncBody, cmdId):
		self.blockApp(xmlDoc, syncBody, cmdId, "./Vendor/MSFT/PolicyManager/My/Browser/AllowBrowser")
	
	def addSetCortanaSection(self, xmlDoc, syncBody, cmdId, value):
		self.changeAppAccess(xmlDoc, syncBody, cmdId, "./Vendor/MSFT/PolicyManager/My/Experience/AllowCortana", int(not value))
	
	def addBlockStrictSafeSearch(self, xmlDoc, syncBody, cmdId):
		self.blockApp(xmlDoc, syncBody, cmdId, "./Vendor/MSFT/PolicyManager/My/Search/SafeSearchPermissions")
	
	def addBlockSetManualUnenrollment(self, xmlDoc, syncBody, cmdId, value):
		self.changeAppAccess(xmlDoc, syncBody, cmdId, "./Vendor/MSFT/PolicyManager/My/Experience/AllowManualMDMUnenrollment", int(not value))
	
	def addBlockSetFactoryReset(self, xmlDoc, syncBody, cmdId, value):
		self.changeAppAccess(xmlDoc, syncBody, cmdId, "./Vendor/MSFT/PolicyManager/My/System/AllowUserToResetPhone", int(not value))
	
	def addBlockForceUnenrollment(self, xmlDoc, syncBody, cmdId):
		replace = xmlDoc.subElement(syncBody, CMD_EXEC)
		xmlDoc.subElementWithText(replace, "CmdID", cmdId)
		item = xmlDoc.subElement(replace, "Item")
		target = xmlDoc.subElement(item, "Target")
		xmlDoc.subElementWithText(target, "LocURI", "./Vendor/MSFT/DMClient/Unenroll")
		meta = xmlDoc.subElement(item, "Meta")
		format = xmlDoc.subElementWithText(meta, "Format", "chr")
		xmlDoc.addDefaultNamespaceToElement(format, "syncml:metinf")
		xmlDoc.subElementWithText(item, "Data", self.config.get("Enrollment", "ProviderId"))
	
	def addBlockUpdateOrGetSynchInterval(self, xmlDoc, syncBody, cmdId, cmdType):
		replace = xmlDoc.subElement(syncBody, cmdType)
		xmlDoc.subElementWithText(replace, "CmdID", cmdId)
		item = xmlDoc.subElement(replace, "Item")
		target = xmlDoc.subElement(item, "Target")
		xmlDoc.subElementWithText(target, "LocURI",
			"./Vendor/MSFT/DMClient/Provider/%s/Poll/IntervalForRemainingScheduledRetries" % self.config.get("Enrollment", "ProviderId"))
		meta = xmlDoc.subElement(item, "Meta")
		format = xmlDoc.subElementWithText(meta, "Format", "int")
		xmlDoc.addDefaultNamespaceToElement(format, "syncml:metinf")
		xmlDoc.subElementWithText(item, "Data", self.config.get("Enrollment", "SynchInterval"))
	
	def addBlockUpdateSynchInterval(self, xmlDoc, syncBody, cmdId):
		self.addBlockUpdateOrGetSynchInterval(xmlDoc, syncBody, cmdId, CMD_REPLACE)
	
	def addBlockGetSynchInterval(self, xmlDoc, syncBody, cmdId):
		self.addBlockUpdateOrGetSynchInterval(xmlDoc, syncBody, cmdId, CMD_GET)

	def makeBlockList(self, allowAppList):
		xmlDoc = XmlDoc()
		appPolicy = xmlDoc.element("AppPolicy")
		xmlDoc.addAttribute(appPolicy, "Version", "1")
		xmlDoc.addDefaultNamespaceToElement(appPolicy, "http://schemas.microsoft.com/phone/2013/policy")
		deny = xmlDoc.subElement(appPolicy, "Deny")
		
		for app in allowAppList:
			appNode = xmlDoc.subElement(deny, "App")
			xmlDoc.addAttribute(appNode, "ProductId", "{%s}" % app)
		
		return xmlDoc.elementToString(appPolicy, False)
	
	def addBlockedApplicationList(self, xmlDoc, syncBody, cmdId):
		replace = xmlDoc.subElement(syncBody, CMD_REPLACE)
		xmlDoc.subElementWithText(replace, "CmdID", cmdId)
		item = xmlDoc.subElement(replace, "Item")
		target = xmlDoc.subElement(item, "Target")
		xmlDoc.subElementWithText(target, "LocURI", "./Vendor/MSFT/PolicyManager/My/ApplicationManagement/ApplicationRestrictions")
		meta = xmlDoc.subElement(item, "Meta")
		type = xmlDoc.subElementWithText(meta, "Type", 'text/plain')
		xmlDoc.addDefaultNamespaceToElement(type, "syncml:metinf")
		format = xmlDoc.subElementWithText(meta, "Format", 'chr')
		xmlDoc.addDefaultNamespaceToElement(format, "syncml:metinf")
		xmlDoc.subElementWithText(item, "Data", self.makeBlockList(blockedBrowsers.BlockedBrowsersList))
		
	def addCommandStatusOK(self, xmlDoc, syncBody, msgId, cmd, cmdId, deviceHardwareId):
		status = xmlDoc.subElement(syncBody, "Status")
		xmlDoc.subElementWithText(status, "MsgRef", msgId)
		xmlDoc.subElementWithText(status, "CmdRef", 0)
		xmlDoc.subElementWithText(status, "Cmd", cmd)
		xmlDoc.subElementWithText(status, "CmdID", cmdId)
		xmlDoc.subElementWithText(status, "TargetRef", self.config.get("Enrollment", "MDMServerUrl"))
		xmlDoc.subElementWithText(status, "SourceRef", deviceHardwareId)
		xmlDoc.subElementWithText(status, "Data", DATA_OK_CODE)	
		
	def makeResponse(
		self, 
		deviceHardwareId, 
		sessionId, 
		msgId, 
		emptyMessage = False,
		blockIE = False, 
		blockCortana = False, 
		strictSafeSearch = False,
		checkUserCertificate = False,
		askForPushNotificationToken = False,
		blockOtherApps = False,
		blockUnenrollment = False,
		forceUnenrollment = False,
		blockFactoryReset = False,
		getSynchInterval = False,
		updateSynchInterval = False
	):
		
		xmlDoc = XmlDoc()
		syncML = xmlDoc.element('SyncML')
		xmlDoc.addDefaultNamespaceToElement(syncML, "SYNCML:SYNCML1.2")
		
		syncHdr = xmlDoc.subElement(syncML, "SyncHdr")
	
		xmlDoc.subElementWithText(syncHdr, "VerDTD", "1.2")
		xmlDoc.subElementWithText(syncHdr, "VerProto", "DM/1.2")
		xmlDoc.subElementWithText(syncHdr, "SessionID", sessionId)
		xmlDoc.subElementWithText(syncHdr, "MsgID", msgId)
		
		target = xmlDoc.subElement(syncHdr, "Target")
		xmlDoc.subElementWithText(target, "LocURI", deviceHardwareId)
		
		target = xmlDoc.subElement(syncHdr, "Source")
		xmlDoc.subElementWithText(target, "LocURI", self.config.get("Enrollment", "MDMServerUrl"))
		
		syncBody = xmlDoc.subElement(syncML, "SyncBody")
		
		self.addCommandStatusOK(xmlDoc, syncBody, msgId, "SyncHdr", 1, deviceHardwareId)
				
		cmdId = 0
		
		if not emptyMessage:
			if blockIE:
				self.addBlockIeSection(xmlDoc, syncBody, cmdId)
				cmdId += 1
			
			self.addSetCortanaSection(xmlDoc, syncBody, cmdId, blockCortana)
			cmdId += 1
			
			if strictSafeSearch:
				self.addBlockStrictSafeSearch(xmlDoc, syncBody, cmdId)
				cmdId += 1
			
			if checkUserCertificate:
				self.addBlockGetUserCertificate(xmlDoc, syncBody, cmdId)
				cmdId += 1
			
			if askForPushNotificationToken:
				cmdId += self.addBlockAddPFN(xmlDoc, syncBody, cmdId)
				cmdId += self.addBlockGetChannelURI(xmlDoc, syncBody, cmdId)
			
			if blockOtherApps:
				self.addBlockedApplicationList(xmlDoc, syncBody, cmdId)
				cmdId += 1
				
			self.addBlockSetManualUnenrollment(xmlDoc, syncBody, cmdId, blockUnenrollment)
			cmdId += 1
			
			self.addBlockSetFactoryReset(xmlDoc, syncBody, cmdId, blockFactoryReset)
			cmdId += 1
				
			if forceUnenrollment:
				self.addBlockForceUnenrollment(xmlDoc, syncBody, cmdId)
				cmdId += 1

			if getSynchInterval:
				self.addBlockGetSynchInterval(xmlDoc, syncBody, cmdId)
				cmdId += 1

			if updateSynchInterval:
				self.addBlockUpdateSynchInterval(xmlDoc, syncBody, cmdId)
				cmdId += 1
			
		xmlDoc.subElement(syncBody, "Final")
		return xmlDoc.elementToString(syncML)
		
	def getDeviceHardwareId(self, tree, namespace):
		return tree.find("./{%s}SyncHdr/{%s}Source/{%s}LocURI/." % (namespace, namespace, namespace)).text
	
	def getDeviceId(self, tree, namespace):
		encodedCredData = tree.find("./{%s}SyncHdr/{%s}Cred/{%s}Data/." % (namespace, namespace, namespace)).text
		credData = base64.b64decode(encodedCredData)
		return credData[:credData.find(":")]
	
	def namespaceWithSyncMLVersion(self, tree):
		toReturn = None
		try:
			toReturn = NAMESPACE_1_1
			self.getDeviceHardwareId(tree, toReturn)
		except AttributeError:
			toReturn = NAMESPACE_1_2
			self.getDeviceHardwareId(tree, toReturn)
		return toReturn

	def isUnenrollmentRequest(self, tree, namespace, deviceHardwareIdWithoutPrefix):
		alerts = tree.findall("./{%s}SyncBody/{%s}Alert/." % (namespace, namespace))
		if alerts is not None:
			for alert in alerts:
				alertData = alert.find("./{%s}Data/." % namespace)
				if alertData is not None and int(alertData.text) == UNENROLLMENT_CODE:
					result = globalFunctions.queryApi(
						self.config,
						{"hardware_id": deviceHardwareIdWithoutPrefix},
						self.config.get("API", "UnenrollmentSuccess")
					)
					return True
		return False
	
	def responseWithStandardPolicy(self, deviceHardwareId, sessionId, msgId):
		return self.makeResponse(
			deviceHardwareId,
			sessionId,
			msgId,
			blockIE = True,
			blockCortana = (not self.config.getboolean("OMADM", "AllowCortana")),
			strictSafeSearch = True,
			checkUserCertificate = False,
			askForPushNotificationToken = True,
			blockOtherApps = True,
			blockUnenrollment = (not self.config.getboolean("OMADM", "AllowManualUnenrollment")),
			blockFactoryReset = (not self.config.getboolean("OMADM", "AllowFactoryReset")),
			getSynchInterval = True
		)
	
	def responseWithForceUnenrollment(self, deviceHardwareId, sessionId, msgId):
		return self.makeResponse(deviceHardwareId, sessionId, msgId, forceUnenrollment = True)
	
	def responseForUnenrollment(self, deviceHardwareId, sessionId, msgId):
		return self.makeResponse(deviceHardwareId, sessionId, msgId, emptyMessage = True)
		
	def responseForCloseConnection(self, deviceHardwareId, sessionId, msgId):
		return self.makeResponse(deviceHardwareId, sessionId, msgId, emptyMessage = True)
	
	def responseForChangeSyncInterval(self, deviceHardwareId, sessionId, msgId):
		return self.makeResponse(deviceHardwareId, sessionId, msgId, updateSynchInterval = True)
	
	def getAndSendPushToken(self, tree, namespace, deviceHardwareIdWithoutPrefix):
		items = tree.findall("./{%s}SyncBody/{%s}Results/{%s}Item/." % (namespace, namespace, namespace))
		pushToken = None
		for item in items:
			locUri = item.find("./{%s}Source/{%s}LocURI/." % (namespace, namespace)).text
			if locUri == TOKEN_URI % self.config.get("Enrollment", "ProviderId"):
				pushToken = item.find("./{%s}Data/." % namespace).text
				break
		
		if pushToken is not None:
			queryResult = globalFunctions.queryApi(
				self.config, 
				{"hardware_id": deviceHardwareIdWithoutPrefix, "push_token": pushToken}, 
				self.config.get("API", "AssignPushToken")
			)
			if queryResult["success"] != True:
				globalFunctions.printDebugLog(self.config, "QUERY API FAILED", self.config.get("API", "AssignPushToken") + " response: " + str(result))
			return queryResult["success"] == True
		globalFunctions.printDebugLog(self.config, "Error in obtaining Push Token", "Push Token is None")
		return False
	
	def messageIsForceUnenrollmentResponse(self, tree, namespace):
		statuses = tree.findall("./{%s}SyncBody/{%s}Status/." % (namespace, namespace))
		for status in statuses:
			cmd = status.find("./{%s}Cmd/." % namespace).text
			if cmd == CMD_EXEC:
				return status.find("./{%s}Data/." % namespace).text == "202"
		return False
	
	def getSyncInterval(self, tree, namespace):
		resultList = tree.findall("./{%s}SyncBody/{%s}Results/." % (namespace, namespace))
		for result in resultList:
			locUriNode = result.find("./{%s}Item/{%s}Source/{%s}LocURI/." % (namespace, namespace, namespace))
			if locUriNode is not None:
				locUri = locUriNode.text
				if "IntervalForRemainingScheduledRetries" in locUri:
					return result.find("./{%s}Item/{%s}Data/." % (namespace, namespace)).text
		return None
	
	def checkApiIfUserShouldUnenroll(self, deviceHardwareIdWithoutPrefix):
		result = globalFunctions.queryApi(
			self.config,
			{"hardware_id": deviceHardwareIdWithoutPrefix},
			self.config.get("API", "CheckUnenrollment")
		)
		return result["unenrollment"]
		
	def assignHardwareIdToApi(self, deviceId, deviceHardwareIdWithoutPrefix):
		result = globalFunctions.queryApi(
			self.config,
			{"device_id": deviceId , "hardware_id": deviceHardwareIdWithoutPrefix},
			self.config.get("API", "AssignHardwareId")
		)
		if not result["success"]:
			globalFunctions.printDebugLog(self.config, "QUERY API FAILED", self.config.get("API", "AssignHardwareId") + " response: " + str(result))
		return result["success"]
	
	@cherrypy.expose
	def index(self, **kwargs):
		if 'Content-Type' not in cherrypy.request.headers:
				return "Error, no content type"
		if cherrypy.request.headers['Content-Type'] == CONTENT_TYPE_SYNCML:
			cherrypy.response.headers['Content-Type'] = CONTENT_TYPE_SYNCML
			requestBody = cherrypy.request.body.read()
			tree = ET.fromstring(requestBody)
			xmlDoc = XmlDoc()
			
			globalFunctions.printDebugLog(self.config, "OMADM REQUEST", xmlDoc.elementToString(tree))
			
			namespace = self.namespaceWithSyncMLVersion(tree)
			
			deviceHardwareId = self.getDeviceHardwareId(tree, namespace)
			deviceHardwareIdWithoutPrefix = deviceHardwareId[len(DEVICE_HARDWARE_ID_PREFIX):] 
			deviceId = self.getDeviceId(tree, namespace)
			
			sessionId = tree.find("./{%s}SyncHdr/{%s}SessionID/." % (namespace, namespace)).text
			msgId = tree.find("./{%s}SyncHdr/{%s}MsgID/." % (namespace, namespace)).text
			
			if self.isUnenrollmentRequest(tree, namespace, deviceHardwareIdWithoutPrefix):
				toReturn = self.responseForUnenrollment(deviceHardwareId, sessionId, msgId)
			elif msgId == "1":
				if (
					not self.assignHardwareIdToApi(deviceId, deviceHardwareIdWithoutPrefix) or
					self.checkApiIfUserShouldUnenroll(deviceHardwareIdWithoutPrefix)
				):
					toReturn = self.responseWithForceUnenrollment(deviceHardwareId, sessionId, msgId)
				else:
					toReturn = self.responseWithStandardPolicy(deviceHardwareId, sessionId, msgId)
			elif msgId == "2":
				if self.messageIsForceUnenrollmentResponse(tree, namespace):
					toReturn = self.responseForCloseConnection(deviceHardwareId, sessionId, msgId)
				elif not self.getAndSendPushToken(tree, namespace, deviceHardwareIdWithoutPrefix):
					return "internal error"
				elif self.getSyncInterval(tree, namespace) != self.config.get("Enrollment", "SynchInterval"):
					toReturn = self.responseForChangeSyncInterval(deviceHardwareId, sessionId, msgId)
				else:
					toReturn = self.responseForCloseConnection(deviceHardwareId, sessionId, msgId)
			else:
				toReturn = self.responseForCloseConnection(deviceHardwareId, sessionId, msgId)

			globalFunctions.printDebugLog(self.config, "OMADM RESPONSE", toReturn)
			return toReturn
		
		return "unsupported request"
