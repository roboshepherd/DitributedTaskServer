#!/usr/bin/env python
import time, os, sys, sched, subprocess, re, signal, traceback
import gobject, dbus, dbus.service, dbus.mainloop.glib 
import multiprocessing
import logging,  logging.config

from RILCommonModules.RILSetup import *
from RILCommonModules.task_info import *
from RILCommonModules.pose import *
from DistributedTaskServer.data_manager import *
from DistributedTaskServer.utils import *

logger = logging.getLogger("EpcLogger")
schedule = sched.scheduler(time.time, time.sleep)

class TaskInfoSignal(dbus.service.Object):
    def __init__(self, object_path):
        dbus.service.Object.__init__(self, dbus.SessionBus(), object_path)
    @dbus.service.signal(dbus_interface= DBUS_IFACE_TASK_SERVER,\
            signature='sa{iad}')
            #signature='siad')
    def TaskInfo(self, sig,  taskinfo):
        # The signal is emitted when this method exits
        print "TaskInfo signal: %s  " % (sig)
        print taskinfo
    def Exit(self):
		global loop
		loop.quit()

#Emit DBus-Signal
def emit_task_signal(sig1,  inc):
        #print "At emit_task_signal():"
        schedule.enter(inc, 0, emit_task_signal, (sig1,  inc)) # re-schedule to repeat this function
        global datamgr_proxy,  task_signal
        try:
            datamgr_proxy.mTaskInfoAvailable.wait()
            taskinfo = datamgr_proxy.mTaskInfo.copy() # use a soft copy
            datamgr_proxy.mTaskInfoAvailable.clear()
            #logging.debug("TaskInfo@Emitter: %s",  taskinfo)
            #print "\tEmitting TaskInfo signal>>> "                  
            neighbor_dict = {}
            neighbor_dict = datamgr_proxy.mTaskNeighbors.copy()
            for taskid in range(1, MAX_SHOPTASK+1):
                ti = {}
                ti[taskid] = taskinfo[taskid] # single task info packed in dict 
                #print "taskinfo: ", ti
                neighbors = []
                try:                
                    if not neighbor_dict[taskid]:
                        break
                    elif neighbor_dict[taskid]:
                        neighbors = neighbor_dict[taskid]
                        #print "neighbors: ", neighbors
                except Exception, e:                    
                    #logger.info("Empty neighbor_dict for task: %s", e)
                    pass
               
                if neighbors:
                    for robotid in neighbors:
                        #task_signal[int(robotid)].TaskInfo(sig1,\
                        # taskinfo[taskid])
                        print "Emit taskinfo signal on /robot%i" %robotid
                        task_signal[robotid -1 ].TaskInfo(sig1, ti)
                else:
                    continue
        except Exception, e:
                logger.warn("Err in emit_task_signal(): %s", e)        
        taskinfo = None # reset 


def emitter_main(datamgr,  dbus_iface= DBUS_IFACE_TASK_SERVER,\
            dbus_path = DBUS_PATH_TASK_SERVER, \
            sig1= SIG_TASK_INFO,  delay = TASK_INFO_EMIT_FREQ,\
            robots_cfg=ROBOTS_PATH_CFG_FILE):
        global task_signal,  datamgr_proxy, loop
        datamgr_proxy = datamgr
        dbus_paths = GetDBusPaths(robots_cfg)
        # proceed only after taskinfo is populated
        datamgr_proxy.mTaskInfoAvailable.wait() 
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        session_bus = dbus.SessionBus()
        print "@Emitter-- TaskInfoAvailable %s"\
            %datamgr_proxy.mTaskInfoAvailable.is_set() 
        try:
            name = dbus.service.BusName(dbus_iface, session_bus)
            task_signal = []
            for p in dbus_paths:
                task_signal.append(TaskInfoSignal(p))
            #print "task_signal[0]]:", task_signal[0]
            #taskinfo = datamgr_proxy.mTaskInfo.copy() # use a soft copy
            #task_signal[0].TaskInfo(sig1, taskinfo)
            loop = gobject.MainLoop()
            print "Running taskinfo signal emitter service."
        except dbus.DBusException:
            traceback.print_exc()
            sys.exit(1)
        try:
                e = schedule.enter(0, 0, emit_task_signal, (sig1,  delay,  ))
                schedule.run()
                loop.run()
        except (KeyboardInterrupt, dbus.DBusException, SystemExit):
                print "User requested exit... shutting down now"
                task_signal.Exit()
                pass
                sys.exit(0)
