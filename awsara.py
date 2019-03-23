#!/opt/telstar-data/venvs/amazonara/bin/python

# Activate the virtualenv
activate_this = '/opt/telstar-data/venvs/amazonara/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

# Setup CRON environment & additional project folder path
import os
from sys import path
path.append('/opt/telstar-data/venvs/amazonara')
os.environ['http_proxy'] = 'http://proxy.###.com:80'
os.environ['https_proxy'] = 'https://proxy.###.com:80'

###
### Version 1.3.1
###
import datetime, logging, re, time, shutil
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from telstar.kcbase import utils
import Locators

### 
### Run time controls
###
# Debug variable enables printing within functions
# Default is False
debug = False
# Flag to determine if Xvfb & virtual display should be used
# Default is True
virtual_display = True
# Flag to write data to the 'rainier_local' directory and not the NAS
# Default is False
use_nonprod_data_dir = False

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
ara_file_delta = ''
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
ara_sdaror_file_suffix = '_Amazon Retail_Ordered Revenue.csv'
ara_sdarsr_file_suffix = '_Amazon Retail_Shipped Revenue.csv'
ara_sdarscogs_file_suffix = '_Amazon Retail_Shipped COGS.csv'
ara_sdafscogs_file_suffix = '_Amazon Fresh_Shipped COGS.csv'
ara_sdapnscogs_file_suffix = '_Amazon Prime Now_Shipped COGS.csv'
ara_sdabor_file_suffix = '_Amazon Business_Ordered Revenue.csv'
ara_sdabsr_file_suffix = '_Amazon Business_Shipped Revenue.csv'
ara_sdabscogs_file_suffix = '_Amazon Business_Shipped COGS.csv'
ara_ihmfg_file_suffix = '_Inventory Health.csv'
ara_np_file_suffix = '_Net PPM.csv'
ara_tdar_file_suffix = "_Traffic_Amazon Retail.csv"
ara_tdaf_file_suffix = "_Traffic_Amazon Fresh.csv"
ara_tdab_file_suffix = "_Traffic_Amazon Business.csv"
ara_fipou_file_suffix = "_Forecast_Ordered Units.csv"
ara_fipsu_file_suffix = "_Forecast_Shipped Units.csv"
# Regular expressions
rx_css_value = re.compile(r'.*value="(.*?)" ')
# The following was picking up the opening '(' 
#rx_viewing_date_range = re.compile(r'[^ ]\d{1,2}/\d{1,2}/\d{1,2}.*\d{1,2}/\d{1,2}/\d{1,2}')
rx_viewing_date_range = re.compile(r'\d{2}/\d{2}/\d{2}.*\d{2}/\d{2}/\d{2}')
rx_viewing_date_tuple = re.compile(r'(\d{2}[-/]\d{2}[-/]\d{2}).*(\d{2}[-/]\d{2}[-/]\d{2})')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler('/var/log/telstar/ara.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%m-%d-%Y %H:%M:%S %Z')
handler.setFormatter(formatter)
logger.addHandler(handler)
# Check log level using the following:
#logging.getLevelName(logging.getLogger(__name__).getEffectiveLevel())
driver = ''

###
### Functions
###
def ara_logout():
    global driver
    try:
        driver.find_element_by_xpath(Locators.logout).click()
    except:
        pass

def driver_screen_shot():
    global driver
    if driver: 
        driver.save_screenshot('{}{}_screen_shot.png'.format(ara_log_path, datetime.datetime.now().strftime('%Y%m%s%H%M%S')))

