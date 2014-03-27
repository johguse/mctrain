#!/usr/bin/python
# -*- coding: utf-8 -*-
from collections import deque
import math

def getDistance(posOne, posTwo):
	return math.sqrt( sum( [ (posOne[x] - posTwo[x]) ** 2 for x in xrange(0, len(posOne)) ] ) )

def componentDivide(dGraph, sClusterNodes):
	lGraphs = []
	sEnd = set([x for x in dGraph if len(dGraph[x]) == 1])
	
	while sEnd:
		curEndNode = sEnd.pop()
		
		sComponent = set([curEndNode])
		sComponentEnd = set()
		
		qLeft = deque([curEndNode])
		while qLeft:
			curNode = qLeft.popleft()
			if len(dGraph[curNode]) == 1:
				sComponentEnd.add(curNode)
				if curNode != curEndNode: sEnd.remove(curNode)
			
			for curAdjacent in dGraph[curNode]:
				if curAdjacent in sComponent: continue
				sComponent.add(curAdjacent)
				qLeft.append(curAdjacent)
		
		# Copy into new graph
		dNewGraph = dict()
		for curNode in sComponent: dNewGraph[curNode] = dGraph[curNode]
		lGraphs.append( (dNewGraph, sComponentEnd, sClusterNodes.intersection(dNewGraph.keys()) ) )
	
	return lGraphs
	
def distanceClusterNodes(dGraph, distJoin):
	# Get end-nodes
	sEnd = set([x for x in dGraph if len(dGraph[x]) == 1])
	
	# Cluster based on distance from end-points
	dCluster = dict()
	lClusters = []
	while sEnd:
		curNode = sEnd.pop()
		if curNode not in dCluster:
			lClusters.append( set([curNode]) )
			dCluster[curNode] = lClusters[-1]
			
		curNodeSet = dCluster[curNode]
		
		for x in sEnd:
			if getDistance(curNode, x) < distJoin:
				# Join two clusters
				if x in dCluster:
					curNodeSet = curNodeSet.union( dCluster[x] )
					dCluster[x] = curNodeSet
					dCluster[curNode] = curNodeSet
				else:
					curNodeSet.add(x)
					dCluster[x] = curNodeSet
	
	# Modify graph based on clustering
	sClusterNodes = set()
	for x in lClusters:
		if len(x) > 1:
			#tKey = ( tuple([sum(y)/len(y) for y in zip(*x)]), str(x))
			
			# The key for the new node will be the average position of all its nodes
			tKey = tuple([sum(y)/len(y) for y in zip(*x)]) 
			sNewAdjacent = set()

			for curClusterNode in x:
				for curAdjacent in dGraph[curClusterNode]:
					if curAdjacent in x: continue # Ignore modifying other nodes also belonging to the cluster, they'll be deleted anyways
					dGraph[curAdjacent].remove(curClusterNode)
					dGraph[curAdjacent].add(tKey)
					sNewAdjacent.add(curAdjacent)
					
				del dGraph[curClusterNode]
			
			dGraph[tKey] = sNewAdjacent
			
			if len(dGraph[tKey]) > 1: # Silently ignore cluster-nodes with only one outgoing edge
				sClusterNodes.add(tKey)
			elif len(dGraph[tKey]) == 0:
				# Remove cluster-nodes without any outgoing edge
				del dGraph[tKey]
								
	return sClusterNodes
			
# Replace each node that has edges to exactly two other nodes (A, B)
# with an edge joining A and B.
# Do not replace nodes with an edge that would result in a cycle dissapearing.
# This corresponds (does it?) to if the nodes A and B already has an edge
# between them.
def minimizeNodes(dGraph, sBlacklist = None ):
	lTwoNodes = []
	for x in dGraph.iterkeys():
		if sBlacklist and x in sBlacklist: continue
		if len(dGraph[x]) == 2: lTwoNodes.append(x)
		
	for curNode in lTwoNodes:
		adjOne = dGraph[curNode].pop()
		adjTwo = dGraph[curNode].pop()
		
		# Order should not matter in bi-directional graph
		if adjTwo not in dGraph[adjOne]:
			del dGraph[curNode]
			dGraph[adjOne].remove(curNode)
			dGraph[adjTwo].remove(curNode)
			dGraph[adjOne].add(adjTwo)
			dGraph[adjTwo].add(adjOne)
		else:
			dGraph[curNode].add(adjOne)
			dGraph[curNode].add(adjTwo)
			print "Keeping this one!"
			
	# Done

def filterPathsAndComponents(dGraph, sEnd, minComponentNodes = None):
	# Identify end-nodes (only one edge)
	# sEnd = set([x for x in dGraph if len(dGraph[x]) == 1])
	
	sKeepNodes = set()
	sAllComponents = set()
	while sEnd:
		curEndNode = sEnd.pop()
		
		sComponent = set([curEndNode])
		sComponentEnd = set()
		dParent = dict()
		dParent[curEndNode] = None
		
		qLeft = deque([curEndNode])
		while qLeft:
			curNode = qLeft.popleft()
			if curNode in sEnd: sComponentEnd.add(curNode)
			
			# These are to prioritize nodes already marked to keep.
			# This prevents finding an additional shortest path if there are several.
			lPrioAdjacent = []
			lAdjacent = []
			
			for curAdjacent in dGraph[curNode]:
				if curAdjacent in sComponent: continue
				if curAdjacent in sKeepNodes:
					lPrioAdjacent.append(curAdjacent)
				else:
					lAdjacent.append(curAdjacent)
					
				sComponent.add(curAdjacent)
				dParent[curAdjacent] = curNode
				
			for curAdjacent in lPrioAdjacent: qLeft.append(curAdjacent)
			for curAdjacent in lAdjacent: qLeft.append(curAdjacent)
			
		# Remember nodes to keep. Work backwards from identified end-nodes -> optimal path
		sCurKeepNodes = set([curEndNode])
		for curNode in sComponentEnd:
			if curNode == curEndNode: continue
			while dParent[curNode]:
				sCurKeepNodes.add(curNode)
				curNode = dParent[curNode]
				
		# If this component with reduced paths is made of too little rail, discard it and its end-nodes
		if minComponentNodes and len(sCurKeepNodes) < minComponentNodes:
			for curComponentEndNode in sComponentEnd:
				if curComponentEndNode != curEndNode:
					sEnd.remove(curComponentEndNode)
			continue
			
		for curKeepNode in sCurKeepNodes: sKeepNodes.add(curKeepNode)
	
	# Remove any nodes that are not part of a shortest path -> partial cycle elimination
	for curNode in dGraph.keys():
		if curNode not in sKeepNodes:
			for curAdjacent in dGraph[curNode]:
				dGraph[curAdjacent].remove(curNode)
			del dGraph[curNode]
		
	# Done!
