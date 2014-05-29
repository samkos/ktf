import getopt, sys, os, socket

import logging
import logging.handlers
import warnings

import math
import time
import subprocess

#import paramiko

DEBUG         = False
WALKING_DEBUG = False
CASE          = False
PROCS         = False
VERSION       = False
CAMPAIGN      = False
DATE          = False
SCANNING_FROM = 0
TARGET        = False
TARGET_ARGS   = False
TARGET_HOME   = False
SYNC_ONLY     = False
SUBMIT        = "llsubmit"
SYNCHRONIZE   = False
SCRATCH       = "/scratch"
SCRATCH_SUBST = "/home"
NB_CORES      = 4
TIMING_RESULT = False

LIST          = False
CREATE        = False
COMPILE       = False
NOCOMPILE     = False
JUSTCOMPILED  = False
CLEAN         = False
RUN           = False
FORCE         = False
FAKE          = False
DRY           = False

ROOT_PATH     = os.path.dirname(__file__)
ROOT_PATH     = "."

MY_MACHINE = TMPDIR = MY_MACHINE_FULL_NAME = ""


ERROR              = -1
INFO_FILE_TEMPLATE = "compile_dir = '' # or 'No_Need' if code does not need to be compiled " +\
                     "\nsource_to_test = '' # or 'No_Need' if code does not need to be compiled " +\
                     "\nexecutable  = '' # or 'No_Need' if executable does not need to be built from source" + \
                     "\nstarting_dir=''\nto_copy = []\nto_copy_with_no_subdirectory = []" +\
                     "\nto_link = []\nto_link_with_no_subdirectory = []\nto_create = []\n#running_configuration = []" + \
                     "\n\n#import math\n\n# uncomment the following if needed \n#" + \
                     "\n#########################################################################" + \
                     "\n# distribution of the domain over the proc" + \
                     "\n#########################################################################" + \
                     "\n#" + \
                     "\n#def distribute_domain(n,balises={}):" + \
                     "\n#    x =int(math.pow(2,int(math.log(n,2)/2)))" + \
                     "\n#    y = n/x" + \
                     "\n#    z = 1" + \
                     "\n#    if not(x*y*z==n):" + \
                     "\n#        raise Exception('I do not know how to distribute data among nodes for n=%d' % n)" + \
                     "\n#    balises['__ELLAPSED_TIME__'] = '2:00:00'" + \
                     "\n#    return (x,y,z)"  + \
                     "\n" + \
                     "\n#########################################################################" + \
                     "\n# computation of the number of pe" + \
                     "\n#########################################################################" + \
                     "\n" + \
                     "\ndef nb_pe_needed(nb_pe):" + \
                     "\n    return nb_pe"
                    

ELLAPSED_TIME      =  "00:29:00"
DATA_REPOSITORY    =  "/project/v08/Test_cases/DATA"

MACHINE_HOME       = {"bgp"   : { "login" : "sam@shaheen",  "home" : "/home/sam", \
                                  "submit" : "llsubmit", "scratch" : ["/home","/scratch"], } , 
                      "neser" : { "login" : "sam@neser",  "home" : "/home/sam", \
                                  "submit" : "llsubmit", "scratch" : ["/home","/scratch"], } , 
                      "cray"  : { "login" : "p01921@cray" , "home" : "/home/users/p01921",\
                                  "submit" : "qsub", "scratch" : ["/ufs/home/users","/lus/scratch"] },
                      "bull"  : { "login" : "xfekis@bull" , "home" : "/home_nfs/xfekis/SAM",\
                                  "submit" : "sbatch", "scratch" : ["/home_nfs","/scratch_lustre_xyratex"] },
                      "hp"  : { "login" : "kaust@hp" , "home" : "/home/kaust/SAM",\
                                "submit" : "sbatch", "scratch" : ["/home","/home"] } , \
                      "fujitsu"  : { "login" : "hpc11@fujitsu" , "home" : "/home/hpc11/SAM",\
                                "submit" : ". ", "scratch" : ["/home","/tmp"] } 
                      }

#########################################################################
# IHM 
#########################################################################

