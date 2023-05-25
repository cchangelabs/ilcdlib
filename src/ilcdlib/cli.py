#
#  Copyright 2023 by C Change Labs Inc. www.c-change-labs.com
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  This software was developed with support from the Skanska USA,
#  Charles Pankow Foundation, Microsoft Sustainability Fund, Interface, MKA Foundation, and others.
#  Find out more at www.BuildingTransparency.org
#
import argparse
import sys

from cli_rack import CLI
from cli_rack.modular import CliAppManager, CliExtension

from ilcdlib import __version__


class VersionCliExtension(CliExtension):
    COMMAND_NAME = "version"
    COMMAND_DESCRIPTION = "Prints application version"

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--short",
            "-s",
            dest="short",
            action="store_true",
            default=False,
            required=False,
            help="Print short version",
        )

    def handle(self, args: argparse.Namespace):
        if args.short:
            CLI.print_info(f"{__version__.VERSION}")
        else:
            CLI.print_info(f"Version: {__version__.VERSION}")
            # CLI.print_info(f"Build: {__version__.BUILD_NUMBER}")
            # CLI.print_info(f"Build Date: {__version__.BUILD_DATE}")
            # CLI.print_info(f"VCS ID: {__version__.VCS_ID}")


def main(argv: list[str]):
    CLI.setup()
    app_manager = CliAppManager(
        "ilcdtool",
        description="CLI tool for ILCD data manipulation",
        epilog=f"ILCD Tool is an open-source developed and maintained by BuildingTransparency.org.\n"
        f"\nVersion {__version__.VERSION}",
    )
    app_manager.parse_and_handle_global()
    app_manager.register_extension(VersionCliExtension)
    # Temporary declared extension, should be replaced with discovery
    from ilcdlib.epd import cli as epd_cli

    app_manager.register_extension(epd_cli.ConvertEpdCliExtension)
    app_manager.setup()
    try:
        # Parse arguments
        parsed_commands = app_manager.parse(argv)
        if len(parsed_commands) == 1 and parsed_commands[0].cmd is None:
            app_manager.args_parser.print_help()
            CLI.fail("At least one command is required", 7)
        # Run
        exec_manager = app_manager.create_execution_manager()
        exec_manager.run(parsed_commands)
    except Exception as e:
        CLI.print_error(e)


def entrypoint():
    main(sys.argv[1:])


if __name__ == "__main__":
    entrypoint()
