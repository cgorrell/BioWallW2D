# Simple Modbus Master
import setup
import time
from pyonep import onep
import sqlite3 as lite
import sys
import serial
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu
from threading import Timer
from pyonep.exceptions import OneException
import logging
import logging.config
#import RPi.GPIO as GPIO

#GPIO.setmode(GPIO.BCM)
#GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


#*******************************************************************************
# TIMER FUNCTIONS***********************************************************
    # get timers from database, and return there values as variables
    # Gets timers at the start of each cycle, and executes functions as the cycle calls out for them.
def Water_timer():
	Water_timer_logger = logging.getLogger("exosite.Water_timer")
	Water_timer_logger.debug("starting new watering cycle")
	con2 = lite.connect('pi.db')
	Water_timer_logger.debug("fetching output timers from database")
	with con2:
		cur = con2.cursor()
		Cycle_length = cur.execute("SELECT Length FROM Timers WHERE Name = ?;", ('Pump_cycle', )).fetchone()[0]
		Time_on = cur.execute("SELECT Length FROM Timers WHERE Name = ?;", ('Pump_timer', )).fetchone()[0]
		Dose_period = cur.execute("SELECT Length FROM Timers WHERE Name = ?;", ('Fertigator_timer', )).fetchone()[0]
		Leak_address = cur.execute("SELECT Address FROM Sensors WHERE Alias = ?;", ('Leak', )).fetchone()[0]
	#if GPIO.input(23) == 1:
	#	setup.Startup()
	#else:
	try:
		Water_timer_logger.debug("Checking for leaks")
		if wall.execute(1, cst.READ_HOLDING_REGISTERS, Leak_address, 1)[0] > 1000:
			Water_on(Dose_period)
			time.sleep(Time_on)
			Water_off()
			time.sleep(abs(Cycle_length - Time_on))
		else:
			Water_timer_logger.warning("Leak detected!")
			Device_alarm("Leak detected!")
			failsafe.py
			time.sleep(300)
	except modbus_tk.modbus.ModbusError, e:
		time.sleep(300)
		Water_timer_logger.error("%s- Code=%d", e, e.get_exception_code())
	except modbus_tk.modbus.ModbusInvalidResponseError, e:
		time.sleep(300)
		Water_timer_logger.error("%s", e)
	except lite.Error as e:
		time.sleep(300)
		Water_timer_logger.error("A sqlite error occured: %s", e.args[0])
	except OneException, exct:
		time.sleep(300)
		Water_timer_logger.error("Exosite error: %s", exct)
	except :
		time.sleep(300)
		Water_timer_logger.error("Device Communication Error")
		Device_alarm("Device Communication Error")
#*******************************************************************************
# MODBUS DATA MANAGER***********************************************************

    # IO management betweeen modbus and exosite
def Data_manager():
	Data_manager_logger = logging.getLogger("exosite.Data_manager")
	Data_manager_logger.debug("Starting new data cycle")
	con3 = lite.connect('pi.db')
	Data_manager_logger.debug("fetching data relay timer from database")
	with con3:
		cur = con3.cursor()
		Relay = cur.execute("SELECT Length FROM Timers WHERE Name = ?;", ('Relay', )).fetchone()[0]
	time.sleep(Relay)
	Sensor_delivery()
	Output_delivery()
	Timer_sync()

def Sensor_delivery():
	Sensor_delivery_logger = logging.getLogger("exosite.Sensor_delivery")
	con3 = lite.connect('pi.db')
	try:
		Sensor_delivery_logger.debug("Getting sensor values from modbus unit")
		Reader = wall.execute(1, cst.READ_HOLDING_REGISTERS, Starting_input, Qty_inputs)
		Sensor_delivery_logger.debug(Reader)
		Wall_data = []
		for data in Reader:    
			Wall_data += [round(data*10.00/(2**bits), 3)]

		Sensor_delivery_logger.debug("Wall sensor values: " + str(Wall_data))
		vals_to_write = []
		Sensor_delivery_logger.debug("Getting alias for sensors")
		with con3:
			cur = con3.cursor()
			cur.execute("SELECT Alias, Address FROM Sensors")
			while True:
				row = cur.fetchone()
				if row == None:
					break
				vals_to_write += [[{'alias':row[0].encode('ascii', 'ignore')}, Wall_data[row[1]-Starting_input]]]
		Sensor_delivery_logger.info(vals_to_write)
		Sensor_delivery_logger.debug("Submitting sensor data to exosite")
		o.writegroup(
			cik,
			vals_to_write)
	    
	except modbus_tk.modbus.ModbusError, e:
		time.sleep(30)
		Sensor_delivery_logger.error("%s- Code=%d", e, e.get_exception_code())
	except modbus_tk.modbus.ModbusInvalidResponseError, e:
		time.sleep(30)
		Sensor_delivery_logger.error("%s", e)
	except lite.Error as e:
		time.sleep(30)
		Sensor_delivery_logger.error("A sqlite error occured: %s", e.args[0])
	except OneException, exct:
		time.sleep(30)
		Sensor_delivery_logger.error("Exosite error: %s", exct)
	except :
		time.sleep(30)
		Sensor_delivery_logger.error("Device Communication Error")
		Device_alarm("Device Communication Error")

