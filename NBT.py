#!/usr/bin/python
# -*- coding: utf-8 -*-
import struct
from io import BytesIO

_dStandardTags = { 0 : (0, ""), 1 : (1, ">B"), 2 : (2, ">h"), 3 : (4, ">i"), 4 : (8, ">q"), 5 : (4, ">f"), 6 : (8, ">d") }
#_lTagName = [ "TAG_End", "TAG_Byte", "TAG_Short", "TAG_Int", "TAG_Long", "TAG_Float", "TAG_Double", "TAG_Byte_Array", "TAG_String", "TAG_List", "TAG_Compund", "TAG_Int_Array" ]

# Reads and returns root tag
def parseRoot(strData):
	# Reset ioData
	ioData = BytesIO(strData)
	curType, curName, curData = _parseTag(ioData)
	return curData
	
def _parseTag(ioData):
	tagType, tagNameLen, tagName = ioData.read(1), 0, ""
	(tagType,) = struct.unpack(">B", tagType)
	
	if tagType != 0:
		tagNameLen = ioData.read(2)
		(tagNameLen,) = struct.unpack(">H", tagNameLen)
		tagName = ioData.read(tagNameLen)

	tagData = _readTag(tagType, ioData)		
	return (tagType, tagName, tagData)
	
def _readTag(tagType, ioData):
	tagData = None
	if tagType in _dStandardTags:
		tagLength, tagUnpack = _dStandardTags[tagType]
		if tagLength > 0:
			tagData = ioData.read(tagLength)
			(tagData,) = struct.unpack( tagUnpack, tagData )
	elif tagType == 7: # Byte array
		sizeArray = _readTag(3, ioData)
		#tagData = [ _readTag(1, ioData) for x in xrange(0,sizeArray) ]
		tagData = ioData.read(sizeArray) # Optimization for bytes
	elif tagType == 11: # Int array
		sizeArray = _readTag(3, ioData)
		tagData = [ _readTag(3, ioData) for x in xrange(0,sizeArray) ]
	elif tagType == 8: # String
		sizeString = _readTag(2, ioData)
		tagData = ioData.read(sizeString)
	elif tagType == 9: # List
		tagId = _readTag(1, ioData)
		countTags = _readTag(3, ioData)
		tagData = [ _readTag(tagId, ioData) for x in xrange(0, countTags) ]
	elif tagType == 10: # Compound
		tagData = dict()
		while True:
			subTagType, subTagName, subTagData = _parseTag(ioData)
			if subTagType == 0: break
			tagData[subTagName] = subTagData
	else:
		raise RuntimeError("Unsupported tag ({0})".format(tagType))		

	return tagData

