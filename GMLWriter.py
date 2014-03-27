#!/usr/bin/python
# -*- coding: utf-8 -*-
import Graph
import xml.sax.saxutils

def generateGML( dGraph, sEndings, sClusterNodes, dLabels, bSwitchAsEndpoint = False, bLabelEdges = False, dWeighEdges = False ):
	dAttrIntersection = { "shape":"ellipse", "style":"filled", "fillcolor":"#000000", "label":"", "height":14, "width":14 }
	dAttrStation = { "shape":"ellipse", "style":"filled", "fillcolor":"#7BF4FF", "label":"STATION\\n{0},{1},{2}" }
	dAttrSwitch = { "shape" : "ellipse", "style" : "filled", "fillcolor":"#FFB879", "label":"", "height":16, "width":16  }
	dAttrEndpoint = { "shape" : "rectangle", "style":"filled", "fillcolor": "#BDFF79", "label":"{0},{1},{2}"}
	
	dEdge = dict()
	dNode = dict()
	lLines = []
	lLines.append(r'<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
	lLines.append(r'<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:y="http://www.yworks.com/xml/graphml" xmlns:yed="http://www.yworks.com/xml/yed/3" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd">')
	lLines.append(r'<key for="edge" id="d9" yfiles.type="edgegraphics"/>')
	lLines.append(r'<key for="node" id="d6" yfiles.type="nodegraphics"/>')
	lLines.append(r'<graph edgedefault="undirected" id="G">')

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
			dNode[curNode]["label"] = dLabels[curNode]
		elif dNode[curNode].get("label", ""):
			dNode[curNode]["label"] = dNode[curNode]["label"].format( *curNode )
							
		for curAdjacent in sAdjacent:
			tEdge = (curAdjacent, curNode)
			if tEdge in dEdge: continue
			dEdge[ (curNode, curAdjacent) ] = dict()
			
			if bLabelEdges: dEdge[ (curNode, curAdjacent) ]["label"] = "{0}".format( int(Graph.getDistance(curNode, curAdjacent) ) )
	
	edgeLenMax = max([ Graph.getDistance(x,y) for (x,y) in dEdge.iterkeys() ])
	
	for curNode, dAttributes in dNode.iteritems():
		lLines.append(r'<node id="{0}">'.format(curNode))
		if dAttributes:
			lLines.append(r'<data key="d6">'.format(curNode))
			lLines.append(r'<y:ShapeNode>'.format(curNode))
			if "width" in dAttributes and "height" in dAttributes: lLines.append(r'<y:Geometry height="{0}" width="{1}" />'.format( dAttributes["height"], dAttributes["width"] ) )
			if "fillcolor" in dAttributes: lLines.append(r'<y:Fill color="{0}" />'.format(dAttributes["fillcolor"]) )
			if "label" in dAttributes: lLines.append(r'<y:NodeLabel>{0}</y:NodeLabel>'.format(xml.sax.saxutils.escape(dAttributes["label"].replace("\\n", "\n")) ) )
			if "shape" in dAttributes: lLines.append(r'<y:Shape type="{0}"/>'.format(dAttributes["shape"]) )
			lLines.append(r'</y:ShapeNode>')
			lLines.append(r'</data>')
		lLines.append(r'</node>')
		
	for (edgeStart, edgeEnd), dAttributes in dEdge.iteritems():
		lLines.append( r'<edge id="{0}" source="{1}" target="{2}">'.format( (edgeStart, edgeEnd), edgeStart, edgeEnd ) )
		lLines.append( r'<data key="d9"><y:PolyLineEdge><y:Arrows source="none" target="none"/></y:PolyLineEdge></data>' )
		lLines.append( r'</edge>' )
		
	lLines.append(r'</graph>')
	lLines.append(r'</graphml>')

	return "\n".join(lLines)