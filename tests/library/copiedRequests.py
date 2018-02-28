#THIS XMLs ARE COPYPASTED FROM MDM DOCUMENTATION
import base64

def getDiscoveryXml():
	return """<?xml version="1.0"?> 
		<s:Envelope xmlns:a="http://www.w3.org/2005/08/addressing" xmlns:s="http://www.w3.org/2003/05/soap-envelope">
			<s:Header>
				<a:Action s:mustUnderstand="1">http://schemas.microsoft.com/windows/management/2012/01/enrollment/IDiscoveryService/Discover</a:Action> 
				<a:MessageID>urn:uuid: 748132ec-a575-4329-b01b-6171a9cf8478</a:MessageID>
				<a:ReplyTo>
					<a:Address>http://www.w3.org/2005/08/addressing/anonymous</a:Address>
				</a:ReplyTo>
				<a:To s:mustUnderstand="1">https://ENROLLTEST.CONTOSO.COM/EnrollmentServer/Discovery.svc</a:To>
			</s:Header>
			<s:Body>
				<Discover xmlns="http://schemas.microsoft.com/windows/management/2012/01/enrollment/">
					<request xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
						<EmailAddress>user@contoso.com</EmailAddress>
						<RequestVersion>2.0</RequestVersion>
						<!-- Updated Windows Phone 8.1 -->
						<DeviceType>WindowsPhone</DeviceType>
						<!--Added in Windows Phone 8.1-->
					</request>
				</Discover>
			</s:Body>
		</s:Envelope>
		"""
def getDiscoveryHeaders():
	return {'Content-Type': 'application/soap+xml; charset=utf-8'}
	
def getEnrollmentXml(username, password):
	return """<?xml version="1.0" ?>
		<s:Envelope 
			xmlns:a="http://www.w3.org/2005/08/addressing"
			xmlns:ns2="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
			xmlns:ns3="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd" 
			xmlns:ns4="http://docs.oasis-open.org/ws-sx/ws-trust/200512" 
			xmlns:ns5="http://schemas.xmlsoap.org/ws/2006/12/authorization" 
			xmlns:s="http://www.w3.org/2003/05/soap-envelope">
			<s:Header>
				<a:Action s:mustUnderstand="1">http://schemas.microsoft.com/windows/pki/2009/01/enrollment/RST/wstep</a:Action>
				<a:MessageID>urn:uuid:0d5a1441-5891-453b-becf-a2e5f6ea3749</a:MessageID>
				<a:ReplyTo>
					<a:Address>http://www.w3.org/2005/08/addressing/anonymous</a:Address>
				</a:ReplyTo>
				<a:To s:mustUnderstand="1">http://dev-mdm.safekiddo.com/EnrollmentServer/Enrollment.svc</a:To>
				<ns2:Security s:mustUnderstand="1">
					<ns2:UsernameToken ns3:Id="uuid-cc1ccc1f-2fba-4bcf-b063-ffc0cac77917-4">
						<ns2:Username>"""+username+"""</ns2:Username>
						<ns2:Password ns2:Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">"""+password+"""</ns2:Password>
					</ns2:UsernameToken>
				</ns2:Security>
			</s:Header>
			<s:Body>
				<ns4:RequestSecurityToken>
					<ns4:TokenType>http://schemas.microsoft.com/5.0.0.0/ConfigurationManager/Enrollment/DeviceEnrollmentToken</ns4:TokenType>
					<ns4:RequestType>http://docs.oasis-open.org/ws-sx/ws-trust/200512/Issue</ns4:RequestType>
					<ns2:BinarySecurityToken 
						EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd#base64binary" 
						ValueType="http://schemas.microsoft.com/windows/pki/2009/01/enrollment#PKCS10">
						MIICcTCCAV0CAQAwMDEuMCwGA1UEAxMlQjFDNDNDRDAtMTYyNC01RkJCLThFNTQtMzRDRjE3REZEM0ExADCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKN2eQIx3/R3OS/xNC0auTYv+2yRxZB3NjkjWV5MGPDk7CxYS43NoR0NBS/YkPGpZn+hnVL5LchjITcZnLnaou0L1S43QblXVkTz9EcU83ah5VNYh5dtxdsHdVDJJAq1ne7buabbVn8nUupBmx/NgwxmNZt+1jMvyoSuKGUzrDM83j812yJNtCYXJiIaASelL1yBozAKKrPuyYMo6lw3gz0Ty4ZSeyfXf/55l1/cR6RqTg2WTqE8E48vEOglkxt2TdSzPrrJnm4FiJbsjaQfZ1y8wu9DOufG/i5LI4ypDaeF09p1Mpo8BuNR/1WqzwVPGGKbiT+AFts1pdS9mBbhNtkCAwEAAaAAMAkGBSsOAwIdBQADggEBAFIeRh1bOwP6Ztf+i7pVr+CLvYy6gGTctx1YUEoCYskxDmjJbfCqcDA4pX+uxbP+lnRSuAJsQcSQg6bEU7vYlFE1xMH0VzxR/lMHqtSRI18Fy9suVccK31maejV+xdBOTffWaZCVj3pvpfYv6A97q3CuCwW7fH3v9+lLW1TyNs8KUEW9rpwY8zqIn9JYSAtfdd5tCjy1XF+Zi3clHSVSVFw8ekuZyrk8MZldg3TzH79M1lS+s3iFWKtEzoH/3LL2jXZ1lD/5GU9yqSm/DyoPVlo5y+1eDpaarF9077EsgnRhg2PBSxpflfyYE4dyGVRRT0aNhx9vC/0GaOq9uVkwsd4=
					</ns2:BinarySecurityToken>
					<ns5:AdditionalContext>
						<ns5:ContextItem Name="DeviceType">
							<ns5:Value>WindowsPhone</ns5:Value>
						</ns5:ContextItem>
						<ns5:ContextItem Name="ApplicationVersion">
							<ns5:Value>8.10.12397.895</ns5:Value>
						</ns5:ContextItem>
					</ns5:AdditionalContext>
				</ns4:RequestSecurityToken>
			</s:Body>
		</s:Envelope>
		"""
	