def error_handler(err_string):
    global logger
    global ara_error_messages, ara_error_count
    logger.error(err_string)
    if not 'INFO' in err_string:
        ara_error_count += 1
    ara_error_messages += '{} - {}\n'.format(datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S'), err_string)

def move_download(file_name):
    try:
        global ara_download_path, ara_file_path, ara_file_count
        progress_timer = 0
        while len(utils.get_dir_filenames(ara_download_path, pattern=None)) == 0:
            if debug and progress_timer%10 == 0: print '__Download progress timer is at {} seconds'.format(progress_timer)
            if progress_timer > ara_download_timeout:
                raise ValueError('Download exceeded maximum wait timer of {} minutes.'.format(ara_download_timeout/60))
            time.sleep(2)
            progress_timer += 2
        src_file = utils.get_dir_filenames(ara_download_path, pattern=None)[0]
        # Remove illegal file system characters
        file_name = re.sub(r'[\/]','-', file_name)
        dst_file = '{}{}'.format(ara_file_path, file_name)
        ara_post_file_cache.add(dst_file)
        shutil.copyfile(src_file, dst_file)
        os.remove(src_file)
        ara_file_count += 1
    except (ValueError, Exception) as e:
        error_handler('Amazon ARA Script: move_download() failed for {}'.format(file_name, e))

def get_date_prefix(day):
    return datetime.datetime.now().replace(day=int(day)).strftime('%m-%d-%Y')

def date_format_week(week):
    return datetime.datetime.strptime(week, '%m/%d/%y').strftime('%m/%d/%Y')

def date_format_week_range(week_range):
    time_tuple = rx_viewing_date_tuple.findall(week_range)[0]
    time_range = [ date_format_week(x) for x in time_tuple ]
    #return '{} - {}'.format(datetime.datetime.strptime(time_tuple[0][0], '%m/%d/%y').strftime('%m/%d/%Y'),datetime.datetime.strptime(time_tuple[0][1], '%m/%d/%y').strftime('%m/%d/%Y'))
    return '{} - {}'.format(time_range[0], time_range[1])

def report_apply_button():
    global driver
    try:
        driver.find_element_by_xpath(Locators.report_filter_apply).click()
        if debug: print 'Clicking apply button...'
    except NoSuchElementException:
        #logging.info('Amazon ARA Script: Skipping apply button action.')
        pass

def reporting_range_to(time_period):
    global driver
    # Change reporting range to daily
    driver.find_element_by_xpath(Locators.report_range_datepicker).click()
    if time_period == 'daily':
        driver.find_element_by_xpath(Locators.report_range_daily).click()
    elif time_period == 'weekly':
        driver.find_element_by_xpath(Locators.report_range_weekly).click()
    elif time_period == 'monthly':
        driver.find_element_by_xpath(Locators.report_range_monthly).click()
    elif time_period == 'quarterly':
        driver.find_element_by_xpath(Locators.report_range_quarterly).click()
    elif time_period == 'yearly':
        driver.find_element_by_xpath(Locators.report_range_yearly).click()
    # Apply
    try:
        driver.find_element_by_xpath(Locators.report_filter_apply).click()
    except:
        pass

def download_as_csv(report_date, file_suffix):
    global driver
    # Click download
    if debug: print 'Click Download...'
    driver.find_element_by_xpath(Locators.download_button).click()
    # Wait for 'Detail View' item 'As CSV(.csv)' to load in the DOM
    if debug: print 'Web driver wait...'
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, Locators.download_item_content)))
    if debug: print 'Check for download conditions...'
    download_element = download_expected_conditions()
    if debug: print 'Click As CSV...'
    download_element.click()
    # Wait for the file to download before proceeding
    if debug: print 'Moving download...'
    move_download('{}{}'.format(report_date, file_suffix))

def download_expected_conditions():    
    global driver
    # To make this function usable across POM's the various EC are evaluated and the function passes response to WebDriverWait
    driver.implicitly_wait(10)
    try:
        ecs = driver.find_element_by_xpath(Locators.download_detail_view_as_csv)
        return ecs
    except:
        pass
    try:
        ecs = driver.find_element_by_xpath(Locators.download_inventory_health_as_csv)
        return ecs
    except:
        pass
    try:
        ecs = driver.find_element_by_xpath(Locators.download_forecast_inventory_planning_as_csv)
        return ecs
    except:
        pass
    driver.implicitly_wait(30)
    raise ValueError('Expected download conditions did not exist.')

