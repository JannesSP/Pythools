# sciProTools
Usefule python scripts for everyday science projects.

# Creator
Jannes Spangenberg<br>
Studying bioinformatics at Friedrich-Schiller-University in Jena Germany<br>

# cProDir
<pre>
usage: cProDir.py [-h] (-p PROJECT_NAME | -g GIT_URL) [-d EXTENSION] [-l PATH]
                  [-ml TRAINDATA VALDATA] [-v]

Version 0.3 enables you to add your project to a precreated remote git repository - see param -g.
cProDir.py helps you with Creating your PROject DIRectory with good structure
for better navigation and reproducibility.

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
  -v, --version         show program's version number and exit

You are currently using version 0.3!
</pre>