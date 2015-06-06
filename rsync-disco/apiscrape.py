import json, urllib, os, time
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename", help="input filename", metavar="FILE")
parser.add_option("-s", "--start", dest="start", default=False, help="projet name to start at")
parser.add_option("-e", "--end", dest="end", default=False, help="projet name to end at")
parser.add_option("-o", "--out", dest="out", help="output file")
parser.add_option("-l", "--log", dest="jsonlogdir", help="JSON log directory, for caching replies")
parser.add_option("-i", "--ignorelocal", action="store_true", dest="ignorelocal", default=False, help="ignore the presence of any local JSON log")
parser.add_option("-w", "--writecache", action="store_true", dest="writecache", default=False, help="write to the local JSON log")
parser.add_option("-a", "--actions", dest="actions", help="comma separated list of data to extract")

(options, args) = parser.parse_args()

def startAndEndSuffix():
    return ("_S_%s" % options.start if options.start else "")+("_E_%s" % options.end if options.end else "")
def pageAndLimitSuffix(page, limit):
    return ("_P%d" % page if page != 1 else "")+("_L%d" % limit if limit != 100 else "")

if not options.jsonlogdir:
    print "You did not specify a JSON log directory, ignoring and won't cache any replies"
    options.ignorelocal = True
    options.writecache = False

if not options.actions:
    print "Defaulting to running getSCM() only"
    actions = ["SCM"]
elif options.actions == 'none':
    if not options.writecache:
        print 'Doing no actions makes no sense without writing to the cache!'
        quit(1)
    print 'Doing no actions, just writing to the cache'
    actions = []
else:
    actions = options.actions.split(",")

if not options.out and actions:
    options.out = os.path.basename(options.filename)+"-"+('-'.join(actions))+startAndEndSuffix()
    print 'No outfile specified, using '+options.out

outfile = None
sums = {}

class sourceforge:

    def __init__(self,project):
        self.project=project
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

    def getStatusCounts(self):
        status = self.item.get('status','[unknown]')
        sums.setdefault(status, 0)
        sums[status] += 1

    def finishStatusCounts(self):
        self.output(`sums`)

    def load(self, path, page=1, limit=100):
        urlpath=self.project+("/"+path if path else "")
        #TODO: Make sure the first two chars of urlpath is an alnum or dash
        baselogdir = options.jsonlogdir+"/"+urlpath[:2].lower()
        logpath=baselogdir+"/"+urlpath.replace('/','_')+pageAndLimitSuffix(page, limit)+".json"
        url = "http://sourceforge.net/rest/p/%s?page=%d&limit=%d" % (urlpath, page, limit)
        if options.ignorelocal:
            print "Ignoring any caching, checking online for " + url
            jsonreply = self.urlReq(url)
        else:
            try:
                jsonreply = open(logpath).read()
            except IOError:
                print 'Unable to open json log, checking online for '+url
                jsonreply = self.urlReq(url)
        try:
            j = json.loads(jsonreply)
            if options.writecache:
                if not os.path.isdir(baselogdir):
                    os.mkdir(baselogdir)
                newreply = json.dumps(j, sort_keys=True)+"\n"
                if jsonreply != newreply:
                    print "Updating cache for "+logpath
                    with open(logpath,'w') as jsonlog:
                        jsonlog.write(newreply)
            return j
        except ValueError as e:
            print "JSON failed for "+url
            raise e
            return {}

    def output(self, txt):
        print "Writing to output file: "+txt
        global outfile
        if not outfile:
            outfile = open(options.out, 'w')
        outfile.write(txt+"\n")

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


with open(options.filename,'r') as infile:
    try:
        startReached = not options.start
        sites = []
        for line in infile.read().splitlines():
            try:
                site = line.split(':')[1]
            except ValueError as e:
                print "missing colon in index file!"
                raise e
            if options.end and site.startswith(options.end):
                break
            if not startReached and site.startswith(options.start):
                startReached = True
            if startReached:
                sites.append(site)

        length = len(sites)
        for n in range(length):
            site = sites[n]
            print '%d/%d (%d%%): Processing %s' % (n, length, int(100*n/length), site)
            test = sourceforge(site)
            if test.item:
                for x in actions:
                    print 'Running get'+x+"()"
                    getattr(test, "get"+x.strip())()

        for x in actions:
            finisher=getattr(test, "finish"+x.strip(), None)
            if finisher:
                print 'Running finish'+x+"()"
                finisher()
    finally:
        if outfile:
            outfile.close()

