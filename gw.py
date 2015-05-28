import os
import random
from random import randrange
from copy import copy

## 
## python convert.py ;
## simulation:
## python gw.py; gtkwave  test_dff.vcd
## pip install --upgrade git+https://github.com/jandecaluwe/myhdl



from myhdl import *

def clk_gen(CLOCK_50, KEY, tick, tick1,tick2, sys_rst ,CLK_FREQ = 48e6 ,LED_RATE =0.000001, DELAY = 8 ): #DE0Nano-Board
#def clk_gen(CLOCK_50, KEY, tick,tick1, tick2, sys_rst,CLK_FREQ = 100 ,LED_RATE = 1 , DELAY = 8 ): #Simulation
    CNT_MAX = int(CLK_FREQ * LED_RATE)
    clk_cnt  = Signal(intbv(0, min=0, max=CNT_MAX+2))

    
    @always_seq(CLOCK_50.posedge, reset = sys_rst) 
    def aClockgen():
        clk_cnt.next = clk_cnt + 1
        if clk_cnt < CNT_MAX:
            tick.next = 0
            tick1.next= 0
            tick2.next= 0
        else:
            clk_cnt.next = 0
            tick.next  = 1

        if clk_cnt == CNT_MAX - DELAY:
            tick1.next = 1

        if clk_cnt ==  DELAY:
            tick2.next = 1
               
    return instances()

def strobe(CLOCK_50, tick,tick1, tick2, LED, sys_rst, G_SENSOR_CS_N, I2C_SCLK, I2C_SDAT):
    t_state_cs = enum("CS_H","CS_L")
    state_cs = Signal(t_state_cs.CS_H)

    t_state_clk = enum("CLK_RUNNING","CLK_READY","CLK_STOP")
    state_clk = Signal(t_state_clk.CLK_STOP)


    comb  = Signal(intbv(0)[8:])
    spi_byte_count = Signal(intbv(0)[8:])
 
    
    @always_seq(CLOCK_50.posedge, reset = sys_rst)
    def a_strobe():
        if tick:            
            G_SENSOR_CS_N.next = 0
            state_cs.next = t_state_cs.CS_L
            spi_byte_count.next = spi_byte_count + 1
            if spi_byte_count == 31:
                state_cs.next  = t_state_cs.CS_H
                spi_byte_count.next = 0

            if  state_cs == t_state_cs.CS_H:                
                state_clk.next = t_state_clk.CLK_READY

        if state_cs == t_state_cs.CS_H and tick2:
            G_SENSOR_CS_N.next = 1
            state_clk.next = t_state_clk.CLK_STOP
        
            
        if  (state_clk == t_state_clk.CLK_READY) and tick2:
            state_clk.next = t_state_clk.CLK_RUNNING
            I2C_SCLK.next = 0

        if state_clk == t_state_clk.CLK_RUNNING and tick and state_clk != t_state_clk.CLK_STOP:
            I2C_SCLK.next  = not I2C_SCLK
                



    t_state_dat = enum("DAT_ACTIV","DAT_PASSIV")
    state_dat = Signal(t_state_dat.DAT_PASSIV)

    DAT_Tick = Signal(bool(1))   

    @always_seq(CLOCK_50.posedge, reset = sys_rst)
    def b_strobe():
        if state_clk == t_state_clk.CLK_RUNNING and tick1 and state_dat == t_state_dat.DAT_PASSIV:
            state_dat.next = t_state_dat.DAT_PASSIV
            DAT_Tick.next = 1

        if state_clk == t_state_clk.CLK_RUNNING and tick2 and state_dat == t_state_dat.DAT_PASSIV:
            state_dat.next = t_state_dat.DAT_ACTIV
                 

        if state_clk == t_state_clk.CLK_RUNNING and tick2 and state_dat == t_state_dat.DAT_ACTIV:
            state_dat.next = t_state_dat.DAT_PASSIV
            DAT_Tick.next = 0            

        if state_clk == t_state_clk.CLK_STOP and tick1:
            state_dat.next = t_state_dat.DAT_PASSIV
            DAT_Tick.next = 0

        if DAT_Tick == 1:
            DAT_Tick.next = 0



    w_adr_1  = Signal(intbv(0x31)[8:0])#31-->31
    w_data1  = Signal(intbv(0x4e)[8:0])#4E-->4E
    w_adr_2  = Signal(intbv(0x80)[8:0])#00-->80
    r_data2  = Signal(intbv(0)[8:0])   # should be DEVID (0xE5)
            

    io = I2C_SDAT.driver()
    io.next = 0
    BitLength = 8
    count_8bit  = Signal(intbv(BitLength, min=-1, max=9) )
    byte_count  = Signal(intbv(0)[4:0])
    ready_for_reading = Signal(bool(0))
    t_state_push = enum("PUSH_WAIT","PUSH_RUN")
    state_push = Signal(t_state_push.PUSH_WAIT)
    

    @always_seq(CLOCK_50.posedge, reset = sys_rst)
    def push_data():
        if state_clk == t_state_clk.CLK_STOP:
            state_push.next = t_state_push.PUSH_RUN
        if DAT_Tick and state_push == t_state_push.PUSH_RUN and byte_count == 0:
            count_8bit.next = count_8bit - 1
            io.next = w_adr_1[count_8bit-1]

        if DAT_Tick and state_push == t_state_push.PUSH_RUN and byte_count == 1:
            count_8bit.next = count_8bit - 1
            io.next = w_data1[count_8bit-1] 
            

        if DAT_Tick and state_push == t_state_push.PUSH_RUN and byte_count == 2:
            count_8bit.next = count_8bit - 1
            io.next = w_adr_2[count_8bit-1]

        if DAT_Tick and state_push == t_state_push.PUSH_RUN and byte_count == 3:
            count_8bit.next = count_8bit - 1
            io.next = None
            ready_for_reading.next = 1

        if  count_8bit == 0:
            count_8bit.next = BitLength
            byte_count.next = byte_count + 1

        if ready_for_reading == 1 and tick2:
            if I2C_SDAT == 1 :
                r_data2.next[count_8bit-1] = 1
            else:
                r_data2.next[count_8bit-1] = 0
            
            
            
            

    
    @always_comb
    def c_strobe():
        LED.next = r_data2
    return instances()
    
  
    

