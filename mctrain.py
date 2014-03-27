#!/usr/bin/python
# -*- coding: utf-8 -*-

# Imports
from concurrent.futures import ProcessPoolExecutor
import RailLoader
import DotWriter
import GMLWriter
import argparse
import Graph
import time
import sys

def labelNodes(dRails, dAllLabels, optLabelDistance):
	dLabels = dict()
	
	for curNode in dRails.iterkeys():
		dPossibleLabels = dict( [ (Graph.getDistance(curNode,x), y[0]) for x, y in dAllLabels.iteritems() ] )
		if not dPossibleLabels: continue
		minDist = min( dPossibleLabels.iterkeys() )
		if minDist > optLabelDistance: continue
		dLabels[curNode] = dPossibleLabels[minDist]
	
	return dLabels

def printHelp(strName):
	print "mctrain.py - johguse@student.chalmers.se"
	print "usage: {0} [options] <region-files>".format(strName)
	print ""
	print "Ease of use:"
	print "\t--set-all=<float> \t\t- Sets a number of variables to this value (recommended: 40)"
	
def parseArg(s, defVal):
	(a,b,c) = s.partition("=")
	if not c:
		print "warning: Missing argument for {0}".format(a)
	else:
		try:
			fReturn = float(c)
			if fReturn < 0.0: raise ValueError
			return fReturn
		except ValueError:
			print "warning: Invalid value for {0}".format(a)
	
	return defVal

# Hack for ProcessPoolExecutor
def railLoaderHelper(strFile):
	global args
	return RailLoader.getRail(strFile, args.strCache, args.bOnlyCache)
		
