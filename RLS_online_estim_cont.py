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

#Set up empty lists for values of both voltage measurements (the second voltage to calculate current) and capacities
volt_list = list()
cur_volt_list = list()
cap_list = list()
Ck = 1


class voltageContinuousInput(tk.Frame):

    def __init__(self, master):
        tk.Frame.__init__(self, master)

        # Configure root tk class
        self.master = master
        self.master.title("Voltage - Continuous Input")
        self.master.iconbitmap("Voltage - Continuous Input.ico")
        self.master.geometry("1100x700")

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
        global data_type_for_graph
        
        # Prevent user from starting task a second time
        self.inputSettingsFrame.startButton['state'] = 'disabled'

        # Shared flag to alert task if it should stop
        self.continueRunning = True

        # Get task settings from the user
        physicalChannel = self.channelSettingsFrame.physicalChannelEntry.get()
        physicalChannel2 = self.channelSettingsFrame.physicalChannelEntry2.get()
        maxVoltage = int(self.channelSettingsFrame.maxVoltageEntry.get())
        minVoltage = int(self.channelSettingsFrame.minVoltageEntry.get())
        sampleRate = int(self.inputSettingsFrame.sampleRateEntry.get())
        self.data_type_for_graph = self.inputSettingsFrame.dataTypeCombobox.get()
        self.numberOfSamples = int(
            self.inputSettingsFrame.numberOfSamplesEntry.get())  # Have to share number of samples with runTask

        #Parameters to set up:
        self.mu = 0.1 # 0 < mu < 1, forgetting factor, the smaller mu, the faster the RLS but noise is amplified
        self.current_meas_resistance = 10000
        delta = 1 #value to initialize Pk(0)


        # initial guesses
        initial_voltage = 2  # voltage, subscript denotes previous step
        initial_r_electrodes = 3000  # resistance of electrodes
        initial_capacity = 9e-12  # capacity of hasel
        initial_current = 1e-10  # current
        self.Pk= delta * np.identity(3) #initial state of recursive function Pk
        self.vk_1 = initial_voltage
        self.ik_1 = initial_current
        self.sampling_time = 1 / sampleRate
        self.theta= np.array([initial_voltage, initial_r_electrodes * initial_current, (self.sampling_time/initial_capacity - initial_r_electrodes) * initial_current])

        # Create and start task
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(physicalChannel, min_val=minVoltage, max_val=maxVoltage)
        self.task.ai_channels.add_ai_voltage_chan(physicalChannel2, min_val=minVoltage, max_val=maxVoltage)
        self.task.timing.cfg_samp_clk_timing(sampleRate, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                             samps_per_chan=2000)  # samps_per_chan=self.numberOfSamples*3)
        self.task.start()

        # spin off call to check
        self.master.after(10, self.runTask)

    def runTask(self):
        # Check if task needs to update the graph
        global Ck
        two_input_vals = self.task.read(nidaqmx.constants.READ_ALL_AVAILABLE)

        for i in range(len(two_input_vals[0])):
            self.ik = two_input_vals[0][i] / self.current_meas_resistance
            self.vk = two_input_vals[1][i]


            phik = np.array([self.vk_1, self.ik, self.ik_1])
            phik_t = phik.transpose()

            #if statement which records the RMS values of both voltage inputs for graph if so desired
            if self.data_type_for_graph == "RMS Voltages":

                volt_list.append(self.vk)
                cur_volt_list.append(two_input_vals[0][i])  
        
        
            #updating estimates
            div_fact = 1 + np.dot(phik_t, np.dot(self.Pk, phik))
            if div_fact != 0:
                self.theta = self.theta + np.dot(self.Pk, phik) / div_fact * (self.vk- np.dot(phik_t, self.theta))
                self.Pk = 1 / self.mu * (self.Pk - np.dot(self.Pk, np.dot(phik, np.dot(phik_t, self.Pk))) / div_fact)
            else:
                print("division by zero while updating")
            #update last measurements to current one for next run
            self.ik_1 = self.ik
            self.vk_1 = self.vk

            self.Rk = self.theta[1] / phik[1] # theta / ik
            Ck = self.sampling_time / (self.theta[2] / phik[2] + self.Rk) # Ts / (theta / ik_1) + Rk
            #print(Ck)
            cap_list.append(Ck)


            self.graphDataFrame.ax.cla()
            if self.data_type_for_graph == "RMS Voltages":
                self.graphDataFrame.ax.set_title("RMS Voltages: ")
                self.graphDataFrame.ax.plot(volt_list)
                self.graphDataFrame.ax.plot(cur_volt_list)
            else:
                self.graphDataFrame.ax.set_title("Capacity: " + str(Ck))
                self.graphDataFrame.ax.plot(cap_list)
            # self.graphDataFrame.ax.plot(cap_list)
            # self.graphDataFrame.ax.plot(vals)
            self.graphDataFrame.graph.draw()

            # check if the task should sleep or stop
            if (self.continueRunning):
                self.master.after(5, self.runTask)

            else:
                cap_list.clear()
                volt_list.clear()
                cur_volt_list.clear()
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
        self.physicalChannelLabel = ttk.Label(self, text="Physical Channels")
        self.physicalChannelLabel.grid(row=0, sticky='w', padx=self.xPadding, pady=(10, 0))

        self.physicalChannelEntry = ttk.Combobox(self, values=["myDAQ1/ai0", "MyDAQ1/ai1"])
        self.physicalChannelEntry.current(0)
        self.physicalChannelEntry.grid(row=1, sticky="ew", padx=self.xPadding)
        #Add space between channels
        self.spacer = ttk.Label(self, text="")
        self.spacer.grid(row=2, sticky="w", padx=self.xPadding, pady=(5,0))
        #Add second Channel
        self.physicalChannelEntry2 = ttk.Combobox(self, values=["myDAQ1/ai0", "myDAQ1/ai1"])
        self.physicalChannelEntry2.current(1)
        self.physicalChannelEntry2.grid(row=3, sticky="ew", padx=self.xPadding)

        self.maxVoltageLabel = ttk.Label(self, text="Max Voltage")
        self.maxVoltageLabel.grid(row=4, sticky='w', padx=self.xPadding, pady=(10, 0))

        self.maxVoltageEntry = ttk.Entry(self)
        self.maxVoltageEntry.insert(0, "10")
        self.maxVoltageEntry.grid(row=5, sticky="ew", padx=self.xPadding)

        self.minVoltageLabel = ttk.Label(self, text="Min Voltage")
        self.minVoltageLabel.grid(row=6, sticky='w', padx=self.xPadding, pady=(10, 0))

        self.minVoltageEntry = ttk.Entry(self)
        self.minVoltageEntry.insert(0, "-10")
        self.minVoltageEntry.grid(row=7, sticky="ew", padx=self.xPadding, pady=(0, 10))



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

        #Add a Combobox widget to choose between "Voltages" and "Capacity"
        self.dataTypeLabel = ttk.Label(self, text="Data type used in graph")
        self.dataTypeLabel.grid(row=5, column=0, sticky='w', padx=self.xPadding, pady=(10,0))
        self.dataTypeCombobox = ttk.Combobox(self, values=["RMS Voltages", "Capacity"])
        self.dataTypeCombobox.current(1)
        self.dataTypeCombobox.grid(row=6, column=0, sticky='ew', padx=self.xPadding)


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
