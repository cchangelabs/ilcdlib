#!/usr/bin/env python3
#
#  Copyright 2024 by C Change Labs Inc. www.c-change-labs.com
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
import csv
from pathlib import Path
import shutil
import sys

from cli_rack import CLI
from cli_rack.utils import ensure_dir, run_bash, run_executable

BATCH_SIZE = 5

F_GROUP = "Group"
F_STANDARD = "Standard"
F_COMMENT = "Comment"
F_UUID = "UUID"
F_URL = "Url"
F_DATASET_TYPE = "Dataset Type"
CSV_FIELDS = (F_GROUP, F_STANDARD, F_DATASET_TYPE, F_COMMENT, F_UUID, F_URL)


def run_ilcd_conversion(links: list[str], target_dir: Path, provider_domain: str | None = None):
    params = ["ilcdtool", "convert-epd", "-s", "-t", str(target_dir), "-e", "-i", "ilcd+epd", "-o", "openEPD"]
    if provider_domain is not None:
        params += ["--provider-domain", provider_domain]
    params += links
    p = run_executable(*params, hide_output=True, mute_output=False)
    if p.returncode != 0:
        CLI.fail("Failed to run ilcdtool: \n" + str(p.stderr), 1)


def process_batch(inputs: list[str], batch_num: int, target_dir: Path, provider_domain: str | None = None):
    CLI.print_info(f"Processing batch #{batch_num}: ")
    CLI.print_info("\n".join([f"\t{x}" for x in inputs]))
    run_ilcd_conversion(inputs, target_dir, provider_domain)
    CLI.print_info(f"Batch #{batch_num} processed\n")


def run(args: list[str]):
    CLI.setup()
    input_file, target_dir, provider_domain = Path(args[0]), Path(args[1]), None
    provider_domain: str | None = args[2] if len(args) > 2 else None
    if not input_file.is_file():
        CLI.fail("Input file does not exist: " + str(input_file), 1)
    if target_dir.is_file():
        CLI.fail("Target directory be the directory, not a file: " + str(target_dir), 1)
    if target_dir.is_dir():
        shutil.rmtree(target_dir)
    ensure_dir(target_dir)
    CLI.print_info("Running batch conversion for input file: " + str(input_file))
    with open(args[0], newline="") as csvfile:
        csv_reader = csv.DictReader(csvfile, CSV_FIELDS)
        csvfile.readline()  # Skip header
        inputs = []
        batch_num = 1
        for row in csv_reader:
            inputs.append(row[F_URL])
            if not row[F_URL]:
                continue
            if csv_reader.line_num % BATCH_SIZE == 0:
                process_batch(inputs, batch_num, target_dir, provider_domain)
                inputs = []
                batch_num += 1
        if len(inputs) > 0:
            process_batch(inputs, batch_num, target_dir, provider_domain)


if __name__ == "__main__":
    run(sys.argv[1:])
