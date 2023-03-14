#!/usr/bin/env python3


#  ***************************************************************************
#  ***************************************************************************
#  *********  Copyright (c) 2017-2022 Metrics Design Automation Inc, *********
#  *********  All rights reserved.                                   *********
#  *********                                                         *********
#  *********  The following source code contains confidential and    *********
#  *********  proprietary information of, and is solely owned by,    *********
#  *********  Metrics Design Automation Inc.                         *********
#  *********                                                         *********
#  *********  Use, copy, disclosure, or distribution is prohibited   *********
#  *********  without prior written permission.                      *********
#  ***************************************************************************

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
from metrics.txt_colors import *
from metrics.monitor import *

#######
##   set the dsim options
if "DSIM_CMD_OPTIONS" in envVars:
    os.environ['DSIM_CMD_OPTIONS'] = envVars.get("DSIM_CMD_OPTIONS") + " -timescale 1ns/1ps"
else:
    os.environ['DSIM_CMD_OPTIONS'] = " -timescale 1ns/1ps"

# Constants
VERSION = "1.1.0"
SUCCESS = 0


# Globals set during argument processing
debug = False
useColor = False
verbose = False
doClean = False
email = ""

# Key paths
reportDir = "" # Directory to which we will write the report
startDir = "" # Directory from which the scripts was invoked
rootDir = "" # Root of the VUNIT repo

doit = True # Set to False if you don't want the script to actually execute

###################################
# Prints a usage line with the set of possible options
def print_usage(retVal):
    print("usage: {}".format(os.path.basename(sys.argv[0])), end=" ")
    print("{--help}", end=" ")
    print("{--version}", end=" ")
    print("{--verbose}", end=" ")
    print("{--color}", end=" ")
    print("{--email=<name>}", end=" ")
    print("")
    do_exit(retVal, debug)

###################################
# Help output
def print_help():
    myexe = os.path.basename(sys.argv[0])

    print_color("NAME", False, Bold, White, BG_Black)
    print("    {}".format(myexe))
    print_color("\nSYNOPSIS", False, Bold, White, BG_Black)
    print("    {} [OPTIONS]".format(myexe))
    print_color("\nDESCRIPTION", False, Bold, White, BG_Black)
    print("    This script will run all of the VUNIT tests")
    print_color("\nOPTIONS", False, Bold, White, BG_Black)
    print("    -h, --help")
    print("        Display's this help information")
    print("    -v, --version")
    print("        Print out the version of this tool")
    print("    -V, --verbose")
    print("        Print out each test as it is executed")
    print("    -C, --color")
    print("        Enable color output")
    print("    --email=<name>")
    print("        If the results need to be emailed to someone, please provide the email name")
    print("        The results will be emailed to <name>@metrics.ca")
    print("        The default is to not email the results")
    print_color("\nCOPYRIGHT", False, Bold, White, BG_Black)
    copyright = get_copyright()
    print("    {}".format(copyright))


###################################
# Checks to see if the user accidentally had the same arg on the command line twice
# or had two or more incompatible arguments on the command line
def check_for_dup_arg(comp):
    if comp:
        print_usage(-1)
    return True

###################################
# Process command line arguments
def process_args():
    global debug
    global verbose
    global useColor
    global doClean
    global email

    foundEmail = False

    try:
        opts, testDirs = getopt.getopt(sys.argv[1:], "hCvVd",
                                                     ["help",
                                                      "color",
                                                      "version",
                                                      "verbose",
                                                      "email=",
                                                      "debug"])
    except getopt.GetoptError as err:
        print_err(str(err))
        print_usage(-2)

    for o, a in opts:
        if o in ("-h", "--help"):
            print_help()
            do_exit(SUCCESS, debug)
        if o in ("-v", "--version"):
            print_key_info("Version: {}".format(VERSION),"",False)
            do_exit(SUCCESS, debug)
        elif o in ("-V", "--verbose"):
            verbose = check_for_dup_arg(verbose)
        elif o in ("-d", "--debug"):
            debug = check_for_dup_arg(debug)
        elif o in ("-C", "--color"):
            useColor = check_for_dup_arg(useColor)
        elif o in ("--email"):
            foundEmail = check_for_dup_arg(foundEmail)
            email = a


