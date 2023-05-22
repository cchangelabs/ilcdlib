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
from pathlib import Path

from cli_rack import CLI
from cli_rack.modular import CliExtension

from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.medium.archive import ZipIlcdReader

SUPPORTED_INPUT_FORMATS = ("ilcd+epd",)
SUPPORTED_OUTPUT_FORMATS = ("openEPD",)


class ConvertEpdCliExtension(CliExtension):
    COMMAND_NAME = "convert-epd"
    COMMAND_DESCRIPTION = "Converts EPD documents between formats"

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--in-format",
            "-i",
            dest="in_format",
            type=str,
            help="Input format",
            required=True,
            choices=SUPPORTED_INPUT_FORMATS,
        )
        parser.add_argument(
            "--out-format",
            "-o",
            dest="out_format",
            type=str,
            help="Output format",
            required=True,
            choices=SUPPORTED_OUTPUT_FORMATS,
        )
        parser.add_argument(
            "--lang",
            "-l",
            dest="lang",
            type=str,
            help="Language code to use while reading the input document. Some of the fields doesn't have the value "
            "in this language any available value will be used.",
            required=False,
            default=None,
        )
        parser.add_argument(
            "doc",
            metavar="doc",
            type=str,
            help="Reference to the input document. Can be a file path or URL "
            "depending on supported converter capabilities.",
        )

    def handle(self, args: argparse.Namespace):
        in_format: str = args.in_format
        out_format: str = args.out_format
        doc_ref: str = args.doc
        lang: str | None = args.lang
        if in_format.lower() != "ilcd+epd":
            CLI.fail(f"Input format {in_format} is not supported.", 1)
        if out_format.lower() != "openepd":
            CLI.fail(f"Output format {out_format} is not supported.", 1)
        if in_format.lower() == out_format.lower():
            CLI.fail(f"Input format {in_format} and output format {out_format} are the same.", 1)
        if not doc_ref.endswith(".zip"):
            CLI.fail(f"Input document {doc_ref} is not a zip file.", 2)
        CLI.print_info(f"Converting document {doc_ref} from {in_format} to {out_format}.")
        epd_reader = IlcdEpdReader(None, None, ZipIlcdReader(Path(doc_ref)))
        supported_langs = epd_reader.get_supported_langs()
        if len(supported_langs) == 0:
            CLI.fail(f"Input document {doc_ref} Doesn't seem to be correct. No language information detected.", 3)
        if lang is None:
            lang = supported_langs[0]
        elif lang.lower() not in supported_langs:
            CLI.fail(
                f"Language {lang} is not supported by the input document. "
                f"Supported languages are: {supported_langs}",
                4,
            )
        open_epd = epd_reader.to_openepd_epd([lang, None])
        CLI.print_data(open_epd.json(indent=2))