def download_daily_reporting_view(start_day_index, end_day_index, file_suffix, ec_locator=None):
    global driver
    for i in range(int(start_day_index), int(end_day_index)):
        if debug: print 'Index is {}...'.format(i)
        try:
            report_day = ''
            # Select view 
            driver.find_element_by_xpath(Locators.report_range_day_picker).click()
            # Select individual end day
            day = driver.find_elements_by_xpath(Locators.report_range_day_picker_available_elements)[i - 1]
            # Capture the report day that will be used to name the file
            report_day = re.findall(r'(\d+/\d+/\d+)', day.text)[0]
            #report_day = datetime.datetime.strptime(report_day, '%m/%d/%y').strftime('%m-%d-%Y')
            report_day = date_format_week(report_day)
            day.click()
            # Apply Button
            report_apply_button()
            # If an Expect Condition 'ec' was passed wait up to 120 seconds
            if ec_locator:
                WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.XPATH,ec_locator)))
            #download_as_csv(get_date_prefix(report_day), file_suffix)
            download_as_csv(report_day, file_suffix)
        except (NoSuchElementException, ValueError, Exception) as e:
            error_handler('Amazon ARA Script Exception: [DDRV] {} Day Index {} Report Day {} - {}'.format(file_suffix[1:-4], i, report_day, e))
            pass

def download_weekly_reporting_view(start_week_index, end_week_index, file_suffix, ec_locator=None):
    global driver
    for i in range(int(start_week_index), int(end_week_index)):
        if debug: print 'Index is {}...'.format(i)
        try:
            report_week = ''
            # Select view 
            driver.find_element_by_xpath(Locators.report_range_day_picker).click()
            # Select individual end day
            week = driver.find_elements_by_xpath(Locators.report_range_day_picker_available_elements)[i - 1]
            # Capture the report day that will be used to name the file
            report_week = rx_viewing_date_range.findall(week.text)[0]
            # Format the date to include the Century
            report_week = date_format_week_range(report_week)
            week.click()
            # Apply Button
            report_apply_button()
            # If an Expect Condition 'ec' was passed wait up to 120 seconds
            if ec_locator:
                WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.XPATH,ec_locator)))
            download_as_csv(report_week, file_suffix)
        except (NoSuchElementException, ValueError, Exception) as e:
            error_handler('Amazon ARA Script Exception: [DWRV] {} Week Index {} Report Week {} - {}'.format(file_suffix[1:-4], i, report_week, e))
            pass

def download_daily_reporting_range(start_day_index, end_day_index, file_suffix, ec_locator=None):
    global driver
    for i in range(int(start_day_index), int(end_day_index)):
        if debug: print 'Index is {}...'.format(i)
        try:
            report_day = ''
            range_list = driver.find_elements_by_xpath(Locators.report_range_calendar_elements)
            # Select start date calendar
            range_list[0].click()
            # Select starting day
            driver.find_elements_by_xpath(Locators.report_range_datepicker_avialable_day_elements)[i * -1].click()
            # Select end date calendar
            range_list[1].click()
            # Select ending day
            day = driver.find_elements_by_xpath(Locators.report_range_datepicker_avialable_day_elements)[i * -1]
            # Capture the report day that will be used to name the file
            report_day = day.text
            # Get Month and Year
            report_month = day.find_element_by_xpath(Locators.report_range_datepicker_current_month).text
            # Format date to include Century
            report_date = datetime.datetime.strptime('{} {}'.format(report_day, report_month), '%d %B %Y').strftime('%m-%d-%Y')
            # Select reporting day
            day.click()
            # Apply Button
            report_apply_button()
            # If an Expect Condition 'ec' was passed wait up to 120 seconds
            if ec_locator:
                WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.XPATH,ec_locator)))
            # Download
            download_as_csv(report_date, file_suffix)
        except (NoSuchElementException, ValueError, Exception) as e:
            error_handler('Amazon ARA Script: [DDRR] {} Day Index {} Report Day {} - {}'.format(file_suffix[1:-4], i, report_day, e))
            pass

