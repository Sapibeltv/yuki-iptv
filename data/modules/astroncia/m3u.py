#!/usr/bin/python3
# Purpose:    
# Usage:    
# Author:    Timmy93
# Date:        
# Version:    
# Disclaimer:    

import os
import re

class M3uParser:
    
    def __init__(self, udp_proxy):
        self.files = []
        self.udp_proxy = udp_proxy
    
    #Read the file from the given path
    def readM3u(self, filename):
        self.filename = filename
        self.readAllLines()
        self.parseFile()
        return self.files

    #Read all file lines
    def readAllLines(self):
        self.lines = [line.rstrip('\n') for line in self.filename.strip().split('\n')]
        if not self.lines[-1]:
            self.lines.pop()
        if self.lines[0].startswith('#EXTM3U'):
            self.lines.pop(0)
        i = -1
        for l in self.lines:
            i += 1
            if l.startswith('#EXTGRP:'):
                self.lines.pop(i)
            self.lines[i] = l.rstrip()
        return len(self.lines)
    
    def parseFile(self):
        numLine = len(self.lines)
        for n in range(numLine):
            line = self.lines[n]
            if line[0] == "#":
                self.manageLine(n)
    
    def manageLine(self, n):
        lineInfo = self.lines[n]
        lineLink = self.lines[n+1]
        if lineInfo != "#EXTM3U":
            m = re.search("tvg-name=\"(.*?)\"", lineInfo)
            try:
                name = m.group(1)
            except AttributeError:
                name = ""
            m = re.search("tvg-ID=\"(.*?)\"", lineInfo)
            try:
                id = m.group(1)
            except AttributeError:
                id = ""
            m = re.search("tvg-logo=\"(.*?)\"", lineInfo)
            try:
                logo = m.group(1)
            except AttributeError:
                logo = ""
            m = re.search("group-title=\"(.*?)\"", lineInfo)
            try:
                group = m.group(1)
            except AttributeError:
                group = "Все каналы"
            if not group:
                group = "Все каналы"
            m = re.search("[,](?!.*[,])(.*?)$", lineInfo)
            try:
                title = m.group(1)
            except AttributeError:
                title = ""
            # ~ print(name+"||"+id+"||"+logo+"||"+group+"||"+title)

            up = self.udp_proxy
            if up and (lineLink.startswith('udp://') or lineLink.startswith('rtp://')):
                lineLink = up + "/" + lineLink.replace("udp://", "udp/").replace("rtp://", "rtp/")
                lineLink = lineLink.replace('//udp/', '/udp/').replace('//rtp/', '/rtp/')    

            test = {
                "title": title,
                "tvg-name": name,
                "tvg-ID": id,
                "tvg-logo": logo,
                "tvg-group": group,
                "url": lineLink
            }
            self.files.append(test)
            
    def exportJson(self):
        #TODO
        print("Not implemented")
    
    #Remove files with a certain file extension
    def filterOutFilesEndingWith(self, extension):
        self.files = list(filter(lambda file: not file["titleFile"].endswith(extension), self.files))
    
    #Select only files with a certain file extension
    def filterInFilesEndingWith(self, extension):
        #Use the extension as list
        if not isinstance(extension, list):
            extension = [extension]
        if not len(extension):
            self.logging.info("No filter in based on extensions")
            return
        new = []
        #Iterate over all files and extensions
        for file in self.files:    
            for ext in extension:
                if file["titleFile"].endswith(ext):
                    #Allowed extension - go to next file
                    new.append(file)
                    break
        self.logging.info("Filter in based on extension: ["+",".join(extension)+"]")
        self.files = new
    
    #Remove files that contains a certain filterWord
    def filterOutFilesOfGroupsContaining(self, filterWord):
        self.files = list(filter(lambda file: filterWord not in file["tvg-group"], self.files))

    #Select only files that contais a certain filterWord
    def filterInFilesOfGroupsContaining(self, filterWord):
        #Use the filter words as list
        if not isinstance(filterWord, list):
            filterWord = [filterWord]
        if not len(filterWord):
            self.logging.info("No filter in based on groups")
            return
        new = []
        for file in self.files:
            for fw in filterWord:    
                if fw in file["tvg-group"]:
                    #Allowed extension - go to next file
                    new.append(file)
                    break
        self.logging.info("Filter in based on groups: ["+",".join(filterWord)+"]")
        self.files = new

    #Getter for the list
    def getList(self):
        return self.files
        
    #Return the info assciated to a certain file name
    def getCustomTitle(self, originalName):
        result = list(filter(lambda file: file["titleFile"] == originalName, self.files))
        if len(result):
            return result
        else:
            print("No file corresponding to: "+originalName)

    #Return a random element
    def getFile(self, randomShuffle):
        if not len(self.files):
            self.logging.error("No files in the array, cannot extract anything")
            return None
        return self.files.pop()
