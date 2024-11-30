#!/usr/bin/env python3

# Additional command line utilities that should be common in these
# packages.

def ask_yn(label, default=True):
    while True:
        answer = input(label + " " + ("(Y/n)" if default else "(y/N)") + " ").lower()
        if not answer and default or answer == 'y':
            return True
        elif not answer and not default or answer == 'n':
            return False
        else:
            print("Invalid option. Choose either y or n.")

def ask_choice(label, choices):
    while True:
        print(label)
        print("choices:")
        for i, choice in enumerate(choices):
            print(" [{}] {}".format(i+1, choice))
        try:
            choice_str = input("choice (default: 1): ")
            choice = 0 if not choice_str else int(choice_str)-1
            return choice
        except ValueError:
            print("error: must specify number choice between 1-{}".format(len(choices)))
