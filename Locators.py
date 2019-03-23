import creds

# Version 1.0.3
# Sign on page locators
signin_email = "//input[@id='ap_email']"
signin_password = "//input[@id='ap_password']"
signin_submit = "//input[@id='signInSubmit']"
logout = "//a[contains(text(), 'Logout')]"
url = "https://arap.amazon.com/"
user = creds.ara_user
password = creds.ara_password

### Sales Diagnostic POM 
# Navigation
sales_diagnostic_link = "//a[contains(text(),'Sales Diagnostic')]"
sales_diagnostic_header = "//span[@class='dashboard-title' and contains(text(), 'Sales Diagnostic')]"
# Program
program_dropdown = "//span[contains(text(), 'Program')]/ancestor::button"
program_amazon_retail = "//a[contains(text(), 'Amazon Retail')]"
program_amazon_fresh = "//a[contains(text(), 'Amazon Fresh')]"
program_amazon_prime_now = "//a[contains(text(), 'Amazon Prime Now')]"
program_amazon_business = "//a[contains(text(), 'Amazon Business')]"
# Sales View
sales_view_dropdown = "//span[text()='Sales View']"
sales_view_ordered_revenue = "//a[contains(text(), 'Ordered Revenue')]"
sales_view_shipped_revenue = "//a[contains(text(), 'Shipped Revenue')]"
sales_view_shipped_cogs = "//a[contains(text(), 'Shipped COGS')]"
# Components
report_range_datepicker = "//span[text()='Reporting Range']/ancestor::button"
report_range_daily = "//a[contains(text(),'Daily')]"
report_range_weekly = "//a[contains(text(),'Weekly')]"
report_range_monthly = "//a[contains(text(),'Monthly')]"
report_range_quarterly = "//a[contains(text(),'Quarterly')]"
report_range_yearly = "//a[contains(text(),'Yearly')]"
report_filter_apply = "//span[contains(text(), 'Apply')]/ancestor::button"
''' The report range calendar uses elements to create a list containing start and end elements '''
report_range_calendar_elements = "//div[contains(@class, 'react-datepicker__input-container')]"
report_range_calendar_input_elements = "//input[contains(@class, 'date-picker-input')]"
''' The report range available reporting days creates a list containing individual day elements '''
report_range_datepicker_avialable_day_elements = "//div[contains(@class, 'react-datepicker__day') and not(contains(@class, 'day--disabled')) and not(contains(@class, 'day-name'))]"
# The current month is XPATH applied to the element from the 'report_range_datepicker_avialable_day_elements'
report_range_datepicker_current_month = "ancestor::div/*/div[contains(@class, '__current-month')]"
#
report_range_datepicker_available_week_elements = "//div[contains(@class, 'react-datepicker__day') and not(contains(@class, 'day--disabled'))]/parent::div[@class='react-datepicker__week']"
report_range_day_picker = "//span[text()='Viewing']"
report_range_day_picker_available_elements = "//a[contains(@class, 'awsui-button-dropdown-item-content')]"
download_button = "//span[contains(text(),'Download')]/parent::button[not(contains(@aria-disabled, 'true'))]"
download_item_content = "//a[contains(@class, 'awsui-button-dropdown-item-content')]"
download_detail_view_as_csv = "//p[contains(text(), 'Detail View')]/..//*[starts-with(text(), 'As CSV') and not(contains(@aria-disabled, 'true'))]"
                
### Inventory Health POM
# Navigation
inventory_health_link = "//a[text()='Inventory Health']"
inventory_health_header = "//span[@class='dashboard-title' and contains(text(), 'Inventory Health')]"
# Distributor View
distributor_view_dropdown = "//span[contains(text(), 'Distributor View')]/ancestor::button"
distributor_view_manufacturing = "//a[contains(text(), 'Manufacturing')]"
distributor_view_sourcing = "//a[contains(text(), 'Sourcing')]"
distributor_view_consignment = "//a[contains(text(), 'Consignment')]"
# Components
download_inventory_health_as_csv = "//p[contains(text(), 'Inventory Health')]/..//*[starts-with(text(), 'As CSV') and not(contains(@aria-disabled, 'true'))]"

### Net PPM POM
# Navigation
net_ppm_link = "//a[text()='Net PPM']"
net_ppm_header = "//span[@class='dashboard-title' and contains(text(), 'Net PPM')]"
# Components
report_range_weekly_view_text = "//span[text()='Viewing']/parent::span"

### Traffic Diagnostic POM
# Navigation
traffic_diagnostic_link = "//a[text()='Traffic Diagnostic']"
traffic_diagnostic_header = "//span[@class='dashboard-title' and contains(text(), 'Traffic Diagnostic')]"
# Note due to differences in data-reactid tags across programs the 't' is purposefully left off the following locator
traffic_diagnostic_detail_container = "//div[contains(@data-reactid, 'rafficDiagnosticDetail')]/*/span[contains(text(), 'Viewing')]"

### Forecast and Inventory Planning POM
# Navigaion
forecast_inventory_planning_link = "//a[text()='Forecast and Inventory Planning']"
forecast_inventory_planning_header = "//span[@class='dashboard-title' and contains(text(), 'Forecast and Inventory Planning')]"
forecast_inventory_planning_detail_container = "//div[contains(@data-reactid, 'orecastAndInventoryPlanningDetail')]/*/span[contains(text(), 'Viewing')]"
# Sales View
sales_view_ordered_units = "//a[contains(text(), 'Ordered Units')]"
sales_view_shipped_units = "//a[contains(text(), 'Shipped Units')]"
# Components
download_forecast_inventory_planning_as_csv = "//p[contains(text(), 'Forecast and Inventory Planning')]/..//*[starts-with(text(), 'As CSV') and not(contains(@aria-disabled, 'true'))]"
