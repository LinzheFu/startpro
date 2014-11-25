#-*- encoding: utf-8 -*-

'''
Created on 2014.04.16

@author: Allen
'''
from importlib import import_module
from inspect import isclass, ismodule, isfunction
from startpro.core import settings
from startpro.core.process import Process
from startpro.core.topcmd import TopCommand
from startpro.common.utils.config import Config
import os

def _get_opts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            if len(argv) > 1:
                opts[argv[0][1:]] = argv[1]  # Add key and value to the dictionary.
            else:
                opts[argv[0][1:]] = None
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts

def load_modeule_auto(root_path, scan_paths):
    paths = set()
    for p in scan_paths:
        for root, _, files in os.walk(import_module(p).__path__[0]):
            for f in files:
                if f.startswith("__") or f.endswith("pyc") or not f.endswith(".py"):
                    continue
                f = os.path.join(root, f)
                f = f.replace(root_path, "").split(os.path.sep)
                module_path = ".".join(f)
                if module_path.startswith("."):
                    module_path = module_path[ 1: -3 ]
                paths.add(module_path)
                import_module(module_path)
    return list(paths)

def load_module(module_path, match=""):
    '''
    Return: [module object] list
    module_path : argument required, package path
    
    when module in this package starts with settings.COMMAND_MODEULE / settings.SCRIPT_MODULE
    and not inner attribute
    '''
    mods = []
    if module_path:
        try:
            print module_path
            # match
            
            mod = import_module(module_path)
            for module in dir(mod):
                # if module_path.startswith(settings.COMMAND_MODEULE) or module_path.startswith(settings.SCRIPT_MODULE):
                if not module.startswith('__'):
                    mods.append(import_module("%s.%s" % (module_path, module)))
            print mods
            print
        except Exception, e:
            print e
    return mods

def __scan_mod(path):
    '''
    Return: [(name, class or function) ] list of tuple
    path : argument required, package path
    
    each package path
    when module in this package is subclass of executable class Process,
    when module in this package starts with 'run'
    '''
    res = []
    for mod in load_module(path):
        for item in dir(mod):
            item = getattr(mod, item)
            if isclass(item) and issubclass(item, Process):
                cls = item()
                if hasattr(cls, 'name'):
                    res.append( (cls.name, cls.run) )
            elif ismodule(item):
                res.extend(__scan_mod(item.__package__))
            else:
                if isfunction(item) and item.__name__.startswith('run'):
                    func_name = "%s.%s" % (mod.__name__, item.__name__)
                    res.append( (func_name, item) )
    return res
    
def get_script(paths, full=False):
    '''
    Return: dict of executable script name 
    '''
    mapping = {}
    for p in paths:
        for re in __scan_mod(p):
            if full:
                mapping[re[0]] = re[1]
            else:
                mapping[".".join(re[0].split(".")[ 1 : ])] = re[1]
    return mapping

def get_command(paths):
    '''
    Return: dict of commands 
    '''
    mapping = {}
    for p in paths:
        for mod in load_module(p):
            for item in dir(mod):
                if item == 'TopCommand':
                    continue
                item = getattr(mod, item)
                if isclass(item) and issubclass(item, TopCommand):
                    mapping[ mod.__name__.split('.')[-1] ] = item()
    return mapping

def load_config(config_file, section):
    '''
    load custom configure by section
    '''
    config = Config(config_file=config_file)
    settings.CONFIG = config
    for re in config.get_config_list(section):
        setattr(settings, re[0].upper(), re[1])

def get_attr(attr_name, default=None):
    '''
    get attribute of startpro.core.settings safety default value
    '''
    if hasattr(settings, attr_name.upper()):
        return getattr(settings, attr_name.upper())
    else:
        return default