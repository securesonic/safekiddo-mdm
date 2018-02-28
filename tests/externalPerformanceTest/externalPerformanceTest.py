#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import subprocess
import urllib2
import json
import time
import sys, os
import multiprocessing

sys.path.append(os.path.abspath(__file__ + '/../../library/'))
import copiedRequests

MDM_HOST = "tst-mdm.safekiddo.com"
PORT = 443
TIMEOUT = 5

DISCOVERY = "discovery"
DISCOVERY_MALFORMED = "discoveryMalformed"
DISCOVERY_WRONG_HEADER = "discoveryWrongHeader"

ENROLLMENT = "enrollment"
ENROLLMENT_MALFORMED = "enrollmentMalformed"
ENROLLMENT_WRONG_HEADER = "enrollmentWrongHeader"

OMADM = "omadm"
OMADM_MALFORMED = "omadmMalformed"
OMADM_WRONG_HEADER = "omadmWrongHeader"
DEVICE_ID = "43"
DEVICE_HARDWARE_ID = "6CAF8D6F-4A44-5802-A7A2-E79E344BABD4"

threads = []

def sendHealthChecks():
	for i in (1, 10):
		req = urllib2.Request("https://%s:%d/healthCheck/" % (MDM_HOST, PORT))
		result = urllib2.urlopen(req, timeout = TIMEOUT).read()
		time.sleep(1)

def sendRequest(type):
	opener = urllib2.build_opener()
	headers = None
	data = None
	catchServerError = False
	url = "https://%s:%d/" % (MDM_HOST, PORT)
	
	if type == DISCOVERY:
		url += "EnrollmentServer/Discovery.svc"
		headers = copiedRequests.getDiscoveryHeaders()
		data = copiedRequests.getDiscoveryXml()
	if type == DISCOVERY_MALFORMED:
		catchServerError = True
		url += "EnrollmentServer/Discovery.svc"
		headers = copiedRequests.getDiscoveryHeaders()
		data = copiedRequests.getDiscoveryXml()[7:50]
	if type == DISCOVERY_WRONG_HEADER:
		url += "EnrollmentServer/Discovery.svc"
		headers = copiedRequests.getEnrollmentHeaders()
		data = copiedRequests.getDiscoveryXml()
	if type == ENROLLMENT:
		url += "EnrollmentServer/Enrollment.svc"
		headers = copiedRequests.getEnrollmentHeaders()
		data = copiedRequests.getEnrollmentXml("36662@tst.safekiddo.com", "1234")
	if type == ENROLLMENT_MALFORMED:
		catchServerError = True
		url += "EnrollmentServer/Enrollment.svc"
		headers = copiedRequests.getEnrollmentHeaders()
		data = copiedRequests.getEnrollmentXml('">\'<', '">\'<')
	if type == ENROLLMENT_WRONG_HEADER:
		catchServerError = True
		url += "EnrollmentServer/Enrollment.svc"
		headers = copiedRequests.getOmadmHeaders()
		data = copiedRequests.getEnrollmentXml('">\'<', '">\'<')	
	if type == OMADM:
		url += "omadm/WindowsPhone.ashx"
		headers = copiedRequests.getOmadmHeaders()
		data = copiedRequests.getOmadmXml(DEVICE_HARDWARE_ID, DEVICE_ID)
	if type == OMADM_MALFORMED:
		catchServerError = True
		url += "omadm/WindowsPhone.ashx"
		headers = copiedRequests.getOmadmHeaders()
		data = copiedRequests.getOmadmXml(DEVICE_HARDWARE_ID, DEVICE_ID)[11:30]
	if type == OMADM_WRONG_HEADER:
		catchServerError = True
		url += "omadm/WindowsPhone.ashx"
		headers = copiedRequests.getDiscoveryHeaders()
		data = copiedRequests.getOmadmXml(DEVICE_HARDWARE_ID, DEVICE_ID)
	
	try:
		request = urllib2.Request(url, data=data, headers=headers)
		response = opener.open(request)
	except urllib2.HTTPError:
		if not catchServerError:
			raise

def main():	
	sockets = {}
	SOCKET_NUM = 200
	
	for i in range(SOCKET_NUM):
		sockets[i] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sockets[i].connect((MDM_HOST, PORT))
	
	print "%d sockets are opened" % SOCKET_NUM
	
	HEALTHCHECK_NUM = 50
	for i in range(HEALTHCHECK_NUM):
		thread = multiprocessing.Process(target=sendHealthChecks)
		threads.append(thread)
		thread.start()
	
	print "%d healtcheck threads started" % HEALTHCHECK_NUM
	
	REPORT_REQUESTS_NUM = 10
	
	types = [
		DISCOVERY, 
		ENROLLMENT, 
		OMADM, 
		DISCOVERY_MALFORMED, 
		ENROLLMENT_MALFORMED, 
		OMADM_MALFORMED, 
		DISCOVERY_WRONG_HEADER, 
		ENROLLMENT_WRONG_HEADER,
		OMADM_WRONG_HEADER
	]
	
	for i in range(REPORT_REQUESTS_NUM):
		for type in types:
			thread = multiprocessing.Process(target=sendRequest, args=[type])
			threads.append(thread)
			thread.start()
	
	print "%d reports threads started" % (REPORT_REQUESTS_NUM * len(types))

if __name__ == '__main__':
	try:
		cleanExit = True
		try:
			main()
		except (SystemExit, KeyboardInterrupt):
			pass # --help in arguments
		except:
			cleanExit = False
			raise
	finally:

		for t in threads:
			t.join()
			if cleanExit:
				assert t.exitcode == 0, "thread exitcode should be 0 but is %s" % t.exitcode

print "OK"
