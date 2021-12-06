# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014-2020, Lars Asplund lars.anders.asplund@gmail.com

"""
Interface for the Metrics DSim simulator
"""

from pathlib import Path
from os.path import relpath
from os import environ
import os
import subprocess
import logging
from ..exceptions import CompileError
from ..ostools import Process, write_file, file_exists
from ..vhdl_standard import VHDL
from . import SimulatorInterface, run_command, ListOfStringOption

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
            "Metrics dsim", description="Metrics dsim-specific flags"
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
    

    def setup_library_mapping(self, project):
        """
        Setup library mapping
        """
        #mapped_libraries = self._get_mapped_libraries()
        mapped_libraries = {}
        for library in project.get_libraries():
            self._libraries.append(library)
            #self.create_library(library.name, library.directory, mapped_libraries)
            print(library.name + " " + library.vhdl_standard._standard)

        # Determine which ieee library to map, based on the VHDL standard in use
        libToMap = self._vhdl_std_to_ieee_lib(self._libraries[0].vhdl_standard) 
        proc = subprocess.run([str(Path(self._prefix) / "dlib"), "map", "-work", self._libraries[0].directory.rstrip("vunit_lib"), "-lib", "ieee", os.getenv("STD_LIBS")+"/"+libToMap+"/sfe/ieee"], capture_output=True, text=True)
        print(proc)

    #def _get_mapped_libraries(self):
        """
        Get mapped libraries from modelsim.ini file
        """
    #    cfg = parse_modelsimini(self._sim_cfg_file_name)
    #    libraries = dict(cfg.items("Library"))
    #    if "others" in libraries:
    #        del libraries["others"]
    #    return libraries

    #def create_library(self, library_name, path, mapped_libraries=None):
        """
        Create and map a library_name to path
        """
    #    mapped_libraries = mapped_libraries if mapped_libraries is not None else {}

        #apath = str(Path(path).parent.resolve())
        #print("apath = " + apath)
        #print("path= " + path)
        #if not file_exists(apath):
        #    os.makedirs(apath)

        #if not file_exists(path):
        #    proc = Process([str(Path(self._prefix) / "vlib"), "-unix", path], env=self.get_env())
        #    proc.consume_output(callback=None)

        #if library_name in mapped_libraries and mapped_libraries[library_name] == path:
        #    return

        #cfg = parse_modelsimini(self._sim_cfg_file_name)
        #cfg.set("Library", library_name, path)
        #write_modelsimini(cfg, self._sim_cfg_file_name)

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
        cmd = str(Path(self._prefix) / "dvhcom")
        args = []
        args += ["-work", source_file.library.directory.rstrip(source_file.library.name)]
        args += ["-lib", source_file.library.name]
        args += ["%s" % self._vhdl_std_opt(source_file.get_vhdl_standard())]
        args += source_file.compile_options.get("metrics.dsim_vhdl_flags", [])
        print(source_file.compile_options.get("metrics.dsim_vhdl_flags", []))
        
        args += [
            '-l %s'
            % str(
                Path(self._output_path)
                / ("metrics_compile_vhdl_file_%s.log" % source_file.library.name)
            )
        ]

        args += ['%s' % source_file.name]
        argsfile = str(
            Path(self._output_path)
            / ("metrics_compile_vhdl_file_%s.args" % source_file.library.name)
        )
        write_file(argsfile, "\n".join(args))
        return [cmd, "-f", argsfile]
   

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

    def simulate(  # pylint: disable=too-many-locals
            self, output_path, test_suite_name, config, elaborate_only=False):
        """
        Elaborates and Simulates
        """

        script_path = str(Path(output_path) / self.name)

        cmd = str(Path(self._prefix) / "dsim")
        args = []
        args += ["-exit-on-error 1"]
        args += config.sim_options.get("metrics.dsim_sim_flags", [])
        args += ['-l %s' % str(Path(script_path) / ("dsim_simulate.log"))]
            
        runner_cfg = config.generics["runner_cfg"]

        for name, value in config.generics.items():
            args += ['-defparam %s=\"%s\"' % (name, value)]

        for library in self._libraries:
            args += ['-L %s' % library.name]

        args += ['-work %s' % library.directory.rstrip(library.name)]
        args += ["+acc+b"]
        args += ["-top %s.%s" % (config.library_name, config.entity_name)]
            
        argsfile = "%s/dsim_simulate.args" % (script_path)
        write_file(argsfile, "\n".join(args))
        if not run_command(
            [cmd, "-f", relpath(argsfile, script_path)],
            cwd=script_path,
            env=self.get_env(),
        ):
            return False
        return True

