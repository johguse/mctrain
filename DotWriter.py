#!/usr/bin/python
# -*- coding: utf-8 -*-
import Graph

def generateDot( dGraph, sEndings, sClusterNodes, dLabels, bSwitchAsEndpoint = False, bLabelEdges = False, dWeighEdges = False ):
	dAttrIntersection = { "shape":"point", "style":"filled", "fillcolor":"black", "label":"\"\"", "height":0.1, "width":0.1 }
	dAttrStation = { "shape":"doublecircle", "style":"filled", "fillcolor":"\"#7BF4FF\"", "label":"\"STATION\\n{0},{1},{2}\"" }
	dAttrSwitch = { "shape" : "doublecircle", "style" : "filled", "fillcolor":"\"#FFB879\"", "label":"\"\"", "height":0.2, "width":0.2  }
	dAttrEndpoint = { "shape" : "box", "style":"filled", "fillcolor": "\"#BDFF79\"", "label":"\"{0},{1},{2}\""}
	
	dEdge = dict()
	dNode = dict()
	lLines = [ "strict graph {" ]
	
	for curNode, sAdjacent in dGraph.iteritems():
		if curNode in dNode: continue
		bLabelNode = False
		
		if curNode in sClusterNodes:
			# Station
			if len(sAdjacent) > 2:
				dNode[curNode] = dAttrStation
				bLabelNode = True
			# Switch
			elif len(sAdjacent) == 2:
				if curNode in dLabels or bSwitchAsEndpoint:
					bLabelNode = True
					dNode[curNode] = dAttrEndpoint
				else:
					dNode[curNode] = dAttrSwitch
			# Madness
			else:
				raise RuntimeError("Non-standard clusternode, should not exist.")
		else:
			if len(sAdjacent) > 1:
				dNode[curNode] = dAttrIntersection
			elif len(sAdjacent) == 1:
				dNode[curNode] = dAttrEndpoint
				bLabelNode = True
			else:
				raise RuntimeError("Single node, should not exist.")
		
		# Copy template
		dNode[curNode] = dNode[curNode].copy()
		
		# Label node
		if curNode in dLabels and bLabelNode:
			dNode[curNode]["label"] = "\"" + dLabels[curNode] + "\""
		elif dNode[curNode].get("label", "\"\"") != "\"\"":
			dNode[curNode]["label"] = dNode[curNode]["label"].format( *curNode )
							
		for curAdjacent in sAdjacent:
			tEdge = (curAdjacent, curNode)
			if tEdge in dEdge: continue
			dEdge[ (curNode, curAdjacent) ] = dict()
			
			if bLabelEdges: dEdge[ (curNode, curAdjacent) ]["label"] = "\"{0}\"".format( int(Graph.getDistance(curNode, curAdjacent) ) )
	
	edgeLenMax = max([ Graph.getDistance(x,y) for (x,y) in dEdge.iterkeys() ])
	
	for curNode, dAttributes in dNode.iteritems():
		if dAttributes:
			lLines.append( "\"" + str(curNode) + "\" [" + ",".join( [ x + "=" + str(y) for x,y in dAttributes.items() ] ) + "];" )
		else:
			lLines.append( "\"" + str(curNode) + "\";" )
		
	for (edgeStart, edgeEnd), dAttributes in dEdge.iteritems():
		if dAttributes:
			if dWeighEdges: dAttributes["penwidth"] = ( Graph.getDistance(edgeStart, edgeEnd) / edgeLenMax ) * dWeighEdges + 1.0
			lLines.append( "\"" + str(edgeStart) + "\" -- \"" + str(edgeEnd) + "\" [" + ",".join( [ x + "=" + str(y) for x,y in dAttributes.items() ] ) + "];" )
		else:
			lLines.append( "\"" + str(edgeStart) + "\" -- \"" + str(edgeEnd) + "\";" )
		
	lLines.append( "}" )
	return "\n".join(lLines)