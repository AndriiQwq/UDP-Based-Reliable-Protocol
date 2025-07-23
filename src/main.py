import math
import os
import random
import socket
import struct
import threading
import time
from tools import get_available_commands, get_welcome_message, get_ipconfig, \
        create_socket, bind_socket, receive_message
from config_manager import ConfigManager
from protocol import Protocol
from command_executor import commands_to_execute

from colorama import Fore, Style, init
import configparser
from crcmod import crcmod

init(autoreset=True)

def main():
    # print welcome message
    print(get_welcome_message())

    # Get config path
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.ini')
    if not os.path.exists(config_path):
        print(Fore.RED + "Configuration file not found. Please create a config.ini file in the src directory.")
        return

    # Initialize ConfigManager with the config file
    config = ConfigManager(config_file=config_path)
    
    # Print available commands
    print(get_available_commands())

    # Print IP configuration
    print(Fore.CYAN + "\nConnection Configuration:")
    print(get_ipconfig(config))

    # Socket Creation and Binding
    Address_Family_Internet_IPv4 = socket.AF_INET
    User_Datagram_Protocol_socket = socket.SOCK_DGRAM

    client_socket = socket.socket(Address_Family_Internet_IPv4, User_Datagram_Protocol_socket)
    client_socket_bind = False
    connection = False
    close_connection = False
    STATUS = 0  # for PC detection 1 - first, 2 - second

    """######################"""
    """# Main protocol object"""
    """######################"""
    NACK = 0b00000000  # 0
    available_protocol = Protocol(seq_num=random.randint(0, 2 ** 16 - 1), ack_num=0, flags=NACK, window_size=config.window_size,
                                data="", config=config, client_socket=client_socket, connection=connection, close_connection=close_connection, STATUS=STATUS)

    if config.auto_bind:
        print(Fore.LIGHTBLUE_EX + "\n~~~Auto binding socket~~~\n")
        create_socket()
        client_socket_bind = bind_socket(client_socket, config.LOCAL_IP, config.IN_PORT)
        receive_message(protocol=available_protocol)

    while True:
        input_command = input()
        
        result = commands_to_execute(input_command, config, available_protocol, client_socket, client_socket_bind, connection, close_connection, STATUS)
        STATUS, close_connection, client_socket_bind, connection, available_protocol, client_socket = result

        if input_command == "exit":
            exit(0)

if __name__ == "__main__":
    main()
