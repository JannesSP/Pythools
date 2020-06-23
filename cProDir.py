# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import argparse as ap
import getpass
import math
import copy
import git
import socket
import platform
import psutil
import GPUtil
from datetime import datetime

version = '0.4'

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

def checkOrcID(orcid):
    # splits orcid into digit set
    digitSets = orcid.split('-')
    # check orcid format
    for digSet in digitSets:
        if not len(digSet) == 4 and bool(re.search(r'^\d{4}$', digSet)):
            return False

    # split into base digits and check digit
    baseDigits = list(map(int, digitSets[0] + digitSets[1] + digitSets[2][:-1]))
    checkDigit = orcid[-1]

    # calculating checksum
    total = 0
    for i in baseDigits:
        total = (total + i) * 2
    remainder = total % 11
    result = (12 - remainder) % 11
    if result == 10:
        result = 'X'

    # comparing checksum with check digit
    return str(result) == checkDigit 

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
        points = '.' * (60-len(f'{tab*depth}|--> {linkdst.split(project_dir)[-1]}'))
        filesize = os.path.getsize(linkdst)
        write(f'``{tab*depth}|--> {linkdst.split(project_dir)[-1]}{points}{humanbytes(filesize)}``<br>', readmemd)
        log(f'Linked {walkpath + linkfile} to ./{project_dir + dst.split(project_dir)[1] + linkfile}')
        files += 1
        foldersize += filesize

    # walk directories
    for linkdir in entry[1]:
        write(f'``{tab*depth}|--> {dst.split(project_dir)[-1]}{linkdir}``<br>', readmemd)
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

def getSpecs():
    cpufreq = psutil.cpu_freq()
    svmem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    gpus = GPUtil.getGPUs()
    gpustring = ''
    for gpu in gpus:
        gpustring += f'ID: {gpu.id}\n\tGPU: {gpu.name}\n\tTotal memory: {gpu.memoryTotal}MB\n'
    
    partitions = psutil.disk_partitions()
    diskstring = ''
    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            continue
        diskstring += (f'Device: {partition.device}\n\t' + 
                       f'Mountpoint: {partition.mountpoint}\n\t' + 
                       f'Disk: {partition.fstype}\n\t' + 
                       f'Total Size: {humanbytes(partition_usage.total)}\n\t' + 
                       f'Used: {humanbytes(partition_usage.used)}\n\t' + 
                       f'Free: {humanbytes(partition_usage.free)}\n\t' +
                       f'Percentage: {partition_usage.percent}\n')

    return ('Project created on:\n' +
            f'System: {platform.system()}\n' + 
            f'Release: {platform.release()}\n' +
            f'Version: {platform.version()}\n' +
            f'Host: {socket.gethostname()}' +
            f'CPU: {platform.processor()}' +
            f'Physical Cores: {psutil.cpu_count(logical=False)}\n' +
            f'Physical Cores: {psutil.cpu_count(logical=True)}\n' +
            f'Max Frequency: {cpufreq.max:.2f}Mhz\n' + 
            f'Min Frequency: {cpufreq.min:.2f}Mhz\n' + 
            f'RAM: {humanbytes(svmem.total)}\n' +
            f'Swap Memory: {humanbytes(swap.total)}\n' +
            diskstring +
            gpustring)

