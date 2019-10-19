# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 22:20:14 2019

@author: qchat
"""

import os

import inspect
from .utilities import emphasize, clean_string


class Element() :

    def __init__(self,parent,element_type,name):   

        self.name = name
        self._element_type = element_type
        self._parent = parent
        self._help = None
        
    def get_address(self):
    
        """ Returns the address of the given element.
        <module.submodule.variable> """
    
        address = [self.name]
        parent_element = self._parent
        while parent_element is not None : 
            address.append(parent_element.name)
            parent_element = parent_element._parent
        return '.'.join(address[::-1])






class Module(Element):

    def __init__(self,parent,config):
        
        Element.__init__(self,parent,'module',config['name'])
        
        self._mod = {}
        self._var = {}
        self._act = {}
    
        # Object - instance
        assert 'object' in config.keys(), f"Module {self.name}: missing module object"
        self.instance = config['object']
        
        # Help
        if 'help' in config.keys():
            assert isinstance(config['help'],str), f"Module {self.get_address()} configuration: Help parameter must be a string"
            self._help = config['help']
     
        # Loading instance
        assert hasattr(self.instance,'get_driver_model'), f"There is no function 'get_driver_model' in the driver class"
        driver_config = self.instance.get_driver_model()

        assert isinstance(driver_config,list), f"Module {self.name} configuration: 'get_driver_model' output must be a list of dictionnaries"
        for config_line in driver_config : 
            
            # General check
            assert isinstance(config_line,dict), f"Module {self.name} configuration: 'get_driver_model' output must be a list of dictionnaries"
            
            # Name check
            assert 'name' in config_line.keys(), f"Module {self.name} configuration: missing 'name' key in one dictionnary"
            assert isinstance(config_line['name'],str), f"Module {self.name} configuration: elements names must be a string"
            name = clean_string(config_line['name'])
            assert name != '', f"Module {self.name}: elements names cannot be empty"
        
            # Element type check
            assert 'element' in config_line.keys(), f"Module {self.name}, Element {name} configuration: missing 'element' key in the dictionnary"
            assert isinstance(config_line['element'],str), f"Module {self.name}, Element {name} configuration: element type must be a string"
            element_type = config_line['element']
            assert element_type in ['module','variable','action'], f"Module {self.name}, Element {name} configuration: Element type has to be either 'module','variable' or 'action'"
            
            if element_type == 'module' :
                
                # Check name uniqueness
                assert name not in self.get_names(), f"Module {self.name}, Submodule {name} configuration: '{name}' already exists"
                self._mod[name] = Module(self,config_line)
                
            elif element_type == 'variable':
                
                # Check name uniqueness
                assert name not in self.get_names(), f"Module {self.name}, Variable {name} configuration: '{name}' already exists"
                self._var[name] = Variable(self,config_line)
                
            elif element_type == 'action' :
                
                # Check name uniqueness
                assert name not in self.get_names(), f"Module {self.name}, Action {name} configuration: '{name}' already exists"
                self._act[name] = Action(self,config_line)


    def get_module(self,name):
        
        """ Returns the submodule of the given name """
        
        assert name in self._mod.keys(), f"The submodule '{name}' does not exist in module {self.name}"
        return self._mod[name]
    
    
    
    def list_modules(self):
        
        """ Returns a list with the names of all existing submodules """
        
        return list(self._mod.keys())
    
    
    
    def get_variable(self,name):
        
        """ Returns the variable with the given name """
        
        assert name in self._var.keys(), f"The variable '{name}' does not exist in module {self.name}"
        return self._var[name]
    
    
    
    def list_variables(self):
        
        """ Returns a list with the names of all existing variables attached to this module """
        
        return list(self._var.keys())
    
    
    
    def get_action(self,name):
        
        """ Returns the action with the given name """
        
        assert name in self._dev.keys(), f"The action '{name}' does not exist in device {self.name}"
        return self._dev[name]
    
    
    
    def list_actions(self):
        
        """ Returns a list with the names of all existing actions attached to this module """
        
        return list(self._act.keys())
    
    
    
    def get_names(self):
        
        """ Returns the list of the names of all the elements of this module """
        
        return list(self._mod.keys()) + list(self._var.keys()) + list(self._act.keys())
    
    

    def __getattr__(self,attr):
        if attr in self._var.keys() : return self._var[attr]
        elif attr in self._act.keys() : return self._act[attr]
        elif attr in self._mod.keys() : return self._mod[attr]
        else : raise AttributeError(f"'{attr}' not found in module '{self.name}'")
        
        
        
    def help(self):
        
        """ This function prints informations for the user about the availables 
        submodules, variables and action attached to the current module """
        
        display ='\n'+emphasize(f'Module {self.name}')+'\n'
        if self._help is not None : 
            display+=f'Help: {self._help}\n'
        
        display += '\n* Submodules: '
        mod_list = self.list_modules()
        if len(mod_list)>0 :
            for mod_name in mod_list : 
                display += f'\n  - {mod_name}'
            display += '\n'
        else : display+='None\n'
        
        display += '\n* Variables: '
        var_list = self.list_variables()
        if len(var_list)>0 :
            for var_name in var_list : 
                display += f'\n  - {var_name}'
            display += '\n'
        else : display+='None'
        
        display += '\n* Actions: '
        act_list = self.list_actions()
        if len(act_list)>0 :
            for act_name in act_list : 
                display += f'\n  - {act_name}'
            display += '\n'
        else : display+='None'

        print(display)
        
        
        
    def __dir__(self):
        
        """ For auto-completion """
        
        return self.list_modules() + self.list_variables() + self.list_actions() + ['help','instance']
    
    
    



        
        
class Variable(Element):
    
    def __init__(self,parent,config):
        
        Element.__init__(self,parent,'variable',config['name'])
        
        import numpy as np
        import pandas as pd
        
        # Type
        assert 'type' in config.keys(), f"Variable {self.get_address()}: Missing variable type"
        assert config['type'] in [int,float,bool,str,bytes,pd.DataFrame,np.ndarray], f"Variable {self.get_address()} configuration: Variable type not supported in usit"
        self.type = config['type']
        
        # Read and write function
        assert 'read' in config.keys() or 'write' in config.keys(), f"Variable {self.get_address()} configuration: no 'read' nor 'write' functions provided"
        
        # Read function
        self.read_function = None
        if 'read' in config.keys():
            assert inspect.ismethod(config['read']), f"Variable {self.get_address()} configuration: Read parameter must be a function"
            self.read_function = config['read']
            
        # Write function
        self.write_function = None
        if 'write' in config.keys():
            assert inspect.ismethod(config['write']), f"Variable {self.get_address()} configuration: Write parameter must be a function"
            self.write_function = config['write']
        
        # Unit
        self.unit = None
        if 'unit' in config.keys():
            assert isinstance(config['unit'],str), f"Variable {self.get_address()} configuration: Unit parameter must be a string"
            self.unit = config['unit']
            
        # Help
        if 'help' in config.keys():
            assert isinstance(config['help'],str), f"Variable {self.get_address()} configuration: Info parameter must be a string"
            self._help = config['help']
                
        # Properties
        self.writable = self.write_function is not None
        self.readable = self.read_function is not None
        self.numerical = self.type in [int,float]
        self.parameter_allowed = self.writable and self.numerical
                
        # Signals for GUI
        self._read_signal = None
        self._write_signal = None
        
        
        
    def save(self,path,value=None):
        
        """ This function measure the variable and saves its value in the provided path """
        
        import pandas as pd
        import numpy as np
        
        assert self.readable, f"The variable {self.name} is not configured to be measurable"
        
        if os.path.isdir(path) :
            path = os.path.join(path,self.get_address()+'.txt')
        
        if value is None : value = self() # New measure if value not provided
        
        if self.type in [int,float,bool,str]:
            with open(path,'w') as f : f.write(str(value))
        elif self.type == bytes :
            with open(path,'wb') as f : f.write(value)
        elif self.type == np.ndarray :
            np.savetxt(path,value)
        elif self.type == pd.DataFrame :
            value.to_csv(path,index=False)
        else :
            raise ValueError("The variable {self.name} of type {self.type} cannot be saved.")  
        
        
        
    def help(self):
        
        """ This function prints informations for the user about the current variable """
        
        display ='\n'+emphasize(f'Variable {self.name}')+'\n'
        if self._help is not None : display+=f'Help: {self._help}\n'
        display += '\n'
        
        display += 'Readable: '
        if self.readable is True : display += f"YES (driver function '{self.read_function.__name__}')\n"
        else : display += 'NO\n'
        
        display += 'Writable: '
        if self.writable is True : display += f"YES (driver function '{self.write_function.__name__}')\n"
        else : display += 'NO\n'
        
        display += 'Unit: '
        if self.unit is not None : display += f'{self.unit}\n'
        else : display += 'None\n'
        
        print(display)
    


    def __call__(self,value=None):
        
        """ Measure or set the value of the variable """
                
        # GET FUNCTION
        if value is None:
            assert self.readable, f"The variable {self.name} is readable"
            answer = self.read_function()
            if self._read_signal is not None : self._read_signal.emit(answer)
            return answer
            
        # SET FUNCTION
        else : 
            assert self.writable, f"The variable {self.name} is writable"
            self.write_function(value)
            if self._write_signal is not None : self._write_signal.emit()
  
        
        

   
    
    
    
        
class Action(Element):
    
    def __init__(self,parent,config):
        
        Element.__init__(self,parent,'action',config['name'])
        
        # Do function
        assert 'do' in config.keys(), f"Action {self.get_address()}: Missing 'do' function"
        assert inspect.ismethod(config['do']), f"Action {self.get_address()} configuration: Do parameter must be a function"
        self.function = config['do'] 
        
        # Help
        if 'help' in config.keys():
            assert isinstance(config['help'],str), f"Action {self.get_address()} configuration: Info parameter must be a string"
            self._help = config['help']
        
        
        
    def help(self):
        
        """ This function prints informations for the user about the current variable """
        
        display ='\n'+emphasize(f'Action {self.name}')+'\n'
        if self._help is not None : display+=f'Help: {self._help}\n'
        display += '\n'
        
        display+=f"Driver function: '{self.function.__name__}'\n"
        
        print(display)
               
    
    
    def __call__(self):
        
        """ Executes the action """
        
        # DO FUNCTION
        assert self.function is not None, f"The action {self.name} is not configured to be actionable"
        self.function()
            
    
        
        
        
        
        
      
        
        

