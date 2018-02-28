import urllib2
import mockupsLib

opener = urllib2.build_opener()
request = urllib2.Request(mockupsLib.getDiscoveryRequestUrl()+"/EnrollmentServer/Discovery.svc", headers={'Content-Type': 'unknown'})
response = opener.open(request)
print response.info()