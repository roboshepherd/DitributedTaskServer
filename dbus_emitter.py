#!/usr/bin/env python
import time, os, sys, sched, subprocess, re, signal, traceback
import gobject, dbus, dbus.service, dbus.mainloop.glib 
import multiprocessing
import logging,  logging.config

from RILCommonModules.RILSetup import *
from RILCommonModules.task_info import *
from RILCommonModules.pose import *
from CentralizedTaskServer.data_manager import *

logger = logging.getLogger("EpcLogger")

schedule = sched.scheduler(time.time, time.sleep)

class TaskInfoSignal(dbus.service.Object):
    def __init__(self, object_path):
        dbus.service.Object.__init__(self, dbus.SessionBus(), object_path)
    @dbus.service.signal(dbus_interface= DBUS_IFACE_TASK_SERVER,\
            signature='sa{iad}')
    def TaskInfo(self, sig,  taskinfo):
        # The signal is emitted when this method exits
        print "TaskInfo signal: %s  " % (sig)
        #print taskinfo
    def Exit(self):
		global loop
		loop.quit()

#Emit DBus-Signal
def emit_task_signal(sig1,  inc):
        #print "At emit_task_signal():"
        schedule.enter(inc, 0, emit_task_signal, (sig1,  inc)) # re-schedule to repeat this function
        global datamgr_proxy,  task_signal
        datamgr_proxy.mTaskInfoAvailable.wait()
        taskinfo = datamgr_proxy.mTaskInfo.copy() # use a soft copy
        datamgr_proxy.mTaskInfoAvailable.clear()
        #logging.debug("TaskInfo@Emitter: %s",  taskinfo)
        #print "\tEmitting TaskInfo signal>>> " 
        task_signal.TaskInfo(sig1,  taskinfo)
        taskinfo = None


def emitter_main(datamgr,  dbus_iface= DBUS_IFACE_TASK_SERVER,\
            dbus_path = DBUS_PATH_TASK_SERVER, \
            sig1= SIG_TASK_INFO,  delay = TASK_INFO_EMIT_FREQ):
        global task_signal,  datamgr_proxy, loop
        datamgr_proxy = datamgr
        # proceed only after taskinfo is populated
        datamgr_proxy.mTaskInfoAvailable.wait() 
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        session_bus = dbus.SessionBus()
        print "@Emitter-- TaskInfoAvailable %s"\
            %datamgr_proxy.mTaskInfoAvailable.is_set() 
        try:
            name = dbus.service.BusName(dbus_iface, session_bus)
            task_signal = TaskInfoSignal(dbus_path)
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
