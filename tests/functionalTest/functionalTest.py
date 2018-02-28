#!/usr/bin/python
# -*- coding: utf-8 -*-
# Test scenario:
# Step 1: Connect to localhost discovery server (first empty msg)
# Step 2: Connect to localhost discovery server and obtain response, parse it and get Enrollment Servel URL
# Step 3: Connect to Enrollment Server from obtained URL, log in with test credentials and obtain OMA DM server URL
# Step 4: Connect to OMA DM server and parse response, check if default config blocks IE and Cortana 

import urllib2
import xml.etree.ElementTree as ET
import base64
import sys, os
import ConfigParser

sys.path.append(os.path.abspath(__file__ + '/../../library/'))
import copiedRequests

sys.path.append(os.path.abspath(__file__ + '/../../../'))
import mdmServer

sys.path.append(os.path.abspath(__file__ + '/../../../../../scripts/library/'))
import runner

processes = {}

ENROLLMENT_USERNAME = "55722@dev.safekiddo.com"
ENROLLMENT_PASSWORD = "1234"
DEVICE_ID = "176"
DEVICE_HARDWARE_ID = "6CAF8D6F-4A44-5802-A7A2-E79E344BABD4"

ENROLLMENT_SERVICE_URL = "http://localhost:59191/EnrollmentServer/Enrollment.svc"
DISCOVERY_URL = "http://localhost:59191/wp"
OMADM_URL = "http://localhost:59191/omadm/WindowsPhone.ashx"

NAMESPACE_S = "http://www.w3.org/2003/05/soap-envelope"
NAMESPACE_ENROLLMENT = "http://schemas.microsoft.com/windows/management/2012/01/enrollment"
NAMESPACE_WSTRUST = "http://docs.oasis-open.org/ws-sx/ws-trust/200512"
NAMESPACE_WSSECURITY = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
NAMESPACE_SYNCML = "SYNCML:SYNCML1.2"

ALLOW_BROWSER_URI = "./Vendor/MSFT/PolicyManager/My/Browser/AllowBrowser"
ALLOW_CORTANA_URI = "./Vendor/MSFT/PolicyManager/My/Experience/AllowCortana"

def main():
	runner.startMdmServer(processes)
		
	#Step 1
	opener = urllib2.build_opener()
	request = urllib2.Request(DISCOVERY_URL, headers={'Content-Type': 'unknown'})
	response = opener.open(request)
	
	#Step 2
	request = urllib2.Request(DISCOVERY_URL, data=copiedRequests.getDiscoveryXml(), headers=copiedRequests.getDiscoveryHeaders())
	response = opener.open(request)
	tree = ET.fromstring(response.read())
	enrollmentServiceUrl = tree.find("./{%s}Body/{%s}DiscoverResponse/{%s}DiscoverResult/{%s}EnrollmentServiceUrl/."
		% (NAMESPACE_S, NAMESPACE_ENROLLMENT, NAMESPACE_ENROLLMENT, NAMESPACE_ENROLLMENT)).text
	assert enrollmentServiceUrl == ENROLLMENT_SERVICE_URL
	
	#Step 3
	opener = urllib2.build_opener()
	request = urllib2.Request(enrollmentServiceUrl, data=copiedRequests.getEnrollmentXml(ENROLLMENT_USERNAME, ENROLLMENT_PASSWORD), headers=copiedRequests.getEnrollmentHeaders())
	response = opener.open(request)
	tree = ET.fromstring(response.read())
	wapXmlInBase64 = tree.find("./{%s}Body/{%s}RequestSecurityTokenResponseCollection/{%s}RequestSecurityTokenResponse/{%s}RequestedSecurityToken/{%s}BinarySecurityToken/."
		% (NAMESPACE_S, NAMESPACE_WSTRUST, NAMESPACE_WSTRUST, NAMESPACE_WSTRUST, NAMESPACE_WSSECURITY)).text
	wapXml = base64.standard_b64decode(wapXmlInBase64)
	wapXmlTree = ET.fromstring(wapXml)
	omaDmUrl = wapXmlTree.find("./characteristic[@type='APPLICATION']/parm[@name='ADDR']/.").get('value')
	assert omaDmUrl == OMADM_URL
	
	#Step 4
	opener = urllib2.build_opener()
	request = urllib2.Request(omaDmUrl, data=copiedRequests.getOmadmXml(DEVICE_HARDWARE_ID, DEVICE_ID), headers=copiedRequests.getOmadmHeaders())
	response = opener.open(request)
	tree = ET.fromstring(response.read())
	syncBody = tree.find("./{%s}SyncBody/." % NAMESPACE_SYNCML)
	
	allowBrowser = None
	allowCortana = None
	for child in syncBody:
		locUriNode = child.find("./{%s}Item/{%s}Target/{%s}LocURI/." 
			% (NAMESPACE_SYNCML, NAMESPACE_SYNCML, NAMESPACE_SYNCML))
		if locUriNode is not None:
			if locUriNode.text == ALLOW_BROWSER_URI:
				allowBrowser = child.find("./{%s}Item/{%s}Data/." % (NAMESPACE_SYNCML, NAMESPACE_SYNCML)).text
			if locUriNode.text == ALLOW_CORTANA_URI:
				allowCortana = child.find("./{%s}Item/{%s}Data/." % (NAMESPACE_SYNCML, NAMESPACE_SYNCML)).text
	
	assert allowBrowser == "0"
	assert allowCortana == "1"
	
	print "ALL TESTS OK"

if __name__ == '__main__':
	try:
		try:
			main()
		except (SystemExit, KeyboardInterrupt):
			pass # --help in arguments
		except:
			runner.testFailed(processes)
			raise
	finally:
		print 'Tearing down'
		runner.teardown(processes)
