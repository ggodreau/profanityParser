import os
import re
import pandas as pd
from tqdm import tqdm

class Zerofucks:
    '''Class container for profanity parser utility

    # instantiate class
    myFinder = Zerofucks()
    
    # load in bad words list from file,
    # write to list my_badwords
    my_badwords = []
    badwords_file = open('./bad_words.txt', "r").readlines()
    for line in badwords_file:
        my_badwords.append(line.rstrip())
    '''
    
    def __init__(self):
        self.df = pd.DataFrame(
            {'file': [], 'line_no': [], 'badword': [], 'content': []}, 
            columns=['file', 'line_no', 'badword', 'content']
        )
    
    def __makeRegex__(self, shitToFind=["fuck", "shit"]):
        '''
        shitToFind is a list of word literals,
        uses word boundary \b

        returns a regex string
        '''
        shitString = ''
        for word in shitToFind:
            # shitString += r"\b" + word + r"\b|"
            
            # case insensitive (?i) has deprecation warning:
            # https://github.com/bottlepy/bottle/issues/949
            shitString += r"(?i)\b" + word + r"\b|"
        return shitString[:-1]
        
    def write_df(self, path='./', filename='out.csv'):
        '''
        path: path to where you want to put the file
        filename: name of file
        
        Writes the csv from self.df to a csv file
        '''
        try:
            self.df.to_csv(path_or_buf=path + filename, index=False, chunksize=1000)
            print("File written to {}".format(path + filename))
        except:
            print("Unable to write csv, did you run .find_shit() yet?")
            
    def erase_in_file(self, input_file, replace_with='',  postfix='', bad_words=['fuck', 'shit']):
        '''
        Erases any bad words from the user specified files.
        
        Takes an input file and writes to an outputfile.
        ALSO returns a dictionary for forensic - what did you change - purposes
        
        input_file: full path to the file you want to process / remove bad words from
        replace_with: the string you'll be replacing the bad word with (defaults to nothing, '')
        postfix: optional string value you want to add to the end of the outputfile. If blank, it'll overwrite the input file.
        '''
        
        print('Replacing bad words in {}...'.format(input_file))
        try:
            tempfile = open(input_file + '.tmp', mode='w')
            with open(input_file, 'r', encoding='iso-8859-15') as infile:
                shit_dict = {}
                for content in tqdm(infile):
                    if len(re.findall(self.__makeRegex__(bad_words), content)) > 0:
                        if re.findall(self.__makeRegex__(bad_words), content)[0] in shit_dict:
                            shit_dict[re.findall(self.__makeRegex__(bad_words), content)[0]] += 1
                        else:
                            shit_dict[re.findall(self.__makeRegex__(bad_words), content)[0]] = 1
                    # the '' in this line is what to replace the bad words with. In this case, nothing at all.
                    tempfile.write(re.sub(self.__makeRegex__(bad_words), replace_with, content))
            # write the tempfile contents to the original file  
            print('overwriting {} with {}'.format(input_file+'.tmp', input_file+postfix))
            os.rename(input_file + '.tmp', input_file+postfix)
            return shit_dict
        except ValueError:
            print(f'Unable to replace bad words in {input_file}.')
            
    def erase_in_dirs(self, root_paths, postfix='', bad_words=['fuck', 'shit'], ignore_extensions=['ipynb']):
        '''
        root_paths: LIST of directories to replace shit in. Must be a list. Cannot be a specific file.
        postfix: string to add to the end of the name of the output file. If input is 'myFile.csv' with a postfix of '_new', the scrubbed file would be 'myFile.csv_new'. No prefix overwrites the existing file.
        bad_words: optional list of words to replace in the files within root_paths
        '''
    
        audit_log = {
            'ignored': [],
            'processed': []
        }

        for root_path in root_paths:
            for (root, dirs, files) in os.walk(root_path):
                for name in files:
                    try:
                        # if the file extension is one we want to ignore
                        file_ext = name.split('.')[-1]
                        if file_ext in ignore_extensions:
                            print(f'ignoring {self.__get_path(root, dirs, name)}')
                            # add the filename to the ignored section of the audit_log
                            audit_log['ignored'].append(self.__get_path(root, dirs, name))
                            continue
                        # otherwise, we'll erase shit in it
                        else:
                            print(f'deleting shit in {self.__get_path(root, dirs, name)}')
                            self.erase_in_file(root+'/'+name, postfix=postfix, bad_words=bad_words)
                            audit_log['processed'].append(self.__get_path(root, dirs, name))
                    # if the filename has no extension, we still process it
                    except:
                        print(f'no file extension in {self.__get_path(root, dirs, name)}, erasing shit anyway')
                        self.erase_in_file(root+'/'+name, postfix=postfix, bad_words=bad_words)
                        audit_log['processed'].append(self.__get_path(root, dirs, name))
        return audit_log

    
    def find_shit(self, root='./', bad_words=['fuck', 'shit'], include_content=True):
        '''
        root: the directory root where you want the crawl to start
        bad_words: list of words you want to search for.
            These can also be regular expressions. It will
            match partials, so 'fuck' will match 'fucking',
            'unfuckingbelievable', etc. Use \b and similar
            to constrain to word boundaries.
        
        The meat and potatoes, this is what conducts the walk
        and writes the resultant dataframe to self.df.
        
        To export the df to a csv, use the write_df() method.
        '''        
        for item in os.walk(root):
            
            # keep records for each directory parsed
            file_df = []
            line_no_df = []
            badword_df = []
            if include_content:
                content_df = []
            
            for file in item[2]:
                print('Searching {}'.format(item[0]+'/'+file))
                try:
                    openfile = open(item[0] + '/' + file, "r").readlines()
                    for line_no, content in enumerate(openfile):
                        if len(re.findall(self.__makeRegex__(bad_words), content)) > 0:
                            for i, badword in enumerate(re.findall(self.__makeRegex__(bad_words), content)):
                                file_df.append(item[0]+'/'+file)
                                line_no_df.append(line_no)
                                badword_df.append(re.findall(self.__makeRegex__(bad_words),content)[i])
                                # rstrip to remove newline character
                                if include_content:
                                    content_df.append(content.rstrip())
                except:
                    pass
                            
#             print(content_df)

            # write the records to the dataframe with each dir parsed
            if include_content:
                self.df = self.df.append(pd.DataFrame({'file': file_df, 
                                'line_no': line_no_df, 
                                'badword': badword_df,
                                'content': content_df},
                                columns=['file', 'line_no', 'badword', 'content']),
                                ignore_index=True)
            else:
                self.df = self.df.append(pd.DataFrame({'file': file_df, 
                    'line_no': line_no_df, 
                    'badword': badword_df},
                    columns=['file', 'line_no', 'badword']),
                    ignore_index=True)
        
        # change the silly auto-detected float line_no to an integer
        self.df['line_no'] = self.df.copy()['line_no'].apply(lambda x: int(x))
        # return self.df
        print("Dataframe successfully created, \n \
            use <obj>.df to print the df, or \n \
            .write_df() method to write to file.")


    def __get_path(self, root, dirs, name):
        '''
        returns the full path as a string
        '''
        dir_string = ''
        num_dirs = len(dirs)
    
        if num_dirs == 0:
            return(root+'/'+name)
        else:
            for idx, dir in enumerate(dirs):
                if idx < num_dirs:
                    dir_string += dir + '/'
                else:
                    dir_string += dir
            return(root+dir_string+name)

