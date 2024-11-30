#!/usr/bin/env python3

import argparse
import sys

parser = argparse.ArgumentParser(description='Code evaluation tool for CS 4253 - Artificial Intelligence. Allows evaluating sample programs for various projects written for class.')
parser.add_argument('project_name', type=str, help='The project to evaluate.')
args = parser.parse_args(sys.argv[1:2])

class Project:
    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.modname = 'src.projects.{}.main'.format(self.proj_name)
        self.module = __import__(self.modname, fromlist=[''])

    def run(self):
        self.module.main(sys.argv[2:])

proj = Project(args.project_name)

proj.run()