def latex():
    log('Create latex files.')
    latexPath = f'./{project_dir}/doc/latex'
    os.makedirs(latexPath)
    log(f'Created {latexPath}')

    # generate main.tex
    with open('./latex_template.tex', 'r') as tex_template:
        with open(f'{latexPath}/main.tex', 'w+') as tex_main:
            for line in tex_template.readlines():
                tex_main.write(line)
        tex_main.close()
    tex_template.close()
    log(f'Created {latexPath}/main.tex')

    # generate title page
    with open(f'{latexPath}/title_page.tex', 'w+') as tex_title:
        titleOrg = ''
        if organization != '':
            titleOrg = '\tOrganization:\\par\n\t{\\scshape\\Large ' + organization + '\\par}\n\t\\vfill\n'

        titleORCID = ''
        if orcid != '':
            titleORCID = f'\tORCID:\thttps://orcid.org/{orcid}\n'

        tex_title.write('\\begin{titlepage}\n' + 
                        '\t\\centering\n' + 
                        '\t\\vfill\n' + 
                        titleOrg +
                        '\tProject:\\par\n' + 
                        '\t{\\scshape\\large ' + project_name + '\\par}\n' +
                        '\t\\vspace{1.5cm}\n' +
                        '\t{\\huge\\bfseries ' + project_description + '\\par}\n' +
                        '\t\\vfill\n' +
                        '\tWritten by:\\par\n' + 
                        '\t{\\large\\itshape ' + author + '\\par}\n' +
                        titleORCID +
                        '\t\\vfill\n' +
                        '\tsupervised by \\par\n' +
                        f'\t{supervisor}\n' +
                        '\t\\vfill\n' +
                        '\t{\\large \\today\\par}\n' + 
                        '\\end{titlepage}')
    tex_title.close()
    log(f'Created {latexPath}/title_page.tex')

    # generate abstract
    with open(f'{latexPath}/abstract.tex', 'w+') as tex_abstract:
        tex_abstract.write('\\section*{Abstract}\n' +
                           '\t\n' + 
                           '\t% TODO: Write your abstract here')
    tex_abstract.close()
    log(f'Created {latexPath}/abstract.tex')

    # generate abbreviations
    with open(f'{latexPath}/abbreviations.tex', 'w+') as tex_abbrev:
        tex_abbrev.write('\\section*{\\Huge Abbreviations}\n' + 
                         '\t\\begin{acronym}\n' +
                         '\t\t\n' +
                         '\t\t%TODO: add abbreviations here.\n' +
                         '\t\t\n' + 
                         '\t\\end{acronym}')
    tex_abbrev.close()
    log(f'Created {latexPath}/abbreviations.tex')

    # prepare doc sections
    sections = {'introduction': 'Introduction',
                'materials_methods': 'Materials and Methods',
                'results': 'Results',
                'discussion': 'Discussion'}

    # generate doc sections
    for section in sections.keys():
        with open(f'{latexPath}/{section}.tex', 'w+') as tex_intro:
            tex_intro.write('\\section{' + sections[section] + '}\n' + 
                            '\n' + 
                            f'\t% TODO: Write {sections[section].lower()} here.\n' + 
                            '\t\n')
        tex_intro.close()
        log(f'Created {latexPath}/{section}.tex')

    # generate attachments 
    with open(f'{latexPath}/attachments.tex', 'w+') as tex_attach:
        tex_attach.write('\\section*{\\Huge Attachments}\n' + 
                         '\t\n' +
                         '\t% TODO: Add your attachments here.\n')
    tex_attach.close()
    log(f'Created {latexPath}/attachments.tex')

    # generate citations
    with open(f'{latexPath}/citations.bib', 'w+') as tex_bib:
        tex_bib.write('% Encoding: UTF-8\n' +
                      '\n' +
                      '% TODO: Add your references here.')
    tex_bib.close()
    log(f'Created {latexPath}/citations.bib')

### PARAMS

parser = ap.ArgumentParser(
    description='cProDir.py helps you with Creating your PROject DIRectory with good structure for better navigation and reproducibility.',
    formatter_class=ap.HelpFormatter,
    epilog=f'You are currently using version {version}!'
)

# required arguments
projectgroup = parser.add_mutually_exclusive_group(required=True, )
projectgroup.add_argument('-p', '--project', metavar='PATH_TO_PROJECT/PROJECT_NAME', default=None, type=str, help='Name of the project you want to create locally. You can add a path, where the project is created.')
projectgroup.add_argument('-g', '--git', metavar='GIT_URL', type=str, default=None, help='Use this argument if you already made an empty repository and want to add your project to the remote repository.')

# optional arguments
parser.add_argument('-pd', '--project_description', metavar='SHORT_DESCRIPTION', default='', type=str, help='Short description about the project.')
parser.add_argument('-l', '--link', metavar='PATH', type=str, default=None, help='Path of the folder of your resources/data.\nThe linked resources or data can be found in ./<project>/res/.')
parser.add_argument('-ml', '--machine_learning', nargs=2, metavar=('TRAINDATA', 'VALDATA'), type=str, default=(None, None), help='Path to traindata and path to validationsdata.\nData gets linked into ./<project>/res/ folder.')
parser.add_argument('-i', '--gitignore', metavar='LIST', action='append', default=None, type=list, help='List of \'directories\' or \'files\' that should be ignored in git version control.\nOnly possible if -g is used!')
parser.add_argument('-a', '--author', metavar='NAME', default=None, type=str, help='Name of the author of the project in quotation marks: "Forename ... Surname".')
parser.add_argument('-s', '--supervisor', metavar='NAME', default='', type=str, help='Name of the supervisor in quotation marks: "Forename ... Surname"..')
parser.add_argument('-org', '--organization', metavar='NAME', default='', type=str, help='Name of the organization in quotation marks: "...".')
parser.add_argument('-oid', '--orcid', metavar='ORCID', default='', type=str, help='ORCID of the author of the project. Should look like XXXX-XXXX-XXXX-XXXX')
parser.add_argument('-tex', '--latex', action='store_true', help='Use this parameter to generate latex files for project work.')
parser.add_argument('-sp','--specs', action='store_true', help='Use this parameter to generate hardware specs in your docfile.')

