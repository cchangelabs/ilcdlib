## 4.11.3 (2024-09-27)

### Fix

- resolve typing issues
- adjust condition to remove deprecation warning

## 4.11.2 (2024-09-16)

### Fix

- typo in Readme

## 4.11.1 (2024-09-13)

### Fix

- add support for openEPD 6.0.0: moved specs

## 4.11.0 (2024-08-01)

### Feat

- extract mass
- add generic estimates support
- **denmark**: extract correct language code

## 4.10.0 (2024-07-24)

### Feat

- **epd**: integrate EPD Denmark
- add datastock argument support while searching for processes

## 4.9.0 (2024-06-05)

### Feat

- **epd**: update gwp mapping regex

## 4.8.0 (2024-05-31)

### Feat

- **impacts**: improve gwp-biogenic search
- **epd**: replace extra text for pcr

## 4.7.0 (2024-05-24)

### Feat

- **epd-norge**: extract correct EPD Norge developer
- **epd-norge**: overwrite third party name

## 4.6.0 (2024-05-17)

### Feat

- **epdnorge**: add support for Norge EPDs

## 4.5.0 (2024-05-02)

### Feat

- update ref retriever logic

## 4.4.0 (2024-05-02)

### Feat

- improve impact parsing

## 4.3.0 (2024-04-30)

### Feat

- overwrite ITB description
- match impact units during ingestion
- improve impact mapping
- cleanup text after spaces for websites
- handle exception during when retrieving epd links
- **epdnorge**: add epd-norge dialect
- **oekobaudat**: add category mapping support
- add openepd category mapping
- add ITB verifier email

### Fix

- fix http client to respect retry configuration
- **soda4lca**: remove hardcoded classification_system

## 4.2.0 (2024-04-25)

### Feat

- update impact mapper
- implement ITB basic support

## 4.1.0 (2024-04-16)

### Feat

- undo changes which break pydantic v1 compatibility

## 4.0.0 (2024-04-15)

## 2.0.0 (2023-07-22)

### Feat

- migrate to openepd v2

## 3.0.0 (2024-03-29)

### Feat

- add pydantic 2.0+ support


- apply strict linters to the project

## 1.2.2 (2023-10-02)

### Fix

- convert dates to datetime to support updated openepd lib

## 1.2.1 (2023-09-15)

### Fix

- calculate a1a2a3 if none provided

## 1.2.0 (2023-09-01)

### Feat

- add epditaly dialect

### Fix

- ignore compliance records with no name
- delete url trailing spaces in cleanup_website method

### Refactor

- set dialect specific xmlns inside dialect definitions

## 1.1.0 (2023-07-25)

### Feat

- **xml**: add default unit mapping if reference is missing

### Fix

- **environdec**: extract url from newer ILCD documents

## 1.0.0 (2023-07-22)

### Feat

- preserve pydantic v1 support in separate branch

## 0.10.1 (2023-07-20)

### Fix

- don't throw error when referenced file doesn't exist
- validate environdec urls

## 0.10.0 (2023-07-13)

### Feat

- parse categories from soda4lca 4x

## 0.9.0 (2023-07-12)

### Feat

- parse environdec url
- parse xml processes

## 0.8.1 (2023-06-21)

### Fix

- update openepd lib to fix impacts deserialization issue
- **oekobaudat**: remove extra product class

## 0.8.0 (2023-06-20)

### Feat

- add utility function to calculate sha1 by URL

### Fix

- add support for non-standard epd2029 xml namespaces

## 0.7.1 (2023-06-16)

### Fix

- replace datamodel with pydantic

## 0.7.0 (2023-06-15)

### Feat

- update verifiers extracting
- update openEPD generation to match new Org schema

### Fix

- construct mypy objects without bypassing validation
- fix unpacking other_params

## 0.6.0 (2023-06-14)

### Feat

- put link to PDF into attachments for EPD and PCR
- add ilcd dataset type information
- map lcia method for impacts
- add ability to extract PCR PDF if possible
- parse scenarios
- **xml**: add support for compliance property
- add data_entry_by extracting
- add `alt_ids` field support
- **cli**: add `target-dir` argument to CLI
- parse publisher
- parse production region
- parse flows and indicators
- add `is_industry_epd` extension
- add `lca_discussion`, `manufacturing_description`, `product_usage_description`

### Fix

- **cli**: fix pdf downloading while converting via CLI
- fix `ep-terr` impact name in mapper
- **soda4lca**: improve url recognition logic
- correct `product_classes` property
- fix product name definition

### Refactor

- move `epd_developer` and `epd_publisher` under `ec3` extensions
- use openEPD extension class instead plain dict
- add extra more generic method for reading process comment
- generalize base scope set reader logic
- move oekobaudat specific logic into dialect

## 0.5.0 (2023-06-01)

### Feat

- **soda4lca**: add `search processes` method to soda4lca client
- **soda4lca**: add `download pdf` method to soda4lca client
- **soda4lca**: add `export to zip` method to soda4lca client
- **soda4lca**: add `get category list` method to soda4lca client
- add base api client

### Fix

- **openepd**: add links to declaration and pdf
- **soda4lca**: add error handling for processes with missing PDFs

### Refactor

- **soda4lca**: rename common http module

## 0.4.0 (2023-05-30)

### Feat

- extract all available product flow properties
- **cli**: automatically detect the dialect basing on the input url
- add bulk processing to cli tool

### Fix

- handle `-` unit properly
- fix phone number sanitizing logic
- preserve address of the contact
- **cli**: extract base url from the doc_ref if possible

## 0.3.0 (2023-05-29)

### Feat

- add ability to extract and safe pdf document (epd format extension 2019)
- extend CLI with ability to preserve input and output on the file system
- add ILCD material properties to openEPD object
- generate openEPD attachments
- add basic impacts extraction support
- add basic mapping layer

### Fix

- preserve unknown classification
- add extrac mapping for `kgSO2e` unit
- remove `ExternalIdentification` model
- add mapping for CFC11e
- add typing marker

## 0.2.2 (2023-05-25)

### Fix

- upgrade openepd library
- fix dependency name

## 0.2.1 (2023-05-24)

### Fix

- add release openepd as a dependency

## 0.2.0 (2023-05-24)

### Feat

- add Oekobaudat dialect
- add Indata dialect
- add MatML reader
- add soda4lca zip import
- add declared unit support
- add pcr support
- add dialect support
- add cli tool
- add basic EPD reader
- add contact reader
- add reader for ILCD contact dataset
- add ILCD zip archive reader

### Fix

- fix unit test
- add quantitative properties to product name if any
