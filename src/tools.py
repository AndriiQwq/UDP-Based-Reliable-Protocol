from colorama import Fore, init
init(autoreset=True)

import socket
import threading
import time

def get_welcome_message():
    """Returns a welcome message for the user."""
    return (
        Fore.GREEN +
        "\n"
        "#######################################################################################################################\n"
        "########################################### Custom Protocol Design Using UDP ##########################################\n"
        "#######################################################################################################################\n"
        f"###############################################{Fore.MAGENTA} Author: Andrii Dokaniev{Fore.GREEN} ###############################################\n"
        "#######################################################################################################################\n"
        "\n"
        + Fore.LIGHTGREEN_EX + "How to start:\n"
        + Fore.LIGHTGREEN_EX + "\t1) Set connection configuration (CSI, CSP, CCP)\n"
        + Fore.LIGHTGREEN_EX + "\t2) Use commands to send messages or files, or change configuration\n"
        + Fore.LIGHTGREEN_EX + "\t3) Close connection (CSI, CSP, CCP)\n"
    )

def get_available_commands():
    """    Returns a list of available commands for the custom protocol."""

    commands_text = '''
    Available commands:
    0) CCR - create socket, bind and receive message | after configure connection (CSI, CSP, CCP)

    1)      help - Show commands
            ipconfig - show ip configuration
            add_cmmds - show additional commands (show_keepalive_activity, show_send_info, show_receive_info, 
                                                show_crc_check_control)

    2)      CSI <new_ip> - Change LOCAL_IP, CRI <new_ip> - Change REMOTE_IP
            CSP <new_port> - Change OUT_PORT, CCP <new_port> - Change IN_PORT

    3)      change_fragment_size <fragment_size> - change fragment size
            change_storage_path <new_path> - change storage path 
            change_error_rate <error_rate> - change error rate
            change_window_size <window_size> - change window size
            change_check_ack_interval <check_ack_interval> - change check ack interval

    4)      send_file - send file to server, if start with reverse_data|<file_name> -> reverse some segment
            send_message - send message to server (stop - stop input massages), 
            if start with reverse_data|<data> -> reverse data

    5)      save_config - save configuration
            load_default_config - load default configuration

    6)      auto_bind - auto bind socket

    7)      close_connection - close the connection
            exit - exit the program
    '''

    return Fore.LIGHTMAGENTA_EX + commands_text

def get_additional_commands():
    return (
        Fore.LIGHTMAGENTA_EX + "show_keepalive_activity - show keepalive activity\n" +
        Fore.LIGHTMAGENTA_EX + "show_send_info - show send info\n" +
        Fore.LIGHTMAGENTA_EX + "show_receive_info - show receive info\n"
    )

def get_ipconfig(config):
    info = (
        Fore.CYAN + "---------------------------------\n" +
        Fore.GREEN + f"LOCAL_IP: {config.LOCAL_IP}\n" +
        Fore.GREEN + f"REMOTE_IP: {config.REMOTE_IP}\n" +
        Fore.GREEN + f"OUT_PORT: {config.OUT_PORT}\n" +
        Fore.GREEN + f"IN_PORT: {config.IN_PORT}\n" +
        Fore.GREEN + f"FRAGMENT_SIZE: {config.FRAGMENT_SIZE}\n" +
        Fore.GREEN + f"error_rate: {config.error_rate}\n" +
        Fore.GREEN + f"window_size: {config.window_size}\n" +
        Fore.GREEN + f"check_ack_interval: {config.check_ack_interval}\n" +
        Fore.GREEN + f"STORAGE_PATH: {config.STORAGE_PATH}\n" +
        Fore.GREEN + f"show_keepalive_activity: {config.show_keepalive_activity_control}\n" +
        Fore.GREEN + f"show_send_info: {config.show_sequence_number_control}\n" +
        Fore.GREEN + f"show_receive_info: {config.show_receive_control}\n" +
        Fore.CYAN + "---------------------------------"
    )
    return info

def create_socket():
    Address_Family_Internet_IPv4 = socket.AF_INET
    User_Datagram_Protocol_socket = socket.SOCK_DGRAM
    client_socket = socket.socket(Address_Family_Internet_IPv4, User_Datagram_Protocol_socket)
    print(Fore.LIGHTBLUE_EX + "Socket created")

    return client_socket

def bind_socket(client_socket, LOCAL_IP, IN_PORT):
    if client_socket is None:
        print(Fore.RED + "Error, don't created socket")
        return
    try:
        client_socket.bind((LOCAL_IP, IN_PORT))
        client_socket_bind = True

        print(Fore.LIGHTBLUE_EX + f"Socket bind complete on {LOCAL_IP}:{IN_PORT}")
    except OSError as e:
        print(Fore.RED + f"Don't bind: {e}")
    except Exception as e:
        print(Fore.RED + f"Don't connect: {e}")

    return client_socket_bind

def receive_message(protocol):
    listener_thread = threading.Thread(target=listen, args=(protocol,))
    listener_thread.daemon = True
    listener_thread.start()
    print(Fore.LIGHTBLUE_EX + "Message receive start")

def listen(protocol):
    while True:
        try:
            protocol.receive_data()
        except Exception as e:
            print(Fore.RED + f"Error to get message: {e}")
            break

def send_message(protocol):  # send protocol
    print(Fore.LIGHTCYAN_EX + "Enter the message to send or stop to stop sanding massage: ")

    while True:
        message = input()
        if message == "stop":
            break
        if message.startswith("reverse_data|"):
            message = message.split("|")[1]
            protocol.data = message

            protocol.wrong_data_next_send()

            protocol.send_message()
            continue
        if message == '':
            print(Fore.RED + "incorrect massage")
            continue
        protocol.data = message
        protocol.send_message()
        time.sleep(0.3)

    return protocol

def send_3_handshake(protocol, connection_status):
    if not connection_status:
        protocol.data = ''
        protocol.flags = 0b00000000
        protocol.send_message()

    return protocol 

def send_4_handshake(protocol):
    close_connection = True
    STATUS = 1
    if close_connection:
        protocol.data = ''
        protocol.flags = 0b10000000
        protocol.send_message()

    return close_connection, STATUS, protocol