ArboNames = ("Codes","Versions","Benchmarks")


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
    global SUBMIT, SCRATCH, SCRATCH_SUBST, NB_CORES, DATA_REPOSITORY 


    tmp_directory = "/tmp"
    machine = socket.gethostname()
    user_message("","socket.gethostname=/%s/" % machine)
    
    if (machine[:4]=="fen1" ):
        machine = "shaheen"
        tmp_directory = "/scratch/tmp"
        SUBMIT = 'llsubmit'
        SCRATCH = '/scratch'
        SCRATCH_SUBST = '/home'
        NB_CORES = 4
    elif (machine[:4]=="fen3" ):
        machine = "neser"
        tmp_directory = "/scratch/tmp"
        SUBMIT = 'llsubmit'
        SCRATCH = '/scratch'
        SCRATCH_SUBST = '/home'
        NB_CORES = 8
    elif (machine[:4]=="fen3"):
        machine = "neser"
        tmp_directory = "/scratch/tmp"
        SUBMIT = 'llsubmit'
        SCRATCH = '/scratch'
        SCRATCH_SUBST = '/home'
        NB_CORES = 8
    elif (machine[:4]=="swan"):
        machine = "swan"
        tmp_directory = "/tmp"
        SUBMIT = 'qsub'
        SCRATCH = '/lus/scratch'
        SCRATCH_SUBST = '/ufs/home/users'
        NB_CORES = 16
        DATA_REPOSITORY    =  "/home/users/p01921/DATA"
    elif (machine[:4]=="sid4"):
        machine = "sid"
        tmp_directory = "/tmp"
        SUBMIT = 'sbatch'
        SCRATCH = '/scratch_lustre_sfa12k'
        SCRATCH_SUBST = '/home_nfs'
        NB_CORES = 16 
        DATA_REPOSITORY    =  "/home_nfsx/xfekix/SAM/DATA"
    elif (machine[:4]=="o185"):
        machine = "hp"
        tmp_directory = "/tmp"
        SUBMIT = 'sbatch'
        SCRATCH = '/home'
        SCRATCH_SUBST = '/home'
        NB_CORES = 24 
        NB_CORES = 16 
        DATA_REPOSITORY    =  "/home/kaust/SAM/DATA"
    elif (machine[:5]=="vhn11"):
        machine = "fujitsu"
        tmp_directory = "/tmp"
        SUBMIT = 'qsub '
        SCRATCH = '/home'
        SCRATCH_SUBST = '/home'
        NB_CORES = 24 
        DATA_REPOSITORY    =  "/home/kaust/SAM/DATA"
    else:
        machine = "localhost"

    return machine, tmp_directory





#########################################################################
# welcome message
#########################################################################


def welcome_message():
    """ welcome message"""

    global MY_MACHINE, TMPDIR, MY_MACHINE_FULL_NAME


    MY_MACHINE, TMPDIR = get_machine()
    MY_MACHINE_FULL_NAME = socket.gethostname()

    print """
                   #########################################
                   #                                       #
                   #   Welcome to KSL Test Framework 0.1!  #
                   #                                       #
                   #########################################

                   
     """
    print "\n\trunning on %s (%s) " %(MY_MACHINE_FULL_NAME,MY_MACHINE)
    print "\n\tprocessing ..."
    print "\t\t", " ".join(sys.argv)



#########################################################################
# usage ...
#########################################################################

    

def usage(message = None, error_detail = ""):
    """ helping message"""
    if message:
        print "\n\tError %s:\n\t\t%s\n" % (error_detail,message)
    else:
      print "\n  usage: \n \t python ktf.py \
             \n\t\t[ --help ] \
             \n\t\t[ --list ] [ --create] [--compile ] [--no-compile] [--clean] \
             \n\t\t[ --run --procs=<nb_procs> [ --force ] ] \
             \n\t\t[ --target=<remote_machine> [ --sync-only ] [ --results ] \
             \n\t\t[ --case=<test_case_name> ] [ --version=<x.y.z> ] \
             \n\t\t[ --time=hh:mm:ss ]\
             \n\t\t[ --debug ] [ --fake ] [ --dry-run ] \
           \n"  


#             \n\t\t[ --kill | --restart ] \
#             \n\t\t[ --stat | --bilan | --info=<job_id> ] \

    sys.exit(1)


#########################################################################
# parsing command line
#########################################################################

def parse(args=sys.argv[1:]):
    """ parse the command line and set global _flags according to it """

    global DEBUG, WALKING_DEBUG, CASE, PROCS, ELLAPSED_TIME, VERSION, \
           CREATE, COMPILE, NOCOMPILE, CLEAN, LIST, RUN, FORCE, PROCS, SCANNING_FROM, \
           CAMPAIGN, DATE, FAKE, DRY, TARGET, TARGET_HOME, TARGET_ARGS, SYNC_ONLY, TIMING_RESULT, \
           SUBMIT, \
           MY_MACHINE, MY_MACHINE_FULL_NAME, SCRATCH_SUBST, SCRATCH  
    
    try:
        opts, args = getopt.getopt(args, "h", 
                          ["help",\
                           "list", "run", "procs=", "force",  "compile", "no-compile", "clean", "create",\
                           "time=","debug","fake", "dry-run", "create", "version=", \
                           "kill","stat","restart","info","bilan","case=", "target=", "sync-only", "results", \
                           "submit=","xxx="])
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
        DEBUG_WALK = True
      elif option in ("--fake"):
        DEBUG = True
        DEBUG_WALK = True
        FAKE = True
      elif option in ("--dry-run"):
        DRY = True
    # second scan to get other arguments
    
    for option, argument in opts:
      if option in ("--case"):
        CASE = argument.upper()
        SCANNING_FROM = 1
      elif option in ("--run"):
        RUN = True
      elif option in ("--procs"):
        RUN = True
        PROCS = argument.split(",")
      elif option in ("--force"):
        if not(RUN) and not(CREATE):
          usage("--force only can be used with --run or --create")
        FORCE = True
      elif option in ("--time"):
        ELLAPSED_TIME = argument
      elif option in ("--version"):
        VERSION = argument
        SCANNING_FROM = 2
      elif option in ("--submit"):
        SUBMIT = argument
      elif option in ("--target"):
        if not (argument in MACHINE_HOME.keys()):
          usage("--target should be one of the following : " + " ".join(MACHINE_HOME.keys()))
        TARGET = MACHINE_HOME[argument]["login"]
        TARGET_HOME = MACHINE_HOME[argument]["home"]
        SUBMIT = MACHINE_HOME[argument]["submit"]
        SCRATCH = MACHINE_HOME[argument]["scratch"][0]
        SCRATCH_SUBST = MACHINE_HOME[argument]["scratch"][1]
        MY_MACHINE = MY_MACHINE_FULL_NAME = argument
        user_message("\nTarget machine : "+TARGET+"\n")
        cmd_args = " ".join(sys.argv[1:])
        TARGET_ARGS = cmd_args.replace("target=","xxx=")
      elif option in ("--sync-only"):
        if not(TARGET):
          usage("in order to synchronize distant machine --target should be valued and placed before --sync in command line")
        SYNC_ONLY=True
        RUN = True
        PROCS = [ "4" ]
      elif option in ("--results"):
        TIMING_RESULT=True
      elif option in ("--create"):
        CREATE = True
      elif option in ("--compile"):
        COMPILE = True
      elif option in ("--no-compile"):
        NOCOMPILE = True
      elif option in ("--list"):
        LIST = "all"
      elif option in ("--clean"):
        COMPILE = True
        CLEAN = True
            

    if not(LIST) and not(CREATE) and not(RUN) and not(COMPILE):
      LIST = True
      #usage("Choose --create, --compile, --clean or --run")


