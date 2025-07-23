from colorama import Fore, init
init(autoreset=True)
import time
import os

from tools import get_available_commands, get_ipconfig, get_additional_commands, \
    create_socket, bind_socket, receive_message, send_3_handshake, \
    send_message, send_4_handshake

def commands_to_execute(command, config, protocol, client_socket, client_socket_bind, connection, close_connection, STATUS):
    """Executes the command based on user input."""
    if command == "exit":
        print(Fore.YELLOW + "Exiting program...")

    elif command.startswith("CSI "):
        new_ip = command.split(" ")[1]
        config.LOCAL_IP = new_ip
        print(Fore.BLUE + f"LOCAL_IP changed to {config.LOCAL_IP}")

    elif command.startswith("CSP "):
        new_port = int(command.split(" ")[1])
        config.OUT_PORT = new_port
        print(Fore.BLUE + f"OUT_PORT changed to {config.OUT_PORT}")

    elif command.startswith("CCP "):
        new_port = int(command.split(" ")[1])
        config.IN_PORT = new_port
        print(Fore.BLUE + f"IN_PORT changed to {config.IN_PORT}")

    elif command.startswith("CRI "):
        new_ip = command.split(" ")[1]
        config.REMOTE_IP = new_ip
        print(Fore.BLUE + f"REMOTE_IP changed to {config.REMOTE_IP}")

    elif command == "ipconfig":
        print(get_ipconfig(config))

    elif command == "help":
        print(get_available_commands())

    elif command == "add_cmmds":
        print(get_additional_commands())

    elif command == "show_keepalive_activity":
        config.show_keepalive_activity_control = not config.show_keepalive_activity_control
        if config.show_keepalive_activity_control:
            print(Fore.BLUE + "Keepalive activity is shown.")
        else:
            print(Fore.BLUE + "Keepalive activity is not shown.")

    elif command == "show_send_info":
        config.show_sequence_number_control = not config.show_sequence_number_control
        if config.show_sequence_number_control:
            print(Fore.BLUE + "Sequence number is shown.")
        else:
            print(Fore.BLUE + "Sequence number is not shown.")

    elif command == "show_receive_info":
        config.show_receive_control = not config.show_receive_control
        if config.show_receive_control:
            print(Fore.BLUE + "Acknowledgment is shown.")
        else:
            print(Fore.BLUE + "Acknowledgment is not shown.")

    elif command == "change_error_rate":
        config.error_rate = float(input(Fore.YELLOW + "Enter new error rate: "))

        if config.error_rate < 0 or config.error_rate > 1:
            print(Fore.RED + "Error rate must be between 0 and 1.")
            return STATUS, close_connection, client_socket_bind, connection, protocol, client_socket

        print(Fore.BLUE + f"Error rate changed to {config.error_rate}")

    elif command.startswith("change_fragment_size "):
        new_size = int(command.split(" ")[1])
        if new_size < 0:
            print(Fore.RED + "Error, fragment size must be greater than 0")
            return STATUS, close_connection, client_socket_bind, connection, protocol, client_socket
        elif new_size > 1459:
            print(Fore.RED + "Error, fragment size must be less than 1459")
            return STATUS, close_connection, client_socket_bind, connection, protocol, client_socket

        config.FRAGMENT_SIZE = new_size
        print(Fore.BLUE + f"Fragment size changed to {config.FRAGMENT_SIZE}")

    elif command == "send_file":
        file_path = input(Fore.YELLOW + "Enter the path of the file to send: ")

        if file_path.startswith("reverse_data|"):
            file_path = file_path.split("|", 1)[1]
            protocol.wrong_data_next_send()

        if not os.path.isfile(file_path):
            print(Fore.RED + f"Path does not exist.")
            return STATUS, close_connection, client_socket_bind, connection, protocol, client_socket

        if not connection:
            protocol.send_message()

        time.sleep(0.3)
        protocol.send_file(file_path)

    elif command == "send_message":
        if client_socket is None:
            print(Fore.RED + "Error, don't created socket")
        else:
            if client_socket_bind:
                if connection:
                    protocol = send_message(protocol)
                else:
                    protocol = send_3_handshake(protocol, connection_status=connection)

                    time.sleep(0.3)
                    protocol = send_message(protocol)
            else:
                print(Fore.RED + "Error, don't bind socket")

    elif command.startswith("change_storage_path "):
        new_path = command.split(" ")[1]
        config.STORAGE_PATH = new_path
        print(Fore.BLUE + f"Storage path changed to {config.STORAGE_PATH}")

    elif command == "auto_bind":
        config.auto_bind = not config.auto_bind
        if config.auto_bind:
            print(Fore.LIGHTBLUE_EX + "Auto binding socket is on.")
        else:
            print(Fore.LIGHTBLUE_EX + "Auto binding socket is off.")

    elif command.startswith("change_window_size "):
        new_window_size = int(command.split(" ")[1])

        if new_window_size < 1:
            print(Fore.RED + "Window size must be greater than 0.")
            return STATUS, close_connection, client_socket_bind, connection, protocol, client_socket

        config.window_size = new_window_size
        print(Fore.BLUE + f"Window size changed to {config.window_size}")

    elif command.startswith("change_check_ack_interval "):
        new_timeout = float(command.split(" ")[1])

        if new_timeout < 0:
            print(Fore.RED + "Timeout must be greater than 0.")
            return STATUS, close_connection, client_socket_bind, connection, protocol, client_socket

        config.timeout = new_timeout
        print(Fore.BLUE + f"Timeout changed to {config.timeout}")

    elif command == "save_config":
        config.save_config()
        print(Fore.BLUE + "Configuration saved.")

    elif command == "load_default_config":
        config.load_default_config()
        print(Fore.BLUE + "Default configuration loaded.")

    elif command == "show_crc_check_control":
        config.show_crc_check_control = not config.show_crc_check_control
        if config.show_crc_check_control:
            print(Fore.BLUE + "CRC check is shown.")
        else:
            print(Fore.BLUE + "CRC check is not shown.")

    elif command == "close_connection":
        # close_connection = True
        close_connection, STATUS, protocol = send_4_handshake(protocol=protocol)

        time.sleep(0.3)
        print(Fore.RED + "Connection closed")
        connection = False
    
    elif command == "CCR":
        create_socket()
        client_socket_bind = bind_socket(client_socket, config.LOCAL_IP, config.IN_PORT)
        receive_message(protocol=protocol)

    return STATUS, close_connection, client_socket_bind, connection, protocol, client_socket