def download_weekly_reporting_range(start_week_index, end_week_index, file_suffix, ec_locator=None):
    global driver
    for i in range(int(start_week_index), int(end_week_index)):
        if debug: print 'Index is {}...'.format(i)
        try:
            report_week= ''
            range_list = driver.find_elements_by_xpath(Locators.report_range_calendar_input_elements)
            # Select start date calendar
            range_list[0].click()
            # Select starting week
            driver.find_elements_by_xpath(Locators.report_range_datepicker_available_week_elements)[i * -1].click()
            # Select ending week
            week = driver.find_elements_by_xpath(Locators.report_range_datepicker_available_week_elements)[i * -1]
            week.click()
            # Apply button
            report_apply_button()
            # Capture the report week that will be used to name the file, use the week date format to add century
            range_list = driver.find_elements_by_xpath(Locators.report_range_calendar_input_elements)
            week_start = date_format_week(range_list[0].get_attribute('value'))
            week_end = date_format_week(range_list[1].get_attribute('value'))
            # Use the following line for a 'MM/DD/YYYY - MM/DD/YYYY_file_suffix.csv' format
            report_week = '{} - {}'.format(week_start, week_end)
            # Use the following line for a 'MM/DD/YYY_file_suffix.csv' format
            #report_week = week_start
            # Apply Button
            report_apply_button()
            # If an Expect Condition 'ec' was passed wait up to 120 seconds
            if ec_locator:
                WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.XPATH,ec_locator)))
            # Download
            download_as_csv(report_week, file_suffix)
        except (NoSuchElementException, ValueError, Exception) as e:
            error_handler('Amazon ARA Script: [DWRR] {} Week Index {} Report Week {} - {}'.format(file_suffix[1:-4], i, report_week, e))
            pass

def ara_setup():
    global driver
    try:
        # Setup Environment

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
        logging.info('ARA run started at: {}, Chrome Environment successfully setup.'.format(datetime.datetime.now()))
        # Login
        driver.get(Locators.url)
        p = driver.find_element_by_xpath(Locators.signin_email)
        p.clear()
        p.send_keys(Locators.user)
        p = driver.find_element_by_xpath(Locators.signin_password)
        p.clear()
        p.send_keys(Locators.password)
        driver.find_element_by_xpath(Locators.signin_submit).click()
        # Wait for the navigation menu containing the Sales Diagnostics Link to be visiable in the DOM
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH,Locators.sales_diagnostic_link)))
        # Populate the pre run file cache
        __garbage = [ara_pre_file_cache.add(this_file.split('/')[-1]) for this_file in utils.get_dir_filenames(ara_file_path, pattern='.*\.csv')]
    except (NoSuchElementException, ValueError, Exception) as e:
        error_handler('Amazon ARA Login: Unable to access Amazon ARA page {}'.format(e))
        # If the driver exists capture a screen shot of the error
        driver_screen_shot()
        raise Exception('Unable to access AMAZON ARA page!')

