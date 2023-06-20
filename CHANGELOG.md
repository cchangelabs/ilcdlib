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
