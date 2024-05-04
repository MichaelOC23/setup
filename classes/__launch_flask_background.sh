#!/bin/bash

# Change to the directory where the code is located
cd /Users/michasmi/.jbi/
source /Users/michasmi/.jbi/jbi_venv/bin/activate
export FLASK_APP=/Users/michasmi/.jbi/000_flask_background.py
# export PYTHONPATH="${PYTHONPATH}:${HOME}/.jbi/classes"
flask run --port 5005
# source /Users/michasmi/.jbi/jbi_venv/bin/activate && flask run /Users/michasmi/.jbi/000_flask_background.py --port 5005
