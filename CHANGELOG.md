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
