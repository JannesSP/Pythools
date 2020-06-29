import os
import sys
import argparse as ap

VERSION = '0.1'
SCRIPT = __file__
SCRIPTPATH = os.path.dirname(os.path.abspath(SCRIPT))
warnings = 0

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

def parse_args(args):

    parser = ap.ArgumentParser(
        description=f'{SCRIPT} helps gathers all plots and inserts them into your documentation file.',
        formatter_class=ap.HelpFormatter,
        epilog=f'You are currently using {SCRIPT} version {VERSION}!'
    )

    # optional arguments
    parser.add_argument('-pl', '--plots', required=True, metavar='PLOTS_DIRECTORY', help='Path to your plots that will be traversed.')
    docfilegroup = parser.add_mutually_exclusive_group(required=True)
    docfilegroup.add_argument('-m', '--markdown', action='store_true', default=False, help='Include plots into README.md file.')
    docfilegroup.add_argument('-t', '--latex', action='store_true', default=False, help='Include plots into doc/attachments.tex file.')
    parser.add_argument('-pr', '--project', required=True, metavar='PROJECT_PATH', default='./', help='Path to a sciProTools project.')

    parser.add_argument('-v', '--version', action='version', version=f'\n%(prog)s {VERSION}')

    return parser.parse_args()

def getPlots(plot_dir, plotlist = []):
    '''Traverse plot_dir and return a list of all files.
    
    Keyword arguments:
    plot_dir -- Path to traverse for files
    plotlist -- List of all found files in plot_dir'''
    # walk files and link them
    entry = next(os.walk(plot_dir))

    for file in entry[2]:
        plotlist.append(file)

    # walk directories
    for dir in entry[1]:
        return plotlist.extend(getPlots(dir))
        
    return plotlist

def checkPlotExt(file):
    '''Check if file has an accepted plot format and return a boolean.
    
    Keyword arguments:
    file -- File to check for format'''
    acceptedplotformats = ['.pdf', '.png', '.jpg', '.jpeg', '.eps']
    if not os.path.splitext(file)[1] in acceptedplotformats:
        return False
    return True

def writeLatex(file, plot, project):
    '''Write tex file to include plot.'''
    with open(file, 'a') as tex:
        tex.write('\t\\begin{figure}[H]\n' + 
                  '\t\t\\centering\n' + 
                  '\t\t\\includegraphics[width=\\textwidth]{' + f'{plot}' + '}\n' +
                  f'\t\t\\caption[{os.path.splitext(plot.split("/")[-1])[0].replace("_", " ")}]' + '{' + f'{os.path.splitext(plot.split("/")[-1])[0].replace("_", " ")}' + '}\n' + 
                  '\t\t\\label{fig:' + f'{os.path.splitext(plot.split("/")[-1])[0]}' + '}\n' + 
                  '\t\\end{figure}\n\n')
    tex.close()

def writeMarkdown(file, plot, project):
    '''Write md file to include plot.'''
    with open(file, 'a') as md:
        md.write(f'## {plot.split("/")[-1]}\n![]({plot})\n')
    md.close()

def main():

    args = parse_args(sys.argv[1:])

    docfile = {'md': args.markdown, 'tex': args.latex}
    plotdir = args.plots
    project = args.project

    if not os.path.exists(project):
        error(f'Path {project} does not exist!', 1)

    for plot in getPlots(plotdir):
        if checkPlotExt(plot):
            log(f'Include {plot} to {project}.')

            if docfile['tex']:
                if os.path.exists(os.path.join(project, "doc", "attachments.tex")):
                    writeLatex(os.path.join(project, "doc", "attachments.tex"), os.path.abspath(plot), project)
                else:
                    error(f'File {os.path.join(project, "doc", "attachments.tex")} does not exist!', 2)

            elif docfile['md']:
                if os.path.exists(os.path.join(project, "README.md")):
                    writeMarkdown(os.path.join(project, "README.md"), os.path.abspath(plot), project)
                else:
                    error(f'File {os.path.join(project, "README.md")} does not exist!', 3)

log(f'STARTING {SCRIPT}')
main()
log(f'EXIT {SCRIPT} with {warnings} warnings.')