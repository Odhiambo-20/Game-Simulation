# CS-4253: Artificial Intelligence

Code for the AI projects for CS-4253.

## Requirements

All projects use Python 3. You will need to install some other
dependencies as well. To do so, run (assuming you are using a Ubuntu
system)

    sudo pip3 install -r requirements.txt

in the root of the folder. If you are on another system, it should be
some variant of `pip install -r requirements.txt`.

You will need Tkinter for Python 3 to use the pygame packages. On
Ubuntu, this can be installed by running

    sudo apt-get install python3-tkinter

in the command line.

## Running Evaluations

The tool `evaluate.py` at the root of this direction can be run using

    python3 evaluate.py <project>

This will automatically run the evaluation code against a project. For
the list of projects, see [src/projects](src/projects).
