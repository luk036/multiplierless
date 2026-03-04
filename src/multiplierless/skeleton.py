"""
Multiplierless Filter Design Examples

This module provides examples for designing multiplierless FIR filters using
the multiplierless package. These examples demonstrate how to use the core
functionality for practical filter design tasks.

References:
    - https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import argparse
import logging
import sys

from multiplierless import __version__

__author__ = "Wai-Shing Luk"
__copyright__ = "Wai-Shing Luk"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

__all__ = ["main", "run"]


# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description="Multiplierless FIR Filter Design Examples"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="multiplierless {ver}".format(ver=__version__),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args(args)


def setup_logging(loglevel: int) -> None:
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    # Force logging to stdout/stderr even if already configured
    logging.basicConfig(
        level=loglevel if loglevel is not None else logging.WARNING,
        stream=sys.stdout,
        format=logformat,
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


def main(args: list[str]) -> None:
    """Wrapper for multiplierless filter design CLI

    This function provides a command-line interface for exploring
    multiplierless filter design capabilities.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose"]``).
    """
    parsed_args = parse_args(args)
    # Set default log level to INFO if not specified
    loglevel = (
        parsed_args.loglevel if parsed_args.loglevel is not None else logging.INFO
    )
    setup_logging(loglevel)
    _logger.debug("Starting multiplierless examples...")
    _logger.info("multiplierless - FIR filter design without multipliers")
    _logger.info("")
    _logger.info("This package provides tools for designing FIR filters")
    _logger.info("that avoid multiplication operations, useful for")
    _logger.info("hardware-constrained implementations.")
    _logger.info("")
    _logger.info("Key modules:")
    _logger.info("  - spectral_fact: Spectral factorization algorithms")
    _logger.info("  - lowpass_oracle_q: Lowpass filter design with CSD constraints")
    _logger.info("")
    _logger.info("For more information, see:")
    _logger.info("  https://github.com/luk036/multiplierless")
    _logger.info("  https://luk036.github.io/multiplierless")
    _logger.info("Script ends here")


def run() -> None:
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m multiplierless.skeleton
    #
    run()
