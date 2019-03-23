from selenium import webdriver
import locators_abvp
linenumber = 1

#enables printing within functions
debug = False
# Used to enable and disable browser view
virtual_display = True
# Flag to write data to the 'rainier_local' directory and not the NAS
use_nonprod_data_dir = False
driver=''


def run():
    global driver
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--test-type")
        #options.add_argument("--headless") 
        #options.binary_location = "/usr/bin/chromium"
        #driver = webdriver.Chrome(chrome_options=options)
        prefs = {'profile.default_content_setting_values.automatic_downloads': 1}
        options.add_experimental_option("prefs", prefs)
        #driver = webdriver.Chrome(executable_path= r'C:\\Users\\U14365\\Desktop\\AMZ extracts\\chromedriver.exe')
        driver = webdriver.Chrome(chrome_options=options)
        driver.implicitly_wait(30)
        driver.set_page_load_timeout(120)
        # Login
        driver.get(locators_abvp.url)
        p = driver.find_element_by_xpath(locators_abvp.signin_email)
        p.clear()
        p.send_keys(locators_abvp.user)
        p = driver.find_element_by_xpath(locators_abvp.signin_password)
        p.clear()
        p.send_keys(locators_abvp.password)
        driver.find_element_by_xpath(locators_abvp.signin_submit).click()
        driver.implicitly_wait(30)
        driver.set_page_load_timeout(120)
        ##running to click 4 links and download
        driver.find_element_by_xpath(locators_abvp.us_xlsx).click()
        driver.implicitly_wait(30)
        driver.set_page_load_timeout(120)
        driver.find_element_by_xpath(locators_abvp.us_raw).click()
        driver.implicitly_wait(30)
        driver.set_page_load_timeout(120)
        driver.find_element_by_xpath(locators_abvp.custom_xlsx).click()
        driver.implicitly_wait(30)
        driver.set_page_load_timeout(120)
        driver.find_element_by_xpath(locators_abvp.custom_raw).click()
        driver.implicitly_wait(30)
        driver.set_page_load_timeout(120)
    except:
        print("ABVP page could not open there is some error in code!")
        pass
    
if __name__ == '__main__':
    run()
        