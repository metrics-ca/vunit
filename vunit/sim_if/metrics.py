# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014-2020, Lars Asplund lars.anders.asplund@gmail.com

"""
Interface for the Metrics DSim simulator
"""

from pathlib import Path
from pathlib import PurePath
from os.path import relpath
from os import environ, makedirs
import os
import subprocess
import logging
from ..exceptions import CompileError
from ..ostools import Process, write_file, file_exists
from ..vhdl_standard import VHDL
from . import SimulatorInterface, run_command, ListOfStringOption

import time

LOGGER = logging.getLogger(__name__)


class MetricsInterface(  # pylint: disable=too-many-instance-attributes
    SimulatorInterface
):
    """
    Interface for the Metrics simulator
    """

    name = "metrics"
    executable = environ.get("DSIM_HOME", "bin")
    supports_gui_flag = False

    compile_options = [
        ListOfStringOption("metrics.dsim_vhdl_flags"),
        ListOfStringOption("metrics.dsim_verilog_flags"),
    ]

    sim_options = [ListOfStringOption("metrics.dsim_sim_flags")]

    @staticmethod
    def add_arguments(parser):
        """
        Add command line arguments
        """
        group = parser.add_argument_group(
            "Metrics DSim", description="Metrics DSim-specific flags"
        )
        group.add_argument(
            "-waves",
            choices=["waves.vcd", "waves.fst"],
            default=None,
            help="Save .vcd or .fst",
        )

    @classmethod
    def from_args(cls, args, output_path, **kwargs):
        """
        Create new instance from command line arguments object
        """
        return cls(
            prefix=cls.find_prefix(),
            output_path=output_path,
            log_level=args.log_level,
            gui=args.gui,
        )

    @classmethod
    def find_prefix_from_path(cls):
        """
        Find Metrics simulator from PATH environment variable
        """
        mdc_prefix = cls.find_toolchain(["mdc"])
        if (mdc_prefix):
           return mdc_prefix
        return cls.find_toolchain(["dsim"])

    @staticmethod
    def supports_vhdl_contexts():
        """
        Returns True when this simulator supports VHDL 2008 contexts
        """
        return True

    def __init__(  # pylint: disable=too-many-arguments
        self, prefix, output_path, gui=False, log_level=None
    ):
        SimulatorInterface.__init__(self, output_path, gui)
        self._prefix = prefix
        self._libraries = []
        self._log_level = log_level
        in_cloud = self.find_toolchain(["mdc"])
        if (in_cloud):
            self._in_cloud = True
        else:
            self._in_cloud = False

    @staticmethod
    def _vhdl_std_to_ieee_lib(vhdl_standard):
        """
        Based on the VHDL standard in use, decide which IEEE library to use
        """
        if vhdl_standard == VHDL.STD_2002:
            return "ieee93"

        if vhdl_standard == VHDL.STD_2008:
            return "ieee08"

        if vhdl_standard == VHDL.STD_1993:
            return "ieee93"

        raise ValueError("Invalid VHDL standard %s" % vhdl_standard)

    def _rel_path(self, path):
        return os.path.relpath(path, os.getcwd())


    def _format_cmd(self, cmd, args):
        metrics_cloud = True
        if self._in_cloud:
            rvalue = ['mdc', cmd, '-a', '{}'.format(' '.join(args))];
            print("MCA rvalue from _exec_cmds = \n")
            print(rvalue);
            return ['mdc', cmd, '-a', '{}'.format(' '.join(args))]
        else:
            rvalue = [cmd] + args;
            print("MCA _format_cmd for on-prem is:")
            print(rvalue)
            return rvalue

    def setup_library_mapping(self, project):
        """
        Setup library mapping
        """
        for library in project.get_libraries():
            self._libraries.append(library)
        #    print(library.name + " " + library.vhdl_standard._standard)
        vhdl_standards = set(
            source_file.get_vhdl_standard()
            for source_file in project.get_source_files_in_order()
            if source_file.is_vhdl
        )

        if not vhdl_standards:
            self._vhdl_standard = VHDL.STD_2008
        #elif len(vhdl_standards) != 1:
        #    raise RuntimeError("GHDL cannot handle mixed VHDL standards, found %r" % list(vhdl_standards))
        else:
            self._vhdl_standard = list(vhdl_standards)[0]

        # Determine which ieee library to map, based on the VHDL standard in use
        #libToMap = self._vhdl_std_to_ieee_lib(self._libraries[0].vhdl_standard)
        libToMap = self._vhdl_std_to_ieee_lib(self._vhdl_standard)
        work = self._rel_path(self._libraries[0].directory.rstrip('vunit_lib'))
        args = ['map', '-work', work, "-lib", "ieee"]
        if self._in_cloud:
            args += [os.path.join('%STD_LIBS%', libToMap, 'sfe/ieee')]
        else:
            args += [os.getenv("STD_LIBS")+"/"+libToMap+"/sfe/ieee"]
        cmd = self._format_cmd('dlib', args)
        print("DLIB", cmd)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        print(proc)


    def compile_source_file_command(self, source_file):
        """
        Returns the command to compile a single source file
        """
        if source_file.is_vhdl:
            return self.compile_vhdl_file_command(source_file)

        if source_file.is_any_verilog:
            return self.compile_verilog_file_command(source_file)

        raise CompileError

    @staticmethod
    def _vhdl_std_opt(vhdl_standard):
        """
        Convert standard to a DSim command line flag
        """
        if vhdl_standard == VHDL.STD_2002:
            return "-vhdl2002"

        if vhdl_standard == VHDL.STD_2008:
            return "-vhdl2008"

        if vhdl_standard == VHDL.STD_1993:
            return "-vhdl93"

        raise ValueError("Invalid VHDL standard %s" % vhdl_standard)

    def compile_vhdl_file_command(self, source_file):
        """
        Returns command to compile a VHDL file
        """
        args = []
        args +=  ["-work", self._rel_path(source_file.library.directory.rstrip(source_file.library.name))]
        args += ["-lib", source_file.library.name]
        args += ["%s" % self._vhdl_std_opt(source_file.get_vhdl_standard())]
        args += source_file.compile_options.get("metrics.dsim_vhdl_flags", [])

        # Assume everything relative to the current directory
        output_path = self._rel_path(self._output_path)

        args += [
            '-l', '%s'
            % os.path.join(output_path,
                           ("metrics_compile_vhdl_file_%s.log" % source_file.library.name))
        ]

        args += ['%s' % self._rel_path(source_file.name)]
        cmd = self._format_cmd('dvhcom', args)
        print("DVHCOM", cmd)
        return cmd

    def compile_verilog_file_command(self, source_file):
        """
        Returns commands to compile a Verilog file
        """
        cmd = str(Path(self._prefix) / "dvlcom")
        args = []
        args += ["-work", source_file.library.directory.rstrip(source_file.library.name)]
        args += ["-lib", source_file.library.name]
        args += source_file.compile_options.get("metrics.dsim_verilog_flags", [])
        args += [
            '-l %s'
            % str(
                Path(self._output_path)
                / ("metrics_compile_verilog_file_%s.log" % source_file.library.name)
            )
        ]

        for include_dir in source_file.include_dirs:
            args += ['+incdir+%s' % include_dir]

        args += ['%s' % source_file.name]
        argsfile = str(
            Path(self._output_path)
            / ("metrics_compile_verilog_file_%s.args" % source_file.library.name)
        )
        write_file(argsfile, "\n".join(args))
        return [cmd, "-f", argsfile]

    @staticmethod
    def _escape_nested_quotes(value):
        """
        Returns copy of string with a separate escape character before
        any nested quotes
        """
        val_copy = ""
        for i in range(len(value)):
            if (value[i] == '"' and (i == 0 or value[i-1] != "\\")):
                val_copy += "\\"
            val_copy += value[i]
        return val_copy

    def simulate(  # pylint: disable=too-many-locals
            self, output_path, test_suite_name, config, elaborate_only=False):
        """
        Elaborates and Simulates
        """
        script_path = str(Path(output_path) / self.name)
        makedirs(script_path)

        args = []
        args += ["-exit-on-error 1"]
        args += config.sim_options.get("metrics.dsim_sim_flags", [])
        args += ['-l dsim_simulate.log']
            
        runner_cfg = config.generics["runner_cfg"]

        for name, value in config.generics.items():
            if isinstance(value, PurePath):
                value = str(value)
            if isinstance(value, str):
                value = self._escape_nested_quotes(value)
                args += ['-defparam %s=\"%s\"' % (name, value)]
            else:
                args += ['-defparam %s=%s' % (name, value)]

        for library in self._libraries:
            args += ['-L %s' % library.name]

        work_path = os.path.relpath(library.directory.rstrip(library.name), script_path)
        args += ['-work %s' % work_path]
        args += ["+acc+b"]
        args += ["-top %s.%s" % (config.library_name, config.entity_name)]
            
        argsfile = "%s/dsim_simulate.args" % (script_path)
        write_file(argsfile, "\n".join(args))
        argsfile = relpath(argsfile, script_path)

        cmd = self._format_cmd("dsim", ['-F', '%s' % argsfile])
        print("DSIM cmd: ", cmd)
        if not run_command(
                cmd,
                cwd=script_path,
                env=self.get_env(),
        ):
            return False
        return True