def Output_delivery():
	Output_delivery_logger = logging.getLogger("exosite.Output_delivery")
	# get outputs from database, get there status, and send there status to exosite.
	con3 = lite.connect('pi.db')
	try:
		Output_delivery_logger.debug("Getting output values from modbus unit")
		Reader = wall.execute(1, cst.READ_HOLDING_REGISTERS, Starting_output, Qty_outputs)
		Wall_state = []
		for data in Reader:
			Wall_state += [data]
		vals_to_write = []
		Output_delivery_logger.info(Wall_state)
		Output_delivery_logger.debug("Getting output Alias from database")
		with con3:
			cur = con3.cursor()
			cur.execute("SELECT Alias, Address FROM Outputs")
			while True:
				row = cur.fetchone()
				if row == None:
					break
				vals_to_write += [[{'alias':row[0].encode('ascii', 'ignore')}, Wall_state[row[1]-Starting_output]]]
		Output_delivery_logger.info(vals_to_write)
		Output_delivery_logger.debug("submitting outputs to exosite")
		o.writegroup(
			cik,
			vals_to_write)
	    
	except modbus_tk.modbus.ModbusError, e:
		time.sleep(300)
		Output_delivery_logger.error("%s- Code=%d" % (e, e.get_exception_code()))
	except modbus_tk.modbus.ModbusInvalidResponseError, e:
		time.sleep(300)
		Output_delivery_logger.error("%s", (e))
	except lite.Error as e:
		time.sleep(300)
		Output_delivery_logger.error("A sqlite error occured: %s", e.args[0])
	except OneException, exct:
		time.sleep(300)
		Output_delivery_logger.error("exosite error %s", exct)
	except :
		time.sleep(300)
		Output_delivery_logger.error("Device Communication Error")
		Device_alarm("Device Communication Error")

def Timer_sync():
	Timer_sync_logger = logging.getLogger("exosite.Timer_sync")	
	con3 = lite.connect('pi.db')
	#Get Timers from database
	with con3:
		Timer_sync_logger.debug("fetching timers from database")
		cur = con3.cursor()
		cur.execute("SELECT Name, Length FROM Timers")
		Timers = cur.fetchall()
	#for each timer that we fetched from the database, get the latest timer from exosite for this device.
	for row in Timers:
		Dataport_alias = row[0].encode('ascii', 'ignore')
		Dataport_value = row[1]
		Timer_sync_logger.debug(Dataport_alias + ": " + str(Dataport_value))
		try:
			isok, response = o.read(
				cik,
				{'alias': Dataport_alias},
				{'limit': 1, 'sort': 'desc', 'selection': 'all'})

			if isok:
		        # if the timer setting in exosite has changed, update the device timer with new value, change it in the database.
		        # expect Read back [[1374522992, 1]]
				if response[0][1] != Dataport_value:
					Dataport_value = response[0][1]
					with con3:
						cur = con3.cursor()
						cur.execute("UPDATE Timers SET Length = ? WHERE Name = ? ;", (Dataport_value, Dataport_alias, ))
					Timer_sync_logger.info("%s is now set to %s seconds.", Dataport_alias, Dataport_value)   
			else:
				Timer_sync_logger.warning("Read failed: %s", response)
		except OneException, exct:
			Timer_sync_logger.error("Failed to check timers against exosite: %s", exct)
#*******************************************************************************
# MODBUS Outputs ***********************************************************

# Setup to run Pump_address as solenoid for running W2D. (change to run_on, run_off with supply vs pump make ups based on recirc)
def Water_on(Dose_period):
	Water_on_logger = logging.getLogger("exosite.Water_on")
	try:
		Water_on_logger.debug("Turning on Water")
		wall.execute(1, cst.WRITE_SINGLE_REGISTER, Supply_address, output_value=1)

	except modbus_tk.modbus.ModbusError, e:
		Water_on_logger.error("%s- Code=%d", e, e.get_exception_code())
	except modbus_tk.modbus.ModbusInvalidResponseError, e:
		Water_on_logger.error("%s", e)
	except lite.Error as e:
		Water_on_logger.error("A sqlite error occured: %s", e.args[0])
	except :
		Water_on_logger.error("Device Communication Error")
		Device_alarm("Device Communication Error")
	Fertigation(Dose_period)

def Water_off():
	Water_off_logger = logging.getLogger("exosite.Water_off")
	try:
		Water_off_logger.debug("Turning off water")
		wall.execute(1, cst.WRITE_SINGLE_REGISTER, Supply_address, output_value=0)

	except modbus_tk.modbus.ModbusError, e:
		Water_off_logger.error("%s- Code=%d", e, e.get_exception_code())
	except modbus_tk.modbus.ModbusInvalidResponseError, e:
		Water_off_logger.error("%s", e)
	except lite.Error as e:
		Water_off_logger.error("A sqlite error occured: %s", e.args[0])
	except :
		Water_off_logger.error("Device Communication Error")
		Device_alarm("Device Communication Error")

