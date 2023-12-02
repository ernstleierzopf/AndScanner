# AndScanner

This repository is a fork of the project [chicharitomu14/AndScanner](https://github.com/chicharitomu14/AndScanner).  
The initial project was created as a tool for the paper “Large-scale Security Measurements on the Android Firmware Ecosystem” in ICSE2022.

Changes in this Fork:
- Repaired dependencies
- Automatically checks API level and uses appropriate image extractor
- Added Batch Scan functionality

___

## Setup

### Requirements

- Python 3.9 ~ 3.11

### Creating Virtual Environment

1. `cd` into the AndScanner root directory

2. Create a virtual environment named `venv`:
    ```shell
    $ python3.11 -m venv venv
    ```

3. Activate the virtual environment:
    ```shell
    $ source venv/bin/activate
    ```

4. Install all the dependencies in requirement.txt in the virtual environment:
    ```shell
    $ python -m pip install -r requirements.txt
    ```

___

## Scanning Images

#### Activate the Virtual Environment

Before starting a scan, activate the virtual environment:
```shell
$ source venv/bin/activate
```

To deactivate the virtual environment after the scans:
```shell
$ deactivate
```

### Single Scan

To scan a single image:
```shell
$ python3 scan.py "path/to/image.zip" "vendor-name" "android-api-level"
```
`scan.py` takes 3 arguments:
1. Path to the image file
2. Name of the image vendor
3. Android API level of the image

### Batch Scan

Instead of scanning individual images, you can consolidate the paths, vendor names, and Android API levels of multiple images into a JSON file.

JSON file format:
```json
[
  {
    "path": "path/to/image/foo.zip",
    "vendor": "vendor foo",
    "api-level": 30
  },
  {
    "path": "path/to/image/bar.zip",
    "vendor": "vendor bar",
    "api-level": 28
  }
]
```

To run a batch scan:
```shell
$ python3 scan.py path/to/the/file.json
```

___

## Project Structure

- ROM Parser: ./romanalyzer_extractor
- Patch Analyzer: ./romanalyzer_patch
- App Analyzer: ./static/androguard-3.3.6

## Limitations

- Only supports images up to Android API level 30

## Images and build.prop Files

Images can be found at the following sources.
Android Dumps provides a wide variety of images and accompanying `build.prop` files.

| Vendor        | Download Source                              |
|---------------|----------------------------------------------|
| Google        | https://developers.google.com/android/images |
| Android Dumps | https://dumps.tadiphone.dev/dumps            |