def top( CLOCK_50, LED, KEY, sys_rst, G_SENSOR_CS_N, I2C_SCLK, I2C_SDAT):
    tick  = Signal(bool(0))
    tick1 = Signal(bool(0))
    tick2 = Signal(bool(0))    
    clk_gen_inst  = clk_gen(CLOCK_50, KEY, tick,tick1, tick2,  sys_rst)
    strobe_inst   = strobe( CLOCK_50, tick,tick1, tick2, LED, sys_rst, G_SENSOR_CS_N, I2C_SCLK, I2C_SDAT)
    return instances()
    
    
    


def test_dff(): 
    LED =   Signal(intbv(0)[8:])
    KEY =   Signal(intbv(0)[2:])
    G_SENSOR_CS_N = Signal(bool(1))
    I2C_SCLK      = Signal(bool(1))
    I2C_SDAT      = TristateSignal(False) 
    sys_rst = ResetSignal(1, active=0, async=True)  
    clk = Signal(bool(0))
    
    dff_inst = top( clk, LED, KEY, sys_rst, G_SENSOR_CS_N, I2C_SCLK, I2C_SDAT)
    
    @always(delay(1))
    def clkgen():
        clk.next = not clk

    return dff_inst, clkgen

def simulate(timesteps): 
    tb = traceSignals(test_dff) 
    sim = Simulation(tb) 
    sim.run(timesteps)

simulate(50000)
