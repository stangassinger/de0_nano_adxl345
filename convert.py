
from myhdl import *
from gw import top


def convert():
    G_SENSOR_CS_N = Signal(bool(1))
    G_SENSOR_INT  = Signal(bool(0))
    I2C_SCLK      = Signal(bool(1))
    I2C_SDAT = TristateSignal(False)    
    CLOCK_50 =   Signal(bool(0))
    LED =   Signal(intbv(0)[8:])
   
    
 ##   toVerilog(top,clock,reset,LED)
 ##   toVHDL(top,CLOCK_50, LED,G_SENSOR_CS_N,G_SENSOR_INT,I2C_SCLK,I2C_SDAT )
    toVerilog(top,CLOCK_50, LED,G_SENSOR_CS_N,G_SENSOR_INT,I2C_SCLK,I2C_SDAT )    

if __name__ == '__main__':
    convert()