###################################
# Builds the sub-script's command for VHDL remote run
class commandRemoteVUNIT:
    def __init__(self, tname, indx, numb = 1):
        self.status = NOT_STARTED
        self.pid = ""
        self.testNum = numb
        self.testName = tname.rstrip("\n")
        self.cmd = "mux-farm bash -c 'python3 ./run.py" + "'"
        self.monitorCmd = "mux-status "
        self.time = 0
        self.indx = indx

    def execute(self, lh):
        if verbose:
            print_str("Running test '{}'".format(self.testName))
        lh.write("Sending: '{}' to mux-farm\n".format(self.testName))
        cmd_list = shlex.split(self.cmd)
        lh.write("  Command is '{}'\n".format(self.cmd))

        os.chdir(os.path.join(".",self.testName))
        print_debug_str(debug, "Test took us to: {}".format(os.getcwd()))
        lh.write("  Running test in {}\n".format(os.getcwd()))
        result = subprocess.run(cmd_list, timeout=TIMEOUT, check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        output = result.stdout.decode('utf-8')
        self.pid = output.rstrip("\n")
        if debug:
            lh.write("  Output of command is '{}'\n".format(output))
        else:
            lh.write("  Process ID is {}\n".format(self.pid))
        self.monitorCmd = self.monitorCmd + self.pid
        self.status = RUNNING
        self.time = 0
        os.chdir(startDir)


###################################
# Do the actual work
def execute(class_tlst):
    retVal = False
    # open a log file for messages out.
    if verbose:
        print_str("Opening log file {}".format(os.path.join(os.getcwd(), "tests_run.log")))
    lh = open ("tests_run.log", "w")
    lh.write("-------------------------------------------\n")
    lh.write("Test run starting\n")
    lh.write("-------------------------------------------\n")

    print_debug_str(debug, "Running tests from {} ".format(startDir))
    for test in class_tlst:
        test.execute(lh)
    
    #  attach monitor of mux jobs
    #monitor(class_tlst, True, True)
    retVal = monitor(class_tlst, debug, verbose)
    
    if not retVal:
        lh.write("All test jobs completed successfully.\n")
    else:
        lh.write("Monitor of test jobs reported {}\n".format(retVal))

    lh.write("-------------------------------------------\n")
    lh.write("Test run completed\n")
    lh.write("-------------------------------------------\n")
    #  close log file.
    lh.close()
    

    if email:
        if verbose:
            print_str("Sending email...")
        do_cmd("cat tests_run.log | mail -s 'VUNIT Regression results' {}@metrics.ca".format(email))
    return retVal


###################################
# Get ready to do the work
def setup():
    if verbose:
        print_str("Setting up the tests...")
    if not exists("tests_to_run.txt"): ## find all the run.py files from here down.
        found = False
        sflist = glob.glob('**/run.py', recursive=True)
        #  write out tests found
        fh = open("tests_to_run.txt", "w")
        for s in sflist:
            #print(str(s))
            fh.write(s.rsplit("/",1)[0] + "\n")
            found = True
        fh.close()

        if not found:
            print("No tests list file was found under 'tests_to_run.txt'\n")
            print("All tests found are listed in file 'test_found_list.txt'\n")
            do_exit(1)

    fh = open("tests_to_run.txt", "r")
    rlst = fh.readlines()
    fh.close()
    
    class_tlst = []
    # create classes of  test cases.
    indx = 0
    for name in rlst:
        if name[0] == "#":
            continue
        # find index to sub in output dir name
        vupath = name.strip() + "/vunit_out"
        #print("vpath: " + vupath)
        # remove output if exists
        if exists(vupath):
            print("Removing previous: " + vupath)
            shutil.rmtree(vupath)
        class_tlst.append(commandRemoteVUNIT(name, indx))
        indx += 1
    
    return class_tlst


###################################
# Set up the global variables needed by the rest of the process
def initialize():
    global rootDir
    global startDir

    startDir = os.getcwd()

    if not cwd_is_in_repo():
        print_err("Must be invoked from within the VUNIT repo.")
        do_exit(-12, debug)

    rootDir = get_root_of_repo(startDir, False)
    if rootDir == "":
        print_err("Could not find the root of the VUNIT repo.")
        do_exit(-13, debug)


######################################################################################
# Main
######################################################################################
def main(argv):
    """  Run vunit examples
    
    This script assumes that the environment is set up.
      -  correct dsim version
      -  vunit environment
      The tests to run are in file named "tests_to_run.txt"
    
    """

    programStatus = False
    set_color_usage(sys.stdout.isatty())

    initialize()

    process_args()

    if not useColor:
        set_color_usage(False)

    class_tlst = setup()

    try:
        programStatus = execute(class_tlst)

        os.chdir(startDir)

    except KeyboardInterrupt:
            print("\nBye")
            sys.exit(0)

    except:
        print(traceback.print_exc())

    do_exit(programStatus, debug)

    
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
