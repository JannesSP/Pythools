# sciProTools
Usefule python scripts for everyday science projects.

# Creator
Jannes Spangenberg<br>
Studying bioinformatics at Friedrich-Schiller-University in Jena Germany<br>

# cProDir
cProDir can be used to create your project directory structure for better navigation and reproducibility in your projects.
This way uniformity is insured thoughout all your projects.
You have the possibility to link your resource data or to use a precreated empty git remote repository to add a version control to your project.

## Usage
<pre>
usage: cProDir.py [-h] (-p PROJECT_NAME | -g GIT_URL) [-d EXTENSION] [-l PATH]
                  [-ml TRAINDATA VALDATA] [-i LIST_FILES] [-v]

Version 0.3 enables you to add your project to a precreated remote git
repository - see param -g. cProDir.py helps you with Creating your PROject
DIRectory with good structure for better navigation and reproducibility.

optional arguments:
  -h, --help            show this help message and exit
  -p PROJECT_NAME, --project PROJECT_NAME
                        Name of the project you want to create locally.
  -g GIT_URL, --git GIT_URL
                        Use this argument if you already made an empty
                        repository and want to add your project to the remote
                        repository.
  -d EXTENSION, --docext EXTENSION
                        DOCumentation datatype EXTension for your
                        documentation files. Standard is md for markdown.
  -l PATH, --link PATH  Path of the folder of your resources/data. The linked
                        resources or data can be found in ./<project>/res/.
  -ml TRAINDATA VALDATA, --machine_learning TRAINDATA VALDATA
                        Path to traindata and path to validationsdata. Data
                        gets linked into ./<project>/res/ folder.
  -i LIST, --gitignore LIST
                        List of directories or files that should be ignored in
                        git version control. Only possible if -g is used!
  -v, --version         show program's version number and exit

You are currently using version 0.3.1!
</pre>

## Your project directory structure:
-   src: containing project scripts
-   res: containing project resources and data
-   bin: containing project binaries
-   lib: containing external libraries
-   doc: containing project documentation files
-   build: containing project binaries
-   temp: containing temporary files
-   out: containing output files, produced by processing/analyzing resources
-   out/plots: containing output plot files and diagrams