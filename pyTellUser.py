import argparse
from os import name
import subprocess

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description='A simple command-line program')

    # Add arguments
    parser.add_argument('type', type=str, default='notify', help='notify or alert')
    parser.add_argument('--title', type=str, default='NOTIFICATION', help='Notification Title')
    parser.add_argument('--message', type=str, default='', help='Notification Message')

    # Parse the arguments
    args = parser.parse_args()

    notify(args.type, args.title, args.message)

def notify(TYPE = 'notify', TITLE = 'NOTIFICATION', MESSAGE = 'default message'):
    if TYPE == 'notify':  # Added colon here
        subprocess.run(["osascript", "-e", f'display notification "{MESSAGE}" with title "{TITLE}"'])

    if TYPE == 'alert':  # Added colon here
        subprocess.run(["osascript", "-e", f'display alert "{TITLE}" message "{MESSAGE}"'])

if __name__ == "__main__":
    notify()
