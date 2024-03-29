import argparse
import sys
import os
import time
import subprocess
import re
import copy
import shlex
import pickle
import datetime
import shutil
import pprint

from engine import engine
from env import *

ERROR = -1


class ktf(engine):

    def __init__(self):
        self.KTF_WORKSPACE_FILE = ".ktf.pickle"
        self.check_python_version()

        self.MATRIX_FILE_TEMPLATE = ""
        self.MACHINE, self.TMPDIR, cores_per_node = get_machine()

        self.KTF_JOB_ID = {}
        self.KTF_JOB_DIR = {}
        self.KTF_JOB_STATUS = {}
        self.KTF_JOB_STAMP = {}
        self.KTF_JOB_TIMINGS = {}
        self.ktf_timing_results = {}
        self.ktf_timing_results["procs"] = []
        self.ktf_timing_results["cases"] = []
        self.ktf_timing_results["runs"] = []
        self.ktf_list_of_experiments = {}
        self.ktf_list_of_experiments_tag = {}
        self.ktf_nb_of_experiments = 0
        self.ktf_results_of_experiments = {}
        self.ktf_results_of_experiments_index = {}
        self.CASE_LENGTH_MAX = 0

        if os.path.exists(self.KTF_WORKSPACE_FILE):
            self.load_workspace()
            #print(self.ktf_timing_results["runs"])
        letters = [ l for l in 'abcdefghijklmnopqrstuvxyzABCDEFGHIJKLMNOPQRSTUVXYZ0123456789' ]
        shortcuts = letters
        for l in letters[:10]:
            x = [ l+x for x in letters ]
            shortcuts = shortcuts + x

        self.shortcuts = shortcuts 


        self.NB_COLUMNS_MAX = 3
        
        engine.__init__(self, "ktf", "0.7")

        self.my_init()
        
        self.start()

    #########################################################################
    # usage ...
    #########################################################################

    def usage(self, message=None, error_detail="", exit=True):
        """ helping message"""
        if message:
            print("\n\tError %s:\n\t\t%s\n" % (error_detail, message))
            print("\ttype ktf -h for the list of available options...")
        else:
            print("\n  usage: \n \t python  run_tests.py \
               \n\t\t[ --help ] [ --init ] \
               \n\t\t[ --status ] \
               \n\t\t[ --launch | --build   [ --what=<filter on case>]   [ --case-file=[exp_file.ktf] ] \
               \n\t\t                       [ --nb=<number of expermiment>   ] \
               \n\t\t                       [ --times=number of repetition>  ] \
               \n\t\t                       [ --reservation=<reservation name] ]\
               \n\t\t[ --exp                [ --what=<filter on test>] [ --case-file=[exp_file.ktf] ] \
               \n\t\t                       [ --today | --now ] ] \
               \n\t\t[ --monitor [ --wide ] [ --when=<filter on date>] [ --what=<filter on test>] ] \
               \n\t\t[ --info ]             [ --info-level=[0|1|2]  ] \
               \n\t\t[ --debug ]            [ --debug-level=[0|1|2] ]   \
             \n")
        if exit:
            sys.exit(1)

    #########################################################################
    # check for tne option on the command line
    #########################################################################
    def initialize_parser(self):
        engine.initialize_parser(self)

        self.parser.add_argument("--init", action="store_true",
                                 help=self.activate_option('init','initialize a ktf environment with example directories'))
        self.parser.add_argument("-m", "--monitor", action="store_true",
                                 help=self.activate_option('monitor','list status of jobs and show experiment results'))
        self.parser.add_argument("-l", "--launch", action="store_true",
                                 help=self.activate_option('launch','launch experiments'))
        self.parser.add_argument("-b", "--build", action="store_true",
                                 help=self.activate_option('build','build experiments without launching them'))
        self.parser.add_argument("-s", "--status", action="store_true",
                                 help=self.activate_option('status','show current status of experiments'))
        self.parser.add_argument("--detail", action="store_true",
                                 help=self.activate_option('detail','show detailed output of experiments per campaign'))
        self.parser.add_argument("-f", "--force-update", action="store_true",
                                 help=self.activate_option('status','force update of results'))
        self.parser.add_argument("-e", "--exp", action="store_true",
                                 help=self.activate_option('exp','list all available experiments'))
        self.parser.add_argument("-w", "--wide", action="store_true",
                                 help=self.activate_option('wide','format results for a wide screen'))
        self.parser.add_argument("-C", "--compact", action="store_true",
                                 help=self.activate_option('wide','format results in a compact format'))

        self.parser.add_argument("-c", "--case-file", type=str, default= "./%s_cases.ktf" % self.MACHINE,
                                 help=self.activate_option('case-file','name of the case file'))
        self.parser.add_argument("-w", "--what", type=str, default="",
                                 help=self.activate_option('what','filter based on the experiment name'))
        self.parser.add_argument("-W", "--when", type=str, default="",
                                 help=self.activate_option('when','filter based on the experiment date'))
        self.parser.add_argument("--today", action="store_true",
                                 help=self.activate_option('today','show only experiment run today'))
        self.parser.add_argument("--now", action="store_true",
                                 help=self.activate_option('now','show only experiment run in the current hour time'))

        self.parser.add_argument("-r", "--reservation", type=str,
                                 help=self.activate_option('reservation','run experiments under a reservation'))
        self.parser.add_argument("-p", "--partition", type=str,
                                 help=self.activate_option('partition','run experiments on this partition'))
        self.parser.add_argument("-a", "--account", type=str,
                                 help=self.activate_option('account','run experiments under this account'))

        self.parser.add_argument("-x", "--times", type=int, default=1,
                                 help=self.activate_option('times','run experiments several times'))
        self.parser.add_argument("-n", "--nb", type=int, default=0,
                                 help=self.activate_option('nb','select experiment # nb only'))

        self.parser.add_argument("--fake", action="store_true",
                                 help=self.activate_option('fake','do not run any call'))
        self.parser.add_argument("-y","--yes", action="store_true",
                                 help=self.activate_option('yes','responds yes to every filtering question'))

        self.parser.add_argument("-np", "--no-pending", action="store_true",
                             help=argparse.SUPPRESS)
        self.parser.add_argument("--create-template", action="store_true",
                             help=argparse.SUPPRESS)
        self.parser.add_argument("--dry", action="store_true",
                             help=argparse.SUPPRESS)
        self.parser.add_argument("--mail-verbosity", action="store_true",
                             help=argparse.SUPPRESS)
        self.parser.add_argument("-nfu", "--no-fix-unconsistent", action="store_true",
                             help=argparse.SUPPRESS)


    #########################################################################
    # starting the dance
    #########################################################################

    def start(self):
        
        self.log_debug('[KTF:start] entering', 4, trace='CALL')
        engine.start(self)
        self.set_variable_from_parsing()
        engine.run(self)
        self.ktf_start()

    #########################################################################
    # set variable from parsing command line
    #########################################################################
    
    def set_variable_from_parsing(self):
        
        self.WHAT = self.args.what
        self.NB = int(self.args.nb)
        self.TIMES = int(self.args.times)
        self.WHEN = self.args.when
        self.EXP = self.args.exp
        self.MONITOR = self.args.monitor
        self.RESERVATION = self.args.reservation
        self.LAUNCH = self.args.launch
        self.BUILD = self.LAUNCH or self.args.build
        self.STATUS = self.args.status
        self.FAKE = self.args.fake
        self.ALREADY_ACKNKOWLEDGE = self.args.yes
        self.FORCE_UPDATE = self.args.force_update
        self.DETAIL = self.args.detail
        
        if self.args.today:
            self.WHEN = datetime.datetime.now().strftime("%y%m%d-")
        if self.args.now:
                self.WHEN = datetime.datetime.now().strftime("%y%m%d-%H")
        if self.args.case_file:
            self.TEST_FILE = self.args.case_file
        if self.args.wide:
                self.NB_COLUMNS_MAX = 9

        filter = "//--%s--//--%s--//" % (self.WHEN,self.WHAT)
        # print(self.KTF_JOB_TIMINGS)
        key = "--filter--"
        if not(key in self.KTF_JOB_TIMINGS.keys()):
               self.KTF_JOB_TIMINGS["--filter--"]=filter
               self.FORCE_UPDATE = True
               print("forcing update")
        elif not(self.KTF_JOB_TIMINGS["--filter--"]==filter):
               self.KTF_JOB_TIMINGS["--filter--"]==filter
               self.FORCE_UPDATE = True
               print("forcing update")
            
        # self.KTF_JOB_TIMINGS[path]

    #########################################################################
    # main work
    #########################################################################
    
    def ktf_start(self):
        if self.args.init:
            self.create_ktf_init()
            sys.exit(0)
            
        if self.LAUNCH and self.MONITOR:
            self.usage("--monitor and --launch can not be asked simultaneously")

        if self.BUILD and self.MONITOR:
            self.usage("--monitor and --build can not be asked simultaneously")

        if not(self.BUILD) and not(self.MONITOR) and not(self.LAUNCH) and not(self.STATUS) and not(self.EXP):
            self.usage(
                "at least --exp, --build, --launch, --status, or --monitor should be asked")

        if self.STATUS:
            self.get_ktf_status()
        elif self.MONITOR:
            self.list_jobs_and_get_time()
            self.save_workspace()
        else:
            self.ALREADY_ACKNKOWLEDGE = False
            for nb_experiment in range(self.TIMES):
                self.ktf_run()
                if self.EXP:
                    self.list_experiments()
                if self.TIMES > 1:
                    time.sleep(1)
    
    #########################################################################
    # save_workspace
    #########################################################################

    def save_workspace(self):

        #print("saving variables to file "+workspace_file)
        workspace_file = self.KTF_WORKSPACE_FILE
        f_workspace = open(workspace_file+".new", "wb")
        pickle.dump(self.KTF_JOB_ID, f_workspace)
        pickle.dump(self.KTF_JOB_STATUS, f_workspace)
        pickle.dump(self.ktf_timing_results, f_workspace)
        pickle.dump(self.KTF_JOB_STAMP, f_workspace)
        pickle.dump(self.KTF_JOB_TIMINGS, f_workspace)
        f_workspace.close()
        if os.path.exists(workspace_file):
            os.rename(workspace_file, workspace_file+".old")
        os.rename(workspace_file+".new", workspace_file)

    #########################################################################
    # load_workspace
    #########################################################################

    def load_workspace(self):

        #print("loading variables from file "+workspace_file)

        f_workspace = open(self.KTF_WORKSPACE_FILE, "rb")
        self.KTF_JOB_ID = pickle.load(f_workspace)
        self.KTF_JOB_STATUS = pickle.load(f_workspace)
        self.ktf_timing_results = pickle.load(f_workspace)
        self.KTF_JOB_STAMP = pickle.load(f_workspace)
        self.KTF_JOB_TIMINGS = pickle.load(f_workspace)
        f_workspace.close()

        # self.log_debug('self.KTF_JOB_ID :' + pprint.pformat(self.KTF_JOB_ID), 2, trace='workspace')
        for job_dir in self.KTF_JOB_ID.keys():
            job_id = self.KTF_JOB_ID[job_dir]
            self.KTF_JOB_DIR[job_id] = job_dir


    #########################################################################
    # send a message to the user
    #########################################################################

    def user_message(self, msg=None, msg_debug=None, action=None):

        if action == ERROR:
            prefix = "Error: "
        else:
            prefix = ""

        br = ""

        if msg_debug:
            self.log_debug(msg_debug)
        else:
            if msg:
                self.log_info(msg)

        if action == ERROR:
            sys.exit(1)

    #########################################################################
    # substitute the template file
    #########################################################################

    def substitute(self, directory, balises):

        job_file = None

        self.user_message(msg_debug="\nsubstituting in "+directory)
        self.user_message(msg_debug="\n\tbalises  = %s\n " % str(balises))

        for root, dirs, files in os.walk(directory):
            self.log_debug("dirs="+" ".join(dirs), 3, trace="TEMPLATE")
            self.log_debug("files="+" ".join(files), 3, trace="TEMPLATE")

            for name in files:
                if ".template" in name and os.path.exists(os.path.join(root, name)):

                    self.log_debug("\t\tsubstituting " +
                                   os.path.join(root, name))
                    fic = open(os.path.join(root, name))
                    t = "__NEWLINE__".join(fic.readlines())
                    fic.close()

                    for b in balises.keys():
                        t = t.replace("__"+b+"__", "%s" % balises[b])

                    name_saved = name.replace(".template", "")
                    fic = open(os.path.join(root, name_saved), "w")
                    fic.write(t.replace("__NEWLINE__", ""))
                    fic.close()

                    if name_saved == "job.%s" % self.MACHINE:
                        job_file = os.path.join(root, name_saved)

    #         for name in dirs:
    #             job_file_candidate = self.substitute(os.path.join(root, name),balises)
    #             if (job_file_candidate):
    #                 job_file = job_file_candidate

        return job_file

    #########################################################################
    # filter with respect to comma separated field
    #########################################################################

    def filtered(self,s,filters):

        for f in filters.split(","):
            if s.find(f)==-1:
                self.log_debug("not found %s in %s" % (f,s),3,trace="FILTER")
                return False
        self.log_debug("found all of %s in %s" % (f,s),3,trace="FILTER")
        return True

    #########################################################################
    # get status of all jobs ever launched
    #########################################################################

    def get_current_jobs_status(self):

        status_error = False

        DIRS = self.KTF_JOB_DIR
        IDS = self.KTF_JOB_ID

        DIRS_CANDIDATES_UNFILTERED = find_files('.', 'job.submit.out')
        self.log_debug('DIRS_CANDIDATES_UNFILTERED:' + pprint.pformat(DIRS_CANDIDATES_UNFILTERED), 1, trace='STATUS')
        DIRS_CANDIDATES = []
        for d in DIRS_CANDIDATES_UNFILTERED:
            if self.filtered(d,self.WHAT) and self.filtered(d,self.WHEN):
                DIRS_CANDIDATES = DIRS_CANDIDATES + [d]
        self.log_debug('DIRS_CANDIDATES:' + pprint.pformat(DIRS_CANDIDATES), 1, trace='STATUS,SCAN')

        if not(len(DIRS_CANDIDATES) == len(IDS)):
            self.log_info(
                'Oops some status jobs are missing... let me try to reconstruct them...')
            self.log_debug('%s dirs and %s jobs to scan ' %
                           (len(DIRS), len(IDS)), 3 , trace="STATUS")
            self.log_debug('%s dirs possibles... vs %s dirs in the box' % (
                len(DIRS_CANDIDATES), len(DIRS)), 3 , trace="STATUS")
            for f in DIRS_CANDIDATES:
                l = open(f, 'r').readline()[:-1]
                job_id = l.split(" ")[-1]
                self.log_debug('j=/%s/ for %s ; l= >>%s<< ' %
                               (job_id, f, l), 1)
                d = os.path.abspath(os.path.dirname(f))
                self.log_debug("DIRS: " + pprint.pformat(DIRS),3,trace='STATUS')
                if not(d in DIRS.keys()):
                    self.log_debug(
                        'adding j=/%s/ for %s ; l= >>%s<< ' % (job_id, d, l), 3 , trace="STATUS")
                    if len(job_id):
                        self.KTF_JOB_DIR[job_id] = d
                        self.KTF_JOB_ID[d] = job_id
                        self.KTF_JOB_STATUS[job_id] = self.KTF_JOB_STATUS[d] = 'NOINFO'
                    else:
                        self.KTF_JOB_ID[d] = -1
                        self.KTF_JOB_STATUS[d] = 'REJECTED'

        jobs_to_check = list()

        for j in DIRS.keys():
            if not(self.filtered("%s"%j,self.WHAT)):
                next
            status = self.job_status(j)
            self.log_debug('status : /%s/ for job %s from dir >>%s<<' %
                           (status, j, DIRS[j]), 1, trace="STATUS")
            if status in ("CANCELLED", "COMPLETED", "FAILED", "TIMEOUT", 'NODE_FAIL', 'BOOT_FAIL', 'SPECIAL_EXIT', 'REJECTED'):
                self.log_debug('--> not updating status' , 1, trace="STATUS")
            else:
                jobs_to_check.append(j)
        if len(jobs_to_check) == 0:
            return

        cmd = ["sacct", "-j", ",".join(jobs_to_check)]
        self.log_debug('cmd so get new status : ///%s///' % " ".join(cmd), 1, trace="STATUS")
        try:
            output = subprocess.check_output(cmd)
            output = output.decode('utf-8')
        except:
            if self.args.debug > 0:
                self.dump_exception(
                    '[get_current_job_status] subprocess with ' + " ".join(cmd))
            else:
                status_error = True
            output = ""
        self.log_debug("output:" + pprint.pformat(output), 2, trace="CMD")
        for l in output.split("\n"):
            try:
                p = re.compile("\s+")
                l = p.sub(' ', l[:-1])
                self.log_debug('l=/%s/' % l)
                j = l.split(" ")[0].split(".")[0]
                fields = l.split(" ")
                if len(fields) > 2:
                    status = fields[-2]
                    if status in ('PENDING', 'RUNNING', 'SUSPENDED', 'COMPLETED', 'CANCELLED', 'CANCELLED+', 'FAILED', 'TIMEOUT',
                                  'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL', 'COMPLETING', 'CONFIGURING', 'RESIZING', 'SPECIAL_EXIT'):
                        self.log_debug("status: %s /  j : %s " % (status,j), 3, "STATUS")
                        if status[-1] == '+':
                            status = status[:-1]
                        self.KTF_JOB_STATUS[j] = self.KTF_JOB_STATUS[DIRS[j]] = status
            except:
                if self.args.debug > 0:
                    self.dump_exception(
                        '[get_current_job_status] parse job_status \n\t with j=/%s/ \n\t with job_status=/%s/ ' % (j, l))
                else:
                    status_error = True
                pass
        self.save_workspace()

        if status_error:
            self.log_info(
                '[get_current_job_status] !WARNING! Error encountered scanning job status, run with --debug to know more', 1)

    #########################################################################
    # get current job status
    #########################################################################
    def job_status(self, id_or_file):

        self.log_debug("[job_status] job_status on %s " % id_or_file, 1)
        if id_or_file == -1:
            return 'REJECTED'

        dirname = "xxx"
        if os.path.isfile(id_or_file):
            dirname = os.path.abspath(os.path.dirname(id_or_file))
        if os.path.isdir(id_or_file):
            dirname = os.path.abspath(id_or_file)

        for key in [id_or_file, dirname]:
            if key in self.KTF_JOB_STATUS.keys():
                status = self.KTF_JOB_STATUS[key]
                self.log_debug("[job_status] job_status on %s --> %s" %
                               (id_or_file, status), 1)
                return status
        self.log_debug(
            "[job_status] job_status on %s --> UNKNOWN" % id_or_file)
        return "NOINFO"

    #########################################################################
    # scan all available job.out
    #########################################################################

    def scan_jobs_and_get_time(self, path=".", level=0, timing=False,
                               dir_already_printed={}):

        self.log_debug("[list_jobs_and_get_time] Benchmarks Availables: ", 2)
        self.log_debug(
            "[list_jobs_and_get_time] scanning %s for timings=%s" % (path, timing), 2)

        if not(os.path.exists(path)):
            return

        if not(os.path.isdir(path)):
            return

        if self.WHEN and not(path == '.'):
            if not(self.filtered(path,self.WHEN)):
                self.log_debug(
                    'rejecting path >>%s<< because of filter applied' % path, 2, trace="FILTER")
                return

        dirs = sorted(os.listdir(path))

        if len(dirs):
            # if level == SCANNING_FROM :
            #  print("%s%d %s Availables: " % ("\t"*(level+1),len(dirs),ArboNames[level]))
            if self.args.debug > 0 > 3:
                print(level, dirs)
            for d in ["job.submit.out"]:
                if os.path.exists(path + "/" + d):
                    if os.path.isfile(path + "/" + d):
                        self.log_debug("[list_jobs_and_get_time] candidate : %s " % (
                                path+"/"+"job.submit.out"), 3, trace="SCAN")
                        # formatting the dirname
                        p = re.match(r"(.*tests_.*_......-.._.._..)/.*", path)
                        if p:
                            dir_match = p.group(1)
                            self.log_debug('dir_match:>>%s<<' % dir_match,  3, trace="SCAN")
    #           else:
    #             dir_match = "??? (%s)" % path

                        path_new = path + "/" + d

                        if self.WHEN and not(self.filtered(path_new,self.WHEN)):
                            continue
                        
                        
                        timing_result = self.get_timing(path)

                        if not(dir_match in dir_already_printed.keys()):
                            self.log_debug("%s- %s " % ("\t"+"   "*(level), dir_match), 3, trace="SCAN")
                        dir_already_printed[dir_match] = False
                        case_match = path_new.replace(dir_match+"/", "")
                        case_match = case_match.replace("/job.submit.out", "")
                        case_match = case_match.replace("32k", "32768")
                        case_match = case_match.replace("16k", "16384")
                        case_match = case_match.replace("8k", "8192")
                        case_match = case_match.replace("4k", "4096")
                        case_match = case_match.replace("2k", "2048")
                        case_match = case_match.replace("1k", "1024")
                        p = re.match(r".*_(\d+).*", case_match)
                        if p:
                            proc_match = p.group(1)
                        else:
                            p = re.match(r"(\d+).*$", case_match)
                            if p:
                                proc_match = p.group(1)
                            else:
                                proc_match = "0"
                        k = "%s.%s.%s" % (dir_match, proc_match, case_match)

                        if not(k in self.ktf_timing_results.keys()):
                            self.ktf_timing_results[k] = []
                        if not(dir_match in self.ktf_timing_results["runs"]):
                            self.ktf_timing_results["runs"].append(dir_match)
                        if not(proc_match in self.ktf_timing_results["procs"]):
                            self.ktf_timing_results["procs"].append(proc_match)
                        if not(case_match in self.ktf_timing_results["cases"]):
                            self.ktf_timing_results["cases"].append(case_match)
                            self.CASE_LENGTH_MAX = max(
                                self.CASE_LENGTH_MAX, len(case_match))

                        self.ktf_timing_results[k] = timing_result
                        self.log_debug("\t\t%10s s \t %5s %40s " % (timing_result, proc_match, case_match), 3, trace="SCAN")
                        if self.args.debug==0:
                            print(".",end='')
                            sys.stdout.flush()

                for d in dirs:
                    if not(d in ["R", ".git", "src"]):
                        path_new = path + "/" + d
                        if os.path.isdir(path_new):
                            if self.WHEN:
                                if not(self.filtered(path_new,self.WHEN)):
                                    self.log_debug(
                                        'rejecting path >>%s<< because of filter applied' % path_new, 2, trace="FILTER")
                                    next
                                else:
                                    self.log_debug(
                                        'accepting path >>%s<< because of filter applied' % path_new, 1, trace="FILTER")
                            self.scan_jobs_and_get_time(
                                path_new, level+1, timing, dir_already_printed)
        self.log_debug(
            "[list_jobs_and_get_time] end of scanning %s for timings=%s" % (path, timing), 2, trace="SCAN")

    #########################################################################
    # display ellapsed time and preparing the linked directory
    #########################################################################

    def get_ktf_status(self, path=".", level=0, timing=False,
                       dir_already_printed={}):

        self.get_current_jobs_status()
        self.scan_jobs_and_get_time(path, level, timing, dir_already_printed)

        print('\n%s experiments availables : ' % len(
            self.ktf_timing_results["runs"]))
        chunks = splitList(self.ktf_timing_results["runs"], 5)
        for runs in chunks:
            for run in runs:
                print("%12s" % run[-15:],end='')
            print

        print('\n%s tests availables : ' % len(self.ktf_timing_results["cases"]))
        chunks = splitList(self.ktf_timing_results["cases"], 5)
        for cases in chunks:
            for case in cases:
                print("%12s" % case,end='')
            print

    #########################################################################
    # display ellapsed time and preparing the linked directory
    #########################################################################

    def list_jobs_and_get_time(self, path=".", level=0, timing=False,
                               dir_already_printed={}):

        self.results_initialize()
        OUTPUT_DUMPED = ""

        status_error_links = False

        self.get_current_jobs_status()

        self.scan_jobs_and_get_time(path, level, timing, dir_already_printed)

        if os.path.exists('R'):
            shutil.rmtree('R')
        os.mkdir('R')

        nb_tests = 0
        total_time = {}
        blank = ""
        self.ktf_timing_results["procs"].sort(key=int)
        #print(self.ktf_timing_results["procs"])

        chunks = splitList(
            self.ktf_timing_results["runs"], self.NB_COLUMNS_MAX, only=self.WHEN)

        format_run = ("%%%ss" % self.CASE_LENGTH_MAX)
        line_sep = '-' * (4+self.NB_COLUMNS_MAX * 20 + self.CASE_LENGTH_MAX*2)

        print
        self.log_debug(line_sep,4,trace="OUTPUT")

        nb_column = 0

        for runs in chunks:

            self.output_initialize()

            blank = " " * 20 * (self.NB_COLUMNS_MAX - len(runs))

            self.log_debug('runs=[%s], nb_column=%s' %
                           (",".join(runs), nb_column), 2, trace="TIME")
            nb_column_start = nb_column
            nb_line = 0

            header = format_run % "Runs"
            self.output_add_field("Runs")
            
            for run in runs:
                header = header + " %19s" % run[-15:]
                self.output_add_field(run[-15:])
            header = header + '%s  # tests / Runs' % blank
            self.output_add_field("# tests / Runs")
            self.output_add_newline()

            cases = splitList(
                self.ktf_timing_results["cases"], 1000, only=self.WHAT)

            if len(cases) == 0:
                continue

            
            self.log_debug(header,4,trace="OUTPUT")
            
            for case in cases[0]:
                nb_line += 1
                for proc in self.ktf_timing_results["procs"]:
                    k0 = "%s.%s" % (proc, case)
                    nb_runs = 0
                    for run in runs:
                        k = "%s.%s.%s" % (run, proc, case)
                        if k in self.ktf_timing_results.keys():
                            nb_runs += 1
                    if nb_runs:
                        nb_column = nb_column_start
                        s = format_run % self.my_format_output(case,"case")
                        self.output_add_field(s)
                        non_null_run = False
                        for run in runs:
                            nb_column += 1
                            k = "%s.%s.%s" % (run, proc, case)
                            if k in self.ktf_timing_results.keys():
                                t = self.ktf_timing_results[k]
                                if  len(t)>0 and str(t).find("None")==-1 and str(t).find("NO RESULTS")==-1:
                                    non_null_run = True
                                #print(case,nb_line-1,(self.shortcuts[nb_column-1],self.shortcuts[nb_line-1]))
                                nb_possible_shortcuts = len(self.shortcuts)
                                if nb_column <= nb_possible_shortcuts:
                                    s1 = self.shortcuts[nb_column-1]
                                else:
                                    s1 = self.shortcuts[(nb_column-1) / nb_possible_shortcuts - 1] + \
                                        self.shortcuts[(nb_column-1) %
                                                       nb_possible_shortcuts]
                                if nb_line <= nb_possible_shortcuts:
                                    s2 = self.shortcuts[nb_line-1]
                                else:
                                    s2 = self.shortcuts[(nb_line-1) / nb_possible_shortcuts - 1] +\
                                        self.shortcuts[(nb_line-1) %
                                                       nb_possible_shortcuts]
                                shortcut = "%s,%s" % (s1, s2)
                                path = run+"/"+case
                                if not(os.path.exists(path)):
                                    path = path + " "
                                    path = path.replace("32768 ", "32k")
                                    path = path.replace("16384 ", "16k")
                                    path = path.replace("8192 ", "8k")
                                    path = path.replace("4096 ", "4k")
                                    path = path.replace("2048 ", "2k")
                                    path = path.replace("1024 ", "1k")
                                try:
                                    os.symlink("."+path, "R/%s" % shortcut)
                                except:
                                    self.log_debug(
                                        '\nZZZZZZZZZZZ symbolic link failed for ' + "ln -s ."+path + " R/%s" % shortcut,
                                        1, trace="TIME"  )
                                    status_error_links = True
                                try:
                                    value = " %13s %4s" % (t, shortcut)
                                    s = s + value
                                    self.output_add_field(value)
                                except:
                                    print('range error ', nb_line-1, nb_column-1)
                                    sys.exit(1)
                                #print("%9s" % (t),end='')
                                nb_tests = nb_tests + 1
                                if not(run in total_time.keys()):
                                    total_time[run] = 0
                                try:
                                    time_of_run = float(t.split("/")[0])
                                    if time_of_run > 0:
                                            total_time[run] += time_of_run
                                except:
                                    self.log_debug('unreadable run time for run %s : %s' % (k,t), 3, trace="TIMER")
                                    pass
                            else:
                                s = s + "%12s       " % "-"
                                self.output_add_field("-")
                                
                        test_summary = "%s / %3s" % (self.my_format_output(case,"case"),nb_runs)
                        s = s + test_summary
                        self.output_add_field(test_summary)
                        if non_null_run or not(self.args.compact):
                            self.log_debug(s,4,trace="OUTPUT")
                            
                        self.output_add_newline()
                        
            s = format_run % "total time"
            self.output_add_field("total time")
            for run in runs:
                if not(run in total_time.keys()):
                    total_time[run] = 0
                s = s + " %18s " % total_time[run]
                self.output_add_field("%18s" % total_time[run])
            s = s + "%s%3s" % (blank, nb_tests) + ' tests in total'
            self.output_add_newline()
            self.output_add_field("%s%3s" % (blank, nb_tests) + ' tests in total')
            self.log_debug(s,4,trace="OUTPUT")
            self.output_add_newline()
            
            self.log_debug(line_sep,4,trace="OUTPUT")
            self.log_debug(
                'at the end of the runs chunk nb_column=%s' % (nb_column), 2, trace="TIME")

            OUTPUT_DUMPED = OUTPUT_DUMPED + self.output_dump(no_print=True)
                

        if not(len(self.all_results_columns)) or self.DETAIL:
            print(OUTPUT_DUMPED)
            
        if len(self.all_results_columns):
            self.results_dump()
            self.results_json()                

                
        if status_error_links:
            self.log_info(
                '!WARNING! Error encountered setting symbolic links in R/ directory, run with --debug to know more', 1)


    #########################################################################
    # output management
    #########################################################################

    def output_initialize(self):
        self.output = {}
        self.output_current_line = self.output_current_column = 0
        self.output_column_max_width = {}
        for i in range(1000):
            self.output_column_max_width[i] = -1
        self.output_column_max = -1
        
    def output_add_field(self,s):
        self.output[self.output_current_line,self.output_current_column] = s
        self.output_column_max_width[self.output_current_column] = max(self.output_column_max_width[self.output_current_column], len(str(s)))
        self.output_column_max = max(self.output_column_max, self.output_current_column)
        self.output_current_column += 1
    
    def output_add_newline(self):
        self.output_current_column = 0
        self.output_current_line += 1

    def output_dump(self,no_print=False):

        format = {}
        total_line_length = 0
        output = ""
        for column in range(self.output_column_max):
            column_width = self.output_column_max_width[column]
            format[column] = "|%%%ds " % column_width
            total_line_length += column_width+2
        total_line_length += 1
        sep = "-" * total_line_length
        output = output + sep+"\n"
        
        for line in range(self.output_current_line):
            if line==1 or line==(self.output_current_line-1):
                output = output + sep + "\n"
            for column in range(self.output_column_max):
                try:
                    output = output + format[column] % self.output[line,column]
                except:
                    output = output + format[column] % "??(%s,%s)" % (line,column) + " "
            output = output + "|\n"
        output = output + sep + "\n"
        if not(no_print):
            print("")
            print(output)
        return output


    def results_initialize(self):
        self.all_results = {}
        self.all_results_columns = {}
        self.all_results_lines = {}

    def results_add(self, line, column, value):
        # print(line,column,self.WHAT,self.WHEN)
        # print(line.find(self.WHEN),column.find(self.WHEN))
        if not(self.filtered(line,self.WHAT)) and not(self.filtered(column,self.WHAT)):
            return
        self.all_results_lines[line] = 1
        self.all_results_columns[column] = 1
        self.all_results[line,column] = value

    def results_dump(self):
        self.output_initialize()
        self.output_add_field(" ")
        self.test_per_column = {}
        for c in self.all_results_columns:
            self.output_add_field(c)
            self.test_per_column[c] = 0
        self.output_add_newline()
        self.all_results_lines_keys = [ l for l in self.all_results_lines]
        self.all_results_lines_keys.sort()
        for l in self.all_results_lines_keys:
            self.output_add_field(l)
            for c in self.all_results_columns:
                try:
                    v = self.all_results[l,c]
                    self.test_per_column[c] += 1
                except:
                    v = "-  "
                self.output_add_field(v)
                

            self.output_add_field("xx")
            self.output_add_newline()

        self.output_add_field("%d tests" % sum([self.test_per_column[c] for c in self.all_results_columns]))
        for c in self.all_results_columns:
            self.output_add_field(self.test_per_column[c])
            
        self.output_add_newline()
        self.output_dump()

    def results_json(self):
        output = "[\n"
        self.all_results_lines_keys = [ l for l in self.all_results_lines]
        self.all_results_lines_keys.sort()
        for l in self.all_results_lines_keys:
            if len(output)>2:
                output = output + ",\n"
            output = output + "  {\n"
            output = output + \
                    """      "exp": "%s",\n""" % (l)
            
            for c in self.all_results_columns:
                try:
                    v = self.all_results[l,c]
                except:
                    v = "-  "
                output = output + \
                    """      "%s": "%s",\n""" % (c,v)
            output = output + "}"
        output = output + "]\n"
        output = output.replace(",\n}","\n  }")

        f = open("out.json","w")
        f.write(output)
                            
    #########################################################################
    # calculation of ellapsed time based on values dumped in job.out
    #########################################################################

    def get_timing(self, path):

        # 1) checking if job is still running
        status = self.job_status(path)
        if status in ("PENDING"):
            return status

        if not(os.path.exists(path+"/job.out")):
            # sk print('NotYet for %s' % path+'/job.out')
            self.log_debug("No job.out found for %s" % path,2,trace='TIMER')
            return "None/"+status  # [:2]

        job_out = path + "/job.out"
        job_out_size = os.path.getsize(job_out) # size in bytes
        job_out_ctime = os.path.getmtime(job_out) # time of last metadata change; it's a bit OS specific.
        self.log_debug("job_out_ctime=%s job_out_size=%s" % \
                       (job_out_ctime, job_out_size), 2, trace='STAMP')

        job_err_size = job_err_ctime = 0
        if os.path.exists(path+"/job.err"):
            if os.path.getsize(path+"/job.err") > 0:
                job_err = path + "/job.err"
                job_err_size = os.path.getsize(job_err) # size in bytes
                job_err_ctime = os.path.getmtime(job_err) # time of last metadata change; it's a bit OS specific.
                self.log_debug("job_err_ctime=%s job_err_size=%s" % \
                       (job_err_ctime, job_err_size), 2, trace='STAMP')
                status = status+"!"
            else:
                status = status+" "
                # return *Error*/+status# [:2]

        global_stamp = "job.out-%s-%s:job.err-%s-%s" % (job_out_size,job_out_ctime,job_err_size,job_err_ctime)
        if path in self.KTF_JOB_STAMP.keys():
          if not(self.FORCE_UPDATE) and global_stamp == self.KTF_JOB_STAMP[path]:
              self.log_debug("returning already saved value for path=%s" % path, 2, trace="STAMP")
              return self.KTF_JOB_TIMINGS[path]
        self.KTF_JOB_STAMP[path] = global_stamp

        fic = open(path+"/job.out")
        t = "__NEWLINE__".join(fic.readlines())
        fic.close()
        p = re.compile("\s+")
        t = p.sub(' ', t)
        p = re.compile("\s*__NEWLINE__\s*")
        t = p.sub('__NEWLINE__', t)

        try:
            start_timing = t.split("======== start ==============")
            self.log_debug("start_timing %s" % start_timing, 3)
            if len(start_timing) < 2:
                return self.my_timing_and_save(path,"NOST",status)
            from_date = start_timing[1].replace(
                "__NEWLINE__", "").replace("\n", "").split(" ")
            (from_month, from_day, from_time) = (
                from_date[1], from_date[2], from_date[3])
            (from_hour, from_minute, from_second) = from_time.split(":")

            end_timing = t.split("======== end ==============")
            if len(end_timing) < 2:
                if status == "RUNNING":
                    now = datetime.datetime.now()
                else:
                    now = datetime.datetime.fromtimestamp(
                        os.path.getmtime(path+"/job.out"))
                ellapsed_time = ((int(now.day)*24.+int(now.hour))*60+int(now.minute))*60+int(now.second) \
                    - (((int(from_day)*24.+int(from_hour)) *
                        60+int(from_minute))*60+int(from_second))
                return self.my_timing_and_save(path,"!%d" % ellapsed_time, status)

            from_date = to_date = "None"

            if len(start_timing) > 1 and len(end_timing) > 1:
                try:
                    to_date = end_timing[1].replace(
                        "__NEWLINE__", "").replace("\n", "").split(" ")
                    (to_month, to_day, to_time) = (
                        to_date[1], to_date[2], to_date[3])
                except:
                    self.dump_exception(
                        "[get_timing] Exception type 2 on time read: >>%s<< " % to_date)
                    ellapsed_time = 'ERROR_2'

                self.log_debug("[get_time] from_time=!%s! start_timing=!%s! from_date = %s" % (
                    from_time, start_timing[1], from_date), 3, trace="SCAN")
                self.log_debug("[get_time]   to_time=!%s!   end_timing=!%s! to_date = %s" % (
                    to_time, end_timing[1], to_date), 3, trace="SCAN")

                (to_hour, to_minute, to_second) = to_time.split(":")
                ellapsed_time = ((int(to_day)*24.+int(to_hour))*60+int(to_minute))*60+int(to_second) \
                    - (((int(from_day)*24.+int(from_hour)) *
                        60+int(from_minute))*60+int(from_second))
                self.log_debug("from_date = %s, to_date=%s, (%s/%s/%s)  to (%s/%s/%s)" %
                               (from_date, to_date, from_month, from_day,from_time, to_month, to_day, to_time), 3, trace="SCAN")
            else:
                self.log_debug("[get_timing] Exception type 1")
                if self.args.debug > 1:
                    except_print()
                ellapsed_time = "NOGOOD"
        except:
            self.dump_exception("[get_timing] Exception type 2  ")
            ellapsed_time = 'ERROR_2'
        # if isinstance(ellapsed_time, basestring):
        #     return ellapsed_time
        return self.my_timing_and_save(path, ellapsed_time, status)

    #########################################################################
    # user defined routine to be overloaded to define user's own timing
    #########################################################################

    def my_init(self):
        return

    def my_timing_and_save(self, path, ellapsed_time, status):
        my_timing = self.my_timing(path, ellapsed_time, status)
        self.KTF_JOB_TIMINGS[path] = my_timing
        return my_timing

    def my_timing(self, dir, ellapsed_time, status):
        self.log_debug(dir,3)
        return ellapsed_time

    def my_format_output(self,value,what):
        return value

    #########################################################################
    # clean a line from the output
    #########################################################################

    def clean_line(self, line):
        self.log_debug("[clean_line] analyzing line !!"+line+"!!",2,trace="PARSE")
        # replace any multiple blanks by one only
        p = re.compile("\s+")
        line = p.sub(' ', line[:-1])
        # get rid of blanks at the end of the line
        p = re.compile("\s+$")
        line = p.sub('', line)
        # get rid of blanks at the beginning of the line
        p = re.compile("^\s+")
        line = p.sub('', line)
        # line is clean!
        self.log_debug("[clean_line] analyzing  line cleaned !!"+line+"!!",2,trace="PARSE")
        return line

    def additional_tag(self, line):
        matchObj = re.match(r'^#KTF\s*(\S+|_)\s*=\s*(.*)\s*$', line)
        if (matchObj):
            # line=line[4:].replace("=2
            # yes! saving it in direct_tag and go to next line
            (t, v) = (matchObj.group(1), matchObj.group(2))
            self.log_debug("[additional_tag] direct tag definitition : " + line, 2, trace="PARSE")
            self.direct_tag[t] = v
            return True
        return False

    #########################################################################
    # generation of the jobs and submission of them if --build
    #########################################################################

    def ktf_run(self):

        test_matrix_filename = self.TEST_FILE
        now = time.strftime('%y%m%d-%H_%M_%S', time.localtime())

        if not(os.path.exists(test_matrix_filename)):
            print("\n\t ERROR : missing test matrix file >>%s<< for machine %s " % (
                test_matrix_filename, self.MACHINE))
            print("\n\t         ktf --init  can be called to create the templates")
            print("\t\tor\n\t         ktf --case-file=<exp ktf file> can be called to read the cases from another file")
            if self.EXP:
                tags_ok = False
                mandatory_fields = ["Case", "Experiment"]

                lines = ['']
            else:
                sys.exit(1)
        else:

            print

            tags_ok = False
            mandatory_fields = ["Case", "Experiment"]

            lines = open(test_matrix_filename).readlines()

        # warning message is sent to the user if filter is applied on the jobs to run

        if len(self.WHAT) or self.NB:
            if not(self.ALREADY_ACKNKOWLEDGE) and not(self.WHAT == ' '):
                self.log_info(
                    "the filter %s will be applied... Only following lines will be taken into account : " % (self.WHAT))
            if self.NB:
                self.log_info("only case %s will be taken " % self.NB)

            self.direct_tag = {}
            nb_case = 1

            for line in lines:
                line = self.clean_line(line)
                if self.additional_tag(line):
                    continue
                if len(line) > 0 and not (line[0] == '#'):
                    if not(tags_ok):
                        tags_ok = True
                        continue
                    for k in self.direct_tag.keys():
                        line = line+" "+self.direct_tag[k]
                    self.log_debug("[run] " + line,2,trace="PARAMS")
                    matchObj = re.match("^.*"+self.WHAT+".*$", line)
                    # prints all the tests that will be selected
                    if (matchObj) and not(self.ALREADY_ACKNKOWLEDGE):
                        if nb_case == 1:
                            for k in self.direct_tag.keys():
                                print("%6s" % k,end='')
                            print()

                        if not(self.NB) or self.NB == nb_case:
                            print("%3d: " % (nb_case),end='')
                            for k in line.split(" "):
                                print("%6s " % k[:20],end='')
                            print()
                        nb_case = nb_case + 1

            # if --exp exiting here
            if self.EXP:
                sys.exit(0)
            # askine to the user if he is ok or not
            if not(self.ALREADY_ACKNKOWLEDGE):
                input_var = input("Is this correct ? (yes/no) ")
                if not(input_var == "yes"):
                    print("ABORTING: No clear confirmation... giving up!")
                    sys.exit(1)
                self.ALREADY_ACKNKOWLEDGE = True

            tags_ok = False

        # direct_tag contains the tags set through #KTF tag = value
        # it needs to be evaluated on the fly to apply right tag value at a given job
        self.direct_tag = {}

        nb_case = 1
        # parsing of the input file starts...
        for line in lines:
            line = self.clean_line(line)
            # is it a tag enforced by #KTF directive?
            if self.additional_tag(line):
                continue

            # if line void or starting with '#', go to the next line
            if len(line) == 0 or (line[0] == '#'):
                continue

            # parsing other line than #KTF directive
            if not(tags_ok):
                # first line ever -> Containaing tag names
                tags_names = line.split(" ")
                tags_ok = True
                continue

            line2scan = line
            for k in self.direct_tag.keys():
                line2scan = line2scan+" "+self.direct_tag[k]
            # if job case are filtered, apply it, jumping to next line if filter not match
            matchObj = re.match("^.*"+self.WHAT+".*$", line2scan)
            nb_case = nb_case+1
            if not(matchObj):
                continue

            if self.NB and not(self.NB == nb_case-1):
                continue

            self.log_debug("[run] line " + line,2,trace="PARAMS")
            self.log_debug("[run] tags_names" + pprint.pformat(tags_names),2,trace="PARAMS")

            #tags = line.split(" ")
            tags = shlex.split(line)

            if not(len(tags) == len(tags_names)):
                print("\tError : pb encountered in reading the test matrix file : %s" % test_matrix_filename,end='')
                print("at  line \n\t\t!%s!" % line)
                print("\t\tless parameters to read than expected... Those expected are")
                print("\t\t\t", tags_names)
                print("\t\tand so far, we read")
                print("\t\t\t", tag)
                sys.exit(1)

            ts = copy.deepcopy(tags_names)
            tag = {}
            self.log_debug("[run] ts " + pprint.pformat(ts),3,trace="PARAMS")
            self.log_debug("[run] tag" + pprint.pformat(tag),3,trace="PARAMS")

            while(len(ts)):
                t = ts.pop(0)
                tag["%s" % t] = tags.pop(0)
                self.log_debug("[run] tag %s : !%s! " % (t, tag["%s" % t]), 3,trace="PARAMS")
            self.log_debug("[run] tag" + pprint.pformat(tag),3,trace="PARAMS")

            # adding the tags enforced by a #KTF directive
            tag.update(self.direct_tag)
            self.log_debug("[run] direct_tag" + pprint.pformat(self.direct_tag),3,trace="PARAMS")
            self.log_debug("[run] tag after update" + pprint.pformat(tag),3,trace="PARAMS")

            # checking if mandatory tags are there
            for c in mandatory_fields:
                if not(c in tag.keys()):
                    print("\n\t ERROR : missing column /%s/ in test matrix file %s for machine %s" % \
                        (c, test_matrix_filename, self.MACHINE))
                    sys.exit(1)

            # all tags are valued at this time
            # creating the job directory indexed by time

            dest_directory = "tests_%s_%s/%s/%s" % (
                self.MACHINE, now, tag['Experiment'], tag["Case"])
            cmd = ""

            if "Submit" in tag.keys():
                submit_command = tag["Submit"]
            else:
                submit_command = self.SUBMIT_COMMAND

            if self.RESERVATION:
                submit_command = submit_command + ' --reservation=%s' % self.RESERVATION

            root_directory = os.getcwd()
            cmd = cmd + \
                "mkdir -p %s\n cd %s \n tar fc - -C %s/tests/%s . | tar xvf - > /dev/null " % \
                (dest_directory, dest_directory,
                 root_directory, tag["Experiment"])

            if "Arch" in tag.keys():
                arch  = tag["Arch"]
            else:
                arch = "unkown"

            # copying contents of the tests/common and tests/<Experiment>/common directory into the directory where the job will take place
            for d in ['tests/common', 'tests/%s/../common' % tag["Experiment"], 'tests/common_%s' % arch, 'tests/%s/../common_%s' % (tag["Experiment"],arch)]:
                common_dir = '%s/%s' % (root_directory, d)
                if os.path.exists(common_dir):
                    cmd = cmd + \
                        "\ntar fc - -C %s . | tar xvf - > /dev/null  " % (
                            common_dir)

            # linking contents of the tests/common_links and tests/<Experiment>/common_links directory into the directory where the job will take place
            for d in ['tests/common_links', 'tests/%s/../common_links' % tag["Experiment"], 'tests/common_%s_links' % arch, 'tests/%s/../common_%s_links' % (tag["Experiment"],arch)]:
                common_dir = '%s/%s' % (root_directory, d)
                if os.path.exists(common_dir):
                    cmd = cmd + \
                        "\nln -s  %s/* .  " % (common_dir)

            comment = "\tcreating test directory %s for %s and populating it from %s : " % (
                dest_directory, self.MACHINE, common_dir)
            self.log_debug(comment, 3, trace='PROCESS')


            tag["STARTING_DIR"] = "."
            if self.EXP:
                self.add_experiment_to_list(tag)
            if self.LAUNCH or self.BUILD:    
                self.system(cmd, comment=comment)
                job_file = self.substitute(dest_directory, tag) 

                if job_file:
                    cmd = "cd %s; %s %s > job.submit.out 2> job.submit.err " % \
                        (os.path.dirname(job_file), submit_command,
                        os.path.basename(job_file))
                    if self.LAUNCH:
                        print("\tsubmitting job %s " % job_file)
                        self.system(
                            cmd, comment="submitting job %s" % job_file)
                        output_file = "%s/job.submit.out" % os.path.dirname(
                            job_file)
                        error_file = "%s/job.submit.err" % os.path.dirname(
                            job_file)
                        if os.path.exists(error_file):
                            if os.path.getsize(error_file) > 0:
                                print("\n\tError... something went wrong when submitting job %s " % job_file)
                                print("\n           here's the error file just after submission : \n\t\t%s\n" % error_file)
                                print("\t\tERR> " + \
                                    "ERR> \t\t".join(
                                        open(error_file, "r").readlines()))
                                print("           here's the submission command: \n\t\t%s\n" % cmd)
                                job_script_content = open(
                                    job_file, 'r').readlines()
                                print("\n           here's the job_script        : ")
                                for chunk in splitList(job_script_content, 12):
                                    print("".join(chunk)[:-1])
                                    input_var = input(
                                        " [ hit only return to continue or any other input to stop]")
                                    if not(input_var == ""):
                                        print("...")
                                        break
                                sys.exit(1)
                        f = open(output_file, "r").readline()[:-1].split(" ")[-1]
                        self.KTF_JOB_ID[os.path.abspath(os.path.dirname(job_file))] = f
                        self.log_debug("[run] job_id" + f,3,trace="PARAMS")

                    else:
                        print("\tshould launch job %s (if --launch added) " % job_file)
                    #print(cmd
                else:
                    print("\t\tWarning... no job file found for machine %s in test directory %s " % \
                        (self.MACHINE, dest_directory))
                print
                self.save_workspace()


    #########################################################################
    # helper function
    #########################################################################

    def add_experiment_to_list(self,tag):
        self.log_debug("tag : " + pprint.pformat(tag), 3, trace="EXP")
        self.ktf_list_of_experiments[self.ktf_nb_of_experiments] = {}
        for (k,v) in tag.items():
            self.ktf_list_of_experiments_tag[k] = True
            self.ktf_list_of_experiments[self.ktf_nb_of_experiments][k] = v
        self.ktf_nb_of_experiments = self.ktf_nb_of_experiments +1

    def list_experiments(self):
        for t in self.ktf_list_of_experiments_tag.keys():
            print("%15s" % t, end="" )
        print()
        for i in range(self.ktf_nb_of_experiments):
            for t in self.ktf_list_of_experiments_tag.keys():
                print("%15s" % self.ktf_list_of_experiments[i][t], end="" )
            print()
        print()

    #########################################################################
    # os.system wrapped to enable Trace if needed
    #########################################################################

    def create_ktf_init(self):

        path = os.getenv('KTF_PATH')
        if not(path):
            path = '.'
        for dirpath, dirs, files in os.walk("%s/templates" % path):
            for filename in files:
                filename_from = os.path.join(dirpath, filename)
                filename_to = filename_from.replace(
                    "%s/templates/" % path, "./")
                if os.path.exists(filename_to):
                    self.log_info(
                        "\t file %s already exists... skipping it!" % filename_to)
                else:
                    dirname = os.path.dirname(filename_to)
                    self.log_debug('working on file %s in dir %s' %
                                   (filename_to, dirname))

                    if not(os.path.exists(dirname)):
                        self.system(
                            "mkdir -p %s" % dirname, comment="creating dir %s" % dirname)
                    self.system("cp %s %s" % (
                        filename_from, filename_to), comment="creating file %s" % filename_to)
                    self.log_info('creating file %s' % (filename_to))


if __name__ == "__main__":
    K = ktf()

    K.save_workspace()
