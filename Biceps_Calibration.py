import time
from tkinter import *
import tkinter as tk
import concurrent.futures
from datetime import datetime, timedelta
import csv



def read_calibration_serial(sampling_time):

    end_time = datetime.now() + timedelta(seconds=sampling_time)
    list_values = []
    while datetime.now() < end_time:
        ser_bytes = ser.readline()
        if ser_bytes[0:len(ser_bytes) - 2].decode("utf-8") != '':
            decoded_bytes = float(ser_bytes[0:len(ser_bytes) - 2].decode("utf-8"))
            print(decoded_bytes)


            list_values.append(decoded_bytes)


    average = float(sum(list_values) / len(list_values))
    print(list_values)
    list_values.clear()
    print(list_values)
    print("Average:", average, "Length: ", len(list_values))
    return average


# Functions
def calib_stretch():

    with concurrent.futures.ThreadPoolExecutor() as executor:
        f1 = executor.submit(read_calibration_serial, int(calibration_time))

        try:
            # the input provided by the user is
            # stored in here :temp
            lb_done1 = tk.Label(text="Done", font=("Arial", 10, ""))
            second1.set(" " + str(calibration_time))
            temp = int(second1.get())
        except:
            print("Please input the right value")
        while temp > -1:
            # divmod(firstvalue = temp//60, secondvalue = temp%60)
            mins, secs = divmod(temp, 60)
            # Converting the input entered in mins or secs to hours,
            # mins ,secs(input = 110 min --> 120*60 = 6600 => 1hr :
            # 50min: 0sec)
            hours = 0
            if mins > 60:
                # divmod(firstvalue = temp//60, secondvalue
                # = temp%60)
                hours, mins = divmod(mins, 60)

            # using format () method to store the value up to
            # two decimal places
            second1.set("{0:2d}".format(secs))

            # updating the GUI window after decrementing the
            # temp value every time
            root.update()
            time.sleep(1)


            # after every one sec the value of temp will be decremented
            # by one
            temp -= 1

        list_calibration[0] = float(f1.result())
        lb_done1.place(x = screen_w/2+30, y = 173)

def calib_cont():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f2 = executor.submit(read_calibration_serial, int(calibration_time))
        try:
            # the input provided by the user is
            # stored in here :temp

            lb_done2 = tk.Label(text="Done", font=("Arial", 10, ""))

            second2.set(" " + str(calibration_time))
            temp = int(second2.get())
        except:
            print("Please input the right value")
        while temp > -1:

            # divmod(firstvalue = temp//60, secondvalue = temp%60)
            mins, secs = divmod(temp, 60)

            # Converting the input entered in mins or secs to hours,
            # mins ,secs(input = 110 min --> 120*60 = 6600 => 1hr :
            # 50min: 0sec)
            hours = 0
            if mins > 60:
                # divmod(firstvalue = temp//60, secondvalue
                # = temp%60)
                hours, mins = divmod(mins, 60)

            # using format () method to store the value up to
            # two decimal places
            second2.set("{0:2d}".format(secs))

            # updating the GUI window after decrementing the
            # temp value every time
            root.update()
            time.sleep(1)


            # after every one sec the value of temp will be decremented
            # by one
            temp -= 1

        list_calibration[1] = float(f2.result())
        lb_done2.place(x = screen_w/2+30, y = 298)

def terminate():
    with open("calibration.txt", 'r+') as file:
        file.truncate(0)

    with open("calibration.txt", "w") as f:
        # Make sure that those values are not the samer, otherwise div by 0
        if list_calibration[0] == list_calibration[1]:
            #lb_cont = tk.Label(
                #text= "Calibration failed, try again",
                #font=("Arial", 10, ""))

            #lb_cont.pack(pady=20)
            f.write(str(1) + "\n")
            f.write(str(0))

        f.write(str(list_calibration[0]) + "\n")
        f.write(str(list_calibration[1]))

    root.destroy() # Terminate after Calibration

# creating Tk window
root = Tk()

# setting geometry of tk window
screen_w = 500
screen_h = 700

root.geometry(str(screen_w) + "x" + str(screen_h))

# Using title() to display a message in
# the dialogue box of the message in the
# title bar.
root.title("Calibration")

# Declaration of variables
calibration_time = 1 #seconds
second1 = StringVar()
second2 = StringVar()

# setting the default value as 0
second1.set(" "+str(calibration_time))
second2.set(" "+str(calibration_time))
# Use of Entry class to take input from the user



# button widget
lb_header = tk.Label(text="HASEL Sensing Calibration", font=("Arial", 18, ""))
lb_header.pack(pady = 20)

lb_stretch = tk.Label(text="Fully stretch out your arm, click <Calibrate> and do not move for" + str(second1.get()) + " seconds", font=("Arial", 10, ""))
lb_stretch.pack(pady=20, side= TOP)


btn_stretch = Button(root, text='Calibrate', bd='5',
             command=calib_stretch)
btn_stretch.pack()

secondEntry = Entry(root, width=3, font=("Arial", 18, ""),
                    textvariable=second1)
secondEntry.pack()


lb_cont = tk.Label(text="Fully contract your arm, click <Calibrate> and do not move for" + str(second2.get()) + " seconds", font=("Arial", 10, ""))
lb_cont.pack(pady=20, side= TOP)


btn_cont = Button(root, text='Calibrate', bd='5',
             command=calib_cont)
btn_cont.pack()
secondEntry = Entry(root, width=3, font=("Arial", 18, ""),
                    textvariable=second2)
secondEntry.pack()

lb = tk.Label(text="Done")


btn_cont = Button(root, text='Terminate Calibration and start Animation', bd='5',
             command=terminate)
btn_cont.pack(pady= 40)


# infinite loop which is required to
# run tkinter program infinitely
# until an interrupt occurs
root.mainloop()
