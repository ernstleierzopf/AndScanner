# AndScanner

This repository is a fork of the project [chicharitomu14/AndScanner](https://github.com/chicharitomu14/AndScanner).  
The initial project was created as a tool for the paper “Large-scale Security Measurements on the Android Firmware Ecosystem” in ICSE2022.

Changes in this Fork:
- Repaired dependencies
- Automatically checks API level and uses appropriate image extractor

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

### Image Extraction and Analysis

To scan and analyze an image:
```shell
$ python3 scan.py "path/to/image.zip" "android-api-level"
```
`scan.py` takes 2 arguments:
1. Path to the image file
2. Android API level of the image

To only extract the image run:
```shell
$ python3 scan.py "path/to/image.zip" "android-api-level" --extract
```

To only run analysis on the extracted image run:
```shell
$ python3 scan.py "path/to/image.zip" "android-api-level" --scan
```

___

## Project Structure

- ROM Parser: ./romanalyzer_extractor
- Patch Analyzer: ./romanalyzer_patch
- App Analyzer: ./static/androguard-3.3.6

## Limitations

~~- Only supports images up to Android API level 30~~ supports images up to API level 34