def getEnrollmentHeaders():
	return {'Content-Type': 'application/soap+xml; charset=utf-8'}
	
def getOmadmXml(deviceHardwareId, deviceId):
	credData = deviceId + ":dummy"
	encodedCredData = base64.b64encode(credData)
	return """<?xml version="1.0" encoding="UTF-8"?>
		<SyncML xmlns="SYNCML:SYNCML1.2">
			<SyncHdr>
				<VerDTD>1.2</VerDTD>
				<VerProto>DM/1.2</VerProto>
				<SessionID>1</SessionID>
				<MsgID>1</MsgID>
				<Target>
					<LocURI>https://dev-mdm.safekiddo.com/omadm/WindowsPhone.ashx</LocURI>
				</Target>
				<Source>
					<LocURI>urn:uuid:""" + deviceHardwareId + """</LocURI>
				</Source>
				<Cred>
					<Meta>
						<Format xmlns="syncml:metinf">b64</Format>
						<Type xmlns="syncml:metinf">syncml:auth-basic</Type>
					</Meta>
					<Data>"""+encodedCredData+"""</Data>
				</Cred>
			</SyncHdr>
			<SyncBody>
				<Alert>
					<CmdID>2</CmdID>
					<Data>1201</Data>
				</Alert>
				<Replace>
					<CmdID>3</CmdID>
					<Item>
						<Source>
							<LocURI>./DevInfo/DevId</LocURI>
						</Source>
						<Data>urn:uuid:""" + deviceHardwareId + """</Data>
					</Item>
					<Item>
						<Source>
							<LocURI>./DevInfo/Man</LocURI>
						</Source>
						<Data>NOKIA</Data>
					</Item>
					<Item>
						<Source>
							<LocURI>./DevInfo/Mod</LocURI>
						</Source>
						<Data>Lumia 630</Data>
					</Item>
					<Item>
						<Source>
							<LocURI>./DevInfo/DmV</LocURI>
						</Source>
						<Data>1.3</Data>
					</Item>
					<Item>
						<Source>
							<LocURI>./DevInfo/Lang</LocURI>
						</Source>
						<Data>en-US</Data>
					</Item>
				</Replace>
				<Final />
			</SyncBody>
		</SyncML>
		"""

def getOmadmHeaders():
	return {'Content-Type': 'application/vnd.syncml.dm+xml'}