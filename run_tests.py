from ktf import *
import glob

class my_ktf(ktf):

  def __init__(self):
    ktf.__init__(self)
    
  def user_defined_timing(self,dir,ellapsed_time):
    if DEBUG or True:
      print dir
    for f in glob.glob('*/results*log'):
      print f
    return ellapsed_time

if __name__ == "__main__":
    K = my_ktf()
    K.welcome_message()
    K.parse()
    if K.TIME:
      K.list_jobs_and_get_time()
    else:
      K.run()
      
