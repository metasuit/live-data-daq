import numpy
import pprint
import nidaqmx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import datetime as dt
import time
from nidaqmx import constants
from nidaqmx.constants import Edge, Slope
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from nidaqmx.stream_readers import AnalogSingleChannelReader

pp = pprint.PrettyPrinter(indent=4)
     
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = []
ys = []

# This function is called periodically from FuncAnimation
def animate(i, xs, ys):

    # Read temperature (Celsius) from TMP102
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan("myDAQ1/ai0")
    
        
        task.timing.cfg_samp_clk_timing(rate=200000,
                                         #source='/cDAQ1/ai/SampleClock',
                                         sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,  # dont use continuous
                                         samps_per_chan=1)
        temp_c = task.read()
    # Add x and y to lists
    xs.append(dt.datetime.now().strftime('%H:%M:%S.%f'))
    ys.append(temp_c)

    # Limit x and y lists to 20 items
    xs = xs[-20:]
    ys = ys[-20:]

    # Draw x and y lists
    ax.clear()
    ax.plot(xs, ys)

    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title('TMP102 Temperature over Time')
    plt.ylabel('Temperature (deg C)')

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=1000)
plt.show()