def sales_diagnostic():
    global driver
    ### Sales Diagnostic POM
    # FIXME: Sales Diagnostics - Any POM load failure will stop execution of this entire script, this needs to be fixed in the next feature release.
    try:
        # Sales Diagnostic Dashboard 
        if debug: print ara_section_header.format('Sales Diag POM')
        driver.find_element_by_xpath(Locators.sales_diagnostic_link).click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,Locators.sales_diagnostic_header)))
    except Exception as e:
        error_handler('Amazon ARA Script: Unable to load Sales Diagnostic page - {}'.format(e))
    
    # Program: Amazon Retail
    # Distributor View: Manufacturing
    # Sales View: Ordered Revenue
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('AROR Daily Start')
        # Switch Program to Amazon Retail
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_retail).click()
        # Switch Sales View to ordered revenue
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_ordered_revenue).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3,4)
        download_daily_reporting_range(1, 5, '_Daily{}'.format(ara_sdaror_file_suffix))
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_sdaror_file_suffix[1:-4], e))
        pass
    
    # Program: Amazon Retail
    # Distributor View: Manufacturing
    # Sales View: Shipped Revenue
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('ARSR Daily Start')
        # Switch Program to Amazon Retail
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_retail).click()
        # Switch Sales View to shipped revenue
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_shipped_revenue).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3,4)
        download_daily_reporting_range(1, 5, '_Daily{}'.format(ara_sdarsr_file_suffix))
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_sdarsr_file_suffix[1:-4], e))
        pass
    
    # Program: Amazon Retail
    # Distributor View: Manufacturing
    # Sales View: Shipped COGS
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('ARSCOGS Daily Start')
        # Switch Program to Amazon Retail
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_retail).click()
        # Switch Sales View to shipped revenue
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_shipped_cogs).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3,4)
        download_daily_reporting_range(1, 5, '_Daily{}'.format(ara_sdarscogs_file_suffix))
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_sdarscogs_file_suffix[1:-4], e))
        pass
    
    # Program: Amazon Fresh
    # Distributor View: Manufaturing
    # Sales View: Shipped COGS
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('AFSCOGS Daily Start')
        # Switch Program to Amazon Fresh
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_fresh).click()
        # Switch Sales View to shipped revenue
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_shipped_cogs).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3)
        download_daily_reporting_view(1, 4, '_Daily{}'.format(ara_sdafscogs_file_suffix))
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_sdafscogs_file_suffix[1:-4], e))
        pass
    
    # Program: Amazon Prime Now
    # Sales View: Shipped COGS
    # Region: All
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('APNSCOGS Daily Start')
        # Switch Program to Amazon Prime Now
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_prime_now).click()
        # Switch Sales View to shipped revenue
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_shipped_cogs).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3,4)
        download_daily_reporting_view(1, 5, '_Daily{}'.format(ara_sdapnscogs_file_suffix))
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_sdapnscogs_file_suffix[1:-4], e))
        pass
    
    # Program: Amazon Business
    # Sales View: Ordered Revenue
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('ABOR Daily Start')
        # Switch Program to Amazon Business
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_business).click()
        # Switch Sales View to ordered revenue
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_ordered_revenue).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3,4)
        download_daily_reporting_range(1, 5, '_Daily{}'.format(ara_sdabor_file_suffix))
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_sdabor_file_suffix[1:-4], e))
        pass
    
    # Program: Amazon Business
    # Sales View: Shipped Revenue
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('ABSR Daily Start')
        # Switch Program to Amazon Business
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_business).click()
        # Switch Sales View to shipped revenue
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_shipped_revenue).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3,4)
        download_daily_reporting_range(1, 5, '_Daily{}'.format(ara_sdabsr_file_suffix))
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_sdabsr_file_suffix[1:-4], e))
        pass
    
    # Program: Amazon Business
    # Sales View: Shipped COGS
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('ABSCOGS Daily Start')
        # Switch Program to Amazon Business
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_business).click()
        # Switch Sales View to shipped revenue
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_shipped_cogs).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3,4)
        download_daily_reporting_range(1, 5, '_Daily{}'.format(ara_sdabscogs_file_suffix))
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_sdabscogs_file_suffix[1:-4], e))
        pass

def inventory_health():
    global driver
    ###
    ### Inventory Health POM
    ###
    try:
        if debug: print ara_section_header.format('Inventory Health POM')
        # Switch to Inventory Health page
        driver.find_element_by_xpath(Locators.inventory_health_link).click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,Locators.inventory_health_header)))
    except Exception as e:
        error_handler('Amazon ARA Script: Unable to load Inventory Health page - {}'.format(e))
    
    # Program: Inventory Health
    # Distributor View: Manufacturing
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('IHMFG Daily Start')
        # Switch Distributor view to Manufacturing
        driver.find_element_by_xpath(Locators.distributor_view_dropdown).click()
        driver.find_element_by_xpath(Locators.distributor_view_manufacturing).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3,4)
        download_daily_reporting_range(1, 5, '_Daily{}'.format(ara_ihmfg_file_suffix))
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_ihmfg_file_suffix[1:-4], e))
        pass
    
    # Program: Inventory Health
    # Distributor View: Manufacturing
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Weekly
    try:
        if debug: print ara_section_header.format('IHMFG Weekly Start')
        # Switch Distributor view to Manufacturing
        driver.find_element_by_xpath(Locators.distributor_view_dropdown).click()
        driver.find_element_by_xpath(Locators.distributor_view_manufacturing).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('weekly')
        # Download week after the last available week reported (2)
        download_weekly_reporting_range(2, 3, '_Weekly{}'.format(ara_ihmfg_file_suffix))
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_ihmfg_file_suffix[1:-4], e))
        pass

