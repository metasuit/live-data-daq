def softwareTimedVoltage():
    import nidaqmx
    import numpy as np
    import matplotlib.pyplot as plt

    # Define variables
    samplesToAcquire = 100
    data = np.zeros(samplesToAcquire)  # pre-allocate numpy array

    print('Acquiring data...', end=' ')

    # * Create a DAQmx task named 'softwareTimedVoltage'
    #   More details at: "help dabs.ni.daqmx.Task"
    #   C equivalent - DAQmxCreateTask
    #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcreatetask/
    with nidaqmx.Task('softwareTimedVoltage') as task:
        # * Set up analog input 0 on device defined by variable devName
        #   It's is also valid to use device and channel only: task.ai_channels.add_ai_voltage_chan('Dev1/ai0');
        #   But see defaults: help(task.ai_channels.add_ai_voltage_chan)
        #   C equivalent - DAQmxCreateAIVoltageChan
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcreateaivoltagechan/
        task.ai_channels.add_ai_voltage_chan('myDAQ1/ai0', min_val=-10, max_val=10)

        for ii in range(samplesToAcquire):
            data[ii] = task.read()

        print('done')

        # Plot data points to screen
        plt.plot(data)
        plt.xlabel('time [samples]')
        plt.ylabel('voltage [V]')
        plt.grid()
        plt.show()


if __name__ == '__main__':
    softwareTimedVoltage()