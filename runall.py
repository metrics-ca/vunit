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

###################################
# Builds the sub-script's command for VHDL remote run
class commandRemoteVUNIT:
    def __init__(self, tname, numb = 0):
        self.status = NOT_STARTED
        self.pid = ""
        self.testNum = numb
        self.testName = tname
        self.cmd = "mux-farm bash -c 'python3 ./run.py" + "'"
        self.monitorCmd = "mux-status "
        self.time = 0
        self.indx = numb

#######################################################
##                   main
def main(argv):
    """  Run vunit examples
    
    This script assumes that the environment is set up.
      -  correct dsim version
      -  vunit environment
      The tests to run are in file named "tests_to_run.txt"
    
    """
    
    ##  find all the run.py files from here down.
    sflist = glob.glob('**/run.py', recursive=True)
    #  write out tests found
    fh = open("test_found_list.txt", "w")
    for s in sflist:
        #print(str(s))
        fh.write(s.rsplit("/",1)[0] + "\n")
    fh.close()
    
    #  now open the test listed to be run
    if exists("tests_to_run.txt"):
        fh = open("tests_to_run.txt", "r")
        rlst = fh.readlines()
        fh.close()
    else:
        print("No tests list file was found under 'tests_to_run.txt'\n")
        print("All tests found are listed in file 'test_found_list.txt'\n")
        return 1
    
    class_tlst = []
    # create classes of  test cases.
    for i in rlst:
        if i[0] == "#":
            continue
        # find index to sub in output dir name
        vupath = i.strip() + "/vunit_out"
        #print("vpath: " + vupath)
        # remove output if exists
        if exists(vupath):
            print("Removing previous: " + vupath)
            shutil.rmtree(vupath)
        class_tlst.append(commandRemoteVUNIT(i))
    
    #  open a log file for messages out.
    lh = open ("tests_run.log", "w")
    lh.write("-------------------------------------------\n")
    lh.write("Test run starting\n")
    lh.write("-------------------------------------------\n")
        
    here = os.getcwd()
    #print("We are here: " + here)
    for t in class_tlst:
        ##  metrics lib  function for regressions.
        lh.write("Sending: " + t.testName)
        cmd_list = shlex.split(t.cmd)
        for i in cmd_list:
            lh.write(i + "\n")
            
        
        os.chdir("./" + t.testName.rstrip("\n"))
        there = os.getcwd()
        #print("We are there: " + there)
        result = subprocess.run(cmd_list, timeout=TIMEOUT, check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        output = result.stdout.decode('utf-8')
        lh.write(output)
        t.pid = output.rstrip("\n")
        t.monitorCmd = t.monitorCmd + t.pid
        t.status = RUNNING
        t.time = 0
        os.chdir(here)
    
    #  attach monitor of  mux jobs
    #monitor(class_tlst, True, True)
    monitor(class_tlst)
    
    #  close log file.
    lh.close()
    
    return 0
    
if __name__ == '__main__':
    main(sys.argv[1:])






    ## pull in global variables that are modified here.
    #global dbg_lvl, gen_seed, rstr, rbit
    
    #pseed = 0
    #bdir = ""
    #gen_size = 0
    ## number of passed params
    #alen = int(len(argv) / 2)
    ## go through them
    #idx = 0
    #for i in range(alen):
    #    op = (argv[idx])
    #    idx = idx+1
    #    val = (argv[idx])
    #    print("Op: " + str(op) + "  Value: " + str(val))
    #    if op == "-h":
    #        print('mxgen.py -s "seed" -d "base directory"')
    #        sys.exit(2)
    #    elif op == "-s":
    #       print("Found pseed ...")
    #       pseed = val
    #    elif op == "-z":
    #       gen_size = int(val)
    #    elif op == "-v":
    #       dbg_lvl = val
    #    elif op == "-d":
    #       bdir = val
    #    else:
    #        print('mxgen.py -s "seed" -d "base directory" -z "regresion size" -v "Verbosity 0-2"')
    #        sys.exit(2)
    #        
    #   idx = idx+1
    #    #print(argv[i])
