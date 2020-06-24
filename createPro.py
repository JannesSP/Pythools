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
from pathlib import Path
from datetime import datetime

### FUNCTIONS

def error(string, error_type=1):
    sys.stderr.write(f'ERROR: {string}\n')
    sys.exit(error_type)

def log(string, newline_before=False):
    if newline_before:
        sys.stderr.write('\n')
    sys.stderr.write(f'LOG: {string}\n')

def write(string, *files):
    for file in files:
        with open(file, 'a+') as w:
            w.write(string + '\n')
        w.close()
    
def writeDirDescription(project_name, *files):
    for file in files:
        write(f'\n## {project_name} directory structure:', file)
        write('-   src: containing project scripts', file)
        write('-   res: containing project resources and data', file)
        write('-   bin: containing project binaries', file)
        write('-   lib: containing external libraries', file)
        write('-   doc: containing project documentation files', file)
        write('-   build: containing project binaries', file)
        write('-   temp: containing temporary files', file)
        write('-   out: containing output files, produced by processing/analyzing resources', file)
        write('-   out/plots: containing output plot files and diagrams', file)

def isORCID(orcid):
    # splits orcid into digit set
    digitSets = orcid.split('-')
    # check orcid format
    for digSet in digitSets:
        if not len(digSet) == 4 or not bool(re.search(r'^\d{3}(\d|X)$', digSet)):
            return False

    # split into base digits and check digit
    baseDigits = list(map(int, digitSets[0] + digitSets[1] + digitSets[2] + digitSets[3][:-1]))
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

def linkAllFiles(project_dir, readmemd, walkpath, dst, depth=0):
    files = 0
    folders = 1
    foldersize = 0

    # check and edit input path strings
    tab = '|---'

    # make sure directory exists
    if not os.path.exists(dst):
        os.makedirs(dst)

    # walk files and link them
    entry = next(os.walk(walkpath))
    for linkfile in entry[2]:
        linkdst = os.path.join(dst, linkfile)
        os.link(src=os.path.join(walkpath, linkfile), dst=linkdst)

        # write readme and log
        points = '.' * (60-len(f'{tab*depth}|--> {linkdst.split(project_dir)[-1]}'))
        filesize = os.path.getsize(linkdst)
        write(f'``{tab*depth}|--> {linkdst.split(project_dir)[-1]}{points}{humanbytes(filesize)}``<br>', readmemd)
        log(f'Linked {walkpath + linkfile} to {os.path.join(project_dir, dst.split(project_dir)[1], linkfile)}')
        files += 1
        foldersize += filesize

    # walk directories
    for linkdir in entry[1]:
        write(f'``{tab*depth}|--> {dst.split(project_dir)[-1]}{linkdir}``<br>', readmemd)
        return tuple(map(sum, zip((files, folders, foldersize), linkAllFiles(project_dir=project_dir, readmemd=readmemd, walkpath=os.path.join(walkpath, linkdir), dst=os.path.join(dst, linkdir), depth=depth + 1))))

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
    cpufreqstring = ''
    try:
        cpufreq = psutil.cpu_freq()
        cpufreqstring = f'-    Max Frequency: {cpufreq.max:.2f}Mhz\n-    Min Frequency: {cpufreq.min:.2f}Mhz\n' 
    except NotImplementedError:
        cpufreqstring = '-    Max Frequency: N/A\n-    Min Frequency: N/A\n'
    svmem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    gpus = GPUtil.getGPUs()
    gpustring = ''
    for gpu in gpus:
        gpustring += f'-    ID: {gpu.id}\n    -    GPU: {gpu.name}\n    -    Total memory: {gpu.memoryTotal}MB\n'
    
    partitions = psutil.disk_partitions()
    diskstring = ''
    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            continue
        diskstring += (f'-    Device: {partition.device}\n\t' + 
                       f'-    Mountpoint: {partition.mountpoint}\n\t' + 
                       f'-    Disk: {partition.fstype}\n\t' + 
                       f'-    Total Size: {humanbytes(partition_usage.total)}\n\t' + 
                       f'-    Used: {humanbytes(partition_usage.used)}\n\t' + 
                       f'-    Free: {humanbytes(partition_usage.free)}\n\t' +
                       f'-    Percentage: {partition_usage.percent}\n')

    return ('## Project created on:\n' +
            f'-    System: {platform.system()}\n' + 
            f'-    Release: {platform.release()}\n' +
            f'-    Version: {platform.version()}\n' +
            f'-    Host: {socket.gethostname()}\n' +
            f'-    CPU: {platform.processor()}\n' +
            f'-    Physical Cores: {psutil.cpu_count(logical=False)}\n' +
            f'-    Logical Cores: {psutil.cpu_count(logical=True)}\n' +
            cpufreqstring + 
            f'-    RAM: {humanbytes(svmem.total)}\n' +
            f'-    Swap Memory: {humanbytes(swap.total)}\n' +
            diskstring +
            gpustring)

