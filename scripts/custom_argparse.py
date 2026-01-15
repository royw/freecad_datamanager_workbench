#!/usr/bin/env python3

# -------------------------------------------------------------------------
#                                                                         -
#  Python Module Argument Parser                                          -
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 04/03/24                                              -
#  https://gist.github.com/fonic/fe6cade2e1b9eaf3401cc732f48aeebd
#                                                                        -
# -------------------------------------------------------------------------

from __future__ import annotations

import argparse
import os
import shutil
import sys
import textwrap
from typing import TYPE_CHECKING, Any, Never


if TYPE_CHECKING:
    from _typeshed import SupportsWrite

SUPPRESS = argparse.SUPPRESS


# ArgumentParser class providing custom help/usage output
class CustomArgumentParser(argparse.ArgumentParser):
    # Expose argparse.SUPPRESS as a class attribute for convenience
    SUPPRESS = argparse.SUPPRESS

    # Postition of 'width' argument: https://www.python.org/dev/peps/pep-3102/
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # At least self.positionals + self.options need to be initialized before calling
        # __init__() of parent class, as argparse.ArgumentParser.__init__() defaults to
        # 'add_help=True', which results in call of add_argument("-h", "--help", ...)
        self.program: dict[str, Any] = {key: kwargs[key] for key in kwargs}
        self.positionals: list[dict[str, Any]] = []
        self.options: list[dict[str, Any]] = []
        self.width: int = shutil.get_terminal_size().columns or 80
        super().__init__(*args, **kwargs)

    def add_argument_group(self, *args: Any, **kwargs: Any) -> argparse._ArgumentGroup:
        """Override to return a group that tracks arguments in our lists."""
        group = super().add_argument_group(*args, **kwargs)
        # Wrap the group's add_argument method to track arguments
        original_add_argument = group.add_argument

        def wrapped_add_argument(*arg_args: Any, **arg_kwargs: Any) -> argparse.Action:
            action = original_add_argument(*arg_args, **arg_kwargs)
            argument: dict[str, Any] = {key: arg_kwargs[key] for key in arg_kwargs}

            # Positional: argument with only one name not starting with '-'
            if len(arg_args) == 0 or (
                len(arg_args) == 1 and isinstance(arg_args[0], str) and not arg_args[0].startswith("-")
            ):
                argument["name"] = arg_args[0] if (len(arg_args) > 0) else argument.get("dest", "")
                self.positionals.append(argument)
            else:
                # Option: argument with flags starting with '-'
                argument["flags"] = list(arg_args)
                self.options.append(argument)

            return action

        group.add_argument = wrapped_add_argument  # type: ignore[method-assign]
        return group

    def add_argument(self, *args: Any, **kwargs: Any) -> argparse.Action:
        action = super().add_argument(*args, **kwargs)
        argument: dict[str, Any] = {key: kwargs[key] for key in kwargs}

        # Positional: argument with only one name not starting with '-' provided as
        # positional argument to method -or- no name and only a 'dest=' argument
        if len(args) == 0 or (len(args) == 1 and isinstance(args[0], str) and not args[0].startswith("-")):
            argument["name"] = args[0] if (len(args) > 0) else argument["dest"]
            self.positionals.append(argument)
            return action

        # Option: argument with one or more flags starting with '-' provided as
        # positional arguments to method
        argument["flags"] = list(args)
        self.options.append(argument)
        return action

    def format_usage(self) -> str:
        # Use user-defined usage message
        if "usage" in self.program:
            prefix = "Usage: "
            wrapper = textwrap.TextWrapper(width=self.width)
            wrapper.initial_indent = prefix
            wrapper.subsequent_indent = len(prefix) * " "
            if self.program["usage"] == "" or str.isspace(self.program["usage"]):
                return wrapper.fill("No usage information available")
            return wrapper.fill(self.program["usage"])

        # Generate usage message from known arguments
        output: list[str] = []

        # Determine what to display left and right, determine string length for left
        # and right
        left1: str = "Usage: "
        left2: str = (
            self.program["prog"]
            if ("prog" in self.program and self.program["prog"] != "" and not str.isspace(self.program["prog"]))
            else os.path.basename(sys.argv[0])
            if (len(sys.argv[0]) > 0 and sys.argv[0] != "" and not str.isspace(sys.argv[0]))
            else "script.py"
        )
        llen: int = len(left1) + len(left2)
        arglist: list[str] = []
        for option in self.options:
            # arglist += [ "[%s]" % item if ("action" in option and (option["action"] == "store_true"
            # or option["action"] == "store_false")) else "[%s %s]" % (item, option["metavar"])
            # if ("metavar" in option) else "[%s %s]" % (item, option["dest"].upper())
            # if ("dest" in option) else "[%s]" % item for item in option["flags"] ]
            flags = str.join("|", option["flags"])
            arglist += [
                f"[{flags}]"
                if ("action" in option and (option["action"] == "store_true" or option["action"] == "store_false"))
                else f"[{flags} {option['metavar']}]"
                if ("metavar" in option)
                else f"[{flags} {option['dest'].upper()}]"
                if ("dest" in option)
                else f"[{flags}]"
            ]
        for positional in self.positionals:
            arglist += [f"{positional['metavar']}" if ("metavar" in positional) else f"{positional['name']}"]
        right: str = str.join(" ", arglist)
        # rlen: int = len(right)

        # Determine width for left and right parts based on string lengths, define
        # output template. Limit width of left part to a maximum of self.width / 2.
        # Use max() to prevent negative values. -1: trailing space (spacing between
        # left and right parts), see template
        lwidth: int = llen
        rwidth: int = max(0, self.width - lwidth - 1)
        if lwidth > int(self.width / 2) - 1:
            lwidth = max(0, int(self.width / 2) - 1)
            rwidth = int(self.width / 2)
        # outtmp = "%-" + str(lwidth) + "s %-" + str(rwidth) + "s"
        outtmp: str = "%-" + str(lwidth) + "s %s"

        # Wrap text for left and right parts, split into separate lines
        wrapper = textwrap.TextWrapper(width=lwidth)
        wrapper.initial_indent = left1
        wrapper.subsequent_indent = len(left1) * " "
        left: list[str] = wrapper.wrap(left2)
        wrapper = textwrap.TextWrapper(width=rwidth)
        right_wrapped: list[str] = wrapper.wrap(right)

        # Add usage message to output
        for i in range(0, max(len(left), len(right_wrapped))):
            left_: str = left[i] if (i < len(left)) else ""
            right_: str = right_wrapped[i] if (i < len(right_wrapped)) else ""
            output.append(outtmp % (left_, right_))

        # Return output as single string
        return str.join("\n", output)

    def _format_argument_left(self, argument: dict[str, Any]) -> str:
        """Format the left side (flags/name) of an argument."""
        if "flags" in argument:  # Option
            if "action" in argument and (argument["action"] == "store_true" or argument["action"] == "store_false"):
                return str.join(", ", argument["flags"])
            return str.join(
                ", ",
                [
                    f"{item} {argument['metavar']}"
                    if ("metavar" in argument)
                    else f"{item} {argument['dest'].upper()}"
                    if ("dest" in argument)
                    else item
                    for item in argument["flags"]
                ],
            )
        # Positional
        return argument["metavar"] if ("metavar" in argument) else argument["name"]

    def _format_argument_right(self, argument: dict[str, Any]) -> str:
        """Format the right side (help text) of an argument."""
        right = ""
        if "help" in argument and argument["help"] != "" and not str.isspace(argument["help"]):
            right += argument["help"]
        else:
            right += "No help available"
        if "choices" in argument and len(argument["choices"]) > 0:
            right += " (choices: {})".format(
                str.join(", ", (f"'{item}'" if isinstance(item, str) else str(item) for item in argument["choices"]))
            )
        if "default" in argument and argument["default"] != argparse.SUPPRESS:
            default_value = (
                f"'{argument['default']}'" if isinstance(argument["default"], str) else str(argument["default"])
            )
            right += f" (default: {default_value})"
        return right

    def _prepare_arguments_for_display(self) -> tuple[int, int]:
        """Prepare all arguments with left/right formatting and return max lengths."""
        lmaxlen = 0
        rmaxlen = 0
        for argument in self.positionals + self.options:
            argument["left"] = self._format_argument_left(argument)
            argument["right"] = self._format_argument_right(argument)
            lmaxlen = max(lmaxlen, len(argument["left"]))
            rmaxlen = max(rmaxlen, len(argument["right"]))
        return lmaxlen, rmaxlen

    def _wrap_arguments(self, lwidth: int, rwidth: int) -> None:
        """Wrap argument text to fit within specified widths."""
        lwrapper = textwrap.TextWrapper(width=lwidth)
        rwrapper = textwrap.TextWrapper(width=rwidth)
        for argument in self.positionals + self.options:
            argument["left"] = lwrapper.wrap(argument["left"])
            right_lines: list[str] = []
            for line in argument["right"].split("\n"):
                if line:
                    right_lines.extend(rwrapper.wrap(line))
                else:
                    right_lines.append("")
            argument["right"] = right_lines

    def _add_arguments_to_output(
        self, output: list[str], arguments: list[dict[str, Any]], title: str, outtmp: str
    ) -> None:
        """Add formatted arguments to output list."""
        if len(arguments) > 0:
            output.append("")
            output.append(title)
            for argument in arguments:
                for i in range(0, max(len(argument["left"]), len(argument["right"]))):
                    left = argument["left"][i] if (i < len(argument["left"])) else ""
                    right = argument["right"][i] if (i < len(argument["right"])) else ""
                    output.append(outtmp % (left, right))

    def format_help(self) -> str:
        output: list[str] = []
        dewrapper = textwrap.TextWrapper(width=self.width)

        # Add usage message
        output.append(self.format_usage())

        # Add description if present
        if (
            "description" in self.program
            and self.program["description"] != ""
            and not str.isspace(self.program["description"])
        ):
            output.append("")
            output.append(dewrapper.fill(self.program["description"]))

        # Prepare arguments and calculate widths
        lmaxlen, rmaxlen = self._prepare_arguments_for_display()
        lwidth = lmaxlen
        rwidth = max(0, self.width - lwidth - 4)
        if lwidth > int(self.width / 2) - 4:
            lwidth = max(0, int(self.width / 2) - 4)
            rwidth = int(self.width / 2)
        outtmp = "  %-" + str(lwidth) + "s  %s"

        # Wrap text for display
        self._wrap_arguments(lwidth, rwidth)

        # Add arguments to output
        self._add_arguments_to_output(output, self.positionals, "Positionals:", outtmp)
        self._add_arguments_to_output(output, self.options, "Options:", outtmp)

        # Add epilog if present
        if "epilog" in self.program and self.program["epilog"] != "" and not str.isspace(self.program["epilog"]):
            output.append("")
            for line in self.program["epilog"].split("\n"):
                if line:
                    output.append(dewrapper.fill(line))
                else:
                    output.append("")

        return str.join("\n", output)

    # Method redefined as format_usage() does not return a trailing newline like
    # the original does
    def print_usage(self, file: SupportsWrite[str] | None = None) -> None:
        if file is None:
            file = sys.stdout
        file.write(self.format_usage() + "\n")
        # file.flush()

    # Method redefined as format_help() does not return a trailing newline like
    # the original does
    def print_help(self, file: SupportsWrite[str] | None = None) -> None:
        if file is None:
            file = sys.stdout
        file.write(self.format_help() + "\n")
        # file.flush()

    def error(self, message: str) -> Never:
        sys.stderr.write(self.format_usage() + "\n")
        sys.stderr.write((f"Error: {message}") + "\n")
        sys.exit(2)


