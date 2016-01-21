#!/usr/bin/python
# simple test program (from the XML-RPC specification)
from xmlrpclib import ServerProxy, ProtocolError, Error, Binary
import datetime, base64, zlib, glob, sys, os, random, time, subprocess
from optparse import OptionParser

#http://code.activestate.com/recipes/134892/
class _Getch:
	"""Gets a single character from standard input.  Does not echo to the screen."""
	def __init__(self):
		try:
			self.impl = _GetchWindows()
		except ImportError:
			self.impl = _GetchUnix()

	def __call__(self): return self.impl()


class _GetchUnix:
	def __init__(self):
		import tty, sys

	def __call__(self):
		import sys, tty, termios
		fd = sys.stdin.fileno()
		old_settings = termios.tcgetattr(fd)
		try:
			tty.setraw(sys.stdin.fileno())
			ch = sys.stdin.read(1)
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		return ch


class _GetchWindows:
	def __init__(self):
		import msvcrt

	def __call__(self):
		import msvcrt
		return msvcrt.getch()


##################################################################################
# Set Configuration Parameters	
##################################################################################
parser = OptionParser()
parser.add_option("-u", "--user", dest="user",
									help='xmlrpc service user name', metavar="USER")
parser.add_option("-p", "--pass", dest="passwd",
									help='xmlrpc service password', metavar="PASS")
parser.add_option("-a", "--authenticate-only", dest="authenticateOnly", default="false",
								 help='if set, returns true[1] or false [0] based on credintials (default false)', metavar="BOOL")
parser.add_option("-x", "--xmlrpcURI", dest="xmlrpcServer", default="mindmodeling.org/jobs/xmlrpc/",
								 help='xmlrpc service URI', metavar="URI")
parser.add_option("-r", "--local-repository", dest="datarepo", metavar="REPO",
								 help='location where all job data exists on the local system')
parser.add_option("-i", "--jobId", dest="jobId", metavar="ID",
								 help='global job idenifier to pull from (use -j or -v option to identify global identifiers for each job)')
parser.add_option("-j", "--jobList", dest="jobList", action="store_true",
								 help='prints out a comma delimeted list of owned jobs ( global job idenifier, job name, job status)')
parser.add_option("-d", "--destination_directory", dest="jobDir", metavar="DIR",
								 help='override location where to place the config file and results file on the local system')
parser.add_option("-s", "--ssl", dest="ssl", metavar="BOOL", 
								 default="true",
								 help='use https (or http) for xmlrpc server calls (default true)')
parser.add_option("-m", "--monitor", dest="monitor", metavar="BOOL", 
								 default="true",
								 help='dictates whether or not to continue trying to download data until the job reaches completion or just to stop once all current results have been obtained (default true)')
parser.add_option("-w", "--wait-time", dest="waitTime", metavar="SECS", default=5,
								 help='the time to wait between retries when no new data is retrieved from the system (defualt 5 secs)')
parser.add_option("-c", "--auto-continue", dest="continueOn", action="store_true",
								 help='if local results already exist, automatically continue downloading job from last position obtained (otherwise prompt user)')
parser.add_option("-o", "--auto-overwrite", dest="overwrite", action="store_true",
								 help='if local results already exist, automatically overwrite and restart download (otherwise prompt user)')
parser.add_option("-l", "--lib", dest="libMode", action="store_true",
								 help='load and parse parameters only -- do not launch interactive interface')
parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
								 help="Do not print '+' (data recieved) and '-' (no data recieved) characters on stdout")
parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
								 help='Print extra data to stdout')


(options, args) = parser.parse_args()
if options.user == None:
	print "User Name:"
	user = sys.stdin.readline().strip()
else:
	user = options.user

if options.passwd == None:
	print "Password:"
	getch = _Getch()
	c = getch()
	passwd = ""
	i=0
	while (c != "\r" and c != "\n" and i < 20):
		i = i + 1
		passwd = passwd + c
		sys.stdout.write("*")
		c = getch()
	passwd = passwd.strip()
	sys.stdout.write("\n")
else:
	passwd = options.passwd

waitTime = options.waitTime

if options.authenticateOnly.lower().strip() == "false" or options.authenticateOnly.lower().strip() == "f" or options.authenticateOnly.strip() == "0":
	authenticateOnly = False
else:
	authenticateOnly = True


if options.monitor.lower().strip() == "false" or options.monitor.lower().strip() == "f" or options.monitor.strip() == "0":
	monitor = False
else:
	monitor = True

