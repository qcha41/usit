# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 18:01:42 2024

@author: Jonathan
"""


import os
import sys

from .gui.icons import icons
from .utilities import input_wrap


def create_shortcut(ask: bool = False):
    """ Create Autolab GUI shortcut on desktop. """
    # Works on Windows with winpython and with base or env conda
    try:
        autolab_icon = icons['autolab']
        userprofile = os.path.expanduser('~')
        desktop = os.path.join(userprofile, 'Desktop')
        link = os.path.join(desktop, 'Autolab GUI.lnk')
        python = sys.base_prefix
        python_env = sys.prefix

        if not os.path.exists(desktop):
            return

        is_conda = os.path.exists(os.path.join(sys.prefix, 'conda-meta'))

        if is_conda:
            if python == python_env:
                if 'envs' in python:
                    python = os.path.dirname(os.path.dirname(python))
        else:  # Suppose WinPython
            python = os.path.dirname(python)

        python_script = os.path.normpath(os.path.join(python, r'Scripts/activate.bat'))

        if not os.path.exists(python_script):
            return

        from comtypes.client import CreateObject
        from comtypes.persist import IPersistFile
        from comtypes.shelllink import ShellLink

        if ask:
            ans = input_wrap('Create Autolab GUI shortcut on desktop? [default:yes] > ')
        else:
            ans = 'yes'

        if ans.strip().lower() == 'no':
            return

        s = CreateObject(ShellLink)
        s.SetPath('cmd.exe')
        s.SetArguments(f'/c {python_script} {python_env} && autolab gui')
        s.SetIconLocation(autolab_icon, 0)
        s.SetDescription('Start Autolab GUI')
        s.SetWorkingDirectory(userprofile)

        p = s.QueryInterface(IPersistFile)
        p.Save(link, True)

    except Exception as e:
        print(f'Cannot create Autolab shortcut: {e}')
