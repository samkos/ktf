NAME
       KTF - KSL Test Framework

SYNOPSIS
       KTF [ command-line switches ] [ filter(s) ]

DESCRIPTION
       KTF  stands for 'KSL (Kaust Supercomputing Lab)  Testing Framework'. It was designed and used to help in the construction
       and runs of benchmark campaign during the procurement on Shaheen II in 2014 and made available to all KSL users  in  June
       2016.

       KTF  eases  the  scripting,  execution and monitoring of several jobs depending on a set of parameters whose all possible
       combination are gathered in a centralized text file called casefile

   KTF Commands
       -h, --help
               Display all the available KTF options available from the command line.

       --init  Initialize the KTF environment, copying example case and template files into the current directory

       --exp   List every possible test cases described in the case file.

       --launch
               Build and launch all the test cases described in the case file.

       --build Only build all the test cases to be launched and save them in a new test_<machine>20yymmdd-hh_mm_ss but does  not
               actually submit them to the machine. Option to be used to check wich jobs will be launched.

       --monitor
               monitors  the  status  of  the  jobs previously submitted and displays the obtained results gathered in a kind of
               dashboard that can easely be filtered and configured to the need of the user.

       --status
               lists the number of experiences, and dates of tests already made or ongoing that were launched from  the  current
               directory. These information can be used in filter --what or --when.

   KTF Options
       --case-file=file.ktf
              reads the  cases from the file given as argument instead of reading the default case file: <machine>_cases.ktf

       --times=number-of-times
              launches the selected cases several times.

   KTF Filters
       --nb=case-number
              selects only the case numbered case-number when listing all of them with ktf --exp command.

       --what=<pattern>
              selects the only cases from the test cases file that match this patterns.

       --when=<pattern>
              selects the only cases from the tests already launched whose date matches this patterns.

       --today
              selects the only cases from the tests launched on the current day

       --now  selects the only cases from the tests launched on the current hour

   Debugging Flags
       KTF  returns  a  zero  exist  status  if  it  succeeds to change to set the maximum speed of the cdrom drive. Non zero is
       returned in case of failure.

AUTHOR
       Written by Samuel Kortas (samuel.kortas (at) kaust.edu.sa)

REPORTING BUGS
       Report KTF bugs to help@hpc.kaust.edu.sa
       KTF home page: <https://bitbucket.org/kaust_KSL/ktf>
       KAUST Supercomputing Laboratory: <http://hpc.kaust.edu.sa/>

COPYRIGHT
       Copyright  (C)  2016-2021 KAUST   Supercomputing   Laboratory   License   GPLv3+:   GNU   GPL   version   3   or   later
       <http://gnu.org/licenses/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.

SEE ALSO
       A  comprehensive  presentation  of KTF has been given by Samuel Kortas during the KSL Workshop entitled 'Boost your effi-
       ciency when dealing with multiple jobs on the Cray XC40 supercomputer Shaheen II' held at KAUST On Sunday June 5th  2016.
       The   workshop   slides   can  be  freely  downloaded  from  <https://www.hpc.kaust.edu.sa/sites/default/files/files/pub-
       lic/many_jobs.pdf>

 