# -------------------------------------
#                                     -
#  Demo                               -
#                                     -
# -------------------------------------

# Demonstrate module usage and features if run directly
if __name__ == "__main__":
    # Create CustomArgumentParser
    parser = CustomArgumentParser(
        description="Description message displayed after usage and before positional arguments and options.\n"
        "Can be used to describe the application in a short summary. Optional, omitted if empty.",
        epilog="Epilog message displayed at the bottom after everything else. "
        "Can be used to provide additional information, e.g. license, contact details, copyright etc. Optional, "
        "omitted if empty.",
        argument_default=argparse.SUPPRESS,
        allow_abbrev=False,
        add_help=False,
    )

    # Add options
    parser.add_argument(
        "-c", "--config-file", action="store", dest="config_file", metavar="FILE", type=str, default="config.ini"
    )
    parser.add_argument(
        "-d",
        "--database-file",
        action="store",
        dest="database_file",
        metavar="file",
        type=str,
        help="SQLite3 database file to read/write",
        default="database.db",
    )
    parser.add_argument(
        "-l",
        "--log-file",
        action="store",
        dest="log_file",
        metavar="file",
        type=str,
        help="File to write log to",
        default="debug.log",
    )
    parser.add_argument(
        "-t", "--threads", action="store", dest="threads", type=int, help="Number of threads to spawn", default=3
    )
    parser.add_argument(
        "-p",
        "--port",
        action="store",
        dest="port",
        type=int,
        help="TCP port to listen on for access to the web interface",
        choices=[80, 8080, 8081],
        default=8080,
    )
    parser.add_argument(
        "--max-downloads",
        action="store",
        dest="max_downloads",
        metavar="value",
        type=int,
        help="Maximum number of concurrent downloads",
        default=5,
    )
    parser.add_argument(
        "--download-timeout",
        action="store",
        dest="download_timeout",
        metavar="value",
        type=int,
        help="Download timeout in seconds",
        default=120,
    )
    parser.add_argument(
        "--max-requests",
        action="store",
        dest="max_requests",
        metavar="value",
        type=int,
        help="Maximum number of concurrent requests",
        default=10,
    )
    parser.add_argument(
        "--request-timeout",
        action="store",
        dest="request_timeout",
        metavar="value",
        type=int,
        help="Request timeout in seconds",
        default=60,
    )
    parser.add_argument(
        "--output-facility",
        action="store",
        dest="output_facility",
        metavar="value",
        type=str.lower,
        choices=["stdout", "stderr"],
        help="Output facility to use for console output",
        default="stdout",
    )
    parser.add_argument(
        "--log-level",
        action="store",
        dest="log_level",
        metavar="VALUE",
        type=str.lower,
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level to use",
        default="info",
    )
    parser.add_argument(
        "--use-color",
        action="store",
        dest="use_color",
        metavar="value",
        type=bool,
        help="Colorize console output",
        default=True,
    )
    parser.add_argument("--log-template", action="store", dest="log_template", metavar="value", type=str)
    parser.add_argument(
        "-s",
        "--some-option",
        action="store",
        dest="some_option",
        metavar="VALUE",
        type=str,
        help="Some fancy option with miscellaneous choices",
        choices=[123, "foobar", False],
    )
    parser.add_argument("-h", "--help", action="help", help="Display this message")

    # Add positionals
    parser.add_argument("input_url", action="store", metavar="URL", type=str, help="URL to download from")
    parser.add_argument("output_file", action="store", metavar="DEST", type=str, help="File to save download as")

    # Parse command line
    args = parser.parse_args()
