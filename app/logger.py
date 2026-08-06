import functools
import logging
import sys
import traceback

import structlog

handler = logging.StreamHandler(sys.stdout)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="%H:%M:%S"),
        structlog.dev.ConsoleRenderer(sort_keys=False),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

main_logger = structlog.get_logger("MainLogger")

logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def inject_traceback(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        f = sys._getframe(kwargs.get("increase_depth", 1))
        loc, line = f.f_code.co_filename, f.f_lineno
        loc = loc[loc.find("app"):]
        func(*args, **kwargs, msg_location=(loc, line))

    return wrapper


class Logger:
    @staticmethod
    def _get_caller_name(increase_depth: int = 0) -> str:
        return f"[{sys._getframe(2 + increase_depth).f_code.co_name}]"

    @staticmethod
    @inject_traceback
    def info(
            msg: str,
            *,
            msg_location: tuple[str, int] = None,
            increase_depth: int = 1,
            event: str = "",
            **kwargs
    ):
        main_logger.info(
            event + Logger._get_caller_name(increase_depth) + str(msg_location),
            msg=msg,
            **kwargs
        )

    @staticmethod
    @inject_traceback
    def debug(msg: str,
              *,
              msg_location: tuple[str, int] = None,
              increase_depth: int = 1,
              event: str = "",
              **kwargs
              ):
        main_logger.debug(
            event + Logger._get_caller_name(increase_depth) + str(msg_location),
            msg=msg,
            **kwargs
        )

    @staticmethod
    @inject_traceback
    def warning(
            msg: str, *,
            error: Exception = None,
            msg_location: tuple[str, int] = None,
            increase_depth: int = 1,
            event: str = "",
            **kwargs
    ):
        main_logger.warning(
            event + Logger._get_caller_name(increase_depth) + str(msg_location),
            msg=msg,
            error=error,
            **kwargs
        )

    @staticmethod
    @inject_traceback
    def error(
            msg: str, *,
            error: Exception = None,
            msg_location: tuple[str, int] = None,
            increase_depth: int = 1,
            event: str = "",
            **kwargs
    ):
        main_logger.error(
            event + Logger._get_caller_name(increase_depth) + str(msg_location),
            msg=msg,
            error=error,
            **kwargs,
            traceback=traceback.format_exc(),
        )


class LoggerMixin:
    @property
    def _log_prefix(self) -> str:
        class_name = self.__class__.__name__
        return f"[{class_name}]"

    def log_info(self, msg: str, **kwargs):
        Logger.info(
            event=self._log_prefix,
            msg=msg,
            increase_depth=2,
            **kwargs
        )

    def log_debug(self, msg: str, **kwargs):
        Logger.debug(
            event=self._log_prefix,
            msg=msg,
            increase_depth=2,
            **kwargs
        )

    def log_warning(self, msg: str, **kwargs):
        Logger.warning(
            event=self._log_prefix,
            msg=msg,
            increase_depth=2,
            **kwargs
        )

    def log_error(self, msg: str, *, error: Exception, **kwargs):
        Logger.error(
            event=self._log_prefix,
            msg=msg,
            error=error,
            increase_depth=2,
            **kwargs
        )