def net_ppm():
    global driver
    ###
    ### Net PPM POM
    ###
    # FIXME: Net PPM - Any POM load failure will stop execution of this entire script, this needs to be fixed in the next feature release.
    try:
        if debug: print ara_section_header.format('Net PPM Dashboard')
        # Switch to Inventory Health page
        driver.find_element_by_xpath(Locators.net_ppm_link).click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,Locators.net_ppm_header)))
    except Exception as e:
        error_handler('Amazon ARA Script: Unable to load Net PPM page - {}'.format(e))
    
    # No Options Available
    try:
        # NOTE - Net PPM Weekly does not use a reporting range picker or ANY picker, it defaults to a single week
        if debug: print ara_section_header.format('Net PPM Weekly Download')
        # Change to weekly reporting range
        reporting_range_to('weekly')
        # Get week range text
        report_week = rx_viewing_date_range.findall(driver.find_element_by_xpath(Locators.report_range_weekly_view_text).text)[0]
        # Fix date to add Century
        report_week = date_format_week_range(report_week)
        # Download CSV file
        download_as_csv(report_week, '_Weekly{}'.format(ara_np_file_suffix))
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_np_file_suffix[1:-4], e))
        pass

def traffic_diagnostic():
    global driver
    ###
    ### Traffic Diagnostic POM
    ###
    # FIXME: Traffic Diagnostic - Any POM load failure will stop execution of this entire script, this needs to be fixed in the next feature release.
    try:
        if debug: print ara_section_header.format('Traffic Diagnostic Dashboard')
        # Switch to Inventory Health page
        driver.find_element_by_xpath(Locators.traffic_diagnostic_link).click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,Locators.traffic_diagnostic_header)))
    except Exception as e:
        error_handler('Amazon ARA Script: Unable to Traffic Diagnostic page - {}'.format(e))
    
    # Program: Amazon Retail
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('TDAR Daily Start')
        # Switch Program to Amazon Retail
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_retail).click()
        # No Apply Required
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3)
        download_daily_reporting_range(1, 4, '_Daily{}'.format(ara_tdar_file_suffix), Locators.traffic_diagnostic_detail_container)
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_tdar_file_suffix[1:-4], e))
        pass
    
    # Program: Amazon Retail
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Weekly
    try:
        if debug: print ara_section_header.format('TDAR Weekly Start')
        # Switch Program to Amazon Retail
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_retail).click()
        # No Apply Required
        # Change reporting range to daily
        reporting_range_to('weekly')
        # Download week prior to last available week reported (2) and week prior (3)
        download_weekly_reporting_range(2, 4, '_Weekly{}'.format(ara_tdar_file_suffix), Locators.traffic_diagnostic_detail_container)
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_tdar_file_suffix[1:-4], e))
        pass
    
    # Program: Amazon Fresh
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('TDAF Daily Start')
        # Switch Program to Amazon Fresh
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_fresh).click()
        # No Apply Required
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2)
        download_daily_reporting_view(1, 3, '_Daily{}'.format(ara_tdaf_file_suffix), Locators.traffic_diagnostic_detail_container)
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_tdaf_file_suffix[1:-4], e))
        pass
    
    # Program: Amazon Fresh
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Weekly
    try:
        if debug: print ara_section_header.format('TDAF Weekly Start')
        # Switch Program to Amazon Retail
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_fresh).click()
        # No Apply Required
        # Change reporting range to daily
        reporting_range_to('weekly')
        # Download last available day reported (1) and days prior (2)
        download_weekly_reporting_view(1, 3, '_Weekly{}'.format(ara_tdaf_file_suffix), Locators.traffic_diagnostic_detail_container)
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_tdaf_file_suffix[1:-4], e))
        pass
    
    # Program: Amazon Business
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('TDAB Daily Start')
        # Switch Program to Amazon Fresh
        driver.find_element_by_xpath(Locators.program_dropdown).click()
        driver.find_element_by_xpath(Locators.program_amazon_business).click()
        # No Apply Required
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3)
        download_daily_reporting_range(1, 4, '_Daily{}'.format(ara_tdab_file_suffix), Locators.traffic_diagnostic_detail_container)
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_tdab_file_suffix[1:-4], e))
        pass