def latex(project_name, project_dir, project_description, organization, author, orcid, supervisor):
    log('Create latex files.')
    latexPath = os.path.join(project_dir, 'doc')
    log(f'Created {latexPath}')

    # generate main.tex
    with open(os.path.join(scriptpath, 'latex_template.tex'), 'r') as tex_template:
        with open(os.path.join(latexPath, 'main.tex'), 'w+') as tex_main:
            for line in tex_template.readlines():
                tex_main.write(line)
        tex_main.close()
    tex_template.close()
    log(f'Created {os.path.join(latexPath, "main.tex")}')

    # generate title page
    with open(os.path.join(latexPath, 'title_page.tex'), 'w+') as tex_title:
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
    log(f'Created {os.path.join(latexPath, "title_page.tex")}')

    # generate abstract
    with open(os.path.join(latexPath, 'abstract.tex'), 'w+') as tex_abstract:
        tex_abstract.write('\\section*{Abstract}\n' +
                           '\t\n' + 
                           '\t% TODO: Write your abstract here')
    tex_abstract.close()
    log(f'Created {os.path.join(latexPath, "abstract.tex")}')

    # generate abbreviations
    with open(os.path.join(latexPath, 'abbreviations.tex'), 'w+') as tex_abbrev:
        tex_abbrev.write('\\section*{\\Huge Abbreviations}\n' + 
                         '\t\\begin{acronym}\n' +
                         '\t\t\n' +
                         '\t\t%TODO: add abbreviations here.\n' +
                         '\t\t\n' + 
                         '\t\\end{acronym}')
    tex_abbrev.close()
    log(f'Created {os.path.join(latexPath, "abbreviations.tex")}')

    # prepare doc sections
    sections = {'introduction.tex': 'Introduction',
                'materials_methods.tex': 'Materials and Methods',
                'results.tex': 'Results',
                'discussion.tex': 'Discussion'}

    # generate doc sections
    for section in sections.keys():
        with open(os.path.join(latexPath, section), 'w+') as tex_intro:
            tex_intro.write('\\section{' + sections[section] + '}\n' + 
                            '\n' + 
                            f'\t% TODO: Write {sections[section].lower()} here.\n' + 
                            '\t\n')
        tex_intro.close()
        log(f'Created {os.path.join(latexPath, section)}')

    # generate attachments 
    with open(os.path.join(latexPath, 'attachments.tex'), 'w+') as tex_attach:
        tex_attach.write('\\section*{\\Huge Attachments}\n' + 
                         '\t\n' +
                         '\t% TODO: Add your attachments here.\n')
    tex_attach.close()
    log(f'Created {os.path.join(latexPath, "attachments.tex")}')

    # generate citations
    with open(os.path.join(latexPath, 'citations.bib'), 'w+') as tex_bib:
        tex_bib.write('% Encoding: UTF-8\n' +
                      '\n' +
                      '% TODO: Add your references here.')
    tex_bib.close()
    log(f'Created {os.path.join(latexPath, "citations.bib")}')

### PARAMS

def parse_args(args):

    parser = ap.ArgumentParser(
        description=f'{script} helps you with Creating your PROject DIRectory with good structure for better navigation and reproducibility.',
        formatter_class=ap.HelpFormatter,
        epilog=f'You are currently using version {version}!'
    )

    # required arguments
    projectgroup = parser.add_mutually_exclusive_group(required=True, )
    projectgroup.add_argument('-p', '--project', metavar='PATH_TO_PROJECT/PROJECT_NAME', default=None, type=str, help='Path and Name of the project you want to create locally. If the path does not exist, it will be created.')
    projectgroup.add_argument('-g', '--git', metavar='GIT_URL', type=str, default=None, help='Use this argument if you already made an empty repository and want to add your project to the remote repository.')

    # optional arguments
    parser.add_argument('-pd', '--project_description', metavar='SHORT_DESCRIPTION', default='', type=str, help='Short description about the project.')
    parser.add_argument('-l', '--link', metavar='PATH', type=str, default=None, help='Path of the folder of your resources/data.\nThe linked resources or data can be found in ./<project>/res/.')
    parser.add_argument('-ml', '--machine_learning', nargs=2, metavar=('TRAINDATA', 'VALDATA'), type=str, default=(None, None), help='Path to traindata and path to validationsdata.\nData gets linked into ./<project>/res/ folder.')
    parser.add_argument('-i', '--gitignore', metavar='LIST', action='append', default=[], type=list, help='List of \'directories\' or \'files\' that should be ignored in git version control.\nOnly possible if -g is used!')
    parser.add_argument('-a', '--author', metavar='NAME', default=None, type=str, help='Name of the author of the project in quotation marks: "Forename ... Surname".')
    parser.add_argument('-s', '--supervisor', metavar='NAME', default='', type=str, help='Name of the supervisor in quotation marks: "Forename ... Surname".')
    parser.add_argument('-org', '--organization', metavar='NAME', default='', type=str, help='Name of the organization in quotation marks: "...".')
    parser.add_argument('-oid', '--orcid', metavar='ORCID', default='', type=str, help='ORCID of the author of the project. Should look like XXXX-XXXX-XXXX-XXXX')
    parser.add_argument('-tex', '--latex', action='store_true', default=False, help='Use this parameter to generate latex files for project work.')
    parser.add_argument('-sp','--specs', action='store_true', default=False, help='Use this parameter to generate hardware specs in your docfile.')
        
    parser.add_argument('-v', '--version', action='version', version=f'\n%(prog)s {version}')

    return parser.parse_args()

