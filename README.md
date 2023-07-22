# ILCD Lib

<p align="center">
<a href="https://pypi.org/project/ilcdlib/"><img src="https://img.shields.io/pypi/l/ilcdlib?style=for-the-badge" title="License: Apache-2"/></a> 
<a href="https://pypi.org/project/ilcdlib/"><img src="https://img.shields.io/pypi/pyversions/ilcdlib?style=for-the-badge" title="Python Versions"/></a> 
<a href="https://github.com/psf/black/"><img src="https://img.shields.io/badge/Code%20Style-black-black?style=for-the-badge" title="Code style: black"/></a> 
<a href="https://pypi.org/project/ilcdlib/"><img src="https://img.shields.io/pypi/v/ilcdlib?style=for-the-badge" title="PyPy Version"/></a> 
<a href="https://pypi.org/project/ilcdlib/"><img src="https://img.shields.io/pypi/dm/ilcdlib?style=for-the-badge" title="PyPy Downloads"/></a> 
<br>
<a href="https://github.com/cchangelabs/ilcdlib/actions/workflows/sanity-check.yml"><img src="https://img.shields.io/github/actions/workflow/status/cchangelabs/ilcdlib/sanity-check.yml?style=for-the-badge" title="Build Status"/></a> 
<a href="https://github.com/cchangelabs/ilcdlib/"><img src="https://img.shields.io/github/last-commit/cchangelabs/ilcdlib?style=for-the-badge" title="Last Commit"/></a> 
<a href="https://github.com/cchangelabs/ilcdlib/releases/"><img src="https://img.shields.io/github/release-date/cchangelabs/ilcdlib?style=for-the-badge" title="Last Release"/></a> 
<a href="https://github.com/cchangelabs/ilcdlib/releases/"><img src="https://img.shields.io/github/v/release/cchangelabs/ilcdlib?style=for-the-badge" title="Recent Version"></a> 
</p>

Python library providing parsing capabilities for ILCD XML files.

## Installation

Install the library from PyPi. The following command will install the library with all optional dependencies:

```bash
pip install "ilcdlib[lxml,cli]"
```

If you don't need CLI tool, you can omit `cli` extra. The following extras are available:

* `lxml` - install lxml library for faster XML parsing
* `cli` - install CLI tool so it could be used from command line via `ilcdtool` command.

## Usage

**❗ ATTENTION**: Pick the right version. There are 2 versions of the library available:

* Use version **below** `2.0.0` if your project uses Pydantic version below `2.0.0`
* Use version `2.x.x` or higher if your project uses Pydantic version `2.0.0` or above

Branch 1.x.x is not maintained anymore, so if you don't use pydantic 2.x.x should be your choice.

### CLI

At the moment the primary function of the CLI tool is to convert ILCD XML files to openEPD (json) format. 

Here is a simple example of how to use it to convert ILCD archive to openEPD format:

```bash
ilcdtool --debug convert-epd -i ilcd+epd -o openEPD "<path/to/archive.zip>"
```

It is also possible to point the tool to the http endpoint instead. At the moment Soda4Lca web UI and api endpoints
are supported.

```bash
ilcdtool convert-epd -i ilcd+epd -o openEPD "https://oekobaudat.de/OEKOBAU.DAT/datasetdetail/process.xhtml?uuid=ee8863aa-7276-4896-b07a-713937a3134d&version=00.00.018&stock=OBD_2021_II&lang=en"
```

Another important feature is the ability to specify a **dialect**. Dialect is a set of rules that define how the handle
provider specific data. It is useful for the cases when provider does not follow the standard or standard is not strict
enough the provider has a multiple options how to persist the data.

```bash
convert-epd -i ilcd+epd -o openEPD -d environdec https://data.environdec.com/showProcess.xhtml?uuid=bfeb8678-b3cb-4a5b-b8cb-2512b551ad17&version=01.00.001&stock=Environdata
```

CLI tool provides comprehensive help for each of the supported commands. Use `ilcdtool --help` to get the list of the 
supported commands and a set of global parameters. And use `ilcdtool <command> --help` to get help for the specific
command.

### Use in Python code

There are 3 primary concepts in the library:

1. `Medium` is a way how application reads ILCD XML data. It could be a zip file, some http API or anything else. 
1. `IlcdXmlReader` is a class that reads ILCD XML data from the medium and provides a set of methods to access the data.
1. `Dialects` are just a subclasses of corresponding readers which override data extraction logic for some of 
the fields.

So very basic usage of the library would look like this:

```python
from ilcdlib.epd.reader import IlcdEpdReader
from ilcdlib.medium.archive import ZipIlcdReader

lang = ["en", None] # Means "en" or any available language

# Create a medium capable to read data from the zip archive
zip_reader = ZipIlcdReader("<path/to/archive.zip>")
# Create a reader that will read data from the given medium and passing the target object to read 
# (identified by id and version)
epd_reader = IlcdEpdReader(
    "2eb43850-0ab2-4068-afe5-218d69a096f8",
    "00.01.000",
    zip_reader,
)

print(epd_reader.get_product_name(lang))    # Extract product name
print(epd_reader.get_declared_unit())       # Extract declared unit  

# Convert to openEPD format
print(epd_reader.to_openepd_epd(lang).json(indent=2))
```

## For Library Maintainers

Maintainer's Guide is available [here](doc/dev-guide.md).

# Credits

This library has been written and maintained by [C-Change Labs](https://c-change-labs.com/).

# License

This library is licensed under [Apache 2](/LICENSE). This means you are free to use it in commercial projects.
