import json
import os
import urllib.request
import shutil
from selenium.webdriver.chrome.options import Options
from firmware_images.scrapers.WebscraperInterface import Webscraper, TMPDIR, DOWNLOAD_DIR
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

base_url = "https://snoopsnitch-api.srlabs.de/chunks/"
url = base_url + "?C=M;O=A"


def scrape(self):
    """Scrape the SnoopSnitch chunks."""
    cache_dir = os.path.join(DOWNLOAD_DIR, self.__class__.__name__)
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)
    for link in links:
        driver.get(link)
        timeout = 15
        try:
            element_present = EC.presence_of_element_located((By.CSS_SELECTOR, ".pc-miuidownload-sidetab_item"))
            WebDriverWait(driver, timeout).until(element_present)
        except TimeoutException:
            self.error_logger.error("Timed out waiting for page to load")

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        device = soup.find("p", class_="rom-phone-info-name").text
        if device not in data["images"]:
            data["images"][device] = []

        divs = soup.find_all("div", class_="pc-miuidownload-sidetab_item")
        for index, div in enumerate(divs):
            region = div.text.split(" ")[-1].lower()
            if self.searched_regions is not None and region != device.split(" ")[-1].lower() and region not in self.searched_regions:
                continue
            s = driver.find_elements(By.CSS_SELECTOR, ".pc-miuidownload-sidetab_item")[index]
            s.click()
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            image = {"base_url": self.url}
            image["name"] = div.text
            link = soup.find("a", class_="rom-download-btn")["href"]
            file = link.split("/")[-1].split("?")[0]
            image["file"] = file

            stats = [p.text for p in soup.find("div", class_="rom-stats_wrapper").find_all("p")]
            for stat in stats:
                key, value = [x.strip() for x in stat.split(":")]
                key = key.lower()
                if key == "author":
                    continue
                if key == "version":
                    value = value.replace("（）", "")
                image[key] = value
            image["link"] = link
            if image["version"] not in [x["version"] for x in data["images"][device]]:
                data["images"][device].append(image)
            if not scouting:
                self.download(image["link"], cache_dir, file, None)
            else:
                self.error_logger.info(f"Downloading {image['link']}")
            self.write_cache(json.dumps(data, indent=2))


def download(self, link, cache_dir, file, size):
    self.error_logger.info(f"Downloading {link}")
    tmpfile = os.path.join(TMPDIR, file)
    destfile = os.path.join(cache_dir, file)
    if os.path.exists(destfile):
        self.error_logger.info(f"File {destfile} already exists. skipping..")
    else:
        urllib.request.urlretrieve(link, tmpfile, Webscraper.show_progress)
        shutil.move(tmpfile, destfile)


def deep_update(mapping, *updating_mappings):
    # adapted from https://github.com/pydantic/pydantic/blob/fd2991fe6a73819b48c906e3c3274e8e47d0f761/pydantic/utils.py#L200
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            elif k in updated_mapping and isinstance(updated_mapping[k], list) and isinstance(v, list):
                for i, val in enumerate(v):
                    if i == 2 and isinstance(updated_mapping[k][i], dict) and isinstance(v[i], dict):
                        updated_mapping[k][i] = deep_update(updated_mapping[k][i], v[i])
                    elif val not in updated_mapping[k]:
                        updated_mapping[k].append(val)
            else:
                res = dict()
                for i, k1 in enumerate(updated_mapping.keys()):
                    res[k1] = updated_mapping[k1]
                    if i == list(updating_mapping.keys()).index(k):
                        res[k] = v
                updated_mapping = res
    return dict(sorted(updated_mapping.items()))


def find_subtests(tests):
    result_list = []
    for subtest in tests["subtests"]:
        if isinstance(subtest, str):
            result_list.append(subtest)
        elif isinstance(subtest, dict):
            result_list += find_subtests(subtest)
    return result_list


options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument("--window-size=1280,1280")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)
driver.get(url)
soup = BeautifulSoup(driver.page_source, 'html.parser')
files = [link.find("a")["href"] for link in soup.find("table").find("tbody").find_all("tr")[3:-1]]
chunks = sorted(os.listdir("chunks"))

#print(files)

#print(chunks)
#print(len([x for x in files if x not in chunks]), len(files), len(chunks), [x for x in files if x not in chunks])

all_vuln_logics = {}
all_basic_tests = {}
all_test_suites = {}
test_api_levels = {}
basic_tests_urls = []

for file in [x for x in files]:
    print(file)
    found_url = os.path.join(base_url, file)
    chunks_file_path = os.path.join("chunks", file)
    if not os.path.exists(chunks_file_path):
        urllib.request.urlretrieve(base_url + file, chunks_file_path)
    with open(chunks_file_path, "r") as f:
        data = json.load(f)
        if "vulnerabilities" in data:
            vuls = data["vulnerabilities"]
            for vul in vuls:
                if vul not in all_vuln_logics:
                    all_vuln_logics[vul] = vuls[vul]
                else:
                    all_vuln_logics[vul] = deep_update(all_vuln_logics[vul], vuls[vul])
                all_vuln_logics[vul] = dict(sorted(all_vuln_logics[vul].items()))

                if "minApiLevel" in vuls[vul]:
                    for api in range(max(vuls[vul]["minApiLevel"], 21), vuls[vul]["maxApiLevel"] + 1):
                        if api not in test_api_levels:
                            test_api_levels[api] = []
                            all_test_suites[api] = {"basicTestUrls": [], "minAppVersion": 10, "version": "2020-07-15.1", "vulnerabilitiesUrls": []}
                        test_api_levels[api] += find_subtests(vuls[vul]["testFixed"])
                        test_api_levels[api] = list(set(test_api_levels[api]))
                        if found_url not in all_test_suites[api]["vulnerabilitiesUrls"]:
                            all_test_suites[api]["vulnerabilitiesUrls"].append(found_url)
        if "basicTests" in data:
            basic_tests = data["basicTests"]
            for test in basic_tests:
                if test not in all_basic_tests:
                    all_basic_tests[test] = basic_tests[test]
            basic_tests_urls.append(found_url)

tmp_dict = {}
for key in sorted(all_vuln_logics):
    tmp_dict[key] = all_vuln_logics[key]
all_vuln_logics = tmp_dict

tmp_dict = {}
for key in sorted(all_basic_tests):
    tmp_dict[key] = all_basic_tests[key]
all_basic_tests = tmp_dict

tmp_dict = {}
for key in sorted(all_test_suites):
    tmp_dict[key] = all_test_suites[key]
    tmp_dict[key]["basicTestUrls"] = basic_tests_urls
all_test_suites = tmp_dict

# with open("allVulnLogics.json", "r") as f:
#     data = json.load(f)
# for key in data["ASLR"]:
#     if key not in all_vuln_logics["ASLR"].keys():
#         print(key)

with open("allVulnLogics.json", "w") as f:
    json.dump(all_vuln_logics, f, indent=2)

with open("allBasicTests.json", "w") as f:
    json.dump(all_basic_tests, f, indent=2)

with open("allTestSuites.json", "w") as f:
    json.dump(all_test_suites, f, indent=2)
