import os
import random
from random import randrange
from copy import copy

## to generate Verilog code:
## python convert.py 
## simulation
## python gw.py; gtkwave  test_dff.vcd




from myhdl import *

def clk_gen(CLOCK_50, tick, tick2, I2C_SCLK):
    #CLK_FREQ = 48e6  # clock frequency
    #LED_RATE = 2.01 # strobe change rate 
    CLK_FREQ = 10   # simulation only !!!!
    LED_RATE = 1 # simulation mode
    CNT_MAX = int(CLK_FREQ * LED_RATE)
    diff_rate = 0.45
    CNT_DIFF = int(CLK_FREQ * diff_rate)
    clk_cnt        = Signal(intbv(0, min=0, max=CNT_MAX+2))
    
    @always(CLOCK_50.posedge) 
    def logic():        
        clk_cnt.next = clk_cnt + 1
        if clk_cnt == CNT_MAX-CNT_MAX/2:
            tick.next = 1
            I2C_SCLK.next = 1

        if clk_cnt == CNT_MAX-CNT_MAX/2+CNT_DIFF:
            tick2.next = 1
            I2C_SCLK.next = 0
            
            
        if clk_cnt == CNT_MAX:
            clk_cnt.next = 0
            tick.next = 0
            tick2.next = 0



   
    return logic



def readData(tick, tick2, G_SENSOR_CS_N,I2C_SDAT,LED , I2C_SCLK, count, START, PAUSE):
    
    w_adr_1  = Signal(intbv(0x8c)[8:0])#31-->31
    w_data1  = Signal(intbv(0xd2)[8:0])#4E-->4E
    w_adr_2  = Signal(intbv(0x01)[8:0])#00-->80
    r_data2  = Signal(intbv(0)[8:0])   # should be DEVID (0xE5)

    io = I2C_SDAT.driver()


    
    @always(tick.negedge)
    def readData_gen():
        

        if count > 37+PAUSE:
            count.next = count -1
            
       
        elif (count >=29+PAUSE) and (count <= 37+PAUSE) : 
            count.next = count - 1
            
            if (count >= 29+PAUSE) and (count <= 36+PAUSE):
                io.next = w_adr_1[36+PAUSE - count]
        
        elif (count >= 21+PAUSE) and (count < 29+PAUSE):
            count.next= count - 1
            io.next = w_data1[28+PAUSE - count]

        elif (count >= 20) and (count < 21+PAUSE):
            count.next= count - 1
            
                
        elif (count >= 11) and (count < 20):
            count.next = count - 1
            if (count > 11) and (count <= 18):            
                io.next = w_adr_2[18 - count]

        elif (count > 0) and (count < 11):
            count.next = count - 1           
            io.next = None


        else:
            count.next = START


    @always(tick2.posedge)
    def c_select():
        if count == (45 + PAUSE):
            G_SENSOR_CS_N.next = 0

        if count == (43 + PAUSE):
            G_SENSOR_CS_N.next = 1

        
        if count == (36 + PAUSE):
            G_SENSOR_CS_N.next = 0

        if count == (20 + PAUSE):
            G_SENSOR_CS_N.next = 1

        if count == 18 :
            G_SENSOR_CS_N.next = 0

        if count == 2 :
            G_SENSOR_CS_N.next = 1


        if (count > 2) and (count < 11):
            if (I2C_SDAT == True):
                r_data2.next[10-count] = 1
            else:
                r_data2.next[10-count] = 0

            
    

    collector = Signal(intbv(0)[8:0])
    @always_comb
    def check_sclk2():

        if I2C_SDAT == 1:
            collector.next[0] = 1
        else:
            collector.next[0] = 0


        if I2C_SCLK == 1:
            collector.next[1] = 1
        else:
            collector.next[1] = 0

        if G_SENSOR_CS_N == 1:
            collector.next[2] = 0
        else:
            collector.next[2] = 1

#################################
        if count == 36+PAUSE:
            collector.next[7] = 1
        else:
            collector.next[7] = 0


        if count == 28+PAUSE:
            collector.next[6] = 1
        else:
            collector.next[6] = 0

        if count == 18:
            collector.next[5] = 1
        else:
            collector.next[5] = 0


        if count <=9 and count >=2:
            collector.next[4] = 1
        else:
            collector.next[4] = 0



    @always_comb
    def collector_comb():
        #LED.next = r_data2
        LED.next = collector 
            
                

        
    return instances()           


def drive_spi(tick, tick2,  G_SENSOR_CS_N,G_SENSOR_INT,I2C_SCLK,I2C_SDAT, LED, count, START, PAUSE):

    read_Adr_inst = readData( tick, tick2,  G_SENSOR_CS_N,I2C_SDAT,LED , I2C_SCLK,count, START, PAUSE)    
           

    return instances()      
    
    

def top( CLOCK_50, LED,G_SENSOR_CS_N,G_SENSOR_INT,I2C_SCLK,I2C_SDAT):
    tick  = Signal(False)
    tick2  = Signal(False)
    START = 40
    PAUSE = 4
    count = Signal(intbv(START, min=-1, max=10000))
    clk_gen_inst = clk_gen(CLOCK_50, tick, tick2, I2C_SCLK)
    drive_spi_inst = drive_spi(tick, tick2, G_SENSOR_CS_N,G_SENSOR_INT,I2C_SCLK,I2C_SDAT, LED, count, START, PAUSE)


    return instances()
    
    
    


def test_dff(): 
    G_SENSOR_CS_N = Signal(bool(1))
    G_SENSOR_INT  = Signal(bool(0))
    I2C_SCLK      = Signal(bool(1))
    I2C_SDAT      = TristateSignal(False)     
    LED =   Signal(intbv(0)[8:])
   
    clk = Signal(bool(0))
    dff_inst = top( clk, LED,G_SENSOR_CS_N,G_SENSOR_INT,I2C_SCLK,I2C_SDAT)
    
    @always(delay(1))
    def clkgen():
        clk.next = not clk

    return dff_inst, clkgen

def simulate(timesteps): 
    tb = traceSignals(test_dff) 
    sim = Simulation(tb) 
    sim.run(timesteps)

simulate(4000)