parser.add_argument('-v', '--version', action='version', version=f'\n%(prog)s {version}')

args = parser.parse_args()

activeParams = {'latex': args.latex, 'specs': args.specs}

datalink = args.link
project_description = args.project_description
organization = args.organization
supervisor = args.supervisor
tex = args.latex
orcid = args.orcid
trainlink = args.machine_learning[0]
vallink = args.machine_learning[1]
author = getpass.getuser()
time = datetime.now().strftime("%Y.%m.%d %H:%M:%S")

# create often used variables
cwd = os.getcwd()

### CHECK INPUT
projectInput = {'local': False, 'git': False}

# check if orcid syntax and checksum
if args.orcid != '':
    if checkOrcID(orcid):
        error('ORCID does not match standards!', 5)

if args.author is not None:
    author = args.author

if args.project is not None:
    project_dir = args.project.replace(' ', '_')
    project_name = args.project.split('/')[-1].replace('_', ' ')
    pwd = cwd + '/' + project_dir + '/'
    projectInput['local'] = True

if args.git is not None:
    giturl = args.git
    project_dir = giturl.split('/')[-1].replace(' ', '_')
    project_name = giturl.split('/')[-1].replace('_', ' ')
    pwd = cwd + '/' + project_dir + '/'
    git_user_name = giturl.split('/')[-2]
    git_service = giturl.split('/')[-3]
    projectInput['git'] = True
    log(f'Using git {giturl} for version control!')

### CREATE PROJECT DIRECTORY

# creating project working directory 'pwd'
if os.path.exists(pwd):
    error(f'Path {pwd} already exists!\nStopped with error code 1!', 1)

if datalink is not None and not os.path.exists(datalink):
    error(f'Path {datalink} does not exist!\nStopped with error code 2!', 2)

if datalink is not None and (trainlink is not None or vallink is not None):
    error(f'Cannot use --link and --machine_learning together! Please choose only one of them!', 3)

if args.gitignore is not None and args.git is None:
    error(f'Can use --gitignore only if --git is used!', 4)

if projectInput['git']:
    repo = git.Repo.clone_from(giturl, pwd)

if projectInput['local']:
    os.makedirs(pwd)

if projectInput['git']:
    for f in args.gitignore:
        write(f, pwd + '.gitignore')

readmemd = pwd + 'README.md'
readmesh = pwd + 'README.sh'
log(f'Created project {project_name} directory in {pwd}')
rpwd = './' + project_dir + pwd.split(project_dir)[1]

# making directories
readmes = {}
project_dirs = ['src', 'res', 'bin', 'lib', 'doc', 'build', 'out', 'out/plots', 'temp']
for dire in project_dirs:

    # check if path already exists
    if os.path.exists(pwd + dire):
        log(f'Path {rpwd+dire} already exists!')    
    else:
        os.makedirs(pwd + dire)
        log(f'Created {rpwd + dire}')
    
    # dont create readmes for out/plots and doc
    if dire != 'out/plots' and dire != 'doc':
        readmes[dire] = rpwd + dire + '/README.md'
        write(f'<!-- Created markdown file for {dire}/ on {time} from {author}. -->', readmes[dire])
        log(f'Created {readmes[dire]}')

write(f'res contains the resource data the way you like, either the hard links to your resource data or the actual resource data files.', readmes['res'])


### CREATE PROJECT FILES

# creating documentation file
docfile = rpwd + f'doc/{project_name}_protocol.md'
write(f'# Project {project_name}: Markdown documentation file of {project_name}.', docfile)
write(f'{project_name} created by {author} on {time}.', docfile)
command = ''
for arg in sys.argv:
    command += arg
