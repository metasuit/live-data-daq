import nidaqmx
import tkinter as tk
from tkinter import ttk
import matplotlib
import numpy as np
import numpy.linalg as lina
import matplotlib.pyplot as plt

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

values = list()
cap_list = list()


#Parameters to set up:
mu = 0.1 # 0 < mu < 1, forgetting factor, the smaller mu, the faster the RLS but noise is amplified
sampleRate = 100000
delta = 1 #value to initialize Pk(0)


# initial guesses
initial_voltage = 2  # voltage, subscript denotes previous step
initial_r_electrodes = 3000  # resistance of electrodes
initial_capacity = 9e-12  # capacity of hasel
initial_current = 1e-10  # current
initial_guess = True
theta= np.array([initial_voltage, initial_r_electrodes * initial_current, (sampling_time/initial_capacity - initial_r_electrodes) * initial_current])
Pk= delta * np.identity(3) #initial state of recursive function Pk


class voltageContinuousInput(tk.Frame):

    def __init__(self, master):
        tk.Frame.__init__(self, master)

        # Configure root tk class
        self.master = master
        self.master.title("Voltage - Continuous Input")
        self.master.iconbitmap("Voltage - Continuous Input.ico")
        self.master.geometry("1100x600")

        self.create_widgets()
        self.pack()
        self.run = False

    def create_widgets(self):
        # The main frame is made up of three subframes
        self.channelSettingsFrame = channelSettings(self, title="Channel Settings")
        self.channelSettingsFrame.grid(row=0, column=1, sticky="ew", pady=(20, 0), padx=(20, 20), ipady=10)

        self.inputSettingsFrame = inputSettings(self, title="Input Settings")
        self.inputSettingsFrame.grid(row=1, column=1, pady=(20, 0), padx=(20, 20), ipady=10)

        self.graphDataFrame = graphData(self)
        self.graphDataFrame.grid(row=0, rowspan=2, column=2, pady=(20, 0), ipady=10)

    def startTask(self):
        # Prevent user from starting task a second time
        self.inputSettingsFrame.startButton['state'] = 'disabled'

        # Shared flag to alert task if it should stop
        self.continueRunning = True

        # Get task settings from the user
        physicalChannel = self.channelSettingsFrame.physicalChannelEntry.get()
        maxVoltage = int(self.channelSettingsFrame.maxVoltageEntry.get())
        minVoltage = int(self.channelSettingsFrame.minVoltageEntry.get())
        sampleRate = int(self.inputSettingsFrame.sampleRateEntry.get())
        self.numberOfSamples = int(
            self.inputSettingsFrame.numberOfSamplesEntry.get())  # Have to share number of samples with runTask

        # Create and start task
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(physicalChannel, min_val=minVoltage, max_val=maxVoltage)
        self.task.ai_channels.add_ai_voltage_chan("myDAQ1/ai1", min_val=minVoltage, max_val=maxVoltage)
        self.task.timing.cfg_samp_clk_timing(sampleRate, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                             samps_per_chan=2000)  # samps_per_chan=self.numberOfSamples*3)
        self.task.start()

        # spin off call to check
        self.master.after(10, self.runTask)

    def runTask(self):
        # Check if task needs to update the graph
        rms = 0
        sampling_time = 1/sampleRate
        two_input_vals = self.task.read(nidaqmx.constants.READ_ALL_AVAILABLE)
        if len(two_input_vals[0]) > 2000:

            # current
            vals = two_input_vals[0][0:2000]
            # voltage
            vals2 = two_input_vals[1][0:2000]

            #values.append(rms)

            # print(rms)
            # print("RMS above")
            # print(type(vals))
            # print(len(vals))
            # values.append(rms)

            if initial_guess:
                vk_1 = initial_voltage
                ik_1 = initial_current

            ik = np.sum(np.abs(vals)) / len(vals)
            phik = np.array([vk_1, ik, ik_1])
            phik_t = phik.transpose() 

            average = np.sum(np.abs(vals2)) / len(vals2)
            vk = np.sqrt(2) * np.pi * average / 4.0 #rms

            #updating estimates
            div_fact = 1 + np.dot(phik_t, np.dot(Pk * phik))
            if div_fact != 0:
                theta = theta + np.dot(Pk, phik) / div_fact * (vk- np.dot(phik_t, theta))
                Pk = 1 / mu * (Pk - np.dot(Pk, np.dot(phik, np.dot(phik_t, Pk))) / div_fact)
            else:
                print("division by zero while updating")
            initial_guess = False #from now on use previously updated estimate

            Rk = theta[1] / phik[1] # theta / ik
            Ck = sampling_time / (theta[2] / phik[2] + Rk) # Ts / (theta / ik_1) + Rk
            print(Ck)
            values.append(Ck)

            """
            for i in range(199):
                deltav1 = vals[i + 1] - vals[i]
                deltav0 = vals2[i + 1] - vals2[i]
                print(deltav0, deltav1)
                denom = 10000 * deltav0 - ((200000 + 10000) * deltav1)
                if denom != 0:
                    capacity = (1) * vals[i] / denom
                    cap_list.append(capacity)
                else:
                    print("division by zero")
            """
        else:
            print("short data")

        self.graphDataFrame.ax.cla()
        self.graphDataFrame.ax.set_title("RMS: " + str(rms))
        self.graphDataFrame.ax.plot(values)
        # self.graphDataFrame.ax.plot(cap_list)
        # self.graphDataFrame.ax.plot(vals)
        self.graphDataFrame.graph.draw()

        # check if the task should sleep or stop
        if (self.continueRunning):
            self.master.after(5, self.runTask)

        else:
            values.clear()
            self.task.stop()
            self.task.close()
            self.inputSettingsFrame.startButton['state'] = 'enabled'

    def stopTask(self):
        # call back for the "stop task" button
        self.continueRunning = False


