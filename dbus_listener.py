import time, os, sys, sched, subprocess, re, signal, traceback
import gobject, dbus, dbus.service, dbus.mainloop.glib 
import multiprocessing
import logging,  logging.config,  logging.handlers

from RILCommonModules.RILSetup import *
from DistributedTaskServer.data_manager import *
from DistributedTaskServer.utils import *

logger = logging.getLogger("EpcLogger")

def tracker_pose_signal_handler(x, y, theta):
    global datamgr_proxy
    print "New pose signal listened" 
    try:
        if (not datamgr_proxy.mTrackerAlive.is_set()):
            datamgr_proxy.mTrackerAlive.set()
        #print "@SwisTrack monitor: Alive"
    except Exception, e:
        print "Err in tracker_pose_signal_handler():", e

def updater_interrupt_handler(state):
    global datamgr_proxy
    print "New server state requested %s" %(state)
    try:
        datamgr_proxy.mTaskUpdaterState[TASK_INFO_UPDTAER_STATE] = str(state)
        datamgr_proxy.mTaskUpdaterStateUpdated.set()
        print "Req. datamgr_proxy.mTaskUpdaterState: "
        print datamgr_proxy.mTaskUpdaterState[TASK_INFO_UPDTAER_STATE]
    except Exception, e:
        print "Err in updater_interrupt_handler():", e
def robot_signal_handler(sig,  robotid,  taskid):
	print "Caught signal  %s (in robot signal handler) "  %(sig)
	print "Robot: %i, engaged in %i" %(robotid, taskid)  
	save_task_status(robotid,  taskid)
 
def task_neighbor_signal_handler(taskid, neighbors):
	global datamgr_proxy
	n = []
	try:
		taskid = eval(str(taskid))
		n = [eval(str(x)) for x in neighbors]
		print "Task: %i, got neighboring robots:" %(taskid)
		print n
		datamgr_proxy.mTaskNeighbors[taskid] = n
		if (not datamgr_proxy.mTaskNeighborsAvailable.is_set()):
			datamgr_proxy.mTaskNeighborsAvailable.set()
	except Exception, e:
		print "Err in task_neighbor_signal_handler():", e

def robot_signal_handler(sig,  robotid,  taskid, known_tasks):
	global datamgr_proxy
	print "Caught signal  %s (in robot signal handler) "  %(sig)
	print "Robot: %i, engaged in %i out of %i tasks"\
	 %(robotid, taskid, known_tasks)  
	try:
		robotid = eval(str(robotid))
		taskid = eval(str(taskid))
		datamgr_proxy.mTaskWorkers[robotid] = taskid
		if(taskid is not 0):
		    datamgr_proxy.mKnownTasks[robotid] = eval(str(known_tasks))
		print "Save Task Status:"
		print datamgr_proxy.mTaskWorkers
	except Exception, e:
		print "Err in save_task_status():", e

def main_loop():
    try:
        loop = gobject.MainLoop()
        loop.run()
    except (KeyboardInterrupt, SystemExit):
        print "User requested exit... shutting down now"
        pass
        sys.exit(0)

def listener_main(data_mgr,  dbus_iface= DBUS_IFACE_EPUCK,\
        dbus_path = DBUS_PATH_BASE,  robots_cfg=ROBOTS_PATH_CFG_FILE,\
        sig= SIG_TASK_STATUS,  delay=1):
	global datamgr_proxy,  robot_signal
	datamgr_proxy = data_mgr
	print "@RecvrMain: Task workers"
	print datamgr_proxy.mTaskWorkers
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	bus = dbus.SessionBus()
	# prepare dbus_paths
	#print "Robot paths %i"  %robots
	dbus_paths = GetDBusPaths(robots_cfg)
	try:
	    for p in dbus_paths:
		    bus.add_signal_receiver(robot_signal_handler, dbus_interface =\
			    dbus_iface, path= p,  signal_name = sig)
	    for task in range(1, MAX_SHOPTASK+1):
		    p = DBUS_TASK_PATH_BASE + str(task)
		    bus.add_signal_receiver(task_neighbor_signal_handler, dbus_interface =\
			    DBUS_IFACE_TRACKER, path= p,  signal_name = SIG_TASK_NEIGHBOR)
	    # catch interrupt signals for task info updater
	    bus.add_signal_receiver(updater_interrupt_handler, dbus_interface =\
		    DBUS_IFACE_TASK_SERVER, path= DBUS_PATH_TASK_SERVER,\
		      signal_name = SIG_TASK_INFO_UPDTAER )
	    bus.add_signal_receiver(tracker_pose_signal_handler,\
		 dbus_interface = DBUS_IFACE_TRACKER,\
		 signal_name = SIG_ROBOT_POSE)

	    main_loop()
	except dbus.DBusException:
		traceback.print_exc()
		sys.exit(1)
