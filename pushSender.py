import cherrypy
import urllib, urllib2
import json
import globalFunctions

HARDWARE_ID = "hardware_id"

class PushSender():
	
	def __init__(self, config):
		self.config = config
		self.accessToken = None
	
	def returnError(self, msg):
		return {"success": False, "error": msg}
	
	def accessTokenRequestContent(self):
		return "grant_type=client_credentials&client_id=%s&client_secret=%s&scope=notify.windows.com" % (self.config.get("OMADM", "SID"), urllib.quote(self.config.get("OMADM", "ClientSecret")))
		
	def authorize(self):
		headers = {'Content-Type': 'application/x-www-form-urlencoded'}
		
		req = urllib2.Request("https://login.live.com/accesstoken.srf", self.accessTokenRequestContent(), headers)
		result = urllib2.urlopen(req)
		resultObject = json.loads(result.read())
		
		self.accessToken = resultObject["access_token"]
		
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def index(self, **kwargs):
		self.authorize()
		
		if "hardware_id" not in cherrypy.request.params:
			return self.returnError("Missing POST parametr - hardware_id")

		headers = {}
		headers['Content-Type'] = 'application/octet-stream'
		headers['Authorization'] = 'Bearer %s' % self.accessToken
		headers['X-WNS-Type'] = "wns/raw"
			
		queryResult = globalFunctions.queryApi(
			self.config, 
			{"hardware_id": cherrypy.request.params["hardware_id"]}, 
			self.config.get("API", "GetPushToken")
		)
		
		if queryResult["success"] != True or "push_token" not in queryResult:
			return self.returnError("Error in communication with API, response: " + str(queryResult))
		
		pushToken = queryResult["push_token"]
		
		try:
			req = urllib2.Request(pushToken, "ok", headers)
			result = urllib2.urlopen(req).read()
		except urllib2.HTTPError, err:
			return self.returnError("Windows Service returned with http code %d" % err.code)
		
		return {"success": True}