def main():
	global args
	argParser = argparse.ArgumentParser(	add_help=True,
											epilog="Don't have any expections on this piece of software. It's an ugly mess of a hack mainly for personal use.",
											usage="%(prog)s [options] regionFile [regionFile ...]")
											
	curGroup = argParser.add_argument_group("cache")
	curGroup.add_argument("--cache", dest="strCache", type=str, metavar="<str>", default=False, help="Path to cache, unique to the region-files specified")
	curGroup.add_argument("--only-cache", dest="bOnlyCache", action="store_true", default=False, help="Don't read region-files, use only the cache")
	
	curGroup = argParser.add_argument_group("generic")
	curGroup.add_argument("--distance-label", dest="distanceLabel", type=float, metavar="<float>", default=False, help="Distance to look for a sign labeling a node")
	curGroup.add_argument("--component-rail", dest="componentRail", type=int, metavar="<int>", default=30, help="Disregard components comprised of too little rail (default: 30)")
	
	curGroup = argParser.add_argument_group("second pass")
	curGroup.add_argument("--distance-cluster", dest="distanceCluster", type=float, metavar="<float>", default=False, help="Distance used for clustering nodes")
	
	curGroup = argParser.add_argument_group("dividing components")	
	curGroup.add_argument("--component-divide", dest="bComponentDivide", action="store_true", default=False, help="Divide graph into connected components <required>")
	curGroup.add_argument("--combine-pairs", dest="bCombinePairs", action="store_true", default=False, help="Combine all pairs of nodes into one graph")
	curGroup.add_argument("--distance-min", dest="distanceMin", type=float, metavar="<float>", default=False, help="Disregard components where the longest distance between end-nodes are too short")
	
	curGroup = argParser.add_argument_group("drawing")	
	curGroup.add_argument("--switch-as-endpoint", dest="bSwitchAsEndpoint", action="store_true", default=False, help="Draw switches as endpoints")
	curGroup.add_argument("--label-edges", dest="bLabelEdges", action="store_true", default=False, help="Label edges according to geometric distance")
	curGroup.add_argument("--edge-weight", dest="edgeWeight", type=float, metavar="<float>", default=False, help="Draw geometrically longer edges as thicker")
	
	curGroup = argParser.add_argument_group("regions")	
	curGroup.add_argument("regionFile", type=str, nargs="+", help="Region files (.mca) that the graph should be generated from")
	args = argParser.parse_args()

	dLabels = dict()
	sClusterNodes = set()
	print "Fetching rail data..."
	timeStart = time.time()
	dRails, dAllLabels = dict(), dict()
	lenRegionsLeft = len(args.regionFile)

	with ProcessPoolExecutor() as executor:
		for dRegionRails, dRegionLabels in executor.map( railLoaderHelper, args.regionFile ):
			lenRegionsLeft -= 1
			print "\r\tReading regions: {0:>6}".format(lenRegionsLeft),
			sys.stdout.flush()
			for x, y in dRegionRails.items() : dRails[x] = y
			for x, y in dRegionLabels.items() : dAllLabels[x] = y
					
	print ""
		
	# Prune non-existant edges and add edge back if it doesn't exist, for example in intersections
	# This will create some illegal intersections if they exist in the map. Tough luck.
	print "\tAdding bidirectionality..."
	for curPos, sEdges in dRails.iteritems():
		sEdges = set([x for x in sEdges if x in dRails])
		for edge in sEdges: dRails[edge].add(curPos)
		dRails[curPos] = sEdges
		
	timePerRegion = (time.time() - timeStart) / len(args.regionFile)
	print "\tSeconds per region: {0:.2}s".format(timePerRegion)
	print "\tNodes = {0}, Labels = {1}".format( len(dRails), len(dAllLabels) )
	
	print "Generating first pass rudimentary graph..."
	print "\tRemoving nodes not used in any shortest path and small components..."
	Graph.filterPathsAndComponents(dRails, set([x for x in dRails if len(dRails[x]) == 1]), args.componentRail)
	print "\tMerging nodes with only two edges..."
	Graph.minimizeNodes(dRails)
	print "\tNodes = {0}".format( len(dRails) )
	
	if args.distanceCluster:
		print "Generating second pass graph based on distance..."
		print "\tClustering neighbouring nodes..."
		sClusterNodes = Graph.distanceClusterNodes(dRails, args.distanceCluster)
		print "\tRemoving nodes not used in any shortest path..."
		Graph.filterPathsAndComponents( dRails, sClusterNodes.union( [x for x in dRails if len(dRails[x]) == 1] ), None )
		sClusterNodes = set( [x for x in sClusterNodes if len(dRails[x]) > 1 ] )
		print "\tMerging nodes with only two edges..."
		Graph.minimizeNodes(dRails, sClusterNodes)
		print "\tNodes = {0}".format( len(dRails) )
		
	if args.distanceLabel: dLabels = labelNodes(dRails, dAllLabels, args.distanceLabel)
		
	if args.bComponentDivide:
		lGraphs = Graph.componentDivide(dRails, sClusterNodes)
	else:
		lGraphs = [(dRails, None, sClusterNodes)]
		
	if args.distanceMin:
		if not args.bComponentDivide:
			print "warning: min distance filter need components to be divided"
		else:
			print "Removing components with distance < {0}".format(args.distanceMin)
			lGraphDistances = []
			for (curGraph, curEndings, sClusterNodes) in lGraphs:
				maxDistance = 0
				for curEnding in curEndings:
					lDistances = [ Graph.getDistance(curEnding, x) for x in curEndings ]
					curMax = max(lDistances)
					if curMax > maxDistance: maxDistance = curMax
				
				lGraphDistances.append(maxDistance)
			
			lenBefore = len(lGraphs)
			lGraphs = [ x for x, y in zip(lGraphs, lGraphDistances) if y > args.distanceMin ]
			lenAfter = len(lGraphs)
			print "\t{0} components removed".format(lenBefore-lenAfter)
					
	if args.bCombinePairs:
		if not args.bComponentDivide:
			print "warning: combining components containing only a pair of nodes needs components to be divided"
		else:
			lGraphPairs = [ (x, y, z) for (x, y, z) in lGraphs if len(y) == 2 ]
			if lGraphPairs > 1:
				lGraphs = [ (x, y, z) for (x, y, z) in lGraphs if len(y) != 2 ]
				dPairCombined = dict()
				sUnionEndings = set()
				sUnionClusterNodes = set()
				for curGraph, curEndings, curClusterNodes in lGraphPairs:
					for x, y in curGraph.iteritems(): dPairCombined[x] = y
					sUnionEndings = sUnionEndings.union(curEndings)
					sUnionClusterNodes = sUnionClusterNodes.union(curClusterNodes)
				
				lGraphs.append( (dPairCombined, sUnionEndings, sUnionClusterNodes) )
	
	# Generate .DOT and write them
	for i in xrange(0, len(lGraphs)):
		strGraphDot = DotWriter.generateDot( lGraphs[i][0], lGraphs[i][1], lGraphs[i][2], dLabels, args.bSwitchAsEndpoint, args.bLabelEdges, args.edgeWeight )
		strGraphGML = GMLWriter.generateGML( lGraphs[i][0], lGraphs[i][1], lGraphs[i][2], dLabels, args.bSwitchAsEndpoint, args.bLabelEdges, args.edgeWeight )
		
		with open("mctrain-graph-{0}.dot".format(i), "w") as fileOut: fileOut.write(strGraphDot)
		with open("mctrain-graph-{0}.graphml".format(i), "w") as fileOut: fileOut.write(strGraphGML)
		
	print "Done."
	return 0
		
if __name__ == "__main__":
	sys.exit(main())
	