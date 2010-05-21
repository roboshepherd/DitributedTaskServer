import multiprocessing
import logging, logging.config
import time
import copy
import random
import sys
from numpy import *
from RILCommonModules.RILSetup import  *
from RILCommonModules.LiveGraph import *
from RILCommonModules.task_info import *
from DistributedTaskServer.data_manager import *

logger = logging.getLogger("EpcLogger")

#  Setup Initial Task Info 
# Fix: Change it to reading from a config file
ti = TaskInfo()
task1 = ShopTask(id=1,  x=1847,  y=1266)
task2 = ShopTask(id=2,  x=2715,  y=1696)
task3 = ShopTask(id=3,  x=1104,  y=1718)
task4 = ShopTask(id=4,  x=1782,  y=472)
#task5 = ShopTask(id=5,  x=2431,  y=2264)
#task6 = ShopTask(id=6,  x=1042,  y=1973)
ti.AddTaskInfo(1,  task1.Info()) 
ti.AddTaskInfo(2,  task2.Info())
ti.AddTaskInfo(3,  task3.Info())
ti.AddTaskInfo(4,  task4.Info()) 
#ti.AddTaskInfo(5,  task5.Info())
#ti.AddTaskInfo(6,  task6.Info())
# LogFiles

taskinfo = copy.deepcopy(ti.all)

# log robot workers status
#---------------------Log recevd. signal/data  ---------------------
class StatusLogger():
    def __init__(self):
        self.writer = None  # for logging recvd. pose signal
	self.known_tasks_writer = None      
        self.step = 0

    def InitLogFiles(self):
        name = "TaskStatus"
        now = time.strftime("%Y%b%d-%H%M%S", time.gmtime())
        desc = "logged in centralized communication mode from: " + now
        # prepare label
        label = "TimeStamp;HH:MM:SS;StepCounter;TaskID;RobotCount;RobotList \n"
        # Data context
        ctx = DataCtx(name, label, desc)
        # Signal Logger
        self.writer = DataWriter("TIUpdater", ctx, now)
	name = "KnownTasks"
	label = "TimeStamp;HH:MM:SS;Step;TotalKnowers;Known_Tasks;TotalInfo\n"
	ctx = DataCtx(name, label, desc)
	self.known_tasks_writer = DataWriter("TIUpdater", ctx, now)

    def _GetCommonHeader(self):
        sep = DATA_SEP
        ts = str(time.time()) + sep + time.strftime("%H:%M:%S", time.gmtime())
        self.step = self.step + 1
        header = ts + sep + str(self.step)
        return header
    
    def AppendLog(self, taskid, robotlist):        
        sep = DATA_SEP
        workers = len(robotlist)
        robotlist.sort() 
        log = self._GetCommonHeader()\
         + sep + str(workers) + sep + str(robotlist) + "\n"
        try: 
            self.writer.AppendData(log)
        except:
            print "TaskStatus logging failed"
            logger.warn("TaskStatus logging failed")

    def AppendInfoLog(self,  knower_dict):        
        sep = DATA_SEP
	knowers = len(knower_dict)
	total_info = 0
	knowledge = eval(knowers_dict)
	for v in knowers_dict.items()
	    total_info += int(eval(v))
        log = self._GetCommonHeader()\
	 + sep + str(knowers) + sep + str(knowledge) +\
	 + sep + str(total_info) \"\n"
        try: 
            self.known_tasks_writer.AppendData(log)
        except:
            print "Known Tasks logging failed"
            logger.warn("Known Tasks logging failed")

    
TASK_URGENCY_LOG = "UrgencyLog-" +\
    time.strftime("%Y%b%d-%H%M%S", time.gmtime()) + ".txt"
TASK_WORKERS_LOG = "WorkersLog-" +\
    time.strftime("%Y%b%d-%H%M%S", time.gmtime()) + ".txt"
urgency_log = ''
workers_log = ''
updater_step = 0

def TimeStampLogMsg():
	global   urgency_log,  workers_log, updater_step
	updater_step = updater_step + 1
	urgency_log = str(time.time()) + "; " +\
	 time.strftime("%H:%M:%S", time.gmtime()) + "; " + str(updater_step)
	workers_log = str(time.time()) + "; " +\
	 time.strftime("%H:%M:%S", time.gmtime()) + "; " + str(updater_step)
    
def PrepareLogMsg(urgency,  workers):
    global   urgency_log,  workers_log
    urg_msg = "; " + str(urgency) 
    urgency_log += urg_msg
    workers_msg = "; " + str(workers)
    workers_log += workers_msg