#########################################################################
# os.system wrapped to enable Trace if needed
#########################################################################

def wrapped_system(cmd,comment="No comment",fake=False):
  global TARGET, DEBUG, TARGET_HOME

  if TARGET:
    present_dir = os.path.abspath(".")      
    # print "present_dir = ",present_dir
    cmd = cmd.replace("%s:%s"% (TARGET,present_dir),"%s:%s" % (TARGET,TARGET_HOME+"/Test_cases"))

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
# distribution of the domain over the proc
#########################################################################

def distribute_domain_default(n,balises={}):
    x =int(math.pow(2,int(math.log(n,2)/3)))
    y =int(math.pow(2,int(math.log(n/x,2)/2)))
    z = n/x/y
    user_message("","using default distribute_domain function")
    if not(x*y*z==n):
        raise Exception("I do not know how to distribute data among nodes for n=%d" % n)
    return (x,y,z)


#########################################################################
# substitute the template file
#########################################################################

def substitute(directory,balises):
    global MY_MACHINE

    job_file = None

    user_message(msg_debug="\nsubstituting in "+directory)
    user_message(msg_debug="\n\tbalises  = %s\n " % str(balises))
        
    for root, dirs, files in os.walk(directory):
        # if DEBUG:
        #     print dirs,files

        for name in files:
            if ".template" in name and os.path.exists(os.path.join(root, name)):
                if DEBUG:
                    print "\t\tsubstituting ",os.path.join(root, name)
                fic = open(os.path.join(root, name))
                t = "__NEWLINE__".join(fic.readlines())
                fic.close()

                for b in balises.keys():
                    t = t.replace(b,"%s"%balises[b])

                name_saved = name.replace(".template","")
                fic = open(os.path.join(root, name_saved),"w")
                fic.write(t.replace("__NEWLINE__",""))
                fic.close()

                if name_saved == "job.%s" % MY_MACHINE:
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
# searching/gathering information abotu the (case,versiomn) to compile
# or to run
#########################################################################
def search_target(balises):
  
  global CASE, VERSION, CAMPAIGN, TARGET, TARGET_HOME

  attempt_directory_case = "./Codes/%s" % CASE

  if not(os.path.exists(attempt_directory_case)):
    print "\n\tTest Case Not Found\n\tAvalaible test Cases : ",\
          sorted(os.listdir("./Codes/"))
    print "\n\tPlease choose one! -->  --case=XXX\n"
    return 0
    
  if os.path.exists(attempt_directory_case):
    if DEBUG:
      print "\tTest Case %s found !" % CASE

  if VERSION:
    attempt_directory_version = attempt_directory_case + "/"+VERSION
    if os.path.exists(attempt_directory_version):
      if DEBUG:
        print "\t\t Version %s found !" % VERSION
  else:
    available_versions = os.listdir(attempt_directory_case)
    if len(available_versions)==1:
      VERSION = available_versions[0]
      print "\n\tPicking only version available for now : ", VERSION
    else:
      print "\n\tVersion Not Found for case %s \n\n\tAvalaible Version : ",\
            available_versions
      print "\n\tPlease choose one! -->  --version=XXX\n"
      return 0
      

  attempt_directory_version = attempt_directory_case + "/"+VERSION
  if DEBUG:
    print "\n\tExecuting from directory : ",attempt_directory_version
  
  code_dir = attempt_directory_version
  info_file = attempt_directory_version+"/info.py"

  if not(os.path.exists(info_file)):
    print "\n\t\tPlease fill out the corresponding information file : \n\t\t\t%s" \
          % info_file
    fic = open(info_file,"w")
    fic.write(INFO_FILE_TEMPLATE)
    fic.close()
    return 0


  cmd  = "".join(open(info_file).readlines())

  campaign = compile_dir = executable = starting_dir = running_configuration = None
  to_link = to_copy = to_link_with_no_subdirectory = to_copy_with_no_subdirectory\
            = to_create = source_to_test = after_tar = None
  compile_dirs = {}
  executable_dirs = {}
  
  
  if PROCS:
    if len(PROCS)>1:
      usage("Not supporting a set of procs set yet","substituting pattern in source code")
  # not that easy to import info.py file...
          
  sys.path.insert(0, "./Codes/%s/%s" % (CASE,VERSION))
  user_message("","\nsourcing info.py file : %s " % info_file)

  warnings.filterwarnings('ignore')
  from info import *
  warnings.filterwarnings('always')

  if PROCS:
    
    #try:
      (nx,ny,nz) = distribute_domain(int(PROCS[0]),balises)
    #except:
    #  (nx,ny,nz) = distribute_domain_default(int(PROCS[0]),balises)
  else:
    nx = ny = nz = None
  del sys.path[0]


