#!/usr/bin/env python
import time, os, sys, sched, subprocess, re, signal, traceback
import multiprocessing
import logging,  logging.config
import pygame

from RILCommonModules.RILSetup import *
from CentralizedTaskServer.data_manager import *

logger = logging.getLogger("EpcLogger")

schedule = sched.scheduler(time.time, time.sleep)

SND_FILE = '/usr/share/sounds/ekiga/dialtone.wav'
# beep
def beep(duration):
    now = int(time.time())
    end = now + duration
    while now < end:
        log = "@Monitor beeping now: %s" %(str(now))
        print log
        logger.warn(log)
        #sys.stdout.write('\a')
        #sys.stdout.flush()
        pygame.init()
        pygame.mixer.Sound(SND_FILE).play()
        time.sleep(1)
        now = int(time.time())
    logger.warn("End of beeping cycle")


def monitor_pose_signal(delay, ):
    global datamgr_proxy
    schedule.enter(delay, 0, monitor_pose_signal, (delay, )) # re-schedule
    try:
        if(datamgr_proxy.mTrackerAlive.is_set()):
            datamgr_proxy.mTaskUpdaterState[TASK_INFO_UPDTAER_STATE] =\
             TASK_INFO_UPDATER_RUN
            if(not datamgr_proxy.mTaskUpdaterStateUpdated.is_set()):
                datamgr_proxy.mTaskUpdaterStateUpdated.set() # for taskinfo updater
        else:
            datamgr_proxy.mTaskUpdaterState[TASK_INFO_UPDTAER_STATE] =\
             TASK_INFO_UPDATER_PAUSE
            #print "\a"
            beep(3)
        if (datamgr_proxy.mTrackerAlive.is_set()):
            datamgr_proxy.mTrackerAlive.clear() # reset tracker state
        # make a short beep        
    except Exception, e:
        print "Err in monitor_pose_signal():", e


def monitor_main(datamgr, delay=TRACKER_MONITOR_FREQ):
        global datamgr_proxy
        datamgr_proxy = datamgr
        try:           
            print "Running SwisTrack monitoring service."           
            e = schedule.enter(0, 0, monitor_pose_signal, (delay, ))
            schedule.run()
        except (KeyboardInterrupt, SystemExit):
                print "User requested exit... shutting down now"
                sys.exit(0)
