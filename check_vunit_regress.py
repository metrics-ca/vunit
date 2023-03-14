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



import sys
import getopt
import os
import subprocess
import shutil
import time
import traceback
from pathlib import Path
import string
from os.path import exists

envVars = os.environ
if "PYTHONPATH" not in envVars:
    if "DSIM_REGRESS" not in envVars:
        print("Error:  DSIM_REGRESS not set.  Exiting.")
        sys.exit(-1)

    sys.path.append(envVars.get("DSIM_REGRESS") + "/lib/python")
    
from metrics.basics import *


# Constants
VERSION = "1.0.0"
SUCCESS = 0


# Globals set during argument processing
debug = False
useColor = False
verbose = False

###################################
# Prints a usage line with the set of possible options
def print_usage(retVal):
    print("usage: {}".format(os.path.basename(sys.argv[0])), end=" ")
    print("{--help}", end=" ")
    print("{--version}", end=" ")
    print("{--verbose}", end=" ")
    print("{--color}", end=" ")
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
    print("    Checks the results of the VUNIT test run for any failures")
    print_color("\nOPTIONS", False, Bold, White, BG_Black)
    print("    -h, --help")
    print("        Display's this help information")
    print("    -v, --version")
    print("        Print out the version of this tool")
    print("    -V, --verbose")
    print("        Print out each test as it is executed")
    print("    -C, --color")
    print("        Enable color output")
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

    try:
        opts, testDirs = getopt.getopt(sys.argv[1:], "hicCvVrdI",
                                                     ["help",
                                                      "color",
                                                      "version",
                                                      "verbose",
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

    set_color_usage(useColor)

#######################################################
##                   main
def main(argv):
    """  Run vunit examples
    
    This script checks that the tests that were expected to
      run are run, and returns the status.
      
      -V will enable a verbose log file output, copy dsim
         output into the vunit_check.output file.
    
    """

    programStatus = False
    set_color_usage(sys.stdout.isatty())

    process_args()

    # setup some default strings
    MapFile = "test_name_to_path_mapping.txt"
    OutPath = "test_output"
    OFile = "output.txt"
    PassMSG = "=N:[VhdlStop]"
    
    # Open checker output log file.
    try:
        lh = open ("vunit_check.log", "w")
    except:
        print_err("Could not open output file {}".format(os.path.join(os.getcwd(),"vunit_check.log")))
        do_exit(-1, debug)
        
    #  now open the test listed to be run
    if exists("tests_to_run.txt"):
        fh = open("tests_to_run.txt", "r")
        rlst = fh.readlines()
        fh.close()
    else:
        print_err("No tests list file was found in 'tests_to_run.txt'")
        print_err("All tests found are listed in file 'test_found_list.txt'")
        do_exit(-1, debug)
    
    ##  go through the tests 
    passed = 0
    failures = 0
    missing = 0
    for test in rlst:
        if test[0] == "#":
            continue
        test = test.strip()
        print_debug_str(debug, "Checking test {}".format(test))
        
        out_dir = os.path.join(".", test, "vunit_out")
        if not exists(out_dir):
            missing += 1
            lh.write(">>>>  ERROR: Expected output directory was not found\n    " + out_dir)
            lh.write("\n")
            lh.write("***************************************************************************\n")
            print_err("Expected output directory: " + os.path.join(os.getcwd(), out_dir) + " was not found")
            continue
        
        #  map file  Map tests to  random naming
        mfile = os.path.join(out_dir, OutPath, MapFile)
        #  if no mapping file continue
        if not exists(mfile):
            print_err("No Name Mapping File found in " + mfile)
            continue
        
        # all seems good,  check the files for passing message.
        try:
            mf = open(mfile , "r")
        except:
            lh.write(">>>>  ERROR: Expected output file was not found\n    " + mfile)
            lh.write("\n")
            lh.write("***************************************************************************\n")
            print_err("Could not open '{}' for read".format(mfile))
            continue

        mlst = mf.readlines()
        for m in mlst:
            sm = m.split()
            
            dtn = os.path.join(out_dir, OutPath, sm[0], OFile)
            
            try:
                with open(dtn, "r") as file:
                    txt = file.read()
                    if not PassMSG in txt:
                        lh.write(">>>>  Test Failed: " + m + "\n")
                        if verbose:
                            lh.write(txt)
                            lh.write("\n")
                            lh.write("***************************************************************************\n")
                        
                        failures += 1
                    else:
                        passed += 1
            except:
                lh.write(">>>>  ERROR: Expected test results file was not found\n    " + dtn)
                lh.write("\n")
                lh.write("***************************************************************************\n")
                print_err("Could not open '{}' for read".format(dtn))
                continue
        
    if failures + missing <= 0:
        lh.write("None\n")
    lh.close()
    if verbose:
        print_str("Passed: " + str(passed) + "\nFailures: " + str(failures) + "\nMissing: " + str(missing))
    return failures + missing
    
if __name__ == '__main__':
    stat = main(sys.argv[1:])
    do_exit(stat, debug)

