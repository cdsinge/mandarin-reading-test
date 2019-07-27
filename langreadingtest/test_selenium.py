from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException,StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# This assumes server is already running

class FunctionalTestCase(LiveServerTestCase):
    def setUp(self):
        self.selenium = webdriver.Firefox(executable_path=r"C:\Users\c1dil\Downloads\geckodriver-v0.24.0-win64\geckodriver.exe")
        super(FunctionalTestCase, self).setUp()

    def tearDown(self):
        self.selenium.quit()
        super(FunctionalTestCase, self).tearDown()

    def test_title_exists(self):
        selenium = self.selenium
        #Opening the link we want to test
        selenium.get('http://localhost:8000/test')
        assert 'Language Test' in selenium.title

    def test_always_incorrect(self):
        # TODO test that this gives a small answer to final question (but currently using main db)
        # TODO once operational, do similar for always_correct, and flipping answer reasonably terminates
        selenium = self.selenium
        selenium.get('http://localhost:8000/test')
        count = 0
        incorrect_element_exists = True
        element = WebDriverWait(selenium, 2).until(
            EC.presence_of_element_located((By.XPATH, '//input[@value="incorrect"]'))
        )

        while incorrect_element_exists:
            incorrect_button = selenium.find_element_by_xpath("//input[@value='incorrect']").submit()
            count += 1
            try:
                def click_element(max_attempts=3):
                    attempt = 1
                    while True:
                        try:
                            element = WebDriverWait(selenium, 2).until(
                                EC.presence_of_element_located((By.XPATH, '//input[@value="incorrect"]'))
                            )
                        except StaleElementReferenceException:
                            if attempt == max_attempts:
                                raise
                            attempt += 1
                click_element()
                # incorrect_element_exists = len(selenium.find_elements_by_xpath("//input[@value='incorrect']")) > 0
            except TimeoutException as te:
                incorrect_element_exists = False
        print ("Total {}".format(count))

    # def test_configure_new_quiz(self):
    #     # TODO Check that the configuration screen appears and has expected options, and redirects to start the quiz
    #     # TODO Check for all datasets
    #     selenium = self.selenium
    #     #Opening the link we want to test
    #     selenium.get('http://localhost:8000/test')

    #     # Assert has a submit button.
    #     # Assert has aHSK1-6 choice

    #     # Choosen HSK1 button
    #     # Submit
    #     # Check have exoected redirection

