#!/usr/bin/env python3
import sys, os
__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(__dir__, '..', 'build'))
sys.path.insert(0, __dir__)
print(f'cwd: {os.getcwd()}')
print(f'__dir__: {__dir__}')
print(f'abs path: {os.path.join(__dir__, "lab13_1_dir")}')
from utils import init_oa, create_lib, make_oa_name, make_oa_string, get_namespace
init_oa()
ns = get_namespace('native')
dirname = os.path.join(__dir__, "lab13_1_dir")
print(f'Creating at: {dirname}')
import shutil
if os.path.exists(dirname):
    shutil.rmtree(dirname)
sn_lib, lib = create_lib("lab13_1_lib", dirname)
print(f'OK')
lib.close()
shutil.rmtree(dirname)
