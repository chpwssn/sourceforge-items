import json, urllib, os, time, re
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename", help="input filename", metavar="FILE")
parser.add_option("-o", "--outfile", dest="outfile", help="output filename", metavar="FILE")

(options, args) = parser.parse_args()

with open(options.outfile,'w') as outfile:
    outfile.write("projectname,mountpoint,rsync,numfiles,filesize(bytes)\n")
    with open(options.filename,'r') as file:
        for line in file.read().splitlines():
            project = re.findall('::p/([^/]*)/', line)
            mountpoint = re.findall('/([^/]*)\s', line)
            rsync = re.findall('\s([^\s]*)\s\.',line)
            if len(project) == 0:
                project = re.findall('rsync://([^.]*)\.',line)
                mountpoint = re.findall('/([^/]*)/\*\s', line)
                if len(project) == 0:
                    project = re.findall('([^.\s]*)\.bzr',line)
            if len(project) > 0:
                print project
                print mountpoint
                print rsync
                response = os.popen("rsync -av --stats --dry-run "+rsync[0]+" foo").read()
                numfiles = re.findall('Number of files: ([0-9]+)', response)
                filesize = re.findall('Total file size: ([^\n]+)', response)
                print filesize
                line =  project[0]+","+mountpoint[0]+","+rsync[0]+","+numfiles[0]+",\""+filesize[0]+"\""
                print line
                outfile.write(line+"\n")
            else:
                print "Failed to parse line: "+line
            #time.sleep(1)
#rsync://easyblockinterf