class channelSettings(tk.LabelFrame):

    def __init__(self, parent, title):
        tk.LabelFrame.__init__(self, parent, text=title, labelanchor='n')
        self.parent = parent
        self.grid_columnconfigure(0, weight=1)
        self.xPadding = (30, 30)
        self.create_widgets()

    def create_widgets(self):
        self.physicalChannelLabel = ttk.Label(self, text="Physical Channel")
        self.physicalChannelLabel.grid(row=0, sticky='w', padx=self.xPadding, pady=(10, 0))

        self.physicalChannelEntry = ttk.Entry(self)
        self.physicalChannelEntry.insert(0, "myDAQ1/ai0")
        self.physicalChannelEntry.grid(row=1, sticky="ew", padx=self.xPadding)

        self.maxVoltageLabel = ttk.Label(self, text="Max Voltage")
        self.maxVoltageLabel.grid(row=2, sticky='w', padx=self.xPadding, pady=(10, 0))

        self.maxVoltageEntry = ttk.Entry(self)
        self.maxVoltageEntry.insert(0, "10")
        self.maxVoltageEntry.grid(row=3, sticky="ew", padx=self.xPadding)

        self.minVoltageLabel = ttk.Label(self, text="Min Voltage")
        self.minVoltageLabel.grid(row=4, sticky='w', padx=self.xPadding, pady=(10, 0))

        self.minVoltageEntry = ttk.Entry(self)
        self.minVoltageEntry.insert(0, "-10")
        self.minVoltageEntry.grid(row=5, sticky="ew", padx=self.xPadding, pady=(0, 10))


class inputSettings(tk.LabelFrame):

    def __init__(self, parent, title):
        tk.LabelFrame.__init__(self, parent, text=title, labelanchor='n')
        self.parent = parent
        self.xPadding = (30, 30)
        self.create_widgets()

    def create_widgets(self):
        self.sampleRateLabel = ttk.Label(self, text="Sample Rate (Max 200K)")
        self.sampleRateLabel.grid(row=0, column=0, columnspan=2, sticky='w', padx=self.xPadding, pady=(10, 0))

        self.sampleRateEntry = ttk.Entry(self)
        self.sampleRateEntry.insert(0, "100000")
        self.sampleRateEntry.grid(row=1, column=0, columnspan=2, sticky='ew', padx=self.xPadding)

        self.numberOfSamplesLabel = ttk.Label(self, text="Number of Samples (Doesnt do anything)")
        self.numberOfSamplesLabel.grid(row=2, column=0, columnspan=2, sticky='w', padx=self.xPadding, pady=(10, 0))

        self.numberOfSamplesEntry = ttk.Entry(self)
        self.numberOfSamplesEntry.insert(0, "200")
        self.numberOfSamplesEntry.grid(row=3, column=0, columnspan=2, sticky='ew', padx=self.xPadding)
        self.startButton = ttk.Button(self, text="Start Task", command=self.parent.startTask)
        self.startButton.grid(row=4, column=0, sticky='w', padx=self.xPadding, pady=(10, 0))

        self.stopButton = ttk.Button(self, text="Stop Task", command=self.parent.stopTask)
        self.stopButton.grid(row=4, column=1, sticky='e', padx=self.xPadding, pady=(10, 0))


class graphData(tk.Frame):

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.create_widgets()

    def create_widgets(self):
        v = tk.StringVar()
        self.graphTitle = ttk.Label(self, text="Voltage Input")
        self.fig = Figure(figsize=(7, 5), dpi=100)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.set_title(v)
        self.graph = FigureCanvasTkAgg(self.fig, self)
        self.graph.draw()
        self.graph.get_tk_widget().pack()


# Creates the tk class and primary application "voltageContinuousInput"
root = tk.Tk()
app = voltageContinuousInput(root)

# start the application

app.mainloop()