if options.ssl.lower().strip() == "false" or options.ssl.lower().strip() == "f" or options.ssl.strip() == "0":
	url= "http://" + user + ":" + passwd +	"@" + options.xmlrpcServer
else:
	url= "https://" + user + ":" + passwd +	"@" + options.xmlrpcServer

if options.libMode == None:
	libMode = False
else:
	libMode = True

if options.overwrite == None:
	autoOverWrite = False
else:
	autoOverWrite = True

if options.jobList == None:
	printJobList = False
else:
	printJobList = True

if options.continueOn == None:
	autoContinue = False
else:
	autoContinue = True

if options.verbose == None:
	verbose = False
else:
	verbose = True
	
if options.quiet == None:
	quiet = False
else:
	quiet = True
	
if options.jobId != None:
	jobId = options.jobId 
else:
	jobId = None
 
if options.jobDir != None:
	jobDir = options.jobDir + '/'
else:
	jobDir = None


##################################################################################
# Checks to see if access to the xmlrpc service is available for a server
# prints to standard out: 1 if authentication is ok, 0 if credentials are bad and -1 on
# if an error; 
# server: (object) proxying all xmlrpc calls to the mm jobs system
# returns exit code 1 if a error occured during check
def authenticate(server):
	try:
		server.User.getId()
		print 1
		return 0
	except ProtocolError, err:
		if str(err.errcode) == "401":
			print 0
			return 0
		else:
			print -1
		sys.stderr.write("A protocol error occurred\n")
		sys.stderr.write("URL: " + str(err.url) + "\n")
		sys.stderr.write("HTTP/HTTPS headers: " + str(err.headers) +"\n")
		sys.stderr.write("Error code: " + str(err.errcode) + "\n")
		sys.stderr.write("Error message: " + str(err.errmsg) + "\n")
		return 1

	except:
		print -1
		e = sys.exc_info()[1]
		sys.stderr.write("Error during authentication check from %s\n\n" % url)
		sys.stderr.write("Error: %s\n" % e )
		return 1

def prettyBytes(bytes):
	bytes = float(bytes)
	if bytes > 1024 * 1024 * 1024: #GB
		return "%.2f GB" % (bytes / 1024 /  1024 / 1024)
	elif bytes > 1024 * 1024: #MB
		return "%.2f MB" % (bytes / 1024 / 1024)
	elif bytes > 1024: #KB
		return "%.2f KB" % (bytes / 1024)
	else:
		return str(bytes) + " B"

def outputRate(size,rate,avgrate,append):
	sys.stdout.write('{0:<25}'.format(size) + '{0:^20}'.format("[" + rate + "/s]") + '{0:^20}'.format("[" + avgrate + "/s]") + append)
	sys.stdout.flush()

