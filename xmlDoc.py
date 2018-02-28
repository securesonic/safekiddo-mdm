import xml.etree.ElementTree as ET
from xml.dom import minidom

class XmlDoc:
	def __init__(self):
		self.Namespaces = {}
		
	def makeNamespaceString(self, namespace):
		namespaceString = ""
		if namespace != None:
			namespaceString = '{'+self.Namespaces[namespace]+'}'
		return namespaceString 
	
	def elementToString(self, elem, pretty = True):
		rough_string = ET.tostring(elem, 'utf-8')
		if pretty:
			reparsed = minidom.parseString(rough_string)
			return reparsed.toprettyxml(indent="  ")
		return rough_string
	
	def addNamespace(self, prefix, uri):
		self.Namespaces[prefix] = uri
		ET.register_namespace(prefix, uri)
		
	def addAttribute(self, element, attribute, value, namespace = None):
		element.set(self.makeNamespaceString(namespace)+attribute, value)
		
	def addText(self, element, value):
		element.text = value
		
	def addDefaultNamespaceToElement(self, element, uri):
		self.addAttribute(element, "xmlns", uri)
		
	def addSchemaXsi(self, element):
		self.addAttribute(element, "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
		
	def addSchemaXsd(self, element):
		self.addAttribute(element, "xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
		
	# Needed to make something like <o:Node  xmlns:o= "http://namespace.com/dummy">	
	def subElementWithNamespace(self, parent, element, prefix, uri):
		toReturn = ET.SubElement(parent, prefix+":"+element)
		self.addAttribute(toReturn, "xmlns:"+prefix, uri)
		return toReturn
		
	def element(self, element, namespace = None):
		return ET.Element(self.makeNamespaceString(namespace)+element)
	
	def subElement(self, parent, element, namespace = None):
		return ET.SubElement(parent, self.makeNamespaceString(namespace)+element)
	
	def subElementWithText(self, parent, element, text, namespace = None):
		toReturn = self.subElement(parent, element, namespace)
		self.addText(toReturn, str(text))
		return toReturn
	