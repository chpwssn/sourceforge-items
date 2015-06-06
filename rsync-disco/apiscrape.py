import json, urllib, os
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename", help="input filename", metavar="FILE")
parser.add_option("-s", "--start", dest="start", default=False, help="projet name to start at")
parser.add_option("-e", "--end", dest="end", default=False, help="projet name to end at")
parser.add_option("-o", "--out", dest="out", help="output file")
parser.add_option("-l", "--log", dest="jsonlogdir", help="JSON log directory, for caching replies")
parser.add_option("-i", "--ignorelocal", action="store_true", dest="ignorelocal", default=False, help="ignore the local JSON log")


(options, args) = parser.parse_args()


class IgnoreExecption(Exception):
    pass

class sourceforge:

    def __init__(self,project):
        try:
            if options.ignorelocal:
                raise IgnoreExecption('Ignoring')
            jsonreply = open(options.jsonlogdir+"/"+project+".json").read()
        except IOError:
            print 'Unable to open log, checking online for '+project
            jsonreply = urllib.urlopen("http://sourceforge.net/rest/p/"+project).read()
            if not options.ignorelocal and os.path.isdir(options.jsonlogdir):
                with open(options.jsonlogdir+"/"+project+".json",'w') as jsonlog:
                    jsonlog.write(jsonreply+"\n")
        except IgnoreExecption:
            print 'Ignoring log, checking online for '+project
            jsonreply = urllib.urlopen("http://sourceforge.net/rest/p/"+project).read()
        try:
            self.item = json.loads(jsonreply)
            print "Loaded "+project+" in status: "+self.item['status']
        except ValueError:
            print "JSON failed for "+project
            self.item={}

    def getSCM(self,project,outfile):
        try:
            for tool in self.item.get('tools', []):
                if tool['name'] == "git":
                    print "rsync -av git.code.sf.net::p/"+project+"/"+tool['mount_point']+".git ."
                    outfile.write("rsync:rsync -av git.code.sf.net::p/"+project+"/"+tool['mount_point']+".git .\n")
                elif tool['name'] == "svn":
                    print "rsync -av svn.code.sf.net::p/"+project+"/"+tool['mount_point']+" ."
                    outfile.write("rsync:rsync -av svn.code.sf.net::p/"+project+"/"+tool['mount_point']+" .\n")
                elif tool['name'] == "hg":
                    print "rsync -av hg.code.sf.net::p/"+project+"/"+tool['mount_point']+" ."
                    outfile.write("rsync:rsync -av hg.code.sf.net::p/"+project+"/"+tool['mount_point']+" .\n")
                elif tool['name'] == "cvs":
                    print "rsync -av rsync://"+project+".cvs.sourceforge.net/cvsroot/"+project+"/* ."
                    outfile.write("rsync -av rsync://"+project+".cvs.sourceforge.net/cvsroot/"+project+"/* .")
                elif tool['name'] == "bzr":
                    print "rsync -av "+project+".bzr.sourceforge.net::bzrroot/"+project+"/* ."
                    outfile.write("rsync -av "+project+".bzr.sourceforge.net::bzrroot/"+project+"/* .")
        except AttributeError:
            print "Couldn't get SCM"

if not options.jsonlogdir:
    print "You did not specify a JSON log directory, ignoring and won't cache any replies"
    options.ignorelocal = True

if not options.out:
    print "You did not specify an output file, I don't know where to go..."
    quit(1)

startReached = False
endReached = False
with open(options.out,'w') as outfile:
    with open(options.filename,'r') as infile:
        if not options.start:
            startReached = True;
        for line in infile.read().splitlines():
            try:
                site = line.split(':')[1]
                if options.end:
                    if options.end == site:
                        endReached = True
                if startReached and not endReached:
                    test = sourceforge(site)
                    test.getSCM(site,outfile)
            except IndexError:
                print "Index Error! "+line
