import nidaqmx
from nidaqmx import task
from nidaqmx.constants import (AcquisitionType)  # https://nidaqmx-python.readthedocs.io/en/latest/constants.html
import numpy as np


def hardwareContinuousVoltageWithCallBackNoPlot():

    # Define variables
    sampleRate = 100000  # Sample Rate in Hz
    pointsToPlot = 40


    def pullDataAndPlot(tTask, event_type, num_samples, callback_data):
        # We reach this point once all data have been read
        data = task.read(number_of_samples_per_channel=pointsToPlot)
        print(np.mean(data))

        return 0

    print('Opening task (ctrl-c to stop)')
    # * Create a DAQmx task named 'softwareTimedVoltage'
    #   More details at: "help dabs.ni.daqmx.Task"
    #   C equivalent - DAQmxCreateTask
    #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcreatetask/
    with nidaqmx.Task('hardwareContinuousVoltageWithCallBackNoPlot') as task:
        # * Set up analog input 0 on device defined by variable devName
        #   It's is also valid to use device and channel only: task.ai_channels.add_ai_voltage_chan('Dev1/ai0');
        #   But see defaults: help(task.ai_channels.add_ai_voltage_chan)
        #   C equivalent - DAQmxCreateAIVoltageChan
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcreateaivoltagechan/
        task.ai_channels.add_ai_voltage_chan('myDAQ1/ai0')

        # * Configure the sampling rate and the number of samples
        #   C equivalent - DAQmxCfgSampClkTiming
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcfgsampclktiming/
        #   More details at: "help(task.cfg_samp_clk_timing)
        #   https://nidaqmx-python.readthedocs.io/en/latest/constants.html
        task.timing.cfg_samp_clk_timing(sampleRate, samps_per_chan=pointsToPlot * 2,
                                        sample_mode=AcquisitionType.CONTINUOUS)

        # * Register a callback funtion to be run every N samples
        task.register_every_n_samples_acquired_into_buffer_event(pointsToPlot, pullDataAndPlot)

        # We configured no triggers, so the acquisition starts as soon as hTask.start is run
        # Start the task and plot the data
        task.start()

        while True:
            pass

    task.stop()

if __name__ == '__main__':
    hardwareContinuousVoltageWithCallBackNoPlot()