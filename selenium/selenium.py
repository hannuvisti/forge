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


class BrowserClass(object):
    def __init__ (self):
        try:
            self.browser = webdriver.Firefox()
            self.browser.implicitly_wait(5)
        except:
            print traceback.format_exc()
            exit(1)
    def close(self):
        self.browser.quit()
        exit(0)

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


    def do_google_search(self,searchtext):
        try:
            self.browser.get("http://www.google.com")
            el = self.browser.find_element_by_name("q")
            el.send_keys(searchtext)
            el.send_keys(Keys.RETURN)
        except:
            exit(1)

b = BrowserClass()

b.do_google_search("Hannu Visti")
sleep(5)
b.close()
