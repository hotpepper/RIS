import csv
import shutil
import os
from Tkinter import Tk
from tkFileDialog import askopenfilename

def file_loc():
    Tk().withdraw()
    filename = askopenfilename() 
    return filename

def get_urls(file_path):
    data = []
    with open(file_path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row['case_link'])
    return data
        
def copy_reports(file_path, url_list):
    out_path = os.path.dirname(file_path) + '\Reports'
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    
    for report in url_list:
        if os.path.isfile(report):
            print 'Copying %s' % report # os.path.basename(report)
            shutil.copyfile(report, os.path.join(out_path, os.path.basename(report)))
        else:
            print '%s Report does not exist'
    os.startfile(out_path)
    
file_path = file_loc() 
copy_reports(file_path, get_urls(file_path))