write(f'Used command for creation is:\n{command}', docfile)
log(f'Created {docfile}')

if activeParams['latex']:
    latex()

# add files to commit for git
if projectInput['git']:
    files = list(readmes.values())
    files.append(docfile)
    repo.index.add(files)
    repo.index.commit(f'initial commit of {project_name} with cProDir {version}')
    log(f'Added {len(files)} files to git commit.')

# writing major readme file
write(f'# Project {project_name} created on {time} from {author}.', readmemd, readmesh)
write(f'# Created with cProDir version {version}.', readmesh)

if projectInput['git']:
    write(f'# Using git {giturl} for version control on account {git_user_name} on {git_service}.', readmesh)
    write(f'-    Using git {giturl} for version control on account {git_user_name} on {git_service}.', readmemd)

write(f'-    Created with cProDir version {version}.', readmemd, docfile)
write(f'-    Project {project_name} created on {time} from {author}.', readmemd, docfile)

if orcid != '':
    write(f'-    ORCID of the author: https://orcid.org/{orcid}', readmemd, docfile)

if supervisor != '':
    write(f'-    Project supervised by: {supervisor}', readmemd, docfile)

if organization != '':
    write(f'-    Project developed in the organization: {organization}', readmemd, docfile)

write(f'\n# {project_dir} directory structure:', readmemd, docfile)
write('-   src: containing project scripts', readmemd, docfile)
write('-   res: containing project resources and data', readmemd, docfile)
write('-   bin: containing project binaries', readmemd, docfile)
write('-   lib: containing external libraries', readmemd, docfile)
write('-   doc: containing project documentation files', readmemd, docfile)
write('-   build: containing project binaries', readmemd, docfile)
write('-   temp: containing temporary files', readmemd, docfile)
write('-   out: containing output files, produced by processing/analyzing resources', readmemd, docfile)
write('-   out/plots: containing output plot files and diagrams', readmemd, docfile)

if activeParams['specs']:
    write('\n' + getSpecs(), readmemd, docfile)

# if no datalink provided create train and validate data folders
if trainlink is not None or vallink is not None:
    os.makedirs(pwd + 'res/traindata/')
    log(f'Created {pwd}res/traindata/')
    os.makedirs(pwd + 'res/valdata/')
    log(f'Created {pwd}res/valdata/')
    write('\n# Data to be analyzed:', readmemd, docfile)
    
    if trainlink is not None:
        write(f'Resources/Data linked from<br>\n{os.path.abspath(trainlink)}<br>', readmemd, docfile)
        (files, folders, datasize) = linkAllFiles(walkpath=trainlink, dst=pwd+'res/traindata/')
        log(f'Linked traindata: {files} files in {folders} folders.')
        log(f'Linked traindata of size {humanbytes(datasize)}')
        write(f'Linked traindata: {files} files in {folders} folders with a total datasize of {humanbytes(datasize)}.<br>\n', readmemd, docfile)

    if vallink is not None:
        write(f'Resources/Data linked from<br>\n{os.path.abspath(vallink)}<br>', readmemd, docfile)
        (files, folders, datasize) = linkAllFiles(walkpath=vallink, dst=pwd+'res/valdata/')
        log(f'Linked validationdata: {files} files in {folders} folders.')
        log(f'Linked validationdata of size {humanbytes(datasize)}')
        write(f'Linked validationdata: {files} files in {folders} folders with a total datasize of {humanbytes(datasize)}.<br>\n', readmemd, docfile)

# linking data
elif datalink is not None:
    write('\n# Data to be analyzed:', readmemd)
    write(f'Resources/Data linked from<br>\n{os.path.abspath(datalink)}<br>', readmemd, docfile)
    (files, folders, datasize) = linkAllFiles(walkpath=datalink, dst=pwd+'res/')
    log(f'Linked {files} files in {folders} folders.')
    write(f'Linked {files} files in {folders} folders with a total datasize of {humanbytes(datasize)}.', readmemd, docfile)
    log(f'Linked data of size {humanbytes(datasize)}')
    log('Done linking resources/data.')

# push commits to git remote
if projectInput['git']:
    repo.remote("origin").push()
    log(f'Pushed files to {giturl}.')

log(f'Created {readmemd}, {readmesh} and {docfile}')
log('Done')