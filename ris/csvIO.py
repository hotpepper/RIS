import csv


def write(out_file, data_to_write, header=[]):

    row_cnt=0
    with open(out_file, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        #write the header of your output file so the next person reading it knows what the fields are 
        if header !=[]:
            writer.writerow(header)
        #loop through your data and write out
        for row in data_to_write:
            writer.writerow(row) # this writes the rows to the csv file row needs to be a list
            row_cnt+=1
    return str(row_cnt)+" rows were written to "+str(out_file)


def get_file_loc():
        '''TK navigate to file for input - used for error input cases'''
        #print '\nNavigate to the file to upload\n'''
        from Tkinter import Tk
        from tkFileDialog import askopenfilename
        Tk().withdraw() # keep the root window from appearing
        filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file
        print filename
        return filename
        
        
def read(in_file='', tries=0):
    row_cnt=0
    data=[]
    
    try:
        with open(in_file, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                data.append(row)
                row_cnt+=1
        print str(row_cnt)+" rows were read from "+str(in_file)   
        return data
    except:
        while tries<5:
            print 'Your input file was invalid, please select the file you wish to read in. You have '+str(5-tries) +' more attempts'
            tries+=1
            return read(get_file_loc(),tries)
            
        
    