def GetTaskUrgency(taskid,  urg):
    global  datamgr_proxy, status_logger
    # urgency 0~1
    urgency = urg
    workers = 0
    worker_list = []
    worker_dict = {}
    knower_list = []
    knower_dict = {}
    try:
	worker_dict = datamgr_proxy.mTaskWorkers
	
	logger.info("Worker dict: %s", worker_dict)
	for k, v in worker_dict.items():
		rid = eval(str(k))
		tid = eval(str(v))
		if(tid == taskid):
			worker_list.append(rid)
	logger.info("Task %d Workers searched", taskid)
	print "Task %d Workers: %s" %(taskid, worker_list)
	print worker_list
	logger.info("Task %d Workers worker_list: %s", taskid, worker_list)
	status_logger.AppendLog(taskid, worker_list)
    except Exception, e:
	logger.warn("@GetTaskUrgency(): err %s", e)
    workers= len(worker_list)
    if workers > 0:
	urgency = urg - workers * DELTA_TASK_URGENCY_DEC
    elif workers == 0:
	urgency = urg +  DELTA_TASK_URGENCY_INC
    else:
	logger.warn("worker count not updated")
    if urgency > MAX_TASK_URGENCY:
	urgency = MAX_TASK_URGENCY
    elif urgency < MIN_TASK_URGENCY:
	urgency = MIN_TASK_URGENCY
# Save data into log
    PrepareLogMsg(urgency,  workers)
    logger.info("task %d, urgency:%f", taskid, urgency)
    print "task %d, urgency:%f" %(taskid, urgency)
    return urgency

def UpdateTaskInfo():
	global  datamgr_proxy, 
	#print "DMP ti2 %s" %id(datamgr_proxy.mTaskInfo)
	# Put TimeStamp on logs
	TimeStampLogMsg()
	#try:
	for taskid, ti  in  datamgr_proxy.mTaskInfo.items():
		urg= ti[TASK_INFO_URGENCY] 
		ti[TASK_INFO_URGENCY] =   GetTaskUrgency(taskid,  urg)
		datamgr_proxy.mTaskInfo[taskid] = ti
			#print task
	#except Exception, e:
		#print "Err @UpdateTaskInfo(): %s", e
		if (not datamgr_proxy.mTaskInfoAvailable.is_set()):
		    print "Setting TASKINFO AVAILABLE"
		    datamgr_proxy.mTaskInfoAvailable.set()
	#print "Updated ti %s" %datamgr_proxy.mTaskInfo
	# known_task  loffing
	knower_dict = datamgr_proxy.mKnownTasks.copy() 
	status_logger.AppendInfoLog(knower_dict)

def InitLogFiles():
    f1 = open(TASK_URGENCY_LOG,  "w")
    f2 = open(TASK_WORKERS_LOG,  "w")
    header = "##;## \n Time; HH:MM:SS; Step#"
    for x in xrange(1, MAX_SHOPTASK+1):
        header += "; "
        header += "Task"
        header += str(x)
    header += "\n"
    f1.writelines(header)
    f2.writelines(header)
    f1.close()
    f2.close()
    
def AppendMsg(file,  msg):
    f = open(file,  'a')
    f.write(msg)
    f.write('\n')
    f.close()
    
def UpdateLogFiles():
    global   urgency_log,  workers_log
    AppendMsg(TASK_URGENCY_LOG, urgency_log )
    AppendMsg(TASK_WORKERS_LOG,  workers_log)
    # reset log msg
    urgency_log = ''
    workers_log = ''

def updater_main(datamgr):
    InitLogFiles()
    global datamgr_proxy,  taskurg, status_logger
    datamgr_proxy = datamgr
    #print "DMP ti1 %s" %id(datamgr_proxy.mTaskInfo)
    taskurg = INIT_TASK_URGENCY
    for k,  v in taskinfo.iteritems():
	    datamgr_proxy.mTaskInfo[k] =v
    # setup logging
    status_logger = StatusLogger()
    status_logger.InitLogFiles()
    # real work starts
    print "@updater:"
    print datamgr_proxy.mTaskInfo
    datamgr_proxy.mTaskInfoAvailable.set()
    datamgr_proxy.mTaskUpdaterState[TASK_INFO_UPDTAER_STATE] =\
     TASK_INFO_UPDATER_RUN
    try:
	while True:
	    state =  str(datamgr_proxy.mTaskUpdaterState[TASK_INFO_UPDTAER_STATE])
	    datamgr_proxy.mTaskUpdaterStateUpdated.clear()
	    print "@TaskInfoUpdater:"
	    #datamgr_proxy.mTrackerAlive.wait()
	    if state == TASK_INFO_UPDATER_RUN:            
		UpdateTaskInfo()
		UpdateLogFiles()
		time.sleep(TASK_INFO_UPDATE_FREQ)
		print "\t TI updated."
	    elif state == TASK_INFO_UPDATER_PAUSE:
		datamgr_proxy.mTaskUpdaterStateUpdated.wait()
		print "\t updater waiting..."
    except (KeyboardInterrupt, SystemExit):
	print "User requested exit... TaskInfoUpdater shutting down now"
	sys.exit(0)
        

