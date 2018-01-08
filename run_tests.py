#!/sw/xc40/python/2.7.9/cnl5.2_gnu4.9.3/bin/python
#
# Copyright (c) 2016 Contributors as noted in the AUTHORS file
#
# This file is part of KTF.

#  KTF is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  KTF is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.

#  You should have received a copy of the GNU Lesser General Public License
#  along with KTF.  If not, see <http://www.gnu.org/licenses/>.

from ktf import *
import glob
from env import *
import math

class my_ktf(ktf):

  def __init__(self):
    ktf.__init__(self)



  def my_timing(self,dir,ellapsed_time,status):
    return "%s/%s" % (ellapsed_time,status)
 
    files = glob.glob(dir+'/job.out')
    self.log_debug("dir===>%s<==,status=/%s/,len(files)=/%s/" % (dir,status,len(files)))
    for filename in files:
      try:
        res = greps("Total Time"   ,filename,-2)
        self.log_debug('res=%s'% res)
        Total_time        = int(float(res[0])*100.)/100. 
        self.log_debug("Total Time: %s" % (Total_time))
        return "%s/%s" % (Total_time,status)
      except:
        self.dump_exception('user_defined_timing in dir %s' % dir) 
        return "PB/"+status
    return "!%s/%s" % (ellapsed_time,status)
      
 

if __name__ == "__main__":
    my_ktf()
