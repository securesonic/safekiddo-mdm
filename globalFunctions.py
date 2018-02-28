import random
import datetime
import urllib, urllib2, json

#GUID is globally unique identifier used in .NET
#it could be in format dddddddd-dddd-dddd-dddd-dddddddddddd where d is from 0 to F
def makeGuid():
	guid = ""
	for i in range (0, 32):
		guid += format(random.randint(0, 16), 'x')
		if i in [6, 10, 14, 18]:
			guid += "-"
	return guid

def printDebugLog(config, name, msg):
	if config.getboolean("Logs", "DebugLog"):
		with open(config.get('Logs', 'stdout'), "a") as logFile:
			logFile.write("####################\n")
			logFile.write("[%s] %s\n" % (str(datetime.datetime.now()), name))
			logFile.write("--------------------\n")
			logFile.write(msg)
			logFile.write("\n####################\n")
		
def queryApi(config, data, path):
	postData = urllib.urlencode(data)
	req = urllib2.Request(config.get("API", "ApiHost") + path, postData)
	resultJson = urllib2.urlopen(req).read()
	return json.loads(resultJson)