def Fertigation(Dose_period):
	Fertigation_logger = logging.getLogger("exosite.Fertigation")
	try:
		Fertigation_logger.debug("Running fertigation cycle")
		wall.execute(1, cst.WRITE_SINGLE_REGISTER, Fertigator_address, output_value=1)
		time.sleep(Dose_period)
		wall.execute(1, cst.WRITE_SINGLE_REGISTER, Fertigator_address, output_value=0)
		Fertigation_logger.debug("Terminating fertigation cycle")
	except modbus_tk.modbus.ModbusError, e:
		Fertigation_logger.error("%s- Code=%d", e, e.get_exception_code())
	except modbus_tk.modbus.ModbusInvalidResponseError, e:
		Fertigation_logger.error("%s", e)
	except lite.Error as e:
		Fertigation_logger.error("A sqlite error occured: %s", e.args[0])
	except :
		Fertigation_logger.error("Device Communication Error")
		Device_alarm("Device Communication Error")


class perpetualTimer():
	
	def __init__(self,t,hFunction):
		self.t=t
		self.hFunction = hFunction
		self.thread = Timer(self.t,self.handle_function)

	def handle_function(self):
		self.hFunction()
		self.thread = Timer(self.t,self.handle_function)
		self.thread.start()
	def start(self):
		self.thread.start()

	def cancel(self):
		self.thread.cancel()

def Device_alarm(alarm):
	Alarm_logger = logging.getLogger("exosite.Device_alarm")
	Alarm_logger.error("alarm has been thrown: %s", alarm)
	o = onep.OnepV1()
	cik = str(Device_code)
	try:
		o.write(
			cik,
			{"alias": "Alarm"},
			alarm,
			{})
	except OneException, exct:
		Alarm_logger.warning("failed to update exosite alarm: %s", exct)
#*******************************************************************************
# MANUAL MODE FUNCTIONS***********************************************************

if __name__ == '__main__':
	#ONLY RUNS ON BOOT
	logging.config.fileConfig("logging.conf")
	logger = logging.getLogger("exosite")
	setup.Startup()
	import failsafe
	c = setup.con
	logger.debug("fetching modbus parameters from database")
	with c:
		cur = c.cursor()
		Modbus_address = cur.execute("SELECT Value FROM Modbus WHERE Name = ?;", ('Modbus_address', )).fetchone()[0]
		baudrate = cur.execute("SELECT Value FROM Modbus WHERE Name = ?;", ('Baudrate', )).fetchone()[0]
		bits = cur.execute("SELECT Value FROM Modbus WHERE Name = ?;", ('Register_bit_length', )).fetchone()[0]
		Starting_input = cur.execute("SELECT Value FROM Modbus WHERE Name = ?;", ('Starting_input', )).fetchone()[0]
		Qty_inputs = cur.execute("SELECT Value FROM Modbus WHERE Name = ?;", ('Qty_inputs', )).fetchone()[0]
		Starting_output = cur.execute("SELECT Value FROM Modbus WHERE Name = ?;", ('Starting_output', )).fetchone()[0]
		Qty_outputs = cur.execute("SELECT Value FROM Modbus WHERE Name = ?;", ('Qty_outputs', )).fetchone()[0]

	logger.debug("getting CIK of device from database")
	with c:
		cur = c.cursor()
		Device_code = cur.execute("SELECT Value FROM Gateway WHERE Name = ?;", ('Device_cik', )).fetchone()[0].encode('ascii', 'ignore')

	logger.debug("getting modbus output addresses from database")
	with c:
		cur = c.cursor()
		Fertigator_address = cur.execute("SELECT Address FROM Outputs WHERE Alias = ?;", ('Fertigator', )).fetchone()[0]
		Supply_address = cur.execute("SELECT Address FROM Outputs WHERE Alias = ?;", ('Solenoid', )).fetchone()[0]

	o = onep.OnepV1()
	cik = str(Device_code)
	try:
		logger.debug("attempting to reset alarm status on exosite")
		o.write(
				cik,
				{"alias": "Alarm"},
				"None",
				{})
		logger.info("reset alarm status on exosite")
	except OneException, exct:
		logger.error("failed to reset alarm because %s", exct)
	try:
		logger.debug("attempting to connect to modbus device")
		wall = modbus_rtu.RtuMaster(serial.Serial(port='/dev/rfxcom', baudrate= baudrate, bytesize=8, parity='N', stopbits=1, xonxoff=0))
		wall.set_timeout(5.0)
		logger.info("connected to modbus device")
	except :
		logger.error("device not connected")
		Device_alarm("slave not connected")

	logger.debug("generating timers")
	Start_hydration= perpetualTimer(.05, Water_timer)
	Start_comm = perpetualTimer(.05, Data_manager)
	Start_hydration.start()
	Start_comm.start()

	