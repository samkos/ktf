#!/sw/xc40cle7/python/3.8.0/sles15_gnu8.3.0/bin/python
from ktf import *
import glob
from env import *
import math

class my_ktf(ktf):

  def __init__(self):
    ktf.__init__(self)


  def my_timing(self,dir,ellapsed_time,status):
    self.log_debug("received  dir : %s, ellapsed_time : %s, status : %s" % (dir,ellapsed_time, status), 3, trace='MYT')
    # default behavior
    try:
      ellapsed_time = int(ellapsed_time)
    except:
      pass
      
    if status.find('COMPLETED')<0:
      return "%s/%s" % (ellapsed_time,status)
    # file to scan
    file_to_greps = glob.glob("%s/rsl.out.0000" % dir) + glob.glob("%s/attempt/*/rsl.out.0000" % dir)
    # file_to_greps = glob.glob("%s/attempt/*/rsl.out.0000" % dir)
    
    self.log_debug("file_to_greps in %s : %s" % (dir,",".join(file_to_greps)), 3, trace='MYT')
    # the file does not exists
    if len(file_to_greps)==0:
       return "!%s/%s" % (ellapsed_time,status)
        
    # or .... greping result in a file
    try:
      Total_time_mains  = []
      Total_time_main_avgs = []
      Total_time_writings = []
      for file_to_grep in file_to_greps:
        res_main = greps("Timing for main",file_to_grep,-3)
        Total_time_main        = int(sum([float(r) for r in res_main])) #*1000.)/1000.
        Total_time_main_avg    = sum([float(r) for r in res_main])/len(res_main)
        self.log_debug("Total Time main: %s" % (Total_time_main))
        res_writing = greps("Timing for Writing",file_to_grep,-3)
        Total_time_writing     = int(sum([float(r) for r in res_writing]) - float(res_writing[0]) - float(res_writing[1])) #*1000.)/1000. 
        self.log_debug("Total Time Writing: %s" % (Total_time_writing ))
        Total_time_main_avgs = Total_time_main_avgs + [ "%4.2f" % Total_time_main_avg ]
        
      return "%s/%s" % (ellapsed_time,"/".join(Total_time_main_avgs))
      return "%s/%s/%s" % (ellapsed_time,Total_time_main,Total_time_writing)
    except:
      self.dump_exception('user_defined_timing in dir %s' % dir)
      # file exists but no Total Time is printed
      return "NO_TIME/"+status

if __name__ == "__main__":
    my_ktf()