#   exec cmd

  if MY_MACHINE in compile_dirs.keys():
    compile_dir = compile_dirs[MY_MACHINE]
    user_message(msg_debug = "\nGetting compilation dir for specific machine %s " % MY_MACHINE )

  if compile_dir == None or len(compile_dir)==0:
    usage("Please provide compile_dir value in file %s" % info_file,"in the setting of the test")

  if MY_MACHINE in executable_dirs.keys():
    executable = executable_dirs[MY_MACHINE]
    user_message(msg_debug = "\nGetting compilation dir for specific machine %s " % MY_MACHINE )

  if executable == None or len(executable)==0:
    usage("Please provide executable in file %s" % info_file,"in the setting of the test")

  if  starting_dir == None or len(starting_dir)==0:
    usage("Please provide starting_dir value in file %s" % info_file,"in the setting of the test")

  if campaign == None or len(campaign)==0:
    campaign = "Campaign1"


  code_dir = os.path.abspath(code_dir)

  if TARGET:
    present_dir = os.path.abspath(".")      
    # print "present_dir = ",present_dir
    remote_code_dir = code_dir.replace(present_dir,"%s/%s" % (TARGET_HOME,"Test_cases"))
  else:
    remote_code_dir = None


  compile_dir = "%s/Src/%s" % (code_dir,compile_dir)
  source_to_test = "%s/Src/%s" % (code_dir,source_to_test)

    
    
  if DEBUG:
    print ("\t\tcode_dir=->%s<-\n\t\tremote_code_dir=->%s<-\n\t\tcompile_dir=->%s<-\n\t\tcompile_dirs=->%s<-\n\t\tsource_to_test=->%s<-\n\t\tafter_tar=->%s<-" +\
           "\n\t\texecutable=->%s<-\n\t\texecutable_dirs=->%s<-\n\t\tstarting_dir=->%s<-\n\t\tcampaign=->%s<-" + \
           "\n\t\trunning_configuration=->%s<-\n\t\tnx=->%s<-\n\t\tny=->%s<-\n\t\tnz=->%s<-" +\
           "\n\t\tbalises=->%s<-\n") %  \
          (code_dir,remote_code_dir,compile_dir,compile_dirs,source_to_test,after_tar,\
          executable,executable_dirs,starting_dir,campaign,running_configuration,nx,ny,nz,balises)
   
  return (code_dir,remote_code_dir,compile_dir,source_to_test,after_tar,\
          executable,starting_dir,\
          to_copy,to_link,to_copy_with_no_subdirectory,to_link_with_no_subdirectory,\
          to_create,campaign,running_configuration,nx,ny,nz)


#########################################################################
# Test running
#########################################################################