##################################################################################
# Sets up the local directory structure for a job and streams results
# until the job is done
#
# server: (object) proxying all xmlrpc calls to the mm jobs system
# jobId: (int) unique identifier for a job in the system
# autoOverWrite: (boolean) whether to prompt the user if the job
#													already exists on the local system (takes presidence)
# autoConinue: (boolean) whether to use existing job data
# waitTime: (int) time is seconds to sleep between empty return requests
# monitor: (boolean) whether to contiue trying to download until the job reaches completion
def getFileDataForJob(server, jobId, jobDir, autoOverWrite, autoContinue, waitTime, monitor):
	global verbose, quiet
	if verbose: print "Entering getFileDataForJob"
	resultsFileName = jobDir + "/results.txt"
	configFileName = jobDir + "/hurricane_config_file.txt"
	
	if os.path.isdir(jobDir) == False:
		if verbose: print "Creating directory structure"
		os.makedirs(jobDir)
	elif autoOverWrite == True:
		if verbose: print "Ensuring onld data is removed"
		subprocess.call("rm -f " + resultsFileName, shell=True)
		subprocess.call("rm -f " + configFileName, shell=True)

	#Get Config File
	skipConfig = False
	if autoContinue == True and os.path.exists(configFileName):
		 skipConfig = True
	elif autoOverWrite == False:
		if os.path.exists(configFileName):
			print "Local config file already exists for the job."
			overwrite = raw_input("Would you like to overwrite it? [Y/n]\n")
			if overwrite.lower().strip() != "n" and overwrite.lower().strip() != "no":
				os.unlink(configFileName)
			else:
				skipConfig = True
	
	if skipConfig == False:
		if verbose: print "Getting hurricane config file data"
		configData = server.Job.getHurricaneConfigFileData(jobId)
		f = open(configFileName, 'w')
		f.write (configData)
		f.close()

	#Get Results Data
	offset = 0
	if autoContinue == True and os.path.exists(resultsFileName):
		offset = os.path.getsize(resultsFileName)
	elif autoOverWrite == False:
		if os.path.exists(resultsFileName):
			print "Local results file already exists for the job."
			overwrite = raw_input("Would you like to restart download? [Y/n]\n('n' will preserve data and continue downloading)\n")
			if overwrite.lower().strip() != "n" and overwrite.lower().strip() != "no":
				os.unlink(resultsFileName)
			else:
				offset = os.path.getsize(resultsFileName)
	bufferSize = 20 * 1024*1024 #5M
	
	if verbose: print "Beginning results data retrieval loop"
	if quiet == False:
		outputRate("Size", "Bytes","Avg Bytes","\n")
	data = " " #not "" to ensure that at least one iteration of the retieval loop below will execute
	totalElapsed = 0
	while (monitor and (server.Job.isRunning(jobId) or server.Job.isPending(jobId))) or data != "":
		startTime = datetime.datetime.now()
		data2 = server.Job.getResultsFileData(jobId,str(offset),bufferSize,True, True)
		elapsed = datetime.datetime.now() - startTime
		if data2 == "":
			data = ""
		else:
			totalElapsed = totalElapsed + elapsed.microseconds
			data = zlib.decompress(str(data2), 15 + 32)
			offset = offset + len(data)
		if data == "":
			if server.Job.isRunning(jobId): #wait a bit before trying again
				if quiet == False:
					outputRate(prettyBytes(offset),"-","-","\r")
				time.sleep(waitTime)
		else:
			f = open(resultsFileName, 'a')
			f.write(data)
			f.close()
			if quiet == False:
				size = prettyBytes(offset)
				rate = "-"
				if elapsed.microseconds > 0:
					rate = prettyBytes(float(len(data))/elapsed.microseconds*1000000.0)
				avgrate = "-"
				if totalElapsed > 0:
					avgrate = prettyBytes(float(offset)/totalElapsed*1000000.0)
				outputRate(size,rate,avgrate,"\r")

##################################################################################
# Command-line Interface
##################################################################################
try:
	server = ServerProxy(url)
except:
	print "Remote MindModeling Data Repository Unavailable"
	sys.exit(1)

try:
	if printJobList:
		jobs = server.User.getJobs() #Array of Job Dictionaries
		for job in jobs:
			if job != "":
				print str(job["Id"]) + "," + job["Name"] + "," + job["Status"]
	elif authenticateOnly == True:
		authenticate(server)
	elif libMode == False:
		if quiet == False:
			print "\nWelcome: ",server.User.getUsername(), "[Id: ", server.User.getId(), "]\n"

		if jobId == None:
			print "Jobs List:"
			jobs = server.User.getJobs() #Array of Job Dictionaries
			i = 0
			for job in jobs:
				if job != "":
					i = i + 1
					print str(i) + ".", job["Name"],
					if verbose == True:
						print '(' + str(job['Id']) + ')' 
					else:
						print ""
			if i == 0:
				print "There are no jobs in the system -- exiting"
			else:
				isValid = False
				while isValid == False:
					print "Pick a job number from the list:"
					jobIndex = sys.stdin.readline().strip()
					try:
						jobIndex = int(jobIndex)
						if (int(jobIndex) >= 1) and (int(jobIndex) <= i):
							isValid = True
						else:
							print "Selection is out of bounds."
					except (ValueError):
						print "That wasn't even a number."

				jobId =jobs[jobIndex - 1]['Id']
		if jobId != None:
			if jobDir == None:
				if options.datarepo == None:
					jobDir = "."
				else:
					jobDir = os.path.expanduser('~') + '/hurricane/' + '/' + str(jobId) + '/'
			getFileDataForJob(server, jobId, jobDir, autoOverWrite, autoContinue, waitTime, monitor)
		
			if quiet == False: 
				print "\nData transfer complete."

except ProtocolError, err:
	sys.stderr.write("A protocol error occurred\n")
	sys.stderr.write("URL: " + str(err.url).replace(passwd,"********",1) + "\n")
	sys.stderr.write("HTTP/HTTPS headers: " + str(err.headers) +"\n")
	sys.stderr.write("Error code: " + str(err.errcode) + "\n")
	sys.stderr.write("Error message: " + str(err.errmsg) + "\n")
	sys.exit(1)

except:
	e = sys.exc_info()[1]
	sys.stderr.write("Error Retrieving Job from %s\n\n" % url.replace(passwd,"********",1))
	sys.stderr.write("Error: %s\n" % e )
	sys.exit(1)
				
