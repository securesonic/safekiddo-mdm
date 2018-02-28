import urllib2
import mockupsLib

#copypast from mdm documentation
xml_string = """<?xml version="1.0"?> <s:Envelope xmlns:a="http://www.w3.org/2005/08/addressing" xmlns:s="http://www.w3.org/2003/05/soap-envelope"> <s:Header> <a:Action s:mustUnderstand="1"> http://schemas.microsoft.com/windows/management/2012/01/enrollment/IDiscoveryService/Discover </a:Action> <a:MessageID>urn:uuid: 748132ec-a575-4329-b01b-6171a9cf8478</a:MessageID> <a:ReplyTo> <a:Address>http://www.w3.org/2005/08/addressing/anonymous</a:Address> </a:ReplyTo> <a:To s:mustUnderstand="1"> https://ENROLLTEST.CONTOSO.COM/EnrollmentServer/Discovery.svc </a:To> </s:Header> <s:Body> <Discover xmlns="http://schemas.microsoft.com/windows/management/2012/01/enrollment/"> <request xmlns:i="http://www.w3.org/2001/XMLSchema-instance"> <EmailAddress>user@contoso.com</EmailAddress> <RequestVersion>2.0</RequestVersion> <!-- Updated Windows Phone 8.1 --> <DeviceType>WindowsPhone</DeviceType> <!--Added in Windows Phone 8.1--> </request> </Discover> </s:Body> </s:Envelope>
"""

opener = urllib2.build_opener()
request = urllib2.Request(mockupsLib.getDiscoveryRequestUrl()+"/EnrollmentServer/Discovery.svc", data=xml_string, headers={'Content-Type': 'application/soap+xml; charset=utf-8'})
response = opener.open(request)
print response.info()
print response.read()