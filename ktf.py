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

DEBUG                = 0
FAKE                 = False
DRY                  = False
MACHINE              = False
MATRIX_FILE_TEMPLATE = ""
BUILD                = False
SUBMIT               = False
SUBMIT_CMD           = False
ALL                  = False

TESTS = {}

KTF_PATH = os.getenv("KTF_PATH")
if not(KTF_PATH):
  KTF_PATH = "/opt/share/ktf/0.1/"

ROOT_PATH     = os.path.dirname(__file__)
ROOT_PATH     = "."

MY_MACHINE = TMPDIR = MY_MACHINE_FULL_NAME = ""
MY_HOSTNAME = TMPDIR = MY_HOSTNAME_FULL_NAME = ""


ERROR              = -1

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
    self.TIME = False

  #########################################################################
  # get machine name and alias 
  #########################################################################
  def get_machine(self):
      """
      determines the machine where tests are run
      """
      global SUBMIT_CMD, MATRIX_FILE_TEMPLATE

      tmp_directory = "/tmp"
      machine = socket.gethostname()
      self.user_message("","socket.gethostname=/%s/" % machine)
      
      if (machine[:4]=="fen1" or machine[:4]=="fen2"):
          machine = "shaheen1"
  #        SUBMIT_CMD = '/opt/share/altd/1.0.1/alias/rerouting/llsubmit'
          SUBMIT_CMD = 'llsubmit'
          MATRIX_FILE_TEMPLATE = """tests/shaheen_cases.txt__SEP2__# test matrix for shaheen

  Test		Directory         NB_CORES       PARTITION_SIZE    ELLAPSED_TIME            EXECUTABLE

  # test test1

  #Code_test1_1024	test1          1024              256            1:10:00         ../../src/code.x.y.z/bin/code
  #Code_test1_512	test1          512               128            1:10:00         ../../src/code.x.y.z/bin/code
  #Code_test1_256	test1          256               64             3:10:00         ../../src/code.x.y.z/bin/code
  #Code_test1_128	test1          128               32             3:10:00         ../../src/code.x.y.z/bin/code

  __SEP1__tests/test1/job.shaheen.template__SEP2__#!/bin/sh
  #@ job_name         = __Test__
  #@ output           = job.out
  #@ error            = job.err
  #@ job_type         = bluegene
  #@ bg_size          = __PARTITION_SIZE__
  #@ wall_clock_limit = __ELLAPSED_TIME__
  ## If required uncomment the following line and add your project ID
  #@ account_no = k01
  #@ queue

  cd __STARTING_DIR__ 
  echo ======== start ==============
  date
  echo ======== start ==============
  mpirun -np __NB_CORES__  -mode VN -exe __EXECUTABLE__   #   -env "BGLMPIO_COMM=1"  -args '-opt xxx'
  echo ======== end ==============
  date
  echo ======== end ==============
  """
      elif (machine[:4]=="fen3" or machine[:4]=="fen4"):
          machine = "neser"
  #        SUBMIT_CMD = '/opt/share/altd/1.0.1/alias/rerouting/llsubmit'
          SUBMIT_CMD = 'llsubmit'
      elif (machine[:4]=="swan"):
          machine = "swan"
          SUBMIT_CMD = 'qsub'
      elif (machine[:4]=="sid4"):
          machine = "sid"
      elif (machine[:4]=="o185"):
          machine = "hp"
          SUBMIT_CMD = 'sbatch'
      elif (machine[:5]=="vhn11"):
          machine = "fujitsu"
          SUBMIT_CMD = 'sbatch'
      elif (machine[:3]=="cdl"):
          machine = "shaheen"
          SUBMIT_CMD = 'sbatch'
          MATRIX_FILE_TEMPLATE = """tests/shaheen_cases.txt__SEP2__# test matrix for shaheen II

  Test		Directory     NB_CORES        ELLAPSED_TIME            EXECUTABLE

  # test test1

  #Code_test1_512	test1          512             1:10:00         ../../src/code.x.y.z/bin/code
  #Code_test1_256	test1          256             3:10:00         ../../src/code.x.y.z/bin/code
  #Code_test1_128	test1          128             3:10:00         ../../src/code.x.y.z/bin/code

  __SEP1__tests/test1/job.shaheen.template__SEP2__#!/bin/bash
  #SBATCH --job-name=__Test__
  #SBATCH --output=job.out
  #SBATCH --error=job.err
  #SBATCH --ntasks=__NB_CORES__
  #SBATCH --time=__ELLAPSED_TIME__

  cd __STARTING_DIR__ 
  echo ======== start ==============
  date
  echo ======== start ==============
  aprun -n __NB_CORES__   __EXECUTABLE__
  echo ======== end ==============
  date
  echo ======== end ==============
  """
      else:
          print "[WARNING]  machine /%s/ unknowwn : using sh to submit  " % machine
          machine = "unknown"
          SUBMIT_CMD = 'sh'

      return machine, tmp_directory





  #########################################################################
  # welcome message
  #########################################################################


  def welcome_message(self):
      """ welcome message"""

      global MY_HOSTNAME, TMPDIR, MY_HOSTNAME_FULL_NAME


      MY_HOSTNAME, TMPDIR = self.get_machine()
      MY_HOSTNAME_FULL_NAME = socket.gethostname()

      print """                   #########################################
                     #   Welcome to KSL Test Framework 0.2!  #
                     #########################################
       """
      print "\trunning on %s (%s) " %(MY_HOSTNAME_FULL_NAME,MY_HOSTNAME)
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
               \n\t\t[ --machine=<machine>] [ --test=<test_nb> ] \
               \n\t\t[ --submit ] [--build ] [ --time ] [ --create-template ] [ --all ]\
               \n\t\t[ --debug ] [ --debug-level=[0|1|2] ] [ --fake ] [ --dry-run ] \
             \n"  

      sys.exit(1)


  #########################################################################
  # parsing command line
  #########################################################################

  def parse(self,args=sys.argv[1:]):
      """ parse the command line and set global _flags according to it """

      global DEBUG, FAKE, MACHINE, TESTS, DRY, SUBMIT, MY_HOSTNAME, ALL, BUILD
      
      try:
          opts, args = getopt.getopt(args, "h", 
                            ["help", "machine=", "test=", \
                               "debug", "debug-level=", "time", "create-template", "build", "all" \
                               "fake", "dry-run", "submit" ])    
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
          DEBUG = 1
        elif option in ("--debug-level"):
          DEBUG = int(argument)
        elif option in ("--time"):
          self.TIME = True
        elif option in ("--create-template"):
          self.create_test_matrix_template()
        elif option in ("--all"):
          ALL = True
        elif option in ("--build"):
          BUILD = True
        elif option in ("--submit"):
          SUBMIT = True
          BUILD = True
        elif option in ("--fake"):
          DEBUG = True
          FAKE = True
        elif option in ("--dry-run"):
          DRY = True
      # second scan to get other arguments
      
      for option, argument in opts:
        if option in ("--machine"):
          MACHINE = argument

      if not(MACHINE):
        if MY_HOSTNAME=="unknown":
          self.usage("Choose --machine=????")
        else:
          MACHINE = MY_HOSTNAME

      if SUBMIT and self.TIME : 
        self.usage("--time and --submit can not be asked simultaneously")

      if BUILD and self.TIME : 
        self.usage("--time and --build can not be asked simultaneously")

      if not(BUILD) and not(self.TIME) and not(SUBMIT):
        self.usage("at least --build, --submit or --time should be asked")

  #########################################################################
  # os.system wrapped to enable Trace if needed
  #########################################################################

  def wrapped_system(self,cmd,comment="No comment",fake=False):
    global TARGET, DEBUG, TARGET_HOME

    if DEBUG:
      print "\tcurrently executing /%s/ :\n\t\t%s" % (comment,cmd)

    if not(fake) and not(FAKE):
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
          
  def user_message(self,msg=None,msg_debug=None,action=None):

    if action==ERROR:
      prefix = "Error: "
    else:
      prefix = ""

    br = ""
        
    if DEBUG and msg_debug:
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
      global MACHINE

      job_file = None

      self.user_message(msg_debug="\nsubstituting in "+directory)
      self.user_message(msg_debug="\n\tbalises  = %s\n " % str(balises))
          
      for root, dirs, files in os.walk(directory):
          if DEBUG:
             print dirs,files

          for name in files:
              if ".template" in name and os.path.exists(os.path.join(root, name)):
                  if DEBUG:
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

                  if name_saved == "job.%s" % MACHINE:
                      job_file = os.path.join(root, name_saved)
                            
  #         for name in dirs:
  #             job_file_candidate = self.substitute(os.path.join(root, name),balises)
  #             if (job_file_candidate):
  #                 job_file = job_file_candidate

      return job_file


  #########################################################################
  # return sub directories
  #########################################################################

  def list_dirs(self,directory,what):
      job_file = None

      if DEBUG:
          print "searching in ",directory


      f = []
      d = []
      for (dirpath, dirnames, filenames) in os.walk(directory):
        f.extend(filenames)
        d.extend(dirnames)

      if what=="DIR":
        return d
      if what=="FILE":
        return f

  #########################################################################
  # create test template (matrix and job)
  #########################################################################
  def create_test_matrix_template(self):
    global MATRIX_FILE_TEMPLATE

    l = MATRIX_FILE_TEMPLATE
    
    print

    for filename_content in l.split("__SEP1__"):
      filename,content = filename_content.split("__SEP2__")
      if os.path.exists(filename):
        print "\ttest matrix file %s already exists... skipping it!" % filename
      else:
        dirname = os.path.dirname(filename)
        if not(os.path.exists(dirname)):
          self.wrapped_system("mkdir -p %s" % dirname,comment="creating dir %s" % dirname)
        f = open(filename,"w")
        f.write(content)
        f.close()
        self.user_message(msg="file %s created " % filename)

    sys.exit(0)

  #########################################################################
  # list all available job.out and print ellapsed time
  #########################################################################


  def scan_jobs_and_get_time(self,path=".",level=0,timing=False,
                             dir_already_printed={},timing_results={},current_dir_match=None):
    global ALL

    if len(timing_results) == 0:
      timing_results["procs"] = []
      timing_results["cases"] = []
      timing_results["runs"] = []
      
    if level==0:
      print "\n\tBenchmarks Availables: "

    
    if DEBUG>3:
      print "\n[list_jobs_and_get_time] scanning ",path," for timings=",timing

    if not(os.path.exists(path)):
      return
    
    if not(os.path.isdir(path)):
      return
      
    dirs = sorted(os.listdir(path))


    if len(dirs):
      #if level == SCANNING_FROM :
      #  print "%s%d %s Availables: " % ("\t"*(level+1),len(dirs),ArboNames[level])
      if DEBUG>3:
        print level,dirs
      for d in [ "job.out" ]:
        if os.path.exists(path + "/" + d) :
          if os.path.isfile(path + "/" + d) :
            if DEBUG:
              print "[list_jobs_and_get_time] candidate : %s " % (path+"/"+"job.out")
            # formatting the dirname
            p = re.match(r"(.*tests_.*)/.*",path)
            if p:
              dir_match = p.group(1)
  #           else:
  #             dir_match = "??? (%s)" % path

            path_new = path + "/" + d

            timing_result = self.get_timing(path_new)
            if timing_result>-1 or ALL:
              if not(dir_match in dir_already_printed.keys()):
                print "%s- %s " % ("\t"+"   "*(level),dir_match)
              dir_already_printed[dir_match] = False
              case_match = path_new.replace(dir_match+"/","")
              case_match = case_match.replace("/job.out","")
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

              if not(k in timing_results.keys()):
                timing_results[k] = []
              if not(dir_match in timing_results["runs"]):
                timing_results["runs"].append(dir_match)
              if not(proc_match in timing_results["procs"]): 
                timing_results["procs"].append(proc_match)
              if not(case_match in timing_results["cases"]):
                  timing_results["cases"].append(case_match)
    
              timing_results[k]=timing_result
              print "\t\t%10s s \t %5s %40s " % ( timing_result, proc_match, case_match)

        
        for d in dirs :
          if not(d in [".git","src"]):
            path_new = path + "/" + d
            if os.path.isdir(path_new):
              timing_results = self.scan_jobs_and_get_time(path_new,level+1,timing,dir_already_printed,timing_results,current_dir_match)

        return timing_results


  def list_jobs_and_get_time(self,path=".",level=0,timing=False,
                             dir_already_printed={},timing_results={},current_dir_match=None):

    timming_results = self.scan_jobs_and_get_time(path,level,timing,dir_already_printed,
                                             timing_results,current_dir_match)

    nb_tests = 0
    total_time = {}
    timing_results["procs"].sort(key=int)

    print "%45s" % "Runs",

    for run in timing_results["runs"]:
      print "%8s" % run.replace("-","").replace("_","")[-8:],
    print
    
    for case in timing_results["cases"]:
      for proc in timing_results["procs"]:
        k0 = "%s.%s" % (proc, case)
        nb_runs = 0
        for run in timing_results["runs"]:
          k = "%s.%s.%s" % (run,proc,case)
          if k in timing_results.keys():
            nb_runs += 1
        if nb_runs:
          print "%45s" % k0,
          for run in timing_results["runs"]:
            k = "%s.%s.%s" % (run,proc,case)
            if k in timing_results.keys():
              print "%8s" % timing_results[k],
              nb_tests = nb_tests + 1
              if not(run in total_time.keys()):
                total_time[run]=0
              total_time[run] += timing_results[k]
            else:
              print "%8s" % "-", 
          print "%3s tests %s" % (nb_runs,k0)
    print "%45s" % "total time",
    for run in timing_results["runs"]:
      print "%8s" % total_time[run],
    print "%3s" % nb_tests,'tests completed'
      
  #########################################################################
  # calculation of ellapsed time based on values dumped in job.out
  #########################################################################


  def get_timing(self,path):
    fic = open(path)
    t = "__NEWLINE__".join(fic.readlines())
    fic.close()
    p = re.compile("\s+")
    t = p.sub(' ',t)
    p = re.compile("\s*__NEWLINE__\s*")
    t = p.sub('__NEWLINE__',t)

    try:
      start_timing = t.split("======== start ==============")
      end_timing = t.split("======== end ==============")
      from_date = to_date = "None"
      if len(start_timing)>1 and len(end_timing)>1:
        from_date = start_timing[1].replace("__NEWLINE__","").replace("\n","").split(" ")
        (from_month,from_day,from_time) = (from_date[1],from_date[2],from_date[3])
        to_date = end_timing[1].replace("__NEWLINE__","").replace("\n","").split(" ")
        (to_month,to_day,to_time) = (to_date[1],to_date[2],to_date[3])
        if DEBUG:
          print "[get_time] from_time=!%s! start_timing=!%s! from_date" % (from_time,start_timing[1]), from_date
          print "[get_time]   to_time=!%s!   end_timing=!%s! to_date" % (to_time,end_timing[1]) , to_date
        (from_hour,from_minute,from_second) = from_time.split(":")
        (to_hour,to_minute,to_second) = to_time.split(":")
        ellapsed_time = ((int(to_day)*24.+int(to_hour))*60+int(to_minute))*60+int(to_second) \
                        - (((int(from_day)*24.+int(from_hour))*60+int(from_minute))*60+int(from_second))
        if DEBUG:
          print from_date,to_date,(from_month,from_day,from_time),(to_month,to_day,to_time)
      else:
        if DEBUG:
          print "[get_timing] Exception type 1"
          if DEBUG>1:
            except_print()
        ellapsed_time = -1
    except:
      if DEBUG:
        print "[get_timing] Exception type 2"
        except_print()
      ellapsed_time=-2
    return ellapsed_time



  #########################################################################
  # routing
  #########################################################################
          
  def run(self):
    global MACHINE, DEBUG, SUBMIT, SUBMIT_CMD

    test_matrix_filename = "tests/%s_cases.txt" % MACHINE
    
    if not(os.path.exists(test_matrix_filename)):
      print "\n\t ERROR : missing test matrix file %s for machine %s" % (test_matrix_filename,MACHINE)
      print "\n\t         ktf --create-test-template can be called to create the templates"
      sys.exit(1)

    print
    
    now = time.strftime('%y%m%d-%H_%M_%S',time.localtime())
    tags_ok = False
    mandatory_fields = ["Test", "Directory"]
    if not(SUBMIT_CMD):
      mandatory_fields.append("Submit")
    for line in open(test_matrix_filename):
      if DEBUG:
        print "analyzing line !!"+line+"!!"
      p = re.compile("\s+")
      line = p.sub(' ',line[:-1])
      p = re.compile("\s+$")
      line = p.sub('',line)
      p = re.compile("^\s+")
      line = p.sub('',line)
      if DEBUG:
        print "analyzing  line cleaned !!"+line+"!!"
      if len(line)>0  and not (line[0]=='#'):
        if not(tags_ok):
          tags_names = line.split(" ")
          for c in mandatory_fields:
            if not( c in tags_names):
              print "\n\t ERROR : missing column %s in test matrix file %s for machine %s" % \
                (c,test_matrix_filename,MACHINE)
              sys.exit(1)
          tags_ok = True
          continue 
        if DEBUG:
          print "testing : ",line
          print "tags_names:",tags_names
    
        tags = line.split(" ")
        tags = shlex.split(line)
        ts = copy.deepcopy(tags_names)
        tag = {}
        if DEBUG:
          print "ts",ts
          print "tags",tags
        try:
          while(len(ts)):
            t = ts.pop(0)
            tag["%s" % t] = tags.pop(0)
            if DEBUG:
              print "tag %s : !%s! " % (t,tag["%s" % t])
          if DEBUG:
            print "tag:",tag
        except:
          print "\tError : pb encountered in reading the test matrix file : %s" % test_matrix_filename,
          print "at  line \n\t\t!%s!" % line
          print "\t\tless parameters to read than expected... Those expected are"
          print "\t\t\t",tags_names
          print "\t\tand so far, we read"
          print "\t\t\t",tag
          sys.exit(1)

        dest_directory = "tests_%s_%s/%s" % (MACHINE,now,tag["Test"])
        cmd = ""

        if os.path.exists(dest_directory):
          dest_directory_old = "%s_%s" % (dest_directory,now)
          print "\tWarning... test directory %s already exists for %s: " % (dest_directory,MACHINE)
          print "\t\tBacked up in %s" % dest_directory_old
          cmd = "mv %s %s \n" % (dest_directory,dest_directory_old)
          
        print "\tcreating test directory %s for %s: " % (dest_directory,MACHINE)

        if "Submit" in tag.keys():
          submit_command = tag["Submit"]
        else:
          submit_command = SUBMIT_CMD
        cmd = cmd + \
              "mkdir -p %s; cd %s ; tar fc - -C ../../tests/%s . | tar xvf - > /dev/null\n " % \
              ( dest_directory, dest_directory,tag["Directory"]) 
        
        if os.path.exists('tests/common'):
          cmd = cmd + \
              "tar fc - -C ../../tests/common . | tar xvf - > /dev/null "
        
        self.wrapped_system(cmd,comment="copying in %s" % dest_directory)

        tag["STARTING_DIR"] = "."
        job_file=self.substitute(dest_directory,tag)

        if job_file:
          cmd = "cd %s; %s %s > job.submit.out 2>&1 " % \
              (os.path.dirname(job_file), submit_command,\
                 os.path.basename(job_file))
          if SUBMIT:
            print "\tsubmitting job %s " % job_file
            self.wrapped_system(cmd,comment="submitting job %s" % job_file)
          else:
            print "\tshould submit job %s (if --submit added) " % job_file
          #print cmd
        else:
          print "\t\tWarning... no job file found for machine %s in test directory %s " % \
                (MACHINE,dest_directory)
        print
        
if __name__ == "__main__":
    K = ktf()
    K.welcome_message()
    K.parse()
    if self.TIME:
      K.list_jobs_and_get_time()
    else:
      run()
      