version = '0.4.1'
script = __file__
scriptpath = os.path.dirname(os.path.abspath(script))

def main():

    log(f'STARTING {script}')

    args = parse_args(sys.argv[1:])

    activeParams = {'latex': args.latex, 'specs': args.specs}

    datalink = args.link
    project_description = args.project_description
    organization = args.organization
    supervisor = args.supervisor
    orcid = args.orcid
    trainlink = args.machine_learning[0]
    vallink = args.machine_learning[1]
    author = getpass.getuser()
    time = datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    ### CHECK INPUT
    projectInput = {'local': False, 'git': False}

    if args.author is not None:
        author = args.author

    if args.project is not None:
        project_dir = args.project.replace(' ', '_')
        project_name = args.project.split('/')[-1].replace('_', ' ')
        projectInput['local'] = True

    if args.git is not None:
        giturl = args.git
        project_dir = giturl.split('/')[-1].replace(' ', '_')
        project_name = giturl.split('/')[-1].replace('_', ' ')
        git_user_name = giturl.split('/')[-2]
        git_service = giturl.split('/')[-3]
        projectInput['git'] = True
        log(f'Using git {giturl} for version control!')

    ### CREATE PROJECT DIRECTORY

    # creating project working directory 'project_dir'
    if os.path.exists(project_dir):
        error(f'Path {project_dir} already exists!\nStopped with error code 1!', 1)

    if datalink is not None and not os.path.exists(datalink):
        error(f'Path {datalink} does not exist!\nStopped with error code 2!', 2)

    if datalink is not None and (trainlink is not None or vallink is not None):
        error(f'Cannot use --link and --machine_learning together! Please choose only one of them!', 3)

    if trainlink is not None and not os.path.exists(trainlink):
        error(f'Cannot find path to training data!', 4)

    if vallink is not None and not os.path.exists(vallink):
        error(f'Cannot find path to validation data!', 5)

    if len(args.gitignore) > 0 and args.git is None:
        error(f'Can use --gitignore only if --git is used!', 6)

    # check if orcid syntax and checksum
    if args.orcid != '':
        if not isORCID(orcid):
            error('ORCID does not match standards!', 7)

    if projectInput['git']:
        repo = git.Repo.clone_from(giturl, project_dir)

    if projectInput['local']:
        os.makedirs(project_dir)

    if projectInput['git']:
        for f in args.gitignore:
            write(f, project_dir + '.gitignore')

    readmemd = os.path.join(project_dir, 'README.md')
    readmesh = os.path.join(project_dir, 'README.sh')
    log(f'Created project \"{project_name}\" directory in {project_dir}')

    # making directories
    readmes = {}
    project_dirs = ['src', 'res', 'bin', 'lib', 'doc', 'build', 'out', 'out/plots', 'temp']
    for dire in project_dirs:

        # check if path already exists
        if os.path.exists(os.path.join(project_dir, dire)):
            log(f'Path {os.path.join(project_dir, dire)} already exists!')    
        else:
            os.makedirs(os.path.join(project_dir, dire))
            log(f'Created {os.path.join(project_dir, dire)}')
        
        # dont create readmes for out/plots and doc
        if dire != 'out/plots' and dire != 'doc':
            readmes[dire] = os.path.join(project_dir, dire, 'README.md')
            write(f'<!-- Created markdown file for {os.path.join(dire, "")} on {time} from {author} with {script} from https://github.com/JannesSP/sciProTools. -->', readmes[dire])
            log(f'Created {readmes[dire]}')

    write(f'res contains the resource data the way you like, either the hard links to your resource data or the actual resource data files.', readmes['res'])

    ### CREATE PROJECT FILES

    command = f'{script} '
    for arg in sys.argv[1:]:
        if arg.startswith('-'):
            command += f'{arg} '
        else:
            command += f'\'{arg}\' '

    # writing major readme file
    write(f'# Project \'{project_name}\' created on {time} from {author}.', readmemd, readmesh)
    write(f'# with {script} version {version}.', readmesh)
    write(f'# Used the following command in {os.getcwd()}', readmesh)
    write(command, readmesh)

    if activeParams['latex']:
        latex(project_name=project_name,
              project_dir=project_dir,
              project_description=project_description,
              organization=organization,
              author=author,
              orcid=orcid,
              supervisor=supervisor)

    # add files to commit for git
    if projectInput['git']:
        files = []
        for file in readmes.values():
            files.append(file.split(os.path.join(project_dir, ''))[1])
        # files = list(readmes.values())
        print(files)
        repo.index.add(files)
        repo.index.commit(f'initial commit of {project_name} with {script} {version}')
        log(f'Added {len(files)} files to git commit.')

    if projectInput['git']:
        write(f'# Using git {giturl} for version control on account {git_user_name} on {git_service}.', readmesh)
        write(f'-    Using git {giturl} for version control on account {git_user_name} on {git_service}.', readmemd)

    write(f'-    Created with {script} version {version} from https://github.com/JannesSP/sciProTools.', readmemd)
    write(f'<pre>\n{command}\n</pre>', readmemd)

    if orcid != '':
        write(f'-    ORCID of the author: https://orcid.org/{orcid}', readmemd)

    if supervisor != '':
        write(f'-    Project supervised by: {supervisor}', readmemd)

    if organization != '':
        write(f'-    Project developed at: {organization}', readmemd)

    writeDirDescription(project_name, readmemd)

    if activeParams['specs']:
        write('\n' + getSpecs(), readmemd)

    # if no datalink provided create train and validate data folders
    if trainlink is not None or vallink is not None:
        os.makedirs(os.path.join(project_dir, 'res' , 'traindata'))
        log(f'Created {os.path.join(project_dir, "res" , "traindata")}')
        os.makedirs(os.path.join(project_dir, 'res', 'valdata'))
        log(f'Created {os.path.join(project_dir, "res", "valdata")}')
        write('\n# Data to be analyzed:', readmemd)
        
        if trainlink is not None:
            write(f'Resources/Data linked from<br>\n{os.path.abspath(trainlink)}<br>', readmemd)
            (files, folders, datasize) = linkAllFiles(project_dir=project_dir, readmemd=readmemd, walkpath=trainlink, dst=os.path.join(project_dir, 'res', 'traindata'))
            log(f'Linked traindata: {files} files in {folders} folders.')
            log(f'Linked traindata of size {humanbytes(datasize)}')
            write(f'Linked traindata: {files} files in {folders} folders with a total datasize of {humanbytes(datasize)}.<br>\n', readmemd)

        if vallink is not None:
            write(f'Resources/Data linked from<br>\n{os.path.abspath(vallink)}<br>', readmemd)
            (files, folders, datasize) = linkAllFiles(project_dir=project_dir, readmemd=readmemd, walkpath=vallink, dst=os.path.join(project_dir, 'res', 'valdata'))
            log(f'Linked validationdata: {files} files in {folders} folders.')
            log(f'Linked validationdata of size {humanbytes(datasize)}')
            write(f'Linked validationdata: {files} files in {folders} folders with a total datasize of {humanbytes(datasize)}.<br>\n', readmemd)

    # linking data
    elif datalink is not None:
        write('\n# Data to be analyzed:', readmemd)
        write(f'Resources/Data linked from<br>\n{os.path.abspath(datalink)}<br>', readmemd)
        (files, folders, datasize) = linkAllFiles(project_dir=project_dir, readmemd=readmemd, walkpath=datalink, dst=os.path.join(project_dir, 'res'))
        log(f'Linked {files} files in {folders} folders.')
        write(f'Linked {files} files in {folders} folders with a total datasize of {humanbytes(datasize)}.', readmemd)
        log(f'Linked data of size {humanbytes(datasize)}')
        log('Done linking resources/data.')

    # push commits to git remote
    if projectInput['git']:
        repo.remote("origin").push()
        log(f'Pushed files to {giturl}.')

    write(f'# Protocol\n## {time.split(" ")[0]}', readmemd)
    log(f'Created {readmemd} and {readmesh}')
    log('Done')

main()