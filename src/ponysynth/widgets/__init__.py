import os
from ponysynth import widgets
from IPython import display as ipd


def load_js(local_filename):
    path = os.path.dirname(widgets.__file__)
    contents = open(f'{path}/{local_filename}').read()
    widget = ipd.Javascript(contents)
    ipd.display(widget)
