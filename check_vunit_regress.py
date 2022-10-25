#!/usr/bin/env python3

#  **********************************************************************
#  **********************************************************************
#  *********  Copyright (c) 2017-2022 Metrics Technologies Inc, *********
#  *********  All rights reserved.                              *********
#  *********                                                    *********
#  *********  Use, disclosure, or distribution is prohibited    *********
#  *********  without prior written permission.                 *********
#  **********************************************************************
#  **********************************************************************

# -*- coding: utf-8 -*-
#import logging
#logger = logging.getLogger(__name__)


#import random
#from random import Random
import string
import sys
import os
from os.path import exists
import shutil
from shutil import copyfile
import glob

envVars = os.environ
if "PYTHONPATH" not in envVars:
    if "DSIM_REGRESS" not in envVars:
        print("Error:  DSIM_REGRESS not set.  Exiting.")
        sys.exit(-1)

    sys.path.append(envVars.get("DSIM_REGRESS") + "/lib/python")
    
from metrics.basics import *

sys.path.append("./metrics_lib")
from monitor import *

#######################################################
##                   main
def main(argv):
    """  Run vunit examples
    
    This script checks that the tests that were expected to
      run are run, and returns the status.
      
      -v will enable a verbose log file output, copy dsim
         output into the vunit_check.output file.
    
    """
    ##  only flag  so is hard coded.
    verbose = 0
    if len(argv) > 0 and argv[0] == "-v":
        verbose = 1
        #print("Verbose")
    # setup some default strings
    MapFile = "test_name_to_path_mapping.txt"
    OutPath = "test_output/"
    OFile = "output.txt"
    PassMSG = "=N:[VhdlStop]"
    
    # Open checker output log file.
    lh = open ("vunit_check.log", "w")
        
    #  now open the test listed to be run
    if exists("tests_to_run.txt"):
        fh = open("tests_to_run.txt", "r")
        rlst = fh.readlines()
        fh.close()
    else:
        print("No tests list file was found under 'tests_to_run.txt'\n")
        print("All tests found are listed in file 'test_found_list.txt'\n")
        return 1
    
    ##  go through the tests 
    failures = 0
    missing = 0
    for t in rlst:
        if t[0] == "#":
            continue
        t = t.strip()
        
        out_dir = "./" + t + "/vunit_out/"
        if not exists(out_dir):
            missing += 1
            lh.write(">>>>  ERROR: Expected output directory was not found\n    " + out_dir)
            lh.write("\n")
            lh.write("***************************************************************************\n")
            print("Expected output: " + out_dir + " Was not found\n")
            continue
        
        #  map file  Map tests to  random naming
        mfile = out_dir + OutPath + MapFile
        #  if now mapping file  continue
        if not exists(mfile):
            print("No Name Mapping File found in " + mfile)
            continue
        
        # all seems good,  check the files for passing message.
        mf = open(mfile , "r")
        mlst = mf.readlines()
        for m in mlst:
            sm = m.split()
            
            dtn = out_dir + OutPath + sm[0] + "/" + OFile
            
            with open(dtn, "r") as file:
                txt = file.read()
                if not PassMSG in txt:
                    lh.write(">>>>  Test Failed: " + m + "\n")
                    if verbose:
                        lh.write(txt)
                        lh.write("\n")
                        lh.write("***************************************************************************\n")
                    
                    failures += 1
    
    print("Failures: " + str(failures) + "\nMissing: " + str(missing))
    return (failures, missing)
    
if __name__ == '__main__':
    stat = main(sys.argv[1:])
    do_exit(stat)

