class Test:

  """
  main class running a test case
  """

  def __init__(self, code_dir = None, remote_code_dir = None, \
               compile_dir = None, source_to_test=None, after_tar = None, executable = None, \
               starting_dir= None, \
               to_copy= None, to_link = None, \
               to_copy_with_no_subdirectory= None, to_link_with_no_subdirectory = None, \
               to_create = None, campaign = None, 
               running_configuration = None, balises = {}, nx = None, ny = None, nz = None):

    global MY_MACHINE

    self.test_campaign = campaign 

    if code_dir:
      self.code_dir = os.path.abspath(code_dir)
      self.remote_code_dir = remote_code_dir
      self.source_to_test = source_to_test
      self.after_tar = after_tar
      self.source_dir  = "%s/Bench/Preparation/" % self.code_dir
      self.bench_preparation_dir = "%s/Bench/Preparation/%s/" % (self.code_dir,self.test_campaign)
      self.bench_result_dir = "%s/Bench/Results/%s/%s/" % (self.code_dir,self.test_campaign,MY_MACHINE)
    
      self.compile_dir = os.path.abspath(compile_dir)
      self.executable = executable
      self.starting_dir = starting_dir
      self.running_configuration = running_configuration
      self.to_copy = to_copy
      self.to_link = to_link
      self.to_copy_with_no_subdirectory = to_copy_with_no_subdirectory
      self.to_link_with_no_subdirectory = to_link_with_no_subdirectory
      self.to_create = to_create
      self.nx = nx
      self.ny = ny
      self.nz = nz
      self.balises = balises
    else:
      self.code_dir = None
      self.remote_code_dir = None
      self.source_to_test = None
      self.after_tar = None
      self.balises = balises

  #########################################################################
  # create
  #########################################################################

  def create(self):
      """ create the code"""
      global VERSION, CASE

      if not(VERSION) or not(CASE):
        usage("when creating a test, please state a case name and a version for the code")

      if os.path.exists("./Codes/%s/%s" % (CASE,VERSION)):
        if not(FORCE):
          usage("Test %s/%s already exists!... use --force to overwrite " % (CASE,VERSION),"Creation of a new test")
        else:
          user_message("forcing reinstallation of case %s/%s " % (CASE,VERSION))

      if not(self.code_dir):
        self.code_dir = "./Codes/%s/%s/" % (CASE,VERSION)
        
      create_cmd = " mkdir -p %s; cd %s; " % (self.code_dir, self.code_dir)  +\
                   " mkdir -p Bench/Preparation/Campaign1/run; " +\
                   " mkdir -p Bench/Results; "
      
      wrapped_system(create_cmd,"creation of %s/%s working directories" % (CASE,VERSION))

      info_file = "%s/%s" % (self.code_dir,"info.py")
      fic = open(info_file,"w")
      fic.write(INFO_FILE_TEMPLATE)
      fic.close()

      print "\n Test %s/%s created..." % (CASE,VERSION)
      

  #########################################################################
  # compilation
  #########################################################################

  def compile(self):
      """ compile the code"""
      global MY_MACHINE, CLEAN

      if str.find(self.compile_dir+"**",'No_Need**')>-1:
        user_message("","No need to compile")
        return
             

      if not(os.path.exists(self.compile_dir)):
        print "\tCompiling directory %s does not even exists!..." % self.compile_dir
        print "\t\t... dezipping sources"

      if not(self.source_to_test) or not(os.path.exists(self.source_to_test)):
        cmd = "cd %s/Src; tar xfz %s.tgz" % (self.code_dir,CASE.lower())
        user_message("","should untar source code")
        #wrapped_system(cmd,"Untarring source code")

        if self.after_tar:
          cmd = "cd %s/Src; %s " % (self.code_dir,self.after_tar)
          wrapped_system(cmd,"Performing some fixing after unzipping sources")
      else:
        user_message(None,"source seems to be already there!")

      # subtistuting any thing in the src file
      substitute("%s/Src" % self.code_dir,self.balises)

      makefile_name = "%s/Makefile.%s" % (self.compile_dir,MY_MACHINE)
      env_name = "%s/env.%s" % (self.compile_dir,MY_MACHINE)
      if not(os.path.exists(makefile_name)):
        message = "No makefile Makefile.%s available for %s in %s directory" % \
              (MY_MACHINE,MY_MACHINE,self.compile_dir)
        if FAKE or DRY:
          user_message(message,message)
        else:
          usage(message,  "at compiling step")
      else:
        env_sourcing = ""
        if os.path.exists(env_name):
          env_sourcing = "source %s; " % env_name
          user_message(msg_debug = "\nSourcing environment %s " % env_name)
        else:
          user_message(msg_debug = "\nSourcing environment %s file does not exist... " % env_name)

        compile_cmd = "cd %s; %s make -f Makefile.%s TARGET=%s " % (self.compile_dir,env_sourcing,MY_MACHINE,MY_MACHINE)
        if CLEAN:
          wrapped_system(compile_cmd + " clean" ,"Cleaning compiling directory...")
        #compile_cmd = compile_cmd + " > out 2>&1 ; cat out"
        else:  
          wrapped_system(compile_cmd,"Compiling...")

  #########################################################################
  # check if executable is there
  #########################################################################

  def check_for_executable(self):
    global NOCOMPILE,JUSTCOMPILED, CLEAN

    nb_balises = len(balises)
    if ("__ELLAPSED_TIME__" in self.balises.keys()):
      nb_balises = nb_balises - 1

    user_message("","Checking executable")

    if  str.find(self.executable+"**",'No_Need**')>-1:
      user_message("","No need to build executable")
      return False
    else:
      if CLEAN:
        print "\n\t\t Cleaning..."
        self.compile()
        return True
      # compiling the code if the executable does not exists yet
      executable = self.executable
      if not(os.path.exists(executable)):
        executable = self.code_dir+"/Src/"+self.executable
      if os.path.exists(executable):
        print "\t\tExecutable %s exists " % executable

      if not(os.path.exists(executable)) or (nb_balises>0 and not(NOCOMPILE) and not(JUSTCOMPILED)):
        print "\n\tExecutable needs to be (re)compiled for this test case "
        print "\n\t\t%s is missing or depends on parameter of the use case" % executable
        print "\t\tCompiling it..."
        self.compile()
        if CLEAN:
          return
        if not(os.path.exists(executable)):
          print "\n\t\tCompilation was not successfull... executable %s not found" % executable
          if not(FAKE) and not(DRY) :
            sys.exit(1)
          else:
            user_message("\t\t!!! Executable \n\t\t\t\t%s not produced, \n\t\t\t\t\t...ok with Fake or Dry-run mode" \
                         % (executable))
            return False
        JUSTCOMPILED = True
      elif (nb_balises>0):
        if not(JUSTCOMPILED):
          print "\n\tExecutable indeed exists yet for this test case ",
          print "but depends on parameter of the use case"
          print "\t\tstill I am not Compiling it at your demand...",
          print " I hope you know what you're doing!!!..."
    return True




  #########################################################################
  # copy, link file into the test directory, with or without
  # the subdirectory arborescence
  #########################################################################

  def duplicate_file_into_test_dir(self,files,as_link=False,with_full_dir_path=False):


    if as_link:
      action_doing = "linking" 
      action_done  = "linked"
    else:
      action_doing = "copying" 
      action_done  = "copied"

    user_message(msg_debug = "\nWorking on %s : \n\t\t%s \n\t\tFull path = %s " %\
                 (action_doing,str(files),with_full_dir_path))

    if files:
      if  str.find(self.compile_dir+"**",'No_Need**')>-1 and "__executable__" in files:
        files.remove("__executable__")

      for c in files:
        source = "%s/Src/%s" % (self.code_dir,c)
        if c=="__executable__":
          source = self.executable
          user_message(msg_debug = "\nReplacing __executable__ by  %s " % source )


        if not(os.path.exists(source)):
          source_from_repository = "%s/%s/%s/Src/%s" % (DATA_REPOSITORY,CASE,VERSION,c)
          if not(os.path.exists(source_from_repository)):
            usage(("One of the file/directory to be %s does not exist: "+\
                  "\n\t\t\t-?-> %s \n\t\t... even in the data repository: "+\
                  "\n\t\t\t-?-> %s") \
                  % (action_done,source,source_from_repository), \
                  "preparing stage")
          source = source_from_repository

            

        cmd = "cd %s/run ; " % self.bench_destination_dir
        dir2create = os.path.dirname(c)

        if os.path.isdir(source):
          user_message(msg_debug = "%s is a directory!" % source)
          c = c + "/"
          if with_full_dir_path:
            if len(dir2create):
              cmd = cmd + "mkdir -p %s; " % (dir2create)
              if as_link:
                cmd = cmd + " cd %s/; " % (source,dir2create)
              else:
                cmd = cmd + " cd %s/..; " % (source,dir2create)
            if as_link:
              cmd = cmd + " ln -s %s ." % (source)
            else:
              cmd = cmd + "  cp -r %s ." % (source)
          else:
            if as_link:
              cmd = cmd + " ln -s %s ." % (source)
            else:
              cmd = cmd + " cp -r %s ." % (source)
        else:
          user_message(msg_debug = "%s is a file!" % source)
          if with_full_dir_path:
            if len(dir2create):
              cmd = cmd + "mkdir -p %s; cd  %s; " % (dir2create,dir2create)
          if as_link:
            cmd = cmd + " ln -s %s ." % source
          else:
            cmd = cmd + " cp %s ." % source

          
        wrapped_system(cmd,"Files/Directories to be %s : " % action_done +c)





  #########################################################################
  # submit test
  #########################################################################

  def submit(self,nb_pe):

    global ELLAPSED_TIME, FORCE, DRY, SUBMIT, SCRATCH, SCRATCH_SUBST, NB_CORES, CASE, MY_MACHINE

    self.balises["__NPX__"] = self.nx
    self.balises["__NPY__"] = self.ny
    self.balises["__NPZ__"] = self.nz

    # checking or guessing number of procs requested to run the test case
    
    if not(nb_pe):
      if not(self.running_configuration):
        usage("Number of procs is missing... any is possible")
      if len(self.running_configuration)==1:
        nb_pe = int(self.running_configuration[0])
        print "\n\t\tDefaut number of procs taken: ", nb_pe
      else :
        print "\n\t\tPossible number of procs for the job : ", self.running_configuration
        usage("Number of procs is missing... pick one of those or use --force")

    if self.running_configuration:
      if not(nb_pe in self.running_configuration) and not(FORCE):
        print "\n\t\tPossible number of procs for the job : ", self.running_configuration
        usage("Number of procs is unacepted... pick one of those or use --force")

    self.check_for_executable()

    # creation of the directory where the test is expected to run
    print "\n\tPreparing all needed files to run the job..."
      
    now = time.strftime('%y%m%d-%H:%M:%S',time.localtime())
    self.bench_destination_dir = os.path.abspath(self.bench_result_dir)+"/%04d-" % nb_pe + now
    self.bench_destination_dir_scratch = self.bench_destination_dir.replace(SCRATCH_SUBST,SCRATCH)
    cmd = "mkdir -p %s; mkdir -p %s; " % \
              (self.bench_result_dir,\
               self.bench_destination_dir_scratch)
    if not (self.bench_destination_dir_scratch == self.bench_destination_dir):
      cmd  = cmd +  "ln -s %s %s" % \
               (self.bench_destination_dir_scratch,self.bench_destination_dir)

    wrapped_system(cmd,"Creating test directory")
    #os.mkdir(self.bench_destination_dir)

    # copy of the needed file translating all the template
        
    if nb_pe % NB_CORES == 0:
      partition_size = nb_pe/NB_CORES
    else:
      partition_size = nb_pe/NB_CORES + 1

    if not ("__ELLAPSED_TIME__" in self.balises.keys()):
      self.balises["__ELLAPSED_TIME__"] = ELLAPSED_TIME
    else:
      user_message("\tEllapsed time has been calculated from input parameters")
      

    self.balises["__PARTITION_SIZE__"] = partition_size
    try:
      nb_pe_new = nb_pe_needed(nb_pe)
      nb_pe = nb_pe_new
      user_message("","computing nb_be from info file")
    except:
      user_message("","keeping nb_be as is")
    self.balises["__PE__"] = nb_pe
    self.balises["__EXECUTABLE__"] = self.bench_destination_dir+"/run/"+self.executable

    self.balises["__STARTING_DIR__"] = self.bench_destination_dir+"/run/"+self.starting_dir
    
    cmd = "mkdir -p %s " % os.path.abspath(self.bench_destination_dir+"/run")

    wrapped_system(cmd,"preparing bench directory for %d procs " % nb_pe)


    # copying and linking directories and files to the test directory
    
    self.duplicate_file_into_test_dir(self.to_copy,as_link=False,with_full_dir_path=True)
    self.duplicate_file_into_test_dir(self.to_link,as_link=True,with_full_dir_path=True)

    self.duplicate_file_into_test_dir(self.to_copy_with_no_subdirectory,\
                                      as_link=False,with_full_dir_path=False)
    self.duplicate_file_into_test_dir(self.to_link_with_no_subdirectory,\
                                      as_link=True,with_full_dir_path=False)


    if self.to_create:
      for c in self.to_create:
        cmd = "cd %s; mkdir -p %s" \
                % (self.bench_destination_dir+"/run",c)

        wrapped_system(cmd,"Directories %s to be created" % c)


    # adding all what's in Bench/Preparation directory

    if os.path.exists(self.bench_preparation_dir):
      cmd = "cd %s; tar fc - -C %s . | tar xf - " \
            % (self.bench_destination_dir+"/run",self.bench_preparation_dir)

      wrapped_system(cmd,"\tmasking from Bench/Preparation directory")
    else:
      user_message("\tNo masking requested for the case %s/%s/%s" % (CASE,VERSION, CAMPAIGN))
      
    user_message("\tsubstituting template")
    job_file = substitute(self.bench_destination_dir,self.balises)


    if  str.find(self.compile_dir+"**",'No_Need**')==-1:
      dir_name = os.path.dirname(self.executable)
      if (self.check_for_executable()) :
        cmd = "cd %s; mkdir -p %s" \
              % (self.bench_destination_dir+"/run",\
                 dir_name)
        cmd = cmd + "; cp %s %s" \
              % (self.code_dir+"/Src/"+self.executable,self.executable)
        
        wrapped_system(cmd,"Copying executable in the bench directory")
      else:
          user_message("\t\t!!! Executable \n\t\t\t\t%s could not be copied in directory \n\t\t\t\t%s/%s \n\t\t\t\t as %s, \n\t\t\t\t\t...ok with Fake or Dry-run mode" \
                           % (self.executable,self.bench_destination_dir,dir_name,self.executable))



    if not(job_file):
      user_message("No job_file found in %s" % self.bench_destination_dir, action=ERROR)

    # creating job file, copying it in the launch directory, submitting job...
    
    launchDir = self.bench_destination_dir+"/run/"+self.starting_dir
    cp = ""
    if not(os.path.abspath("%s/%s" % (launchDir,os.path.basename(job_file)))==os.path.abspath(job_file)):
      cp = " cp %s .; " % (job_file)
    cmd = "cd %s/; %s  %s %s > llsubmit.out 2>&1  " % (launchDir,cp,SUBMIT,job_file)

    if DRY:
          print "\n\tdry run : not submitting the job "+job_file
    else:
      user_message("submitting job","submitting job "+job_file)

      wrapped_system(cmd,"submitting job")
    
      check_job = "".join(open("%s/llsubmit.out" % launchDir).readlines())
      if str.find(check_job,"has been submitted"):
        print "\t... job has been submitted!"
      else:
        print "\t... A problem occurred during job submission!"
        print check_job


    # creating a fast link
    cmd = "mkdir -p JOBS/; ln -s %s JOBS/%s-%s; \\rm -rf %s-%s-%s; ln -s JOBS/%s-%s %s-%s-%s; " % \
          (launchDir,CASE,os.path.basename(self.bench_destination_dir),\
           CASE,nb_pe,MY_MACHINE,\
           CASE,os.path.basename(self.bench_destination_dir),CASE,nb_pe,MY_MACHINE)
    if str.find(self.compile_dir+"**",'No_Need**')<0:
      cmd = cmd+ " mkdir -p %s-%s/compile; cp -r %s %s-%s/compile/" % \
            (CASE, os.path.basename(self.bench_destination_dir),\
            self.compile_dir,CASE,os.path.basename(self.bench_destination_dir))
    wrapped_system(cmd,"fast link created...")

  #########################################################################
  # list all available benchmarks
  #########################################################################

  def list(self,path="./Codes",level=0,timing=False):

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
        if level==0:
          path_new = path + "/" + d
          if not(CASE) or CASE==d:
            print "%s- %s " % ("\t\t"+"   "*(level),d)
            self.list(path_new,level+1,timing)
        elif level==1:
          if not(VERSION) or VERSION==d:
            info_file = "%s/%s/info.py" % (path,d)
            cmd = ""
            if (os.path.exists(info_file)):
              cmd  = "".join(open(info_file).readlines())
            
            print "%s- %-10s " % ("\t\t"+"   "*(level),d),

            running_configuration = ""
            executable = "None"
            if len(cmd):
              exec cmd

            if len(executable)==0:
              usage("Please provide executable value in file %s" % info_file,"in the setting of the test")

            executable_to_be_checked = "%s/%s/Src/%s" % (path,d,executable)
            if DEBUG:
              print "\tChecking executable : ", executable_to_be_checked
              
            if os.path.exists(executable_to_be_checked):
              print "\tCompiled", 
            else:
              print "\tnot Compiled",
            if len(cmd):
              print running_configuration
            else:
              print "<- missing file !%s!" % (info_file)

            path_new = path + "/%s/Bench/Results" % d
            self.list(path_new,level+1,timing)
        elif level==2:
          if not(CAMPAIGN) or CAMPAIGN==d:
            if not(d==".gitkeep"):
              print "%s- %s " % ("\t\t"+"   "*(level),d)
              path_new = path + "/" + d
              self.list(path_new,level+1,timing)
        elif level>=3 and (LIST=="all" or timing) :
          if not(DATE) or DATE==d:
            if not(d==".gitkeep") and level==3:
              print "%s- %s " % ("\t\t"+"   "*(level),d)
          if timing:
                path_new = path + "/" + d
                if d=="job.out":
                  timing_result = self.get_timing(path_new)
		  if timing_result>-1:
                    print "\t%10s s \t %s  " % ( timing_result, path_new)
                self.list(path_new,level+1,timing)


  def get_timing(self,path):
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
          
  def run(self):
    global PROCS, RUN, COMPILE, CREATE, TARGET, TARGET_ARGS, SYNC_ONLY, TIMING_RESULT

    if COMPILE:
      #self.compile()
      self.check_for_executable()
    elif CREATE:
      self.create()
    elif LIST or TIMING_RESULT:
      self.list(timing=TIMING_RESULT)
    elif RUN:
      for p in PROCS:
        self.submit(int(p))

    
