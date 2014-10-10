#!/usr/bin/python

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
from random import choice
from random import randrange
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import sys
import traceback
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

class BrowserClass(object):
    def __init__ (self):
        try:
            #profile = webdriver.FirefoxProfile(profile_directory="/tmp/x")
            self.browser = webdriver.Firefox()
            self.browser.implicitly_wait(5)
        except:
            print traceback.format_exc()
            exit(1)
    def close(self):
        print self.browser.quit()
        exit(0)

    def open_page(self,url):
        try:
            self.browser.get(url)
        except:
            print traceback.format_exc()
            exit(1)

    def do_n_clicks(self,url,n,random=False):
        count = randrange(n,n*2) if random else n
        try:
            self.browser.get(url)
        except:
            exit(1)

        el = self.browser.find_elements_by_tag_name("a")
        i=0
        while i < count:
            try:
                choice(el).click()
                self.browser.back()
            except ElementNotVisibleException:
                pass
            except StaleElementReferenceException:
                self.browser.refresh()
                el = self.browser.find_elements_by_tag_name("a")
            finally:
                i += 1


    def do_google_search(self,searchtext,clickresult=0):
        try:
            self.browser.get("http://www.google.com")
            el = self.browser.find_element_by_name("q")
            el.send_keys(searchtext)
            el.send_keys(Keys.RETURN)
        except:
            exit(1)

        if clickresult == 0:
            return
        WebDriverWait(self.browser,10).until(EC.presence_of_element_located
                                             ((By.ID,"resultStats")))
        el = self.browser.find_elements_by_xpath("//*[@id='rso']//h3/a")

        if len(el) < clickresult:
            print >>sys.stderr, "Search returned %d results, less than %d" % (len(el),clickresult)
            exit(1)
        el[clickresult-1].click()


b = BrowserClass()
sleep(3)
#
#
# Inject your code here and finish by calling b.close()


