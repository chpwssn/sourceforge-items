import json, urllib
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename", help="input filename", metavar="FILE")
parser.add_option("-s", "--start", dest="start", default=False, help="projet name to start at")
parser.add_option("-e", "--end", dest="end", default=False, help="projet name to end at")
parser.add_option("-o", "--out", dest="out", help="output file")

(options, args) = parser.parse_args()


class sourceforge:
    
    def __init__(self,project):
        try:
            self.item = json.loads(urllib.urlopen("http://sourceforge.net/rest/p/"+project).read())
            print "Loaded "+project+" in status: "+self.item['status']
        except ValueError:
            print "JSON failed for "+project

    def getSCM(self,project,outfile):
        try:
            for tool in self.item['tools']:
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
                    print "rsync -av cvs.code.sf.net::p/"+project+"/"+tool['mount_point']+" ."
                    outfile.write("rsync -av cvs.code.sf.net::p/"+project+"/"+tool['mount_point']+" .\n")
                elif tool['name'] == "bazaar":
                    print "rsync -av bazaar.code.sf.net::p/"+project+"/"+tool['mount_point']+" ."
                    outfile.write("rsync -av bazaar.code.sf.net::p/"+project+"/"+tool['mount_point']+" .\n")
        except AttributeError:
            print "Couldn't get SCM"


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