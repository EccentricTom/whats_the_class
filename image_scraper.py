# This code was heavily inspired by that found in this article:
# https://www.lostbraincells.com/2021/05/scraping-images-from-web-using-selenium.html


# import necessary libraries

import io
import os
import requests
from PIL import Image
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm, trange
import time

#check for a data folder and create if it doesn't exist
data_folder_path = os.getcwd()+"/data/"
if not os.path.isdir(data_folder_path):
    os.mkdir(data_folder_path)

# These options stop the browser from opening visibly
options = webdriver.chrome.options.Options()
options.headless = True
options.add_argument("--window-size=1920,1200")
# instantiate the driver to start collecting images
driver = webdriver.Chrome('Driver/chromedriver.exe', options=options)
driver.implicitly_wait(20)
os.chdir(data_folder_path)

# define a function to scroll to the bottom of the page
def scroll_to_end(driver):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

# this function gets image urls and adds them to a set
def getImageURLS(name, total_imgs, driver=driver):
    #url = f"https://www.bing.com/images/search?q={name}&form=HDRSC2&first=1&tsc=ImageHoverTitle"
    url = "https://google.com"
    driver.get(url)
    try:
        WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.XPATH,
                "/html/body/div[2]/div[2]/div[3]/span/div/div/div[3]/button[2]"))).click()
    except:
        pass
    search = driver.find_element_by_name("q")
    search.send_keys(name, Keys.ENTER)
    elem = driver.find_element_by_link_text('Images')
    elem.get_attribute('href')
    elem.click()
    image_urls = set()
    img_count = 0
    results_start = 0
    while img_count < total_imgs:
        scroll_to_end(driver)
        thumbnails = driver.find_elements_by_xpath("//img[contains(@class, 'Q4LuWd')]")
        total_results = len(thumbnails)
        print(f"Found: {total_results} search results. Extracting links from {results_start}: {total_results}")

        for img in thumbnails[results_start:total_results]:
            try:
                WebDriverWait(driver, 30).until(
                    expected_conditions.presence_of_element_located((By.XPATH, "//img[contains(@class, 'Q4LuWd')]")))
                driver.execute_script("arguments[0].click();", img)
                time.sleep(1)
            except exceptions.StaleElementReferenceException as e:
                print(e)
                pass

            actual_images = driver.find_elements_by_css_selector('img.n3VNCb')
            for image in actual_images:
                if image.get_attribute('src') and 'https' in image.get_attribute('src'):
                    image_urls.add(image.get_attribute('src'))
            img_count = len(image_urls)

            if img_count >= total_imgs:
                print("Found {} image links".format(img_count))
                break
            else:
                print("Found:", img_count, "looking for more image links ...")
                driver.execute_script("document.querySelector('.mye4qd').click();")
                results_start = len(thumbnails)
    return image_urls
    driver.quit()


# this function downloads images into a folder
def download_images(folder, name, url):
    try:
        image_content = requests.get(url).content
    except Exception as e:
        print(f"ERROR: could not download {url} - {e}")
    try:
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert("RGB")
        file_path = os.path.join(folder, name)

        with open(file_path, 'wb') as f:
            image.save(f, "JPEG", quality=90)
        print(f"SAVED - {url} - AT: {file_path}")
    except Exception as e:
        print(f"ERROR: Could not save {url} - {e}")


# this function combines the previous functions into one
def scrape_to_folder(search_names, modifier, dest_dir, total_images, driver=driver):
    for name in tqdm(list(search_names), position=0, desc= "Overall Progress",
                     leave=False):
        path = os.path.join(dest_dir, name)
        if not os.path.isdir(path):
            os.mkdir(path)
        print(f"Current Path: {path}")
        search_name = "'" + name + " " + modifier + "'"
        total_links = getImageURLS(search_name, total_images, driver)
        print(f"NUMBER OF LINKS: {len(total_links)}")
        if total_links is None:
            print("Images not found for: ", name)
        else:
            for i, link in enumerate(total_links):
                file_name = f"{i:150}.jpg"
                download_images(path, file_name, link)


search_query = ["warlock", "wizard", "sorceror", "cleric", "paladin", 'fighter', 'barbarian',
                'rogue', "artificer", "druid", "bard", "monk", "ranger"]
search_query.sort()
print(search_query)
dest_dir = os.getcwd()
total_imgs = 300


scrape_to_folder(search_query, "dnd 5e", dest_dir, total_imgs, driver=driver)
