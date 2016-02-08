from ktf import *


class my_ktf(ktf):
  pass

if __name__ == "__main__":
    K = my_ktf()
    K.welcome_message()
    K.parse()
    if K.TIME:
      K.list_jobs_and_get_time()
    else:
      K.run()
      
