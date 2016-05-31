
from ktf import *
import glob
from env import *
import math

class my_ktf(ktf):

  def __init__(self):
    ktf.__init__(self)



  def my_timing(self,dir,ellapsed_time,status):
    if status[0]=='!':
      status  = status[1:]
    return "!%s/%s" % (ellapsed_time,status)
 
    files = glob.glob(dir+'/job.out')
    self.log_debug("dir===>%s<==,status=/%s/,len(files)=/%s/" % (dir,status,len(files)))
    for filename in files:
      try:
        res = greps("Total Time"   ,filename,-2)
        self.log_debug('res=%s'% res)
        Total_time        = int(float(res[0])*100.)/100. 
        self.log_debug("Total Time: %s" % (Total_time))
        #return "%s/%s" % (int(float(res[1])),int(float(res2[1]))) #,int(float(res3[1])
        return "%s/%s" % (Total_time,status)
      
      except:
        self.dump_exception('user_defined_timing')
        job_out = "___".join(open(dir+'/job.out').readlines())
        if job_out.find("CANCELLED")>-1:
          return "CANCELLED/"+status
        if self.DEBUG:
          print "pb on ",filename
        return "PB/"+status
 

if __name__ == "__main__":
    my_ktf()