if __name__ == "__main__":
    welcome_message()
    parse()
    

    if CREATE or LIST:
      t = Test()
      t.run()
      sys.exit(0)

    balises = {}
    rep = search_target(balises)
    if rep:
      (code_dir,remote_code_dir,\
       compile_dir,source_to_test,after_tar,executable,\
       starting_dir,to_copy,to_link,\
       to_copy_with_no_subdirectory,to_link_with_no_subdirectory,\
       to_create,campaign,running_configuration,nx,ny,nz) = rep

    if rep or (CASE=="NONE" and SYNC_ONLY):
      if TARGET:
        cmd= "\n scp ktf.py %s:%s/Test_cases/ " % (TARGET,TARGET_HOME) 
        if os.path.exists("./SOFTS") :
          cmd = cmd + \
                "\n rsync -av  SOFTS %s:%s/Test_cases/; " % (TARGET,TARGET_HOME)
        if os.path.exists("./DOC/%s" % TARGET) :
          cmd = cmd + \
                "\n rsync -av  DOC/%s %s:%s/Test_cases/DOC/; " % (TARGET,TARGET,TARGET_HOME)
        wrapped_system(cmd,"propagating last version of ktf.py")
        if rep:
          cmd = cmd + "\n ssh %s 'mkdir -p %s/Src; '; " % (TARGET,remote_code_dir) 
          if os.path.exists("./DATA/%s"  % CASE) :
            cmd = cmd + \
                  "\n rsync -av  DATA/%s %s:%s/Test_cases/DATA/; " % (CASE,TARGET,TARGET_HOME)
          user_message("Synchronizing %s/%s directory and running ktf.py remotely" % (CASE,VERSION))
          # print rep
          here = os.path.abspath(".")
          arb = code_dir.split("/")
          dest = "/".join(arb[:-1])
          cmd = cmd + \
                "\n rsync -av  %s %s:%s; " % (code_dir,TARGET,dest) 

        wrapped_system(cmd,"syncing target")
        if not SYNC_ONLY:
          cmd =   "\n ssh %s 'cd %s/Test_cases; python ktf.py %s --submit=%s'" % (TARGET,TARGET_HOME,TARGET_ARGS,SUBMIT)
          wrapped_system(cmd,"submitting job")
        sys.exit(0)

      t = Test(code_dir,remote_code_dir,compile_dir,source_to_test,after_tar,\
               executable,starting_dir,\
               to_copy,to_link,\
               to_copy_with_no_subdirectory,to_link_with_no_subdirectory,\
               to_create,campaign,running_configuration,\
               balises,nx,ny,nz)
      t.run()
      