def forecast_inventory_planning():
    global driver
    ###
    ### Forecast & Inventory Planning POM
    ###
    # FIXME: Forecast & Inventory Planning - Any POM load failure will stop execution of this entire script, this needs to be fixed in the next feature release.
    try:
        if debug: print ara_section_header.format('Forecast & Inventory Planning Dashboard')
        # Switch to Forecast & Inv. Planning Page
        driver.find_element_by_xpath(Locators.forecast_inventory_planning_link).click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,Locators.forecast_inventory_planning_header)))
    except Exception as e:
        error_handler('Amazon ARA Script: Unable to Forecast and Inventory Planning page - {}'.format(e))
    
    # Distributor View: Manufacturing
    # Sales View: Ordered Units
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('FIPOU Daily Start')
        # Switch Sales View to Ordered Units
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_ordered_units).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3,4,5)
        download_daily_reporting_range(1, 6, '_Daily{}'.format(ara_fipou_file_suffix), Locators.forecast_inventory_planning_detail_container)
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_fipou_file_suffix[1:-4], e))
        pass
    
    # Distributor View: Manufacturing
    # Sales View: Ordered Units
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Weekly
    try:
        if debug: print ara_section_header.format('FIPOU Weekly Start')
        # Switch Sales View to Ordered Units
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_ordered_units).click()
        # Apply button
        report_apply_button()
        # Change reporting range to weekly
        reporting_range_to('weekly')
        # Download last available day reported (1) and days prior (2,3)
        download_weekly_reporting_range(1, 4, '_Weekly{}'.format(ara_fipou_file_suffix), Locators.forecast_inventory_planning_detail_container)
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_fipou_file_suffix[1:-4], e))
        pass
    
    # Distributor View: Manufacturing
    # Sales View: Shipped Units
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Daily
    try:
        if debug: print ara_section_header.format('FIPSU Daily Start')
        # Switch Sales View to Ordered Units
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_shipped_units).click()
        # Apply button
        report_apply_button()
        # Change reporting range to daily
        reporting_range_to('daily')
        # Download last available day reported (1) and days prior (2,3,4)
        download_daily_reporting_range(1, 5, '_Daily{}'.format(ara_fipsu_file_suffix), Locators.forecast_inventory_planning_detail_container)
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_fipsu_file_suffix[1:-4], e))
        pass
    
    # Distributor View: Manufacturing
    # Sales View: Shipped Units
    # Category: All
    # Subcategory: All
    # Brand: All
    # Reporting Range: Weekly
    try:
        if debug: print ara_section_header.format('FIPSU Weekly Start')
        # Switch Sales View to Ordered Units
        driver.find_element_by_xpath(Locators.sales_view_dropdown).click()
        driver.find_element_by_xpath(Locators.sales_view_shipped_units).click()
        # Apply button
        report_apply_button()
        # Change reporting range to weekly
        reporting_range_to('weekly')
        # Download 
        # Starting week index at 2 from last available reporting period based on
        # the most recent week never being available during all the test iterations
        download_weekly_reporting_range(2, 4, '_Weekly{}'.format(ara_fipsu_file_suffix), Locators.forecast_inventory_planning_detail_container)
    except Exception as e:
        error_handler('Amazon ARA Script: {} {}'.format(ara_fipsu_file_suffix[1:-4], e))
        pass

def ara_teardown():
    global display, driver
    ### TEARDOWN ENVIRONMENT
    try:
        logging.info('ARA run ended at: {}, Chrome Environment successfully shutdown.'.format(datetime.datetime.now()))
        # Logout of Amazon ARA
        ara_logout()
        # Close the Chrome web driver instance
        driver.quit()
        # Check if the virtual display should be used.
        if virtual_display:
            display.stop()
        # Compare file caches for new files
        __garbage = [ara_post_file_cache.add(this_file.split('/')[-1]) for this_file in utils.get_dir_filenames(ara_file_path, pattern='.*\.csv')]
        ara_file_delta = '<br>'.join(list(ara_post_file_cache - ara_pre_file_cache))
    except:
        pass

if __name__ == '__main__':
    ara_setup()
    sales_diagnostic()
    inventory_health()
    net_ppm()
    traffic_diagnostic()
    forecast_inventory_planning()
    ara_teardown()
    utils.writeLog('{}ara_logfile.txt'.format(ara_log_path), ara_error_messages)
  
