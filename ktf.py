import getopt, sys, os, socket, traceback

import logging
import logging.handlers
import warnings

import math
import time
import subprocess
import re
import copy
import shlex
import pickle
import getpass
import datetime
import string
import shutil

WORKSPACE_FILE = "workspace.pickle"


KTF_PATH = os.getenv("KTF_PATH")
if not(KTF_PATH):
  KTF_PATH = "/opt/share/ktf/0.1/"

ERROR              = -1
DUMP_EXCEPTION_AT_SCREEN = True

#########################################################################
# set log file
#########################################################################


for d in ["%s/LOGS" % KTF_PATH]:
  if not(os.path.exists(d)):
    os.mkdir(d)

logger = logging.getLogger('ktf.log')
logger.propagate = None
logger.setLevel(logging.INFO)
log_file_name = "%s/" % KTF_PATH+"LOGS/ktf.log"
open(log_file_name, "a").close()
handler = logging.handlers.RotatingFileHandler(
     log_file_name, maxBytes = 20000000,  backupCount = 5)
formatter = logging.Formatter("%(asctime)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

loggerror = logging.getLogger('ktf_err.log')
loggerror.propagate = None
loggerror.setLevel(logging.DEBUG)
log_file_name = "%s/" % KTF_PATH+"LOGS/ktf_err.log"
open(log_file_name, "a").close()
handler = logging.handlers.RotatingFileHandler(
     log_file_name, maxBytes = 20000000,  backupCount = 5)
handler.setFormatter(formatter)
loggerror.addHandler(handler)




#########################################################################
# function handling exception and debugging message
#########################################################################

class MyError(Exception):
    """
    class reporting own exception message
    """
    def __init__(self, value):
        self.value  =  value
    def __str__(self):
        return repr(self.value)

def except_print():

    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    print "!!!!!!!!!!!!!!!!!!!!!!!!!"
    print exc_type
    print exc_value

    print "!!!!!!!!!!!!!!!!!!!!!!!!!"
    traceback.print_exception(exc_type, exc_value, exc_traceback,
                              file=sys.stderr)


def print_debug(s,r="nulll"):
  if debug:
    if r=="nulll":
      print s
    else:
      print s,":",r



def dump_exception(where,fic_contents_initial= None):
    global DUMP_EXCEPTION_AT_SCREEN

    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
    if DUMP_EXCEPTION_AT_SCREEN:
      traceback.print_exception(exceptionType,exceptionValue, exceptionTraceback,\
                                file=sys.stdout)
      if fic_contents_initial:
        print "\n============ Additional Info ===========\n"+\
            "\n".join(fic_contents_initial)+\
            "\n========== end =========\n"

    print '!!!! Erreur in %s check error log file!!!' % where
    logger.info('!!!! Erreur in %s check error log file!!!' % where)
    loggerror.error('Erreur in %s' % where, exc_info=True)
    if fic_contents_initial:
        loggerror.error("\n============ Additional Info ===========\n"+\
                        "\n".join(fic_contents_initial)+\
                        "========== end content of file =========\n")




class ktf:

  def __init__(self):

    self.check_python_version()
    
    self.TIME = False
    self.DEBUG = 0
    self.ONLY = ""
    self.BUILD = False
    self.MATRIX_FILE_TEMPLATE = ""
    self.FAKE                 = False
    self.SUBMIT               = False
    self.SUBMIT_CMD           = False
    self.MACHINE              = False

    self.MY_MACHINE = self.MACHINE_FULL_NAME = ""
    self.MY_HOSTNAME = self.TMPDIR = self.MY_HOSTNAME_FULL_NAME = ""
    
    self.JOB_ID = {}
    self.JOB_DIR = {}
    self.JOB_STATUS = {}
    self.timing_results = {}
    self.timing_results["procs"] = []
    self.timing_results["cases"] = []
    self.timing_results["runs"] = []
    if os.path.exists(WORKSPACE_FILE):
      self.load_workspace()
      #print self.timing_results["runs"]
      
  #########################################################################
  # get machine name and alias 
  #########################################################################
  def get_machine(self):
      """
      determines the machine where tests are run
      """

      tmp_directory = "/tmp"
      machine = socket.gethostname()
      self.user_message("","socket.gethostname=/%s/" % machine)
      
      if (machine[:3]=="cdl" or True):
          machine = "shaheen"
          self.SUBMIT_CMD = 'sbatch'
          self.MATRIX_FILE_TEMPLATE = """tests/shaheen_cases.txt__SEP2__# test matrix for shaheen II

Test		   NB_CORES        ELLAPSED_TIME            

# Global variables

#KTF SLURM_ACCOUNT = kxxxx
#KTF EXECUTABLE = my_code
#KTF Directory = test1


# test test1

#Code_test1_512	     512             1:10:00         
#Code_test1_256	     256             3:10:00   
#Code_test1_128	     128             3:10:00   

__SEP1__run_tests.py*__SEP2__
from ktf import *
import glob

class my_ktf(ktf):

  def __init__(self):
    ktf.__init__(self)



  def my_timing(self,dir,ellapsed_time,status):

    if self.DEBUG:
      print dir,status
    for filename in glob.glob(dir+'/*/results*log'):
      try:
        f = open(filename).readlines()
        if len(f)<2:
          if status=="COMPLETED":
            return "?%s/%s" %(ellapsed_time,status[:2])
          else:
            return "NOLOG/"+status[:2] 
        l = f[-2][:-1]
        l = l.replace("Total time :","")
        if self.DEBUG:
          print l,filename
        return int(float(l))
      except:
        dump_exception('user_defined_timing')
        job_out = "___".join(open(dir+'/job.out').readlines())
        if job_out.find("CANCELLED")>-1:
          return "CANCELLED/"+status[:2]
        if self.DEBUG:
          print "pb on ",filename
        return "PB/"+status[:2]
    return "!%s" % ellapsed_time

if __name__ == "__main__":
    K = my_ktf()
    K.welcome_message()
    K.parse()
    if K.TIME:
      K.list_jobs_and_get_time()
    else:
      K.run()
__SEP1__tests/test1/job.shaheen.template__SEP2__#!/bin/bash
#SBATCH --job-name=__Test__
#SBATCH --output=job.out
#SBATCH --error=job.err
#SBATCH --ntasks=__NB_CORES__
#SBATCH --time=__ELLAPSED_TIME__
#SBATCH -A __SLURM_ACCOUNT__

cd __STARTING_DIR__ 
echo ======== start ==============
date
echo ======== start ==============
srun -o 0 --ntasks=__NB_CORES__  --cpus-per-task=1 --hint=nomultithread --ntasks-per-node=32 --ntasks-per-socket=16 --ntasks-per-core=1 --cpu_bind=cores   __EXECUTABLE__
echo ======== end ==============
date
echo ======== end ==============
  """
      else:
          print "[WARNING]  machine /%s/ unknowwn : using sh to submit  " % machine
          machine = "unknown"
          self.SUBMIT_CMD = 'sh'

      return machine, tmp_directory




  def check_python_version(self):
    try:
      subprocess.check_output(["ls"])
    except:
      print ("ERROR : Please use a more recent version of Python > 2.7.4")
      sys.exit(1)

  #########################################################################
  # welcome message
  #########################################################################


  def welcome_message(self):
      """ welcome message"""


      self.MY_HOSTNAME, self.TMPDIR = self.get_machine()
      self.MY_HOSTNAME_FULL_NAME = socket.gethostname()

      print """                     #########################################
                     #   Welcome to KSL Test Framework 0.3!  #
                     #########################################
       """
      print "\trunning on %s (%s) " %(self.MY_HOSTNAME_FULL_NAME,self.MY_HOSTNAME)
      print "\n\tprocessing ..."
      print "\t\t", " ".join(sys.argv)



  #########################################################################
  # usage ...
  #########################################################################

      

  def usage(self,message = None, error_detail = ""):
      """ helping message"""
      if message:
          print "\n\tError %s:\n\t\t%s\n" % (error_detail,message)
          print "\ttype ktf -h for the list of available options..."
      else:
        print "\n  usage: \n \t python  run_tests.py \
               \n\t\t[ --help ] \
               \n\t\t --submit | --build | --time | --create-template [ --only=pattern]\
               \n\t\t[ --debug ] [ --debug-level=[0|1|2] ] [ --fake ]  \
             \n"  

      sys.exit(1)


  #########################################################################
  # parsing command line
  #########################################################################

  def parse(self,args=sys.argv[1:]):
      """ parse the command line and set global _flags according to it """

      try:
          opts, args = getopt.getopt(args, "h", 
                            ["help", "machine=", "test=", \
                               "debug", "debug-level=", "create-template", "time", "build", "only=", \
                               "fake",  "submit" ])    
      except getopt.GetoptError, err:
          # print help information and exit:
          self.usage(err)

      # first scan opf option to get prioritary one first
      # those who sets the state of the process
      # especially those only setting flags are expected here
      for option, argument in opts:
        if option in ("-h", "--help"):
          self.usage("")
        elif option in ("--debug"):
          self.DEBUG = 1
        elif option in ("--debug-level"):
          self.DEBUG = int(argument)
        elif option in ("--create-template"):
          self.create_test_matrix_template()
        elif option in ("--only"):
          self.ONLY = argument
        elif option in ("--build"):
          self.BUILD = True
        elif option in ("--time"):
          self.TIME = True
        elif option in ("--submit"):
          self.SUBMIT = True
          self.BUILD = True
        elif option in ("--fake"):
          self.DEBUG = True
          self.FAKE = True
      # second scan to get other arguments
      
      self.MACHINE = self.MY_HOSTNAME

      if self.SUBMIT and self.TIME : 
        self.usage("--time and --submit can not be asked simultaneously")

      if self.BUILD and self.TIME : 
        self.usage("--time and --build can not be asked simultaneously")

      if not(self.BUILD) and not(self.TIME) and not(self.SUBMIT):
        self.usage("at least --build, --submit or --time should be asked")




  #########################################################################
  # save_workspace
  #########################################################################

  def save_workspace(self,workspace_file=WORKSPACE_FILE):
      
      #print "saving variables to file "+workspace_file
      
      f_workspace = open( workspace_file+".new", "wb" )
      pickle.dump(self.JOB_ID    ,f_workspace)
      pickle.dump(self.JOB_STATUS,f_workspace)
      pickle.dump(self.timing_results,f_workspace)
      f_workspace.close()
      if os.path.exists(workspace_file):
        os.rename(workspace_file,workspace_file+".old")
      os.rename(workspace_file+".new",workspace_file)
      

  #########################################################################
  # load_workspace
  #########################################################################

  def load_workspace(self,workspace_file = WORKSPACE_FILE ):

      #print "loading variables from file "+workspace_file

      f_workspace = open( workspace_file, "rb" )
      self.JOB_ID    = pickle.load(f_workspace)
      self.JOB_STATUS = pickle.load(f_workspace)
      self.timing_results = pickle.load(f_workspace)
      f_workspace.close()

      for job_dir in self.JOB_ID.keys():
        job_id  = self.JOB_ID[job_dir]
        self.JOB_DIR[job_id] = job_dir


  #########################################################################
  # os.system wrapped to enable Trace if needed
  #########################################################################

  def wrapped_system(self,cmd,comment="No comment",fake=False):

    if self.DEBUG:
      print "\tcurrently executing /%s/ :\n\t\t%s" % (comment,cmd)

    if not(fake) and not(self.FAKE):
      #os.system(cmd)
      #subprocess.call(cmd,shell=True,stderr=subprocess.STDOUT)
      proc = subprocess.Popen(cmd, shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      output = ""
      while (True):
          # Read line from stdout, break if EOF reached, append line to output
          line = proc.stdout.readline()
          #line = line.decode()
          if (line == ""): break
          output += line
      if len(output):
        print output
      sys.stdout.flush()
          
  #########################################################################
  # send a message to the user
  #########################################################################

  def user_message(self,msg=None,msg_debug=None,action=None):

    if action==ERROR:
      prefix = "Error: "
    else:
      prefix = ""

    br = ""
        
    if self.DEBUG and msg_debug:
      if len(msg_debug)>0:
        while len(msg_debug)>1 and msg_debug[0]=='\n':
          br = br+"\n"
          msg_debug = msg_debug[1:]
        print "%s\t%s%s" % (br,prefix,msg_debug)
    else:
      if msg :
        if len(msg)>0:
          while len(msg)>1 and msg[0:1]=='\n':
            br = br+"\n"
            msg = msg[1:]
          print "%s\t%s%s" % (br,prefix,msg)

    if action==ERROR:
      sys.exit(1)


  #########################################################################
  # substitute the template file
  #########################################################################

  def substitute(self,directory,balises):

      job_file = None

      self.user_message(msg_debug="\nsubstituting in "+directory)
      self.user_message(msg_debug="\n\tbalises  = %s\n " % str(balises))
          
      for root, dirs, files in os.walk(directory):
          if self.DEBUG:
             print dirs,files

          for name in files:
              if ".template" in name and os.path.exists(os.path.join(root, name)):
                  if self.DEBUG:
                      print "\t\tsubstituting ",os.path.join(root, name)
                  fic = open(os.path.join(root, name))
                  t = "__NEWLINE__".join(fic.readlines())
                  fic.close()

                  for b in balises.keys():
                      t = t.replace("__"+b+"__","%s"%balises[b])

                  name_saved = name.replace(".template","")
                  fic = open(os.path.join(root, name_saved),"w")
                  fic.write(t.replace("__NEWLINE__",""))
                  fic.close()

                  if name_saved == "job.%s" % self.MACHINE:
                      job_file = os.path.join(root, name_saved)
                            
  #         for name in dirs:
  #             job_file_candidate = self.substitute(os.path.join(root, name),balises)
  #             if (job_file_candidate):
  #                 job_file = job_file_candidate

      return job_file


  #########################################################################
  # create test template (matrix and job)
  #########################################################################
  def create_test_matrix_template(self):

    l = self.MATRIX_FILE_TEMPLATE
    
    print

    for filename_content in l.split("__SEP1__"):
      filename,content = filename_content.split("__SEP2__")
      if os.path.exists(filename):
        print "\ttest matrix file %s already exists... skipping it!" % filename
      else:
        dirname = os.path.dirname(filename)
        if not(os.path.exists(dirname)):
          self.wrapped_system("mkdir -p %s" % dirname,comment="creating dir %s" % dirname)
        executable = False
        if filename[-1]=="*":
          filename = filename[:-1]
          executable = True
        f = open(filename,"w")
        f.write(content)
        f.close()
        if executable:
          self.wrapped_system("chmod +x %s" % filename)
        self.user_message(msg="file %s created " % filename)

    sys.exit(0)


  #########################################################################
  # get status of all jobs ever launched
  #########################################################################
  def get_current_jobs_status(self):

    if self.DEBUG:
      print len(self.JOB_ID)
    jobs_to_check = list()
    for j in self.JOB_DIR.keys():
      if self.DEBUG:
        print j,self.JOB_DIR[j],self.job_status(j),
      if self.job_status(j) in ("CANCELLED","COMPLETED"):
        if self.DEBUG:
          print 'not asking for ',j
      else:
        jobs_to_check.append(j)
        
    cmd = ["sacct","-j",",".join(jobs_to_check)]
    try:
      output = vsubprocess.check_output(cmd)
    except:
      output=""
    for l in output.split("\n"):
        try:
          if self.DEBUG:
            print l
          j=l.split(" ")[0]
          status=l.split(" ")[-8]
          if status in ('PENDING','TIMEOUT','FAILED','RUNNING','COMPLETED','CANCELLED','CANCELLED+'):
            if self.DEBUG:
              print status,j
            if status[-1]=='+':
              status  = status[:-1]
            self.JOB_STATUS[j] = self.JOB_STATUS[self.JOB_DIR[j]] = status
        except:
          pass
    self.save_workspace()
      
  #########################################################################
  # get current job status
  #########################################################################
  def job_status(self,id_or_file):

    dirname="xxx"
    if os.path.isfile(id_or_file):
      dirname = os.path.abspath(os.path.dirname(id_or_file))
    if os.path.isdir(id_or_file):
      dirname = os.path.abspath(id_or_file)

    for key in [id_or_file,dirname]:
      if key in self.JOB_STATUS.keys():
        return self.JOB_STATUS[key]
    if self.DEBUG:
      print "UNKNOWN for ",id_or_file,dirname
    return "UNKNOWN"

   

  #########################################################################
  # scan all available job.out
  #########################################################################


  def scan_jobs_and_get_time(self,path=".",level=0,timing=False,
                             dir_already_printed={}):
    if level==0 and self.DEBUG:
      print "\n\tBenchmarks Availables: "

    
    if self.DEBUG>3:
      print "\n[list_jobs_and_get_time] scanning ",path," for timings=",timing

    if not(os.path.exists(path)):
      return
    
    if not(os.path.isdir(path)):
      return
      
    dirs = sorted(os.listdir(path))


    if len(dirs):
      #if level == SCANNING_FROM :
      #  print "%s%d %s Availables: " % ("\t"*(level+1),len(dirs),ArboNames[level])
      if self.DEBUG>3:
        print level,dirs
      for d in [ "job.submit.out" ]:
        if os.path.exists(path + "/" + d) :
          if os.path.isfile(path + "/" + d) :
            if self.DEBUG:
              print "[list_jobs_and_get_time] candidate : %s " % (path+"/"+"job.submit.out")
            # formatting the dirname
            p = re.match(r"(.*tests_.*)/.*",path)
            if p:
              dir_match = p.group(1)
  #           else:
  #             dir_match = "??? (%s)" % path

            path_new = path + "/" + d

            timing_result = self.get_timing(path)
            
            if self.DEBUG and not(dir_match in dir_already_printed.keys()):
              print "%s- %s " % ("\t"+"   "*(level),dir_match)
            dir_already_printed[dir_match] = False
            case_match = path_new.replace(dir_match+"/","")
            case_match = case_match.replace("/job.submit.out","")
            case_match = case_match.replace("32k","32768")
            case_match = case_match.replace("16k","16384")
            case_match = case_match.replace("8k","8192")
            case_match = case_match.replace("4k","4096")
            case_match = case_match.replace("2k","2048")
            case_match = case_match.replace("1k","1024")
            p = re.match(r".*_(\d+).*",case_match)
            if p:
              proc_match = p.group(1)
            else:
              p = re.match(r"(\d+).*$",case_match)
              if p:
                proc_match = p.group(1)
              else:
                proc_match = "???"
            k = "%s.%s.%s" % (dir_match,proc_match, case_match)

            if not(k in self.timing_results.keys()):
              self.timing_results[k] = []
            if not(dir_match in self.timing_results["runs"]):
              self.timing_results["runs"].append(dir_match)
            if not(proc_match in self.timing_results["procs"]): 
              self.timing_results["procs"].append(proc_match)
            if not(case_match in self.timing_results["cases"]):
              self.timing_results["cases"].append(case_match)
    
            self.timing_results[k]=timing_result
            if self.DEBUG:
              print "\t\t%10s s \t %5s %40s " % ( timing_result, proc_match, case_match)
            else:
              print ".",
              sys.stdout.flush()

        
        for d in dirs :
          if not(d in ["R",".git","src"]):
            path_new = path + "/" + d
            if os.path.isdir(path_new):
              self.scan_jobs_and_get_time(path_new,level+1,timing,dir_already_printed)


  #########################################################################
  # display ellapsed time and preparing the linked directory
  #########################################################################

  def list_jobs_and_get_time(self,path=".",level=0,timing=False,
                             dir_already_printed={}):

    self.get_current_jobs_status()

    self.scan_jobs_and_get_time(path,level,timing,dir_already_printed)

    if os.path.exists('R'):
      shutil.rmtree('R')
    os.mkdir('R')

    nb_tests = 0
    total_time = {}
    self.timing_results["procs"].sort(key=int)
    #print self.timing_results["procs"]
    
    print
    print "%45s" % "Runs",
    
    for run in self.timing_results["runs"]:
      print "%12s" % run.replace("-","").replace("_","")[-8:],
    print
    
    nb_line = 0
    for case in self.timing_results["cases"]:
      nb_line += 1
      for proc in self.timing_results["procs"]:
        k0 = "%s.%s" % (proc, case)
        nb_runs = 0
        nb_column = 0
        for run in self.timing_results["runs"]:
          k = "%s.%s.%s" % (run,proc,case)
          if k in self.timing_results.keys():
            nb_runs += 1
        if nb_runs:
          print "%45s" % case,
          for run in self.timing_results["runs"]:
            nb_column += 1
            k = "%s.%s.%s" % (run,proc,case)
            if k in self.timing_results.keys():
              t = self.timing_results[k]
              shortcut = "%s%s" % (string.lowercase[nb_column-1],string.lowercase[nb_line-1])
              path = run+"/"+case
              if not(os.path.exists(path)):
                path = path + " "
                path = path.replace("32768 ","32k")
                path = path.replace("16384 ","16k")
                path = path.replace("8192 " ,"8k" )
                path = path.replace("4096 " ,"4k" )
                path = path.replace("2048 " ,"2k" )
                path = path.replace("1024 " ,"1k" )
                
              os.symlink("."+path,"R/%s" % shortcut)
              try:
                print "%9s %s" % (t,shortcut),
              except:
                print 'range error ',nb_line-1,nb_column-1
                sys.exit(1)
              #print "%9s" % (t),
              nb_tests = nb_tests + 1
              if not(run in total_time.keys()):
                total_time[run]=0
              if t>0:
                try:
                  total_time[run] += self.timing_results[k]
                except:
                  pass
            else:
              print "%12s" % "-", 
          print "%3s tests %s" % (nb_runs,case)
    print "%45s" % "total time",
    for run in self.timing_results["runs"]:
      print "%9s   " % total_time[run],
    print "%3s" % nb_tests,'tests in total'
      
  #########################################################################
  # calculation of ellapsed time based on values dumped in job.out
  #########################################################################


  def get_timing(self,path):

    # 1) checking if job is still running
    status = self.job_status(path)
    if status in ("PENDING"):
      return status

    if not(os.path.exists(path+"/job.out")):
      #sk print 'NotYet for %s' % path+'/job.out'
      return "NotYet/"+status[:2]

    if os.path.getsize(path+"/job.err")>0:
       return "Error/"+status[:2]
    
    fic = open(path+"/job.out")
    t = "__NEWLINE__".join(fic.readlines())
    fic.close()
    p = re.compile("\s+")
    t = p.sub(' ',t)
    p = re.compile("\s*__NEWLINE__\s*")
    t = p.sub('__NEWLINE__',t)

    try:
      start_timing = t.split("======== start ==============")
      #print len(start_timing),start_timing
      if len(start_timing)<2:
        return "NOST/"+status[:2]
      from_date = start_timing[1].replace("__NEWLINE__","").replace("\n","").split(" ")
      (from_month,from_day,from_time) = (from_date[1],from_date[2],from_date[3])
      (from_hour,from_minute,from_second) = from_time.split(":")
            
      end_timing = t.split("======== end ==============")
      if len(end_timing)<2:
        if status=="RUNNING":
          now = datetime.datetime.now()
          
          ellapsed_time = ((int(now.day)*24.+int(now.hour))*60+int(now.minute))*60+int(now.second) \
                        - (((int(from_day)*24.+int(from_hour))*60+int(from_minute))*60+int(from_second))
          return "%d/RU" % ellapsed_time 
        return "NOEND/"+status[:2]
      from_date = to_date = "None"
      if len(start_timing)>1 and len(end_timing)>1:
        to_date = end_timing[1].replace("__NEWLINE__","").replace("\n","").split(" ")
        (to_month,to_day,to_time) = (to_date[1],to_date[2],to_date[3])
        if self.DEBUG:
          print "[get_time] from_time=!%s! start_timing=!%s! from_date" % (from_time,start_timing[1]), from_date
          print "[get_time]   to_time=!%s!   end_timing=!%s! to_date" % (to_time,end_timing[1]) , to_date
      
        (to_hour,to_minute,to_second) = to_time.split(":")
        ellapsed_time = ((int(to_day)*24.+int(to_hour))*60+int(to_minute))*60+int(to_second) \
                        - (((int(from_day)*24.+int(from_hour))*60+int(from_minute))*60+int(from_second))
        if self.DEBUG:
          print from_date,to_date,(from_month,from_day,from_time),(to_month,to_day,to_time)
      else:
        if self.DEBUG:
          print "[get_timing] Exception type 1"
          if self.DEBUG>1:
            except_print()
        ellapsed_time = "NOGOOD"
    except:
      if self.DEBUG:
        print "[get_timing] Exception type 2"
        except_print()
      ellapsed_time=-2
    if isinstance(ellapsed_time,basestring):
      return ellapsed_time
    return self.my_timing(path,ellapsed_time,status)


  #########################################################################
  # user defined routine to be overloaded to define user's own timing
  #########################################################################

  def my_timing(self,dir,ellapsed_time,status):
    if self.DEBUG:
      print dir
    return ellapsed_time


  #########################################################################
  # clean a line from the output
  #########################################################################

  def clean_line(self,line):
   if self.DEBUG:
     print "analyzing line !!"+line+"!!"
   # replace any multiple blanks by one only
   p = re.compile("\s+")
   line = p.sub(' ',line[:-1])
   # get rid of blanks at the end of the line
   p = re.compile("\s+$")
   line = p.sub('',line)
   # get rid of blanks at the beginning of the line
   p = re.compile("^\s+")
   line = p.sub('',line)
   # line is clean!
   if self.DEBUG:
     print "analyzing  line cleaned !!"+line+"!!"
   return line


  def additional_tag(self,line):
    matchObj = re.match(r'^#KTF\s*(\S+|_)\s*=\s*(.*)\s*$',line)
    if (matchObj):
      # yes! saving it in direct_tag and go to next line
      (t,v) = (matchObj.group(1), matchObj.group(2))
      if self.DEBUG:
        print "direct tag definitition : ",line
      self.direct_tag[t] = v
      return True
    return False

  #########################################################################
  # generation of the jobs and submission of them if --build 
  #########################################################################
          
  def run(self):

    test_matrix_filename = "tests/%s_cases.txt" % self.MACHINE
    
    if not(os.path.exists(test_matrix_filename)):
      print "\n\t ERROR : missing test matrix file %s for machine %s" % (test_matrix_filename,self.MACHINE)
      print "\n\t         ktf --create-test-template can be called to create the templates"
      sys.exit(1)

    print
    
    now = time.strftime('%y%m%d-%H_%M_%S',time.localtime())
    tags_ok = False
    mandatory_fields = ["Test", "Directory"]

    lines = open(test_matrix_filename).readlines()

    # warning message is sent to the user if filter is applied on the jobs to run
    
    if len(self.ONLY):
      print "the filter %s will be applied... Only following lines will be taken into account :"
      self.direct_tag = {}
      for line in lines:
        line = self.clean_line(line)
        if self.additional_tag(line):
          continue
        if len(line)>0  and not (line[0]=='#'):
          if not(tags_ok):
            tags_ok=True
            continue
          for k in self.direct_tag.keys():
            line = line+" "+self.direct_tag[k]
          if self.DEBUG:
            print line
          matchObj = re.match("^.*"+self.ONLY+".*$",line)
          # prints all the tests that will be selected
          if (matchObj):
            print "\t"+"\t".join(line.split(" "))
      # askine to the user if he is ok or not
      input_var = raw_input("Is this correct ? (yes/no) ")
      if not(input_var == "yes"):
          print "ABORTING: No clear confirmation... giving up!"
          sys.exit(1)
          
      tags_ok = False
          
    # direct_tag contains the tags set through #KTF tag = value
    # it needs to be evaluated on the fly to apply right tag value at a given job
    self.direct_tag = {}

    # parsing of the input file starts...
    for line in lines:
      line = self.clean_line(line)
      # is it a tag enforced by #KTF directive?
      if self.additional_tag(line):
        continue
      
      # if line void or starting with '#', go to the next line
      if len(line)==0 or (line[0]=='#'):
        continue

      # parsing other line than #KTF directive
      if not(tags_ok):
        # first line ever -> Containaing tag names
        tags_names = line.split(" ")
        tags_ok = True
        continue 

      # if job case are filtered, apply it, jumping to next line if filter not match
      matchObj = re.match("^.*"+self.ONLY+".*$",line)
      if not(matchObj):
        continue

      if self.DEBUG:
        print "testing : ",line
        print "tags_names:",tags_names
    
      tags = line.split(" ")
      tags = shlex.split(line)

      if not(len(tags)==len(tags_names)):
        print "\tError : pb encountered in reading the test matrix file : %s" % test_matrix_filename,
        print "at  line \n\t\t!%s!" % line
        print "\t\tless parameters to read than expected... Those expected are"
        print "\t\t\t",tags_names
        print "\t\tand so far, we read"
        print "\t\t\t",tag
        sys.exit(1)

      
      ts = copy.deepcopy(tags_names)
      tag = {}
      if self.DEBUG:
        print "ts",ts
        print "tags",tags
      
      while(len(ts)):
        t = ts.pop(0)
        tag["%s" % t] = tags.pop(0)
        if self.DEBUG:
          print "tag %s : !%s! " % (t,tag["%s" % t])
      if self.DEBUG:
        print "tag:",tag
          
      # adding the tags enforced by a #KTF directive
      tag.update(self.direct_tag)

      if self.DEBUG:
        print self.direct_tag
        print "tag after update:",tag

      # checking if mandatory tags are there
      for c in mandatory_fields:
         if not( c in tag.keys()):
            print "\n\t ERROR : missing column /%s/ in test matrix file %s for machine %s" % \
              (c,test_matrix_filename,self.MACHINE)
            sys.exit(1)

      # all tags are valued at this time
      # creating the job directory indexed by time
      dest_directory = "tests_%s_%s/%s" % (self.MACHINE,now,tag["Test"])
      cmd = ""

      print "\tcreating test directory %s for %s: " % (dest_directory,self.MACHINE)


      if "Submit" in tag.keys():
        submit_command = tag["Submit"]
      else:
        submit_command = self.SUBMIT_CMD
      cmd = cmd + \
            "mkdir -p %s; cd %s ; tar fc - -C ../../tests/%s . | tar xvf - > /dev/null\n " % \
            ( dest_directory, dest_directory,tag["Directory"]) 
      

      # copying contents of the tests/common directory into the directory where the job will take place
      if os.path.exists('tests/common'):
        cmd = cmd + \
            "tar fc - -C ../../tests/common . | tar xvf - > /dev/null "
      
      self.wrapped_system(cmd,comment="copying in %s" % dest_directory)

      tag["STARTING_DIR"] = "."
      job_file=self.substitute(dest_directory,tag)

      if job_file:
        cmd = "cd %s; %s %s > job.submit.out 2> job.submit.err " % \
            (os.path.dirname(job_file), submit_command,\
               os.path.basename(job_file))
        if self.SUBMIT:
          print "\tsubmitting job %s " % job_file
          self.wrapped_system(cmd,comment="submitting job %s" % job_file)
          output_file = "%s/job.submit.out" % os.path.dirname(job_file)
          error_file = "%s/job.submit.err" % os.path.dirname(job_file)
          if os.path.exists(error_file):
            if os.path.getsize(error_file)>0:
              print "\n\tError... something went wrong when submitting job %s " % job_file
              print "\n           here's the error file just after submission : \n\t\t%s\n" % error_file
              print "\t\tERR> "+ "ERR> \t\t".join(open(error_file,"r").readlines())
              sys.exit(1)
          f = open(output_file,"r").readline()[:-1].split(" ")[-1]
          self.JOB_ID[os.path.abspath(os.path.dirname(job_file))] = f
          if self.DEBUG:
            print 'job_id -> ',f
              
        else:
          print "\tshould submit job %s (if --submit added) " % job_file
        #print cmd
      else:
        print "\t\tWarning... no job file found for machine %s in test directory %s " % \
              (self.MACHINE,dest_directory)
      print
      self.save_workspace()
        
    
if __name__ == "__main__":
    K = ktf()
    K.welcome_message()
    K.parse()
    if self.TIME:
      K.list_jobs_and_get_time()
    else:
      run()
      
    self.save_workspace()
