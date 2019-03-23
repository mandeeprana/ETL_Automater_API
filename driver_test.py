#!/opt/telstar-data/venvs/amazonara/bin/python2.7

# Activate the virtualenv
activate_this = '/opt/telstar-data/venvs/amazonara/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

### Version 1.0.2
import datetime, logging, pandas, time, os
from StringIO import StringIO
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from telstar.kcbase import utils
import Locators

os.environ['http_proxy'] = 'http://proxy.kcc.com:80'
os.environ['https_proxy'] = 'https://proxy.kcc.com:80'
utils.writeLog('/opt/telstar-data/venvs/amazonara/logs/cronenv.log', utils.spcall('env')) 

###
### Run time controls
###
# Debug variable enables printing within functions
debug = False
# Flag to determine if Xvfb & virtual display should be used
virtual_display = True
# Flag to write data to the 'rainier_local' directory and not the NAS
use_nonprod_data_dir = True

###
### Variables
###
# Flags and other counters
ara_pre_file_cache = set()
ara_post_file_cache = set()
ara_download_timeout = 300
ara_error_messages = ''
ara_error_count = 0
ara_file_count = 0
# Use the following file path to control where data is written, either
# D&A NAS 'cifs' path and use virtualenv 'rainier_local' folder
ara_download_path = '/opt/telstar-data/venvs/amazonara/downloads/'
ara_log_path = '/opt/telstar-data/venvs/amazonara/logs/'
ara_file_path = '/cifs/rainier/'
if use_nonprod_data_dir:
    # Override production ara_file_path set above 
    ara_file_path = '/opt/telstar-data/venvs/amazonara/rainier_local/'

# Headers and File Names
ara_section_header = "-"*25 + "\n- {}\n" + "-"*25

###
### Functions
###
def error_handler(err_string):
    global ara_error_messages, ara_error_count
    logger.error(err_string)
    if not 'INFO' in err_string:
        ara_error_count += 1
    ara_error_messages += '{} - {}\n'.format(datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S'), err_string)

###
### MAIN SCRIPT
###
try:
    # Setup Environment
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('/var/log/telstar/ara.log')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%m-%d-%Y %H:%M:%S %Z')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Check log level using the following:
    #logging.getLevelName(logging.getLogger(__name__).getEffectiveLevel())
    #
    # Check if the virtual display should be used from pyvirtualdisplay that uses a X video frame buffer for chromedriver 
    if virtual_display:
        display = Display(visible=0, size=(1024, 768))
        display.start()
    
    # Documentation for Chrome Flags
    # https://github.com/GoogleChrome/chrome-launcher/blob/master/docs/chrome-flags-for-tools.md
    options = webdriver.ChromeOptions()
    options.add_argument("--test-type")
    prefs = {'profile.default_content_setting_values.automatic_downloads': 1, 
            'download.default_directory': ara_download_path}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(chrome_options=options)
    driver.implicitly_wait(30)
    driver.set_page_load_timeout(120)
    __garbage = [ara_pre_file_cache.add(this_file.split('/')[-1]) for this_file in utils.get_dir_filenames(ara_file_path, pattern=None)]
    logging.info('Driver Test: {}, Chrome Environment successfully setup.'.format(datetime.datetime.now()))
except (NoSuchElementException, ValueError, Exception) as e:
    logging.info('Driver Test: Unable to access driver test page {}'.format(e))
    raise Exception('Unable to access page!')

try:
    url = 'https://bucky.dynu.com'
    button_http_headers = "//a[contains(text(), 'HTTP Headers')]"
    button_show_headers = "//button[contains(text(), 'Show Headers')]"
    driver.get(url)
    driver.find_element_by_xpath(button_http_headers).send_keys('\n')
    driver.switch_to_window(driver.window_handles[-1])
    driver.find_element_by_xpath(button_show_headers).click()
    time.sleep(5)
    # Screenshot
    # wpath = '/var/www/html'
    # driver.save_screenshot('{}/a.png'.format(wpath))
    # Wait for the Show Header button to become visable in teh DOM
    #WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, button_show_headers)))
    restable = driver.page_source
    df = pandas.read_html(StringIO(restable))[0]
    if debug: print df.to_html()
    utils.writeLog('{}{}_bucky_ip_header.html'.format(ara_file_path, datetime.datetime.now().strftime('%Y%m%d%H%M%S')), df.to_html())
except (NoSuchElementException, ValueError, Exception) as e:
    error_handler('Driver Test: Exception {}'.format(e))
    pass

### 
### TEARDOWN ENVIRONMENT
### 
try:
    logging.info('Driver Test ended at: {}, Chrome Environment successfully shutdown.'.format(datetime.datetime.now()))
    # Close the Chrome web driver instance
    if driver:
        driver.quit()
    # Check if the virtual display should be used.
    if virtual_display:
        display.stop()
    __garbage = [ara_post_file_cache.add(this_file.split('/')[-1]) for this_file in utils.get_dir_filenames(ara_file_path, pattern=None)]
    ara_file_delta = '<br>'.join(list(ara_post_file_cache - ara_pre_file_cache))
except:
    pass

utils.writeLog('{}driver_test_logfile.txt'.format(ara_log_path), ara_error_messages)
utils.sendMail('ustwl099@kcc.com', ['jay.butzler@kcc.com'], 'Driver Test Script Ran','Files:<br><br>{}'.format(ara_file_delta))
