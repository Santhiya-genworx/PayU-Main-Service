"""This module sets up the logging configuration for the PayU Main Service. It defines a structured log format that includes the timestamp, log level, logger name, and message. The logging is configured to output to standard output (stdout) with an INFO log level. A logger named "payu-main-service" is created for use throughout the application to ensure consistent logging practices. This configuration allows for better observability and debugging by providing clear and structured log messages that can be easily filtered and analyzed."""

import logging
import sys

# Structured log format
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format=LOG_FORMAT)

logger = logging.getLogger("payu-main-service")
