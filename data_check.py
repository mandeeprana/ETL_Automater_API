#!/opt/telstar-data/venvs/amazonara/bin/python

# Activate the virtualenv
activate_this = '/opt/telstar-data/venvs/amazonara/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import datetime, re 
from telstar.kcbase import utils

use_nonprod_data_dir = False

ara_download_path = '/opt/telstar-data/venvs/amazonara/downloads/'
ara_log_path = '/opt/telstar-data/venvs/amazonara/logs/'
ara_file_path = '/cifs/rainier/'
if use_nonprod_data_dir:
    # Override production ara_file_path set above 
    ara_file_path = '/opt/telstar-data/venvs/amazonara/rainier_local/'

results = ''
data_files = utils.get_dir_filenames(ara_file_path, pattern='^.*\.csv$')
file_list = [x.split('/')[-1] for x in data_files]
file_list.sort(reverse=True)
for this_file in file_list:
    results += 'File:  {}\n{}\n'.format(this_file, utils.spcall('head -n 1 {}{}'.format(ara_file_path, re.sub(r' ', '\ ', this_file))))

#RX_ARA = re.compile(r'(Program=\[.*?\])|(Distributor View=\[.*?\])|(Sales View=\[.*?\])|(Reporting Range=\[.*?\])')
RX_ARA = re.compile(r'Program=\[(.*?)\]|Distributor View=\[(.*?)\]|Sales View=\[(.*?)\]|Reporting Range=\[(.*?)\]')

def stringer(in_list):
    result = ''
    dis_hold = ''
    for l in in_list:
        for i, val in enumerate(l):
            if i == 1 and val:
                dis_hold = ' {}'.format(val)
            elif val:
                result += ' {}, '.format(val)
    result += dis_hold
    return result    

compare_string = ''
for i in results.splitlines():
    #print '------------{}'.format(i)
    if 'File' in i:
        compare_string += '{}\n'.format(i.split('/')[-1])
    else:
        try:
            compare_string += '{}\n'.format(stringer(RX_ARA.findall(i)))
        except:
            pass

a =[]
a.sort

utils.writeLog('{}{}_data_check.txt'.format(ara_log_path, datetime.datetime.now().strftime('%Y%m%d%H%M%S')), compare_string)