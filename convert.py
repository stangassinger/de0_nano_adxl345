
from myhdl import *
from gw import top


def convert():
    CLOCK_50=   Signal(bool(0))
    LED     =   Signal(intbv(0)[8:])
    KEY     =   Signal(intbv(0)[2:])
    sys_rst = ResetSignal(1, active=0, async=True)
    G_SENSOR_CS_N = Signal(bool(1))
    I2C_SCLK      = Signal(bool(1))
    I2C_SDAT = TristateSignal(False)    
   
    
 
    toVHDL(top,CLOCK_50, LED, KEY, sys_rst,G_SENSOR_CS_N, I2C_SCLK, I2C_SDAT )


if __name__ == '__main__':
    convert()
