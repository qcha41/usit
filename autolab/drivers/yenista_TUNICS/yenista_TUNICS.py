#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Supported instruments (identified): Yenista Tunics.
- 
"""


class Driver():
    
    category = 'Optical source'
    
    def __init__(self):
        self.write('MW')
        
    def wait(self):
        self.getID() # Not fantastic but programming interface really basic
             
    def get_id(self):
        return self.query('*IDN?')
    
    def set_frequency(self,value):
        self.write(f"F={value}")
        self.wait()
        
    def get_frequency(self):
        return self.query("F?")

    def set_wavelength(self,value):
        self.write(f"L={value}")
        self.wait()
        
    def get_wavelength(self):
        return self.query("L?")
    
    def set_power(self,value):
        self.write(f"P={float(value)}")
        if value == 0 : self.set_output(False)
        else : 
            if self.get_output() is False : self.set_output(True)
        self.wait()
        
    def get_power(self):
        ans=self.query("P?")
        if ans == 'DISABLED' : return 0
        else : return ans
    
    def set_intensity(self,value):
        self.write(f"I={float(value)}")
        if value == 0 : self.set_output(False)
        else :
            if self.get_output() is False : self.set_output(True)
        self.wait()
        
    def get_intensity(self):
        ans=self.query("I?")
        if isinstance(ans,str) is True and ans == 'DISABLED' : return 0
        else : return ans
        
    def set_output(self,state):
        if state is True : self.write("ENABLE")
        else : self.write("DISABLE")
        self.wait()
        
    def get_output(self):
        ans = self.query("P?")
        if ans == 'DISABLED' : return False
        else : return True
        
        
        
        
    def get_motor_speed(self):
        return self.query("MOTOR_SPEED?")   
 
    
    def set_motor_speed(self,value):  # from 1 to 100 nm/s
        self.write("MOTOR_SPEED={float(value)}")
        self.wait()


    def get_driver_model(self):
        
        config = []

        config.append({'element':'variable','name':'wavelength','unit':'nm','type':float,
                       'read':self.get_wavelength,'write':self.set_wavelength})
    
        config.append({'element':'variable','name':'frequency','unit':'GHz','type':float,
                       'read':self.get_frequency,'write':self.set_frequency})

        config.append({'element':'variable','name':'power','unit':'mW','type':float,
                       'read':self.get_power,'write':self.set_power})

        config.append({'element':'variable','name':'intensity','unit':'mA','type':float,
                       'read':self.get_intensity,'write':self.set_intensity})
    
        config.append({'element':'variable','name':'output','type':bool,
                       'read':self.get_output,'write':self.set_output})

        config.append({'element':'variable','name':'motor_speed','unit':'nm/s','type':float,
                       'read':self.get_motor_speed,'write':self.set_motor_speed})
    
        return config



#################################################################################
############################## Connections classes ##############################
class Driver_VISA(Driver):
    def __init__(self, address='GPIB0::2::INSTR', **kwargs):
        import visa    
        
        self.TIMEOUT = 15000 #ms
        
        rm = visa.ResourceManager()
        self.controller = rm.open_resource(address)
        self.controller.timeout = self.TIMEOUT
        
        Driver.__init__(self)
    
    def close(self):
        try : self.controller.close()
        except : pass

    def query(self,command):
        result = self.controller.query(command)
        result = result.strip('\n')
        if '=' in result : result = result.split('=')[1]
        try : result = float(result)
        except: pass
        return result
    
    def write(self,command):
        self.controller.write(command)
    
    def read(self):
        return self.controller.read()


############################## Connections classes ##############################
#################################################################################
        

