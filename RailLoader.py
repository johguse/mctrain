#!/usr/bin/python
# -*- coding: utf-8 -*-
import RegionReader
import os.path

# cPickle or pickle
try: import cPickle as pickle
except ImportError: import pickle
	
def getRail( strFile, strPathCache = None, bOnlyCache = False):
	curRegionName = os.path.basename(strFile)
	bNeedLoad = True
	dRegionRails = dict()
	dRegionLabels = dict()
	
	if strPathCache:
		try:
			curRegionCache = os.path.join(strPathCache, curRegionName)
			curRegionCacheModTime = curRegionCache + ".time"
			with open(curRegionCacheModTime, "r") as fileIn: curModTime = pickle.load(fileIn)
			
			if not curModTime < os.path.getmtime(strFile) or bOnlyCache:
				with open(curRegionCache, "r") as fileIn: (dRegionRails, dRegionLabels) = pickle.load(fileIn)
				bNeedLoad = False
		except IOError:
			pass
		except EOFError:
			pass
			
	if bNeedLoad:
		if bOnlyCache: raise RuntimeError("No cache for region file, but only-cache option is enabled ({0})".format(curRegionName))
			
		RegionReader.readRegionRails(strFile, dRegionRails, dRegionLabels)
		
		if strPathCache:
			try:
				curModTime = os.path.getmtime(strFile)
				with open(curRegionCacheModTime, "w") as fileOut: pickle.dump(curModTime, fileOut)
				with open(curRegionCache, "w") as fileOut: pickle.dump((dRegionRails, dRegionLabels), fileOut)
			except IOError:
				print "warning: failed to write to region-cache"
				
	return (dRegionRails, dRegionLabels)
