-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this file,
-- You can obtain one at http://mozilla.org/MPL/2.0/.
--
-- Copyright (c) 2017, Lars Asplund lars.anders.asplund@gmail.com

use work.log_levels_pkg.all;
use work.log_handler_pkg.all;
use work.integer_vector_ptr_pkg.all;

package logger_pkg is

  -- Logger record, all fields are private
  type logger_t is record
    p_data : integer_vector_ptr_t;
  end record;
  constant null_logger : logger_t := (p_data => null_ptr);
  constant root_logger : logger_t;

  -- Get a logger with name.
  -- Can also optionally be relative to a parent logger
  impure function get_logger(name : string;
                             parent : logger_t := null_logger) return logger_t;

  -------------------------------------
  -- Log procedures for each log level
  -------------------------------------
  procedure debug(logger : logger_t;
                  msg : string;
                  line_num : natural := 0;
                  file_name : string := "");

  procedure verbose(logger : logger_t; msg : string;
                    line_num : natural := 0;
                    file_name : string := "");

  procedure info(logger : logger_t; msg : string;
                 line_num : natural := 0;
                 file_name : string := "");

  procedure warning(logger : logger_t; msg : string;
                    line_num : natural := 0;
                    file_name : string := "");

  procedure error(logger : logger_t; msg : string;
                  line_num : natural := 0;
                  file_name : string := "");

  procedure failure(logger : logger_t; msg : string;
                    line_num : natural := 0;
                    file_name : string := "");

  ------------------------------------------------
  -- Log procedure short hands for default logger
  ------------------------------------------------

  -- The default logger, all log calls without logger argument go to this logger.
  constant default_logger : logger_t;

  procedure debug(msg : string;
                  line_num : natural := 0;
                  file_name : string := "");

  procedure verbose(msg : string;
                    line_num : natural := 0;
                    file_name : string := "");

  procedure info(msg : string;
                 line_num : natural := 0;
                 file_name : string := "");

  procedure warning(msg : string;
                    line_num : natural := 0;
                    file_name : string := "");

  procedure error(msg : string;
                  line_num : natural := 0;
                  file_name : string := "");

  procedure failure(msg : string;
                    line_num : natural := 0;
                    file_name : string := "");

  -- Log procedure with level as argument
  procedure log(logger : logger_t;
                msg : string;
                log_level : log_level_t := info;
                line_num : natural := 0;
                file_name : string := "");

  procedure log(msg : string;
                log_level : log_level_t := info;
                line_num : natural := 0;
                file_name : string := "");

  -- Get the name of this logger get_name(get_logger("parent:child")) = "child"
  impure function get_name(logger : logger_t) return string;

  -- Get the full name of this logger get_name(get_logger("parent:child")) = "parent:child"
  impure function get_full_name(logger : logger_t) return string;

  -- Get the parent of this logger
  impure function get_parent(logger : logger_t) return logger_t;

  -- Get the number of children of this logger
  impure function num_children(logger : logger_t) return natural;

  -- Get the idx'th child of this logger
  impure function get_child(logger : logger_t; idx : natural) return logger_t;

  -- Stop simulation for all levels >= level for this logger and all children
  procedure set_stop_level(logger : logger_t; log_level : log_level_t);

  -- Stop simulation for all levels >= level
  procedure set_stop_level(level : log_level_t);

  -- Disable stopping simulation for this logger and all children
  -- Equivalent with set_stop_level(logger, above_all_log_levels)
  procedure disable_stop(logger : logger_t);

  -- Disable stopping simulation
  -- Equivalent with set_stop_level(above_all_log_levels)
  procedure disable_stop;

  -- Disable logging for all levels < level to this handler. Additional log
  -- levels may have been disabled with the block filter setting
  procedure set_log_level(log_handler : log_handler_t;
                          level : log_level_t);

  -- Disable logging for all levels < level to this handler from specific
  -- logger and all children. Additional log levels may have been disabled with the
  -- block filter setting
  procedure set_log_level(logger : logger_t;
                          log_handler : log_handler_t;
                          level : log_level_t);

  -- Disable logging for the specified levels to this handler. Additional log
  -- levels may have been disabled by the log level setting
  procedure set_block_filter(log_handler : log_handler_t;
                             levels : user_log_level_vec_t);

  -- Disable logging for the specified levels to this handler from specific
  -- logger and all children. Additional log levels may have been disabled by
  -- the log level setting
  procedure set_block_filter(logger : logger_t;
                             log_handler : log_handler_t;
                             levels : user_log_level_vec_t);


  -- Enable all log levels to the log handler
  -- equivalent with setting log level to below_all_log_levels
  procedure enable_all(log_handler : log_handler_t);

  -- Enable all log levels for this handler from specific logger and all children
  -- equivalent with setting log level to below_all_log_levels
  procedure enable_all(logger : logger_t;
                       log_handler : log_handler_t);

  -- Disable all log levels for this handler
  -- equivalent with setting log level to above_all_log_levels
  procedure disable_all(log_handler : log_handler_t);

  -- Disable all log levels for this handler from specific logger and all children
  -- equivalent with setting log level to above_all_log_levels
  procedure disable_all(logger : logger_t;
                        log_handler : log_handler_t);


  -- Return true if logging to this logger at this level is enabled in any handler
  -- Can be used to avoid expensive string creation when not logging a specific
  -- level
  impure function is_enabled(logger : logger_t;
                             level : log_level_t) return boolean;

  -- Returns true if a logger at this level is enabled to this handler
  impure function is_enabled(logger : logger_t;
                             log_handler : log_handler_t;
                             level : log_level_t) return boolean;

  -- Get the current log level setting for a specific logger to this log handler
  impure function get_log_level(logger : logger_t;
                                log_handler : log_handler_t) return log_level_t;

  -- Get the number of levels disabled by the block filter setting for a specific logger to this log handler
  impure function num_block_filter_levels(logger : logger_t;
                                          log_handler : log_handler_t) return natural;

  -- Get the current block filter setting for a specific logger to this log handler
  impure function get_block_filter(logger : logger_t;
                                   log_handler : log_handler_t) return user_log_level_vec_t;

  -- Get the number of log handlers attached to this logger
  impure function num_log_handlers(logger : logger_t) return natural;

  -- Get the idx'th log handler attached to this logger
  impure function get_log_handler(logger : logger_t; idx : natural) return log_handler_t;

  -- Get all log handlers attached to this logger
  impure function get_log_handlers(logger : logger_t) return log_handler_vec_t;

  -- Set the log handlers for this logger and all children
  procedure set_log_handlers(logger : logger_t;
                             log_handlers : log_handler_vec_t);

  -- Get number of logs to a specific level or all levels when level = null_log_level
  impure function get_log_count(
    logger : logger_t;
    log_level : log_level_t := null_log_level) return natural;

  -- Reset the log count of a specific level or all levels when level = null_log_level
  procedure reset_log_count(
    logger : logger_t;
    log_level : log_level_t := null_log_level);

  ---------------------------------------------------------------------
  -- Mock procedures to enable unit testing of code performing logging
  ---------------------------------------------------------------------

  -- Mock the logger preventing simulaton abort and recording all logs to it
  procedure mock(logger : logger_t);

  -- Unmock the logger returning it to its normal state
  -- Results in failures if there are still unchecked log calls recorded
  procedure unmock(logger : logger_t);

  -- Returns true if the logger is mocked
  impure function is_mocked(logger : logger_t) return boolean;

  -- Get the log count of specific or all log levels occured during mocked state
  impure function get_mock_log_count(
    logger : logger_t;
    log_level : log_level_t := null_log_level) return natural;

  -- Constant to ignore time value when checking log call
  constant no_time_check : time := -1 ns;

  -- Check that the earliest recorded log call in the mock state matches this
  -- call or fails. Also consumes this recorded log call such that subsequent
  -- check_log calls can be used to verify a sequence of log calls
  procedure check_log(logger : logger_t;
                      msg : string;
                      log_level : log_level_t;
                      log_time : time := no_time_check;
                      line_num : natural := 0;
                      file_name : string := "");

  -- Check that there is only one recorded log call remaining
  procedure check_only_log(logger : logger_t;
                           msg : string;
                           log_level : log_level_t;
                           log_time : time := no_time_check;
                           line_num : natural := 0;
                           file_name : string := "");

  -- Check that there are no remaining recorded log calls, automatically called
  -- during unmock
  procedure check_no_log(logger : logger_t);

end package;