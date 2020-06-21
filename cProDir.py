# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse as ap
import getpass
import math
from datetime import datetime

version = 0.1

### FUNCTIONS

def error(string, error_type=1):
    sys.stderr.write(f'ERROR: {string}\n')
    sys.exit(error_type)

def log(string, newline_before=False):
    if newline_before:
        sys.stderr.write('\n')
    sys.stderr.write(f'LOG: {string}\n')

def write(string, filepath1, filepath2=None):
    with open(filepath1, 'a+') as w:
        w.write(string + '\n')
    w.close()
    if filepath2 is not None:
        with open(filepath2, 'a+') as w:
            w.write(string + '\n')
        w.close()

def linkAllFiles(walkpath, dst, depth=0):
    files = 0
    folders = 1
    foldersize = 0

    # check and edit input path strings
    tab = '|---'
    if dst[-1] != '/' and dst != '':
        dst+='/'
    if walkpath[-1] != '/':
        walkpath+='/'

    # make sure directory exists
    if not os.path.exists(dst):
        os.makedirs(dst)

    # walk files and link them
    entry = next(os.walk(walkpath))
    for linkfile in entry[2]:
        linkdst = dst + linkfile
        os.link(src=walkpath + linkfile, dst=linkdst)

        # write readme and log
        points = '.' * (60-len(f'{tab*depth}|--> {linkdst.split(project_name)[-1]}'))
        filesize = os.path.getsize(linkdst)
        write(f'``{tab*depth}|--> {linkdst.split(project_name)[-1]}{points}{humanbytes(filesize)}``<br>', readmemd)
        log(f'Linked {walkpath + linkfile} to {dst + linkfile}')
        files += 1
        foldersize += filesize

    # walk directories
    for linkdir in entry[1]:
        write(f'``{tab*depth}|--> {dst.split(project_name)[-1]}{linkdir}``<br>', readmemd)
        return tuple(map(sum, zip((files, folders, foldersize), linkAllFiles(walkpath=walkpath + linkdir + '/', dst=dst + linkdir + '/', depth=depth + 1))))

    return (files, folders, foldersize)

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


### PARAMS

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

### CHECK INPUT

project_name = args.project
datalink = args.link
ext = args.docext
mlbool = args.machine_learning
user = getpass.getuser()
time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# create often used variables
cwd = os.getcwd()
pwd = cwd + '/' + project_name + '/'

### CREATE PROJECT DIRECTORY

# creating project working directory 'pwd'
if os.path.exists(pwd):
    error(f'Path {pwd} already exists!\nStopped with error code 1!', 1)

os.makedirs(pwd)
readmemd = pwd + 'README.md'
readmesh = pwd + 'README.sh'
log(f'Created project {project_name} directory in {pwd}')

# making directories
readmes = {}
project_dirs = ['src', 'res', 'bin', 'lib', 'doc', 'build', 'out', 'out/plots', 'temp']
for dire in project_dirs:
    os.makedirs(pwd + dire)
    log(f'Created {pwd + dire}')
    if dire != 'out/plots' and dire != 'doc':
        readmes[dire] = pwd + dire + '/README.md'
        write(f'# Created markdown file for {dire} on {time} from {user}.', readmes[dire])
        log(f'Created {readmes[dire]}')


### CREATE PROJECT FILES

# creating documentation file
docfile = pwd + f'doc/{project_name}.{ext}'
write(f'# Project {project_name}: {ext} documentation file of {project_name}.', docfile)
write(f'{project_name} created by {user} on {time}.', docfile)
log(f'Created {docfile}')

# writing major readme file
write(f'# Project {project_name}', readmemd, readmesh)
write(f'# Created with cProDir version {version}.', readmesh)
write(f'# Project {project_name} created on {time} from {user}.', readmesh)
write(f'-    Created with cProDir version {version}.', readmemd)
write(f'-    Project {project_name} created on {time} from {user}.', readmemd)
write(f'\n# {project_name} directory structure:', readmemd)
write('-   src: containing project scripts', readmemd)
write('-   res: containing project resources and data', readmemd)
write('-   bin: containing project binaries', readmemd)
write('-   lib: containing external libraries', readmemd)
write('-   doc: containing project documentation files', readmemd)
write('-   build: containing project binaries', readmemd)
write('-   temp: containing temporary files', readmemd)
write('-   out: containing output files, produced by processing/analyzing resources', readmemd)
write('-   out/plots: containing output plot files and diagrams', readmemd)

# if no datalink provided create train and validate data folders
if datalink is None and mlbool:
    os.makedirs(pwd + 'res/traindata/')
    log(f'Created {pwd}res/traindata/')
    os.makedirs(pwd + 'res/valdata/')
    log(f'Created {pwd}res/valdata/')

# linking data
elif datalink is not None:
    write('\n# Data to be analyzed:', readmemd)
    write(f'Resources/Data linked from<br>\n{os.path.abspath(datalink)}<br>', readmemd)
    (files, folders, datasize) = linkAllFiles(walkpath=datalink, dst=pwd+'res/')
    log(f'Linked {files} files in {folders} folders.')
    write(f'Linked {files} files in {folders} folders with a total datasize of {humanbytes(datasize)}.', readmemd)
    log(f'Linked data of size {humanbytes(datasize)}')
    log('Done linking resources/data.')

log(f'Created {readmemd} and {readmesh}')
