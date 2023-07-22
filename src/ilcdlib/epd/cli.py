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
from cli_rack.utils import ensure_dir
from openepd.model.epd import Epd

from ilcdlib.epd.factory import EpdReaderFactory
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.medium.archive import ZipIlcdReader
from ilcdlib.medium.soda4lca import Soda4LcaZipReader

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
            "--dialect",
            "-d",
            dest="dialect",
            type=str,
            help="Dialect of the ILCD to use while reading the input document, e.g. `Environdec`, `oekobau.dat`, `ibu`",
            required=False,
            default=None,
        )
        parser.add_argument(
            "--save",
            "-s",
            dest="save",
            action="store_true",
            help="Preserve the source document downloaded from remote location as well as the output.",
            required=False,
            default=False,
        )
        parser.add_argument(
            "--target-dir",
            "-t",
            dest="target_dir",
            type=str,
            help="Target directory to save the output document. If not specified the current directory will be used.",
            required=False,
            default=None,
        )
        parser.add_argument(
            "--extract-pdf",
            "-e",
            dest="extract_pdf",
            action="store_true",
            help="If possible extract PDF file from the input document and save it as a separate file.",
            required=False,
            default=False,
        )
        parser.add_argument(
            "--provider-domain",
            dest="provider_domain",
            type=str,
            help="Domain name of the provider to be used in alt_ids as a key.",
            required=False,
            default=None,
        )
        parser.add_argument(
            "doc",
            metavar="doc",
            type=str,
            nargs="+",
            help="Reference to the input document. Can be a file path or URL "
            "depending on supported converter capabilities.",
        )

    def handle(self, args: argparse.Namespace):
        in_format: str = args.in_format
        out_format: str = args.out_format
        doc_refs: list[str] = args.doc
        lang: str | None = args.lang
        dialect: str | None = args.dialect
        save: bool = args.save
        extract_pdf: bool = args.extract_pdf
        target_dir: Path = Path(args.target_dir) if args.target_dir is not None else Path.cwd()
        provider_domain: str | None = args.provider_domain
        if in_format.lower() != "ilcd+epd":
            CLI.fail(f"Input format {in_format} is not supported.", 1)
        if out_format.lower() != "openepd":
            CLI.fail(f"Output format {out_format} is not supported.", 1)
        if in_format.lower() == out_format.lower():
            CLI.fail(f"Input format {in_format} and output format {out_format} are the same.", 1)
        if extract_pdf and not save:
            CLI.fail("Extracting PDF requires saving the input document. Consider adding -s flag", 1)
        if target_dir.is_file():
            CLI.fail(f"Target directory {target_dir} is a file. It must be either dir or nor existing path.", 1)
        epd_reader_factory = EpdReaderFactory()
        if dialect is not None and not epd_reader_factory.is_dialect_supported(dialect):
            CLI.fail(f"Dialect {dialect} is not supported.", 3)
        for doc in doc_refs:
            self.process_single_doc(
                doc,
                epd_reader_factory,
                dialect=dialect,
                extract_pdf=extract_pdf,
                in_format=in_format,
                lang=lang,
                out_format=out_format,
                save=save,
                target_dir=target_dir,
                provider_domain=provider_domain,
            )

    def process_single_doc(
        self,
        doc_ref: str,
        epd_reader_factory: EpdReaderFactory,
        *,
        dialect: str | None,
        in_format: str,
        out_format: str,
        lang: str | None = None,
        extract_pdf: bool = False,
        save: bool = False,
        target_dir: Path | None = None,
        provider_domain: str | None = None,
    ) -> None:
        CLI.print_info(f"Converting document {doc_ref} from {in_format} to {out_format}.")
        reader_cls, dialect = (
            (epd_reader_factory.get_reader_class(dialect), dialect)
            if dialect
            else epd_reader_factory.autodiscover_by_url(doc_ref)
        )
        CLI.print_info("Effective dialect: " + (dialect if dialect is not None else "Generic"))
        medium = Soda4LcaZipReader(doc_ref) if doc_ref.startswith("http") else ZipIlcdReader(Path(doc_ref))
        epd_reader = reader_cls(None, None, medium)
        supported_langs = epd_reader.get_supported_langs()
        if len(supported_langs) == 0:
            CLI.fail(f"Input document {doc_ref} Doesn't seem to be correct. No language information detected.", 4)
        prioritize_english = False
        if lang is None:
            prioritize_english = "en" in supported_langs and "en" != supported_langs[0]
            lang = supported_langs[0]
        elif lang.lower() not in supported_langs:
            CLI.fail(
                f"Language {lang} is not supported by the input document. "
                f"Supported languages are: {supported_langs}",
                4,
            )
        lang_list = [lang, None]
        if prioritize_english:
            lang_list.insert(0, "en")
        CLI.print_info("Language priority: " + ",".join([x if x is not None else "any other" for x in lang_list]))
        base_url = self.__extract_base_url(doc_ref)
        open_epd = epd_reader.to_openepd_epd(lang_list, base_url=base_url, provider_domain=provider_domain)
        CLI.print_data(open_epd.model_dump_json(indent=2, exclude_none=True, exclude_unset=True))
        if save:
            self.save_results(epd_reader, open_epd, extract_pdf=extract_pdf, base_dir=target_dir)

    def save_results(
        self, epd_reader: IlcdEpdReader, result: Epd, *, extract_pdf: bool = False, base_dir: Path | None = None
    ):
        if base_dir is None:
            base_dir = Path.cwd()
        output_dir = base_dir / Path(epd_reader.get_uuid())
        ensure_dir(output_dir)
        with open(output_dir / "openEPD.json", "w") as f:
            f.write(result.model_dump_json(indent=2, exclude_none=True, exclude_unset=True))
        if isinstance(epd_reader.data_provider, ZipIlcdReader):
            epd_reader.data_provider.save_to(output_dir / "ilcd_epd.zip")
        if extract_pdf:
            # EPD Pdf
            pdf_stream = epd_reader.get_epd_document_stream()
            if pdf_stream is None and isinstance(epd_reader.data_provider, Soda4LcaZipReader):
                try:
                    pdf_stream = epd_reader.data_provider.download_pdf()
                except ValueError:
                    pdf_stream = None
            if pdf_stream is not None:
                with open(output_dir / "original.pdf", "wb") as f, pdf_stream:
                    f.write(pdf_stream.read())
            # PCR PDF
            pcr_reader = epd_reader.get_pcr_reader()
            if pcr_reader:
                pdf_stream = pcr_reader.get_digital_file_stream()
                if pdf_stream:
                    with open(output_dir / "pcr.pdf", "wb") as f, pdf_stream:
                        f.write(pdf_stream.read())
        CLI.print_info("Output saved to " + str(output_dir.absolute()))

    def __extract_base_url(self, doc_ref: str) -> str | None:
        if doc_ref.startswith("http"):
            if "/datasetdetail/" in doc_ref:
                return doc_ref.split("/datasetdetail/", 1)[0]
            elif "/resource/" in doc_ref:
                return doc_ref.split("/resource/", 1)[0]
            elif "/showProcess.xhtml" in doc_ref:
                return doc_ref.split("/showProcess.xhtml", 1)[0]
            return None
        else:
            return None
