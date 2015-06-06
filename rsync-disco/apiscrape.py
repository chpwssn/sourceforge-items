import json, urllib, os, time
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename", help="input filename", metavar="FILE")
parser.add_option("-s", "--start", dest="start", default=False, help="projet name to start at")
parser.add_option("-e", "--end", dest="end", default=False, help="projet name to end at")
parser.add_option("-o", "--out", dest="out", help="output file")
parser.add_option("-l", "--log", dest="jsonlogdir", help="JSON log directory, for caching replies")
parser.add_option("-i", "--ignorelocal", action="store_true", dest="ignorelocal", default=False, help="ignore the local JSON log")
parser.add_option("-a", "--actions", dest="actions", help="comma separated list of data to extract")

(options, args) = parser.parse_args()

if not options.jsonlogdir:
    print "You did not specify a JSON log directory, ignoring and won't cache any replies"
    options.ignorelocal = True

if not options.out:
    print "You did not specify an output file, I don't know where to go..."
    quit(1)

if not options.actions:
    options.actions = "SCM"

class sourceforge:

    def __init__(self,project, outfile):
        self.project=project
        self.outfile=outfile
        self.item = self.load("")
        status = self.item.get('status')
        if status:
            print "Loaded "+project+" in status: "+self.item['status']
        else:
            print "Unable to load "+project

    def getSCM(self):
        try:
            for tool in self.item.get('tools', []):
                if tool['name'] == "git":
                    self.output("rsync -av git.code.sf.net::p/"+self.project+"/"+tool['mount_point']+".git .")
                elif tool['name'] == "svn":
                    self.output("rsync -av svn.code.sf.net::p/"+self.project+"/"+tool['mount_point']+" .")
                elif tool['name'] == "hg":
                    self.output("rsync -av hg.code.sf.net::p/"+self.project+"/"+tool['mount_point']+" .")
                elif tool['name'] == "cvs":
                    self.output("rsync -av rsync://"+self.project+".cvs.sourceforge.net/cvsroot/"+self.project+"/* .")
                elif tool['name'] == "bzr":
                    self.output("rsync -av "+self.project+".bzr.sourceforge.net::bzrroot/"+self.project+"/* .")
        except AttributeError as e:
            print "Couldn't get SCM"
            raise e

    def getTrackers(self):
        for tool in self.item.get('tools',[]):
            if tool['name'] == 'tickets':
                tracker = self.load(tool['mount_point'], limit=1)
                self.output("%s/%s: %d" % (self.project, tool['mount_point'], tracker['count']))
                
    def load(self, path, page=1, limit=100):
        urlpath=self.project+("/"+path if path else "")
        assert urlpath[:2].isalnum()
        logpath=options.jsonlogdir+"/"+urlpath[:2].lower()+"/"+urlpath.replace('/','_')+".json"
        url = "http://sourceforge.net/rest/p/%s?page=%d&limit=%d" % (urlpath, page, limit)
        if options.ignorelocal:
            print "Ignoring any caching, checking online for "+url
            jsonreply = self.urlReq(url)
        else:
            try:
                jsonreply = open(logpath).read()
            except IOError:
                print 'Unable to open json log, checking online for '+url
                jsonreply = self.urlReq(url)
        try:
            j = json.loads(jsonreply)
            if not options.ignorelocal:
                with open(logpath,'w') as jsonlog:
                    jsonlog.write(json.dumps(j)+"\n")
            return j
        except ValueError as e:
            print "JSON failed for "+url
            raise e
            return {}

    def output(self, txt):
        print txt
        self.outfile.write(txt+"\n")
        
    def urlReq(self, url, retry=1):
        try:
            u = urllib.urlopen(url)
            if u.code == 404:
                print "404 Not Found for "+url
                return "{}"
            if u.code == 504:
                print "504 Gateway Timeout for "+url
                if retry>5:
                    raise IOError("Too many retries!")
                time.sleep(5)
                return self.urlReq(url, retry+1)
            if u.code != 200:
                raise IOError("Unexpected HTTP code: %d" % (u.code))
            return u.read()
        except IOError as e:
            print "urlopen failed for "+url
            raise e
            return "invalid JSON"


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
                    test = sourceforge(site, outfile)
                    if test.item:
                        for x in options.actions.split(","):
                            print 'Running get'+x+"()"
                            getattr(test, "get"+x.strip())()
            except IndexError as e:
                print "Index Error! "+line
                raise e
