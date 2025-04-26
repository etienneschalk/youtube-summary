"""Logging Utility Module

This module provides utility functions for setting up and configuring loggers
with customized formatting and handlers.

Constants
---------
DEFAULT_STDOUT_FORMATTER : str
    Colored formatter string for stdout logging.
DEFAULT_STDOUT_FORMATTER_NO_COLOR : str
    Non-colored formatter string for file logging.
STDOUT_HANDLER_NAME : str
    Name for the stdout handler.

Functions
---------
get_logger
create_stream_handler
create_file_handler
add_file_handler_to_logger

See Also
--------
logging : Python's built-in logging module.
colorama : Used for colored console output.

"""

import logging
import sys
from pathlib import Path

import pandas as pd
from colorama import Back, Fore, Style

# For the sake of convenience, split log header from content
DEFAULT_STDOUT_FORMATTER_TWO_LINES = (
    f"{Fore.YELLOW}%(asctime)s %(relativeCreated)12d"
    f" {Fore.WHITE}[{Style.BRIGHT}%(levelname)+8s{Style.RESET_ALL}]"
    f" {Fore.BLUE}{Fore.GREEN}%(name)s{Fore.RESET}\n   "
    f" {Fore.CYAN}%(funcName)s{Style.RESET_ALL}{Back.RESET}{Fore.RESET}:"
    f" {Fore.WHITE}%(message)s{Style.RESET_ALL}"
)
DEFAULT_STDOUT_FORMATTER = (
    f"{Fore.YELLOW}%(asctime)s"
    f" {Fore.WHITE}[{Style.BRIGHT}%(levelname)+8s{Style.RESET_ALL}]"
    f" {Fore.BLUE}{Fore.GREEN}%(name)12.12s{Fore.RESET}:"
    # f" {Fore.BLUE}{Fore.GREEN}%(name)s{Fore.RESET}"
    # f" {Fore.CYAN}(%(funcName)24.24s):{Style.RESET_ALL}{Back.RESET}{Fore.RESET}:"
    f" {Fore.WHITE}%(message)s{Style.RESET_ALL}"
)
DEFAULT_STDOUT_FORMATTER_NO_COLOR = (
    "%(asctime)s [%(levelname)+8s] %(name)s    (%(funcName)48.48s): %(message)s"
)
STDOUT_HANDLER_NAME = "stdout"


def get_logger(name: str, *, level: str | int = logging.INFO) -> logging.Logger:
    """Get or create a logger with the specified name and logging level.

    Parameters
    ----------
    name : str
        The name of the logger to retrieve or create.
    level : str | int
        The logging level to set for the logger. Default is logging.INFO.

    Returns
    -------
    logging.Logger
        A configured logger object.

    Notes
    -----
    - Adds a stream handler if one named STDOUT_HANDLER_NAME doesn't exist.

    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not any(h.name == STDOUT_HANDLER_NAME for h in logger.handlers):
        handler = create_stream_handler(level)
        logger.addHandler(handler)

    return logger


def create_stream_handler(level: str | int) -> logging.StreamHandler:
    """Create a stream handler for logging to stdout.

    Parameters
    ----------
    level : str | int
        The logging level for the handler.

    Returns
    -------
    logging.StreamHandler
        A configured stream handler.

    Notes
    -----
    - Uses DEFAULT_STDOUT_FORMATTER for colored output.

    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.name = STDOUT_HANDLER_NAME
    formatter = logging.Formatter(DEFAULT_STDOUT_FORMATTER)
    handler.setFormatter(formatter)
    return handler


def create_file_handler(
    *,
    file_path: Path,
    mode: str,
    level: str | int,
    formatter: str = DEFAULT_STDOUT_FORMATTER_NO_COLOR,
) -> logging.FileHandler:
    """Create a file handler for logging to a file.

    Parameters
    ----------
    file_path : Path
        The path to the log file.
    mode : str
        The file opening mode (e.g., 'a' for append).
    level : str | int
        The logging level for the handler.
    formatter : str
        The formatter string to use. Default is DEFAULT_STDOUT_FORMATTER_NO_COLOR.

    Returns
    -------
    logging.FileHandler
        A configured file handler.

    """
    file_handler = logging.FileHandler(file_path, mode=mode)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(formatter))
    return file_handler


def add_file_handler_to_logger(
    logger: logging.Logger,
    log_file_path: Path,
    *,
    log_level: str | int | None = None,
) -> logging.FileHandler:
    """Add a file handler to an existing logger.

    Parameters
    ----------
    logger : logging.Logger
        The logger to add the file handler to.
    log_file_path : Path
        The path to the log file.
    log_level : str | int | None
        The logging level for the file handler. If None, uses the logger's level.

    Returns
    -------
    logging.FileHandler
        The created and added file handler.

    Notes
    -----
    - Creates necessary directories for the log file.
    - Appends to the log file if it already exists.

    """
    if log_level is None:
        log_level = logger.level
    log_file_path.parent.mkdir(exist_ok=True, parents=True)
    file_handler = create_file_handler(
        file_path=log_file_path,
        level=log_level,
        mode="a+",
    )
    logger.addHandler(file_handler)
    return file_handler


def generate_log_file_path_for_one_run(
    identifier: str,
    suffix: str,
) -> Path:
    """Generate a unique log file path for a single run.

    This function creates a log file path based on the current UTC timestamp,
    an identifier, and a suffix. The log file is organized in a directory
    structure that includes the year and month.

    Parameters
    ----------
    identifier : str
        A string identifier for the run, typically representing the type of
        operation or the module being executed.
    suffix : str
        A suffix to be added to the log file name, often used to distinguish
        between different types of logs or processing stages. For instance,
        having one log file per network.

    Returns
    -------
    Path
        A Path object representing the full path to the log file.

    Notes
    -----
    The generated log file path follows this structure:
    logs/{identifier}/{YYYY-MM}/ytsummary_run__{YYYYMMDDTHHMMSSZ}__{identifier}{suffix}.log

    Where:
    - {identifier} is the provided identifier
    - {YYYY-MM} is the year and month of the current UTC time
    - {YYYYMMDDTHHMMSSZ} is the full UTC timestamp
    - {suffix} is the provided suffix

    Examples
    --------
    >>> generate_log_file_path_for_one_run("network_analysis", "_results")
    Path('logs/network_analysis/2023-05/ytsummary_run__20230515T123456Z__network_analysis_results.log')

    """
    utcnow = pd.Timestamp.utcnow()
    log_filename = f"ytsummary_run__{utcnow:%Y%m%dT%H%M%S%fZ}__{identifier}{suffix}.log"
    log_file_path_for_one_run = (
        Path("logs") / identifier / f"{utcnow:%Y-%m}" / log_filename
    )
    return log_file_path_for_one_run
