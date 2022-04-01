#!/Users/brettwiseman/opt/miniconda3/bin/python
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import time
import sys
import os

# Constants
def set_path():
    if os.name == "posix":
        return "{}/{}".format(os.getcwd(), "chromedriver")
    elif os.name == "nt":
        return "{}\{}".format(os.getcwd(), "chromedriver.exe")

PATH = set_path()
PAGE_START = '1'
PAGE_H = "/us/stores/?cat=bps&page="
URL = "https://www.morphmarket.com"

def usage(status=0):
    ''' Display usage and exit with status '''
    print('''Usage: {} [options]
    -a:             append instead make new file / overwrite
    -l: LIMIT       limit of how many pages to search
    -s: START       page to start on
    -f: FILE_NAME   file to write to
    -p:             makes each page on a new file with name data(count).csv
    -h:             display usage
    '''.format(os.path.basename(sys.argv[0])))
    sys.exit(status)

def open_driver(url, path=PATH):
    ''' Opens and returns driver from given url and path

        url: url to open
        path: path to driver
    '''

    driver = webdriver.Chrome(path)
    driver.get(url)

    return driver

def build_url_dict(k=1, url=URL, page_num=PAGE_START, path=PATH, page_h=PAGE_H):
    ''' Builds dict of all urls for bps on webpage ofr a certain number of pages and from a starting page

        k: number of page limit
        url: the url to main website
        page_num: what page the search starts
        path: path to chromedriver
        page_h: set extension for seaching what we want

        returns: dict of urls
        Snakes = {
            page : [list of links]
        }
    '''

    # set variables
    page_count = 0
    Snakes = {}
    next_page = True

    # while there is a next page or under page limit
    while next_page and page_count < k:

        # open driver with url
        curl = url + page_h + page_num
        driver = open_driver(curl)

        # get page source
        page = driver.page_source

        # build links list at page
        Snakes[page_num] = [item for item in re.findall(r'<a href="(.*)">', page) if re.search(r'cat', item) and not re.search(r'/us/', item)]

        # searches if next page
        if not re.search(r'page-item  disabled', page):
            page_num = re.findall(r'title="Next Page" href="\?cat=bps&amp;page=(.*)"><span', page)[0]
        else:
            next_page = False

        # quit driver - seems to need to happen otherwire thinks we are a bot
        driver.quit()

        # increase page count
        page_count += 1

    return Snakes

def follow_url(store, url=URL, path=PATH):
    ''' Follows url and builds a data dict

        store: url extension fo store
        url: the url to main website
        path: path to chromedriver

        returns: data
        data = {
            'Name' : "",
            'Owner' : "",
            'Phone' : ""
        }
        If no phone, the N/A
    '''

    # open driver with url
    curl = url + store
    driver = open_driver(curl)

    print(f'store: {store}
    # get page source
    page = driver.page_source

    # build store infor list
    store_info = [el for el in driver.find_elements(By.CLASS_NAME, "store-info-item")]
    if len(store_info) == 0:
        driver.quit()
        return {"Name" : "error", "Owner" : "error", "Phone" : "error"}

    # build data dict -  assumes data is in same order on website
    #   Name is in title of page, and has " - MorphMarket" in it
    #   Owner is first
    #   Phone is 3, and if there, assumes in ***-***-**** format

    data = {}
    data['Name'] = re.findall(r'(.*) - MorphMarket', driver.title)[0].replace(",", " ")
    data['Owner'] = str(store_info[0].text).replace(",", " ")
    if re.search(r'\d{3}-\d{3}-\d{4}', store_info[2].text):
        data['Phone'] = store_info[2].text
    else:
        data['Phone'] = "N/A"

    # quit driver
    driver.quit()

    return data

def find_data(Snake_links):
    ''' Goes to each store page and collects data

        Snake_links: dict of all links
        Snake_links = {
            page : [list of links]
        }

        returns: Snake_data
        Snake_data = {
            page : [list of data dicts]
        }
    '''

    # build dict that has all data from every link
    Snake_data = {}
    for page in Snake_links:
        print(f'Page: {page}')
        Snake_data[page] = [follow_url(link) for link in Snake_links[page]]

    return Snake_data

def write_data(Snake_data, append=False, file="data.csv", sep_page=False, init=0):
    ''' Writes data from Snakes dict to a csv file

        Snakes: dict of all data
        file: file we want to write to

        returns: None
    '''

    # write data into a csv file
    if sep_page:
        file_p = file
        count = init
    elif not append:
        f = open(file, "w")
        f.write("Name,Owner,Phone\n")
    else:
        f = open(file, "a")

    for page in Snake_data:
        if sep_page:
            file = file_p.split('.')[0] + str(count) + ".csv"
            f = open(file, "w")
            f.write("Name,Owner,Phone\n")
            count += 1

        for d in Snake_data[page]:
                line = "{},{},{}\n".format(d['Name'], d['Owner'], d['Phone'])
                f.write(line)

def main():
    # flags
    doAppend = False
    limit = 1
    start = '1'
    file_name = "data.csv"
    pages = False

    # parse arguments
    args = sys.argv[1:]
    while args and args[0].startswith('-'):
        arg = args.pop(0)

        if arg == "-l":
            limit = int(args.pop(0))
        elif arg == "-a":
            doAppend = True
        elif arg == "-s":
            start = args.pop(0)
        elif arg == "-f":
            file_name = args.pop(0)
        elif arg == "-p":
            pages = True
            doAppend = False
        elif arg == "-h":
            usage(0)
        else:
            usage(1)

    # build dict of links
    Snake_links = build_url_dict(k=limit, page_num=start)

    # get data from all links
    Snake_data = find_data(Snake_links)

    # print to file
    write_data(Snake_data, append=doAppend, file=file_name, sep_page=pages, init=int(start))

if __name__ == '__main__':
    main()
