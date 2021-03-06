#!/usr/bin/env python

import os, signal, subprocess, re, sys
robotid = sys.argv[1]

if(len(sys.argv) < 1):
    print "%s : script-name" %sys.argv[0]
    sys.exit(1)
else:
    script = sys.argv[1]

cmd = "ps aux | grep " + script
subproc = subprocess.Popen([cmd, ], stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
out = subproc.communicate()
print "\t ps says:" + out[0]
print "\n"
lines=  out[0].split("\n")
#print "\t Output lines: \n", lines
for line in lines:
	#print "Line:-->", line
	output = line.split()
	try:
		if (output[12] == robotid):
			print "*!*!* proc not killed"
			continue
		else:
			print "Killing PID:", output[1]
			pid = int(output[1])
	except Exception, e:
		print e
	# Killing valid PID	
	if(pid > 0):
	    try:
		os.kill(pid, signal.SIGKILL)
	    except Exception, e:
		print e
	else:
		print "PID not OK"
