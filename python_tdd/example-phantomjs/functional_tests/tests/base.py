from datetime import datetime
from django.test import LiveServerTestCase
from functools import wraps
from os import path
from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException, WebDriverException
)

from selenium.webdriver.support.ui import WebDriverWait
import sys
import tempfile

DEFAULT_TIMEOUT = 5


def snapshot_on_error(test_method):
    @wraps(test_method)
    def wrapped_method(self, *_):
        try:
            return test_method(self, *_)
        except (AssertionError, WebDriverException):
            self.take_screenshot()
            self.dump_html()
            raise
    return wrapped_method


class FunctionalTest(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        for arg in sys.argv:
            if 'liveserver' in arg:
                cls.server_url = 'http://' + arg.split('=')[1]
                return
        LiveServerTestCase.setUpClass()
        cls.server_url = cls.live_server_url

    @classmethod
    def tearDownClass(cls):
        if cls.server_url == cls.live_server_url:
            LiveServerTestCase.tearDownClass()

    def start_browser(self):
        return webdriver.PhantomJS()

    def setUp(self):
        self.browser = self.start_browser()
        self.browser.implicitly_wait(DEFAULT_TIMEOUT)

    def tearDown(self):
        self.browser.quit()


    def take_screenshot(self):
        timestamp = datetime.now().isoformat().replace(':', '.')
        filename = path.join(
            tempfile.gettempdir(),
            'webdriver-screenshot-{}.png'.format(timestamp)
        )
        print('screenshotting to', filename)
        self.browser.get_screenshot_as_file(filename)

    def dump_html(self):
        timestamp = datetime.now().isoformat().replace(':', '.')
        filename = path.join(
            tempfile.gettempdir(),
            'webdriver-html-{}.html'.format(timestamp)
        )
        print('dumping page HTML to', filename)
        with open(filename, 'w') as f:
            f.write(self.browser.page_source)


    def wait_for(self, wait_fn):
        def wrapped_wait(_):
            try:
                wait_fn()
                return True
            except AssertionError:
                return False
        WebDriverWait(self.browser, timeout=2).until(wrapped_wait)


    def wait_for_url_to_match_regex(self, regex):
        self.wait_for(
            lambda: self.assertRegex(self.browser.current_url, '/lists/.+')
        )



    def get_item_input_box(self):
        return self.browser.find_element_by_id('id_text')


    def check_for_row_in_list_table(self, row_text):
        def check_for_row_in_list_table(browser):
            try:
                table = browser.find_element_by_id('id_list_table')
                rows = table.find_elements_by_tag_name('tr')
                return row_text in  [row.text for row in rows]
            except StaleElementReferenceException:
                return False
        WebDriverWait(self.browser, timeout=DEFAULT_TIMEOUT).until(check_for_row_in_list_table)

