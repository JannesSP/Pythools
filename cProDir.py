# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse as ap
import getpass
import math
from datetime import datetime

#import ArgumentParser, ArgumentDefaultsHelpFormatter

version = 0.1

# FUNCTIONS

def error(string, error_type=1):
    sys.stderr.write(f'ERROR: {string}\n')
    sys.exit(error_type)

def log(string, newline_before=False):
    if newline_before:
        sys.stderr.write('\n')
    sys.stderr.write(f'LOG: {string}\n')

def write(string, filepath):
    with open(filepath, 'a+') as w:
        w.write(string + '\n')
    w.close()

def linkAllFiles(walkpath, dst, depth=0, tabsize=0):
    # check and edit input path strings
    tab = '\t'
    if dst[-1] != '/' and dst != '':
        dst+='/'
    if walkpath[-1] != '/':
        walkpath+='/'

    tabsize += math.ceil(len(walkpath.split("/")[-2])/8)
    sepFileSize = tab*(10-tabsize)

    # make sure directory exists
    if not os.path.exists(dst):
        os.makedirs(dst)

    # walk files and link them
    entry = next(os.walk(walkpath))
    for linkfile in entry[2]:
        linkdst = dst + linkfile
        os.link(src=walkpath + linkfile, dst=linkdst)

        # write readme and log
        write(f'{tab*depth}| --> {linkdst.split(project_name)[-1]}{sepFileSize}{humanbytes(os.path.getsize(linkdst))}', readmefile)
        log(f'Linked {walkpath + linkfile} to {dst + linkfile}')
    
    # walk directories
    for linkdir in entry[1]:
        linkAllFiles(walkpath=walkpath + linkdir + '/', dst=dst + linkdir + '/', depth=depth + 1, tabsize=tabsize + 1)

# https://stackoverflow.com/questions/12523586/python-format-size-application-converting-b-to-kb-mb-gb-tb
def humanbytes(B):
    '''Return the given bytes as a human friendly KB, MB, GB, or TB string'''
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2) # 1,048,576
    GB = float(KB ** 3) # 1,073,741,824
    TB = float(KB ** 4) # 1,099,511,627,776

    if B < KB:
        return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
    elif KB <= B < MB:
        return '{0:.4f} KB'.format(B/KB)
    elif MB <= B < GB:
        return '{0:.4f} MB'.format(B/MB)
    elif GB <= B < TB:
        return '{0:.4f} GB'.format(B/GB)
    elif TB <= B:
        return '{0:.4f} TB'.format(B/TB)


# PARAMS

parser = ap.ArgumentParser(
    description='cProDir.py helps you with creating your working directory to your wishes and desires.',
    formatter_class=ap.HelpFormatter,
    epilog=f'You are currently using version {version}!'
)

# required arguments
parser.add_argument('project', metavar='project', type=str)

# optional arguments
parser.add_argument('-d', '--docext', metavar='EXTENSION', default='md', type=str, help='DOCumentation datatype EXTension for your documentation files. Standard is md for markdown.\n')
parser.add_argument('-l', '--link', metavar='PATH', type=str, default=None, help='Path of the folder of your resources/data.\nThe linked resources or data can be found in ./<project>/res/.')
parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {version}')
parser.add_argument('-ml', '--machine_learning', type=bool, default=False, help='')

args = parser.parse_args()

# CHECK INPUT

project_name = args.project
datalink = args.link
ext = args.docext
mlbool = args.machine_learning
user = getpass.getuser()

# time
now = datetime.now()
current_time = now.strftime("%Y-%m-%d_%H-%M-%S")

# create often used variables
cwd = os.getcwd()
pwd = cwd + '/' + project_name + '/'

# CREATE PROJECT DIRECTORY

# creating project working directory 'pwd'
if os.path.exists(pwd):
    error(f'Path {pwd} already exists!\nStopped with error code 1!', 1)

os.makedirs(pwd)
readmefile = pwd + 'README.md'
log(f'Created project {project_name} directory in {pwd}')

os.makedirs(pwd + 'src/')
log(f'Created {pwd}src/')

os.makedirs(pwd + 'res/')
log(f'Created {pwd}res/')

os.makedirs(pwd + 'bin/')
log(f'Created {pwd}bin/')

os.makedirs(pwd + 'lib/')
log(f'Created {pwd}lib/')

os.makedirs(pwd + 'doc/')
docfile = pwd + f'doc/{project_name}.{ext}'
log(f'Created {pwd}doc/')

os.makedirs(pwd + 'build/')
log(f'Created {pwd}build/')

os.makedirs(pwd + 'out/')
os.makedirs(pwd + 'out/plots/')
log(f'Created {pwd}out/')
log(f'Created {pwd}out/plots/')

os.makedirs(pwd + 'temp/')
log(f'Created {pwd}temp/')

# CREATE PROJECT FILES

# creating documentation file
write(f'# Markdown documentation file of {project_name}.', docfile)
log(f'Created {docfile}')

# writing readme file
write(f'# Project {project_name}', readmefile)
write(f'-    Created with cProDir version {version}.', readmefile)
write(f'-    Project {project_name} created on {current_time} from {user}.', readmefile)
write(f'\n# {project_name} directory structure:', readmefile)
write('-   src: containing project scripts', readmefile)
write('-   res: containing project resources and data', readmefile)
write('-   bin: containing project binaries', readmefile)
write('-   lib: containing external libraries', readmefile)
write('-   doc: containing project documentation files', readmefile)
write('-   build: containing project binaries', readmefile)
write('-   temp: containing temporary files', readmefile)
write('-   out: containing output files, produced by processing/analyzing resources', readmefile)
write('-   out/plots: containing output plot files and diagrams', readmefile)

# if no datalink provided create train and validate data folders
if datalink is None and mlbool:
    os.makedirs(pwd + 'res/traindata/')
    log(f'Created {pwd}res/traindata/')
    os.makedirs(pwd + 'res/valdata/')
    log(f'Created {pwd}res/valdata/')

# linking data
elif datalink is not None:
    write('\n# Data to be analyzed:', readmefile)
    write(f'Resources/Data linked from\n{os.path.abspath(datalink)}', readmefile)
    linkAllFiles(walkpath=datalink, dst=pwd+'res/')
    log('Done linking resources/data.')

    # entry1 = next(os.walk(datalink))
        
    # # write files from level 1 in readmefile
    # for res_file in entry1[2]:
    #     write(f'| --> {res_file}', readmefile)

    # # look into resource directories level 1
    # for res_dir1 in entry1[1]:
    #     write(f'| --> {res_dir1}/', readmefile)
    #     entry2 = next(os.walk(datalink + res_dir1))

    #     # write files from level 2 in readmefile
    #     for res_file in entry2[2]:
    #         write(f'      | --> {res_file}     {os.path.getsize(res_dir1 + res_file)}', readmefile)

    #     # look into resource directories level 2
    #     for res_dir2 in entry2[1]:
    #         write(f'      | --> {res_dir2}/', readmefile)

log(f'Created {readmefile}')