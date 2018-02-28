import urllib2
import mockupsLib

#copypast from mdm documentation
xml_string = """<?xml version="1.0" encoding="UTF-8"?><SyncML xmlns="SYNCML:SYNCML1.2"><SyncHdr><VerDTD>1.2</VerDTD><VerProto>DM/1.2</VerProto><SessionID>1</SessionID><MsgID>1</MsgID><Target><LocURI>https://dev-mdm.safekiddo.com/omadm/WindowsPhone.ashx</LocURI></Target><Source><LocURI>urn:uuid:CE9DF168-3B6A-5099-83CB-A49FC6613F9D</LocURI></Source><Cred><Meta><Format xmlns="syncml:metinf">b64</Format><Type xmlns="syncml:metinf">syncml:auth-basic</Type></Meta><Data>ZHVtbXk6ZHVtbXk=</Data></Cred></SyncHdr><SyncBody><Alert><CmdID>2</CmdID><Data>1201</Data></Alert><Replace><CmdID>3</CmdID><Item><Source><LocURI>./DevInfo/DevId</LocURI></Source><Data>urn:uuid:CE9DF168-3B6A-5099-83CB-A49FC6613F9D</Data></Item><Item><Source><LocURI>./DevInfo/Man</LocURI></Source><Data>NOKIA</Data></Item><Item><Source><LocURI>./DevInfo/Mod</LocURI></Source><Data>Lumia 630</Data></Item><Item><Source><LocURI>./DevInfo/DmV</LocURI></Source><Data>1.3</Data></Item><Item><Source><LocURI>./DevInfo/Lang</LocURI></Source><Data>en-US</Data></Item></Replace><Final /></SyncBody></SyncML>
"""

opener = urllib2.build_opener()
request = urllib2.Request(mockupsLib.getDiscoveryRequestUrl()+"/omadm/WindowsPhone.ashx", data=xml_string, headers={'Content-Type': 'application/vnd.syncml.dm+xml'})
response = opener.open(request)
print response.info()
print response.read()