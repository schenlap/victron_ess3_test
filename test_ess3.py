#!/usr/bin/env python3

import logging
from pymodbus.constants import Endian
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.payload import BinaryPayloadDecoder
from time import sleep

# Konfigurationsparameter
IP_ADDRESS = '10.0.0.202'  # Die IP-Adresse des Victron MultiPlus
PORT = 502  # Standard Modbus-TCP-Port
UNIT_ID_HUB4 = 100
UNIT_ID_VEBUS = 239 # change this if needed. 239=venusos on raspberry

# Beispielregisteradressen (diese sollten gemäß der Dokumentation angepasst werden)
REGISTER_ADDRESS_ESS_MODE_HUB4 = 2902
REGISTER_ADDRESS_MODE_VEBUS = 33
REGISTER_ADDRESS_AC_POWER_L1_MODE3_VEBUS = 37
REGISTER_ADDRESS_DISABLE_CHARGE_FLAG_VEBUS = 38
REGISTER_ADDRESS_DISABLE_FEEDIN_FLAG_VEBUS = 39
REGISTER_ADDRESS_MAX_DISCHARGE_POWER_HUB4 = 2704
REGISTER_ADDRESS_MAX_FEEDIN_POWER_HUB4 = 2706

# Beispielwerte
ESS_MODE_3 = 3
ENABLE = 1
DISABLE = 0

# Logger-Konfiguration
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def read_register(client, slaveid, register, scale, name=''):
    try:
        result = client.read_holding_registers(register, 1, slave=slaveid)
        decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big)
        if result.isError():
            logger.error(f'Fehler beim Lesen des Registers {name} {register}: {result}')
            return None
        else:
            #value = result.registers[0]
            value = decoder.decode_16bit_int() / scale
            logger.info(f'Aktueller Wert von Register {name} {register}: {value}')
            return value
    except ModbusException as e:
        logger.error(f'Modbus-Fehler beim Lesen des Registers {name} {register}: {e}')
        return None

def set_register(client, slaveid, register, scale, value, name=''):
    try:
        result = client.write_register(register, int(value * scale), slave=slaveid)
        if result.isError():
            logger.error(f'Fehler beim Setzen des Registers {name} {register}: {result}')
        else:
            logger.info(f'Register {name} {register} erfolgreich auf {value} gesetzt')
    except ModbusException as e:
        logger.error(f'Modbus-Fehler beim Setzen des Registers {name} {register}: {e}')

def read_all_registers(client):
    read_register(client, UNIT_ID_HUB4, REGISTER_ADDRESS_ESS_MODE_HUB4, 1, "ESS MODE")
    read_register(client, UNIT_ID_HUB4, REGISTER_ADDRESS_MAX_DISCHARGE_POWER_HUB4, 0.1, "MAX DISCHARGE POWER")
    read_register(client, UNIT_ID_HUB4, REGISTER_ADDRESS_MAX_FEEDIN_POWER_HUB4, 0.01, "MAX FEEDIN POWER")
    read_register(client, UNIT_ID_VEBUS, REGISTER_ADDRESS_MODE_VEBUS, 1, "SWITCH POSITION") # /Mode 1=Charger Only;2=Inverter Only;3=On;4=Off
    read_register(client, UNIT_ID_VEBUS, REGISTER_ADDRESS_AC_POWER_L1_MODE3_VEBUS, 1, "AC POWER")
    read_register(client, UNIT_ID_VEBUS, REGISTER_ADDRESS_DISABLE_CHARGE_FLAG_VEBUS, 1, "DISABLE CHARGE FLAG")
    read_register(client, UNIT_ID_VEBUS, REGISTER_ADDRESS_DISABLE_FEEDIN_FLAG_VEBUS, 1, "DISABLE FEEDINFLAG")

def main():
    client = ModbusTcpClient(IP_ADDRESS, port=PORT)

    try:
        if client.connect():
            logger.info(f'Verbindung zu {IP_ADDRESS}:{PORT} hergestellt.')
            read_all_registers(client)

            # AC-Leistung in einer Schleife sekündlich setzen
            #while True:
            #    set_register(client, REGISTER_ADDRESS_AC_POWER, AC_POWER)
            #    sleep(1)  # 1 Sekunde warten
            set_register(client, UNIT_ID_VEBUS, REGISTER_ADDRESS_AC_POWER_L1_MODE3_VEBUS, 1, 50, 'AC POWER') # change power value !
            sleep(1)
            read_register(client, UNIT_ID_VEBUS, REGISTER_ADDRESS_AC_POWER_L1_MODE3_VEBUS, 1, "AC POWER")
            logger.info('Waiting 65 seconds to reset register')
            sleep(65)  # 1 Sekunde warten
            read_register(client, UNIT_ID_VEBUS, REGISTER_ADDRESS_AC_POWER_L1_MODE3_VEBUS, 1, "AC POWER")
        else:
            logger.error('Verbindung konnte nicht hergestellt werden.')
    finally:
        client.close()

if __name__ == "__main__":
    main()

