#!/usr/bin/python
# -*- coding: utf-8 -*-
import zlib
import struct
import heapq
import NBT

def parseRegionFile(strFile):
	qOffsets = []
	lChunks = []
	
	with open(strFile, "rb") as fileIn:
		# Read and parse locations
		dataLocations = fileIn.read(4096)
		lChunkSize = []
		for i in xrange(0,1024):
			curLocation = dataLocations[i*4:i*4 + 4]
			(curData,) = struct.unpack(">I", curLocation)
			curOffset, curLength = curData >> 8, curData & 0xFF
			if curOffset == 0 and curLength == 0: continue
			
			heapq.heappush(qOffsets, curOffset * 4096)
		
		# Read chunks
		while qOffsets:
			curOffset = heapq.heappop(qOffsets)
			fileIn.seek( curOffset, 0 )
			
			# Parse length of chunk
			lenChunk = fileIn.read(4)
			(lenChunk, ) = struct.unpack(">I", lenChunk)
			
			# Read chunk
			dataChunkCompressed = fileIn.read(lenChunk)
			(curCompression,) = struct.unpack(">B", dataChunkCompressed[0])
			
			# Decompress and add to list
			if curCompression != 2: raise RuntimeError("Unsupported compression used ({0})".format(curCompression))
			lChunks.append( zlib.decompress(dataChunkCompressed[1:]) )
	
	lChunks = [ NBT.parseRoot(x) for x in lChunks ]
	return lChunks

# Coordinates
# ===========
# X increases East, decreases West
# Y increases upwards, decreases downwards
# Z increases South, decreases North

# Rail connections
_lRailConnection = [
	( ( 0, 0,  1),  ( 0,  0, -1) ), # Flat track going north-south
	( ( 1, 0,  0),  (-1,  0,  0) ), # Flat track going west-east
	( ( 1, 1,  0),  (-1, -1,  0) ), # Track ascending to the east
	( (-1, 1,  0),  ( 1, -1,  0) ), # Track ascending to the west
	( ( 0, 1, -1),  ( 0, -1,  1) ), # Track ascending to the north
	( ( 0, 1,  1),  ( 0, -1, -1) ), # Track ascending to the south
	( ( 1, 0,  0),  ( 0,  0,  1) ), # Northwest corner (connecting east and south)
	( (-1, 0,  0),  ( 0,  0,  1) ), # Northeast corner (connecting west and south)
	( (-1, 0,  0),  ( 0,  0, -1) ), # Southeast corner (connecting west and north)
	( ( 1, 0,  0),  ( 0,  0, -1) ), # Southwest corner (connecting east and north)
]

def _getConnectingTiles( tPos, blockId, blockData ):
	global _lRailConnection
	
	# Only regular rails have corner connections
	if blockId != 66 and blockData > 5:
		blockData = blockData & 0b111
	
	tConnection = _lRailConnection[blockData]
	tPosOne = tuple( [ sum(x) for x in zip( tPos, tConnection[0] ) ] )
	tPosTwo = tuple( [ sum(x) for x in zip( tPos, tConnection[1] ) ] )
	
	return set([tPosOne, tPosTwo])
	
def readRegionRails(strRegionFile, dRails = None, dLabels = None ):
	if dRails == None: dRails = dict()
	if dLabels == None: dLabels = dict()
	
	lRailID = [27, 28, 66, 42, 157]
	
	lChunks = parseRegionFile(strRegionFile)
	for dData in lChunks:
		for curSection in dData["Level"]["Sections"]:
			yOffset = curSection["Y"] * 16
			xOffset = dData["Level"]["xPos"] * 16
			zOffset = dData["Level"]["zPos"] * 16
			
			for i in xrange(0,4096):
				curBlockId = ord(curSection["Blocks"][i])
				if curBlockId in lRailID:
					# Position
					x, z, y = i % 16 + xOffset, (i / 16) % 16 + zOffset, (i / 256) + yOffset
					tPos = (x,y,z)
					
					# Additional data
					blockDataPos = i / 2
					blockDataRot = (i % 2) * 4
					dataBlock = (ord(curSection["Data"][blockDataPos]) >> blockDataRot) & 0x0F
					
					# Neighbours
					neighbours = _getConnectingTiles( (x,y,z), curBlockId, dataBlock )
					
					# Add to rails
					if tPos in dRails: raise RuntimeError("Rail in duplicate position!")
					dRails[tPos] = neighbours
		
		for curEntity in dData["Level"]["TileEntities"]:
			if curEntity.get("id","") != "Sign": continue
			if curEntity["Text1"] != "-MCTRAIN-": continue
			strDescription = curEntity["Text2"] + curEntity["Text3"]
			strDescription = strDescription.replace("\"", "\\")
			if curEntity["Text4"]:
				dLabels[ (curEntity["x"], curEntity["y"], curEntity["z"]) ] = ( curEntity["Text2"], curEntity["Text4"] )
			else:
				dLabels[ (curEntity["x"], curEntity["y"], curEntity["z"]) ] = (strDescription,strDescription)
			
	return (dRails, dLabels)