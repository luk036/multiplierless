import pytest

from multiplierless.skeleton import main, parse_args, setup_logging

__author__ = "Wai-Shing Luk"
__copyright__ = "Wai-Shing Luk"
__license__ = "MIT"


def test_parse_args() -> None:
    """Test argument parsing"""
    # Test basic argument (no required args)
    args = parse_args([])
    assert args.loglevel is None

    # Test verbose flag
    args = parse_args(["-v"])
    assert args.loglevel == 20  # INFO level

    # Test very verbose flag
    args = parse_args(["-vv"])
    assert args.loglevel == 10  # DEBUG level

    # Test long form flags
    args = parse_args(["--verbose"])
    assert args.loglevel == 20

    args = parse_args(["--very-verbose"])
    assert args.loglevel == 10


def test_main(capsys: pytest.CaptureFixture) -> None:
    """CLI Tests"""
    # capsys is a pytest fixture that allows asserts agains stdout/stderr
    # https://docs.pytest.org/en/stable/capture.html
    main([])
    captured = capsys.readouterr()
    # Check both stdout and stderr since logging goes to stderr
    output = captured.out + captured.err
    assert "multiplierless - FIR filter design without multipliers" in output
    assert "spectral_fact" in output
    assert "lowpass_oracle_q" in output


def test_main_with_verbose(capsys: pytest.CaptureFixture) -> None:
    """Test main function with verbose output"""
    main(["--verbose"])
    captured = capsys.readouterr()
    # Check both stdout and stderr since logging goes to stderr
    output = captured.out + captured.err
    assert "multiplierless - FIR filter design without multipliers" in output


def test_setup_logging() -> None:
    """Test logging setup"""
    import logging

    # Test INFO level
    setup_logging(logging.INFO)
    logger = logging.getLogger()
    assert logger.level == logging.INFO

    # Test DEBUG level
    setup_logging(logging.DEBUG)
    assert logger.level == logging.DEBUG
