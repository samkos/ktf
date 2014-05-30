import getopt, sys, os, socket

import logging
import logging.handlers
import warnings

import math
import time
import subprocess
import re
import copy

DEBUG         = False
FAKE          = False
DRY           = False
MACHINE       = False
BUILD         = False
SUBMIT        = False
SUBMIT_CMD    = False
TIME          = False
ALL           = False

TESTS = {}
ROOT_PATH     = os.path.dirname(__file__)
ROOT_PATH     = "."

MY_MACHINE = TMPDIR = MY_MACHINE_FULL_NAME = ""
MY_HOSTNAME = TMPDIR = MY_HOSTNAME_FULL_NAME = ""


ERROR              = -1

#########################################################################
# set log file
#########################################################################


for d in ["%s/LOGS" % ROOT_PATH]:
  if not(os.path.exists(d)):
    os.mkdir(d)

logger = logging.getLogger('ktf.log')
logger.propagate = None
logger.setLevel(logging.INFO)
log_file_name = "%s/" % ROOT_PATH+"LOGS/ktf.log"
open(log_file_name, "a").close()
handler = logging.handlers.RotatingFileHandler(
     log_file_name, maxBytes = 20000000,  backupCount = 5)
formatter = logging.Formatter("%(asctime)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

loggerror = logging.getLogger('ktf_err.log')
loggerror.propagate = None
loggerror.setLevel(logging.DEBUG)
log_file_name = "%s/" % ROOT_PATH+"LOGS/ktf_err.log"
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



#########################################################################
# get machine name and alias 
#########################################################################
def get_machine():
    """
    determines the machine where tests are run
    """
    global SUBMIT_CMD

    tmp_directory = "/tmp"
    machine = socket.gethostname()
    user_message("","socket.gethostname=/%s/" % machine)
    
    if (machine[:4]=="fen1" or machine[:4]=="fen2"):
        machine = "shaheen"
        SUBMIT_CMD = '/opt/share/altd/1.0.1/alias/rerouting/llsubmit'
    elif (machine[:4]=="fen3" or machine[:4]=="fen4"):
        machine = "neser"
        SUBMIT_CMD = '/opt/share/altd/1.0.1/alias/rerouting/llsubmit'
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
    else:
        machine = "unknown"
        SUBMIT_CMD = 'sh'

    return machine, tmp_directory





#########################################################################
# welcome message
#########################################################################


def welcome_message():
    """ welcome message"""

    global MY_HOSTNAME, TMPDIR, MY_HOSTNAME_FULL_NAME


    MY_HOSTNAME, TMPDIR = get_machine()
    MY_HOSTNAME_FULL_NAME = socket.gethostname()

    print """                   #########################################
                   #   Welcome to KSL Test Framework 0.1!  #
                   #########################################
     """
    print "\trunning on %s (%s) " %(MY_HOSTNAME_FULL_NAME,MY_HOSTNAME)
    print "\n\tprocessing ..."
    print "\t\t", " ".join(sys.argv)



#########################################################################
# usage ...
#########################################################################

    

def usage(message = None, error_detail = ""):
    """ helping message"""
    if message:
        print "\n\tError %s:\n\t\t%s\n" % (error_detail,message)
        print "\ttype ktf -h for the list of available options..."
    else:
      print "\n  usage: \n \t python  run_tests.py \
             \n\t\t[ --help ] \
             \n\t\t[ --machine=<machine>] [ --test=<test_nb> ] \
             \n\t\t[ --submit ] [--build ] [ --time ] [ --all ]\
             \n\t\t[ --debug ] [ --fake ] [ --dry-run ] \
           \n"  

    sys.exit(1)


#########################################################################
# parsing command line
#########################################################################

def parse(args=sys.argv[1:]):
    """ parse the command line and set global _flags according to it """

    global DEBUG, FAKE, MACHINE, TESTS, DRY, SUBMIT, MY_HOSTNAME, TIME, ALL, BUILD
    
    try:
        opts, args = getopt.getopt(args, "h", 
                          ["help", "machine=", "test=", \
                             "debug", "time", "build", "all" \
                             "fake", "dry-run", "submit" ])    
    except getopt.GetoptError, err:
        # print help information and exit:
        usage(err)

    # first scan opf option to get prioritary one first
    # those who sets the state of the process
    # especially those only setting flags are expected here
    for option, argument in opts:
      if option in ("-h", "--help"):
        usage("")
      elif option in ("--debug"):
        DEBUG = True
      elif option in ("--time"):
        TIME = True
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
        usage("Choose --machine=????")
      else:
        MACHINE = MY_HOSTNAME

    if SUBMIT and TIME : 
      usage("--time and --submit can not be asked simultaneously")

    if BUILD and TIME : 
      usage("--time and --build can not be asked simultaneously")

    if not(BUILD) and not(TIME) and not(SUBMIT):
      usage("at least --build, --submit or --time should be asked")

#########################################################################
# os.system wrapped to enable Trace if needed
#########################################################################

def wrapped_system(cmd,comment="No comment",fake=False):
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
        
def user_message(msg=None,msg_debug=None,action=None):

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

def substitute(directory,balises):
    global MACHINE

    job_file = None

    user_message(msg_debug="\nsubstituting in "+directory)
    user_message(msg_debug="\n\tbalises  = %s\n " % str(balises))
        
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
#             job_file_candidate = substitute(os.path.join(root, name),balises)
#             if (job_file_candidate):
#                 job_file = job_file_candidate

    return job_file


#########################################################################
# return sub directories
#########################################################################

def list_dirs(directory,what):
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
# list all available job.out and print ellapsed time
#########################################################################

def list_jobs_and_get_time(path=".",level=0,timing=False,dir_already_printed={},current_dir_match=None):
  global ALL


  if level==0:
    print "\n\tBenchamarks Availables: " 
  
  if DEBUG:
    print "\n scanning ",path," for timings=",timing

  if not(os.path.exists(path)):
    return
  
  if not(os.path.isdir(path)):
    return
    
  dirs = sorted(os.listdir(path))
    
  if len(dirs):
    #if level == SCANNING_FROM :
    #  print "%s%d %s Availables: " % ("\t"*(level+1),len(dirs),ArboNames[level])
    if DEBUG:
      print level,dirs
    for d in dirs :
      path_new = path + "/" + d
      if d=="job.out":
        # formatting the dirname
        p = re.match(r"(.*tests_.*)/.*",path)
        if p:
          dir_match = p.group(1)
        else:
          dir_match = "??? (%s)" % path

        timing_result = get_timing(path_new)
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
            p = re.match(r".*(\d+).*$",case_match)
            if p:
              proc_match = p.group(1)
            else:
              proc_match = "???"
          print "\t\t%10s s \t %5s %s  " % ( timing_result, proc_match, case_match)
      if os.path.isdir(path_new):
        list_jobs_and_get_time(path_new,level+1,timing,dir_already_printed,current_dir_match)





    
#########################################################################
# calculation of ellapsed time based on values dumped in job.out
#########################################################################


def get_timing(path):
  fic = open(path)
  t = "__NEWLINE__".join(fic.readlines())
  fic.close()
  try:
    start_timing = t.split("======== start ==============")
    end_timing = t.split("======== end ==============")
    from_date = to_date = "None"
    if len(start_timing)>1 and len(end_timing)>1:
      from_date = start_timing[1].replace("__NEWLINE__","").replace("\n","").split(" ")
      (from_month,from_day,from_time) = (from_date[1],from_date[2],from_date[3])
      to_date = end_timing[1].replace("__NEWLINE__","").replace("\n","").split(" ")
      (to_month,to_day,to_time) = (to_date[1],to_date[2],to_date[3])
      (from_hour,from_minute,from_second) = from_time.split(":")
      (to_hour,to_minute,to_second) = to_time.split(":")
      ellapsed_time = ((int(to_day)*24.+int(to_hour))*60+int(to_minute))*60+int(to_second) \
                      - (((int(from_day)*24.+int(from_hour))*60+int(from_minute))*60+int(from_second))
      if DEBUG:
        print from_date,to_date,(from_month,from_day,from_time),(to_month,to_day,to_time)
    else:
      if DEBUG:
        print "None"
      ellapsed_time = -1
  except:
      ellapsed_time=-2
  return ellapsed_time



#########################################################################
# routing
#########################################################################
        
def run():
  global MACHINE, DEBUG, SUBMIT, SUBMIT_CMD

  test_matrix_filename = "tests/%s_cases.txt" % MACHINE
  
  if not(os.path.exists(test_matrix_filename)):
    print "\n\t ERROR : missing test matrix file %s for machine %s" % (test_matrix_filename,MACHINE)
    sys.exit(1)

  print
  
  now = time.strftime('%y%m%d-%H:%M:%S',time.localtime())
  tags_ok = False
  mandatory_fields = ["Test", "Directory"]
  if not(SUBMIT_CMD):
    mandatory_fields.append("Submit")
  for line in open(test_matrix_filename):
    p = re.compile("\s+")
    line = p.sub(' ',line[:-1])
    if DEBUG:
      print "analyzing line !!"+line+"!!"
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
      ts = copy.deepcopy(tags_names)
      tag = {}
      if DEBUG:
        print "ts",ts
        print "tags",tags
      while(len(ts)):
        t = ts.pop(0)
        tag["%s" % t] = tags.pop(0)
        if DEBUG:
          print "tag %s : !%s! " % (t,tag["%s" % t])
      if DEBUG:
        print "tag:",tag


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
      
      wrapped_system(cmd,comment="copying in %s" % dest_directory)

      tag["STARTING_DIR"] = "."
      job_file=substitute(dest_directory,tag)

      if job_file:
        cmd = "cd %s; %s %s > job.submit.out 2>&1 " % \
            (os.path.dirname(job_file), submit_command,\
               os.path.basename(job_file))
        if SUBMIT:
          print "\tsubmitting job %s " % job_file
          wrapped_system(cmd,comment="submitting job %s" % job_file)
        else:
          print "\tshould submit job %s (if --submit added) " % job_file
        #print cmd
      else:
        print "\t\tWarning... no job file found for machine %s in test directory %s " % \
              (MACHINE,dest_directory)
      print
        
if __name__ == "__main__":
    welcome_message()
    parse()
    if TIME:
      list_jobs_and_get_time()
    else:
      run()
      
