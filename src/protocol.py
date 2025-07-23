import os
import struct
import threading
import time
import random
import math
import crcmod
from colorama import Fore, init
init(autoreset=True)

# 1100 1000
ACK = 0b00001000  # 4
SYN = 0b01000000  # 7
FIN = 0b10000000  # 8

SYN_ACK = 0b01001000

massage_flag = 0b00000001  # 1
file_flag = 0b00000010  # 2
NACK = 0b00000000  # 0

First_Fragment = 0b00010000  # 5
Last_Fragment = 0b00100000  # 6
keep_alive_flag = 0b00000100  # 3

r_SYN = r_SYN_ACK = r_ACK = s_SYN = s_SYN_ACK = s_ACK = False
s_FIN = r_FIN = False

file_transmission = False

first_segment = False
first_segment_time = None

NACK_for_single_incorrect_fragment = False
end_file_transmission = False

count_of_inc_receive_data = 0
min_size_of_fragment = 2500
max_size_of_fragment = 0

class Protocol:
    def __init__(self, seq_num, ack_num, flags, window_size, data, config, client_socket, connection, close_connection, STATUS):
        self.seq_num = int(seq_num)
        self.ack_num = int(ack_num)
        self.flags = int(flags)
        self.window_size = int(window_size)
        self.checksum = 0
        self.data = ''

        self.last_received_time = time.time()

        self.wrong_data = False
        self.sent_packets = {}
        self.received_packets = {}

        self.file_path = None

        self.base = 0  # base for sliding window
        self.ack_received = set()

        self.timeout = 1 + (self.window_size - 1) * 0.2  # timeout for waiting for ACKs

        self.received_seq_numbers = set()

        # added to compatibility with old code
        self.config = config
        self.client_socket = client_socket
        self.connection = connection
        self.close_connection = close_connection
        self.STATUS = STATUS

    def global_var_set_None(self):
        global r_SYN, r_SYN_ACK, r_ACK, s_SYN, s_SYN_ACK, s_ACK, r_FIN, s_FIN
        r_SYN = r_SYN_ACK = r_ACK = s_SYN = s_SYN_ACK = s_ACK = r_FIN = s_FIN = self.close_connection = self.connection = False
        self.STATUS = 0

    def store_sent_packet(self, seq_num, data):
        self.sent_packets[seq_num] = data

    def store_received_packet(self, seq_num, data):
        if seq_num not in self.received_packets:
            self.received_packets[seq_num] = data
            self.received_seq_numbers.add(seq_num)
        else:
            print(Fore.RED + f"Data for seq_num {seq_num} already received.")

    def retrieve_data_for_seq_num(self, seq_num):
        if seq_num in self.sent_packets:
            return self.sent_packets[seq_num]
        else:
            print(Fore.RED + "No data found for seq_num {seq_num}.")
            return None  # no data found

    def create_protocol_header(self):  # HEADER
        header = struct.pack('!IIBHH', self.seq_num, self.ack_num, self.flags, self.window_size, self.checksum)

        return header

    def keep_alive(self):
        probes_sent = 0
        connection_lost = False

        wait_time_offset = random.uniform(0.2, 2.2)
        time.sleep(wait_time_offset)

        while self.connection:
            if not file_transmission:

                if self.config.show_keepalive_activity_control:
                    print(Fore.LIGHTGREEN_EX + "\nSend keepalive probe.")

                self.flags = keep_alive_flag
                self.data = ''

                header = self.create_protocol_header()
                message = header + self.data.encode('utf-8')
                self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))

                time.sleep(self.config.keepalive_interval)

                interval_between_last_received_data = time.time() - self.last_received_time

                if interval_between_last_received_data < self.config.keepalive_interval:
                    if connection_lost:
                        print(Fore.LIGHTGREEN_EX + "Connection restored.")
                        connection_lost = False
                        probes_sent = 0
                    # time.sleep(self.config.keepalive_interval - interval_between_last_received_data)
                    continue
                elif probes_sent < self.config.keepalive_probes:

                    probes_sent += 1
                    continue
                else:
                    if probes_sent >= self.config.keepalive_probes:
                        print(Fore.RED + "Connection lost.")
                        self.connection = False
                        break

    def calculate_checksum(self, data):
        crc16_ccitt = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, xorOut=0x0000)
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, (bytes, bytearray)):
            raise TypeError(Fore.RED + "Data must be a string, bytes, or bytearray")
        crc = crc16_ccitt(data)
        return crc

    def verify_checksum(self, data):
        check_crc = self.calculate_checksum(data)
        return check_crc == self.checksum

    #############################
    # to 3,4 handshake function #
    #############################
    def send_SYN(self):
        global s_SYN
        self.flags = SYN

        self.seq_num = random.randint(0, 2 ** 16 - 1)
        self.ack_num = 0

        # create header and pack message
        header = self.create_protocol_header()
        message = header
        # send message

        print(Fore.BLUE + "1send SYN")
        s_SYN = True
        self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))

    def send_ACK_handshake(self):
        global s_ACK

        self.flags = ACK

        temp_seq = self.seq_num
        self.seq_num = self.ack_num
        self.ack_num = temp_seq + 1

        # send message
        if self.close_connection:
            print(Fore.LIGHTYELLOW_EX + "send_fragment->4send ACK\n")
        else:
            print(Fore.BLUE + "3send ACK\n")
            """ked maju odlisnu velkost fragmentov, tak tuto cast nepotrebujeme"""
            """self.data = str(FRAGMENT_SIZE) """

        # create header and pack message
        header = self.create_protocol_header()
        message = header + self.data.encode('utf-8')

        s_ACK = True
        self.connection = True

        self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))

    def send_SYN_ACK(self):
        global s_SYN_ACK

        self.ack_num = self.seq_num + 1
        self.seq_num = random.randint(0, 2 ** 16 - 1)

        self.flags = SYN_ACK
        header = self.create_protocol_header()
        message = header + self.data.encode('utf-8')
        # send message

        print(Fore.BLUE + "2send SYN-ACK")
        s_SYN_ACK = True
        self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))

    def send_FIN(self):
        global s_FIN

        self.flags = FIN
        header = self.create_protocol_header()
        message = header + self.data.encode('utf-8')
        s_FIN = True
        self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))

    def send_NACK(self, missing_seq_num):
        self.flags = NACK
        self.ack_num = missing_seq_num
        self.seq_num += 1
        self.data = ''

        header = self.create_protocol_header()
        message = header + self.data.encode('utf-8')
        self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))

    def send_ACK(self, temp_ack_num, temp_seq_num):
        temp_ack = temp_ack_num
        self.ack_num = temp_seq_num
        self.seq_num = temp_ack + 1
        self.flags = ACK
        self.data = ''

        header = self.create_protocol_header()
        message = header + self.data.encode('utf-8')
        self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))

    def send_message(self):
        global file_transmission

        self.last_received_time = time.time()

        ###############
        # 3 handshake #
        ###############
        if not self.connection:
            if not s_SYN and not r_SYN:
                self.send_SYN()
                print(Fore.LIGHTYELLOW_EX + "send_fragment->1send SYN\n")
                return
            elif (self.flags & SYN) and (self.flags & ACK) and not r_SYN_ACK:
                self.send_SYN_ACK()
                print(Fore.LIGHTYELLOW_EX + "send_fragment->2send SYN-ACK\n")
                return
            elif s_SYN and r_SYN_ACK and not s_ACK:  # we didn't send ||| step SYN
                self.send_ACK_handshake()
                print(Fore.LIGHTYELLOW_EX + "send_fragment->3send ACK\n")

                self.keep_alive_thread = threading.Thread(target=self.keep_alive)
                self.keep_alive_thread.daemon = True
                self.keep_alive_thread.start()
            return

        ###############
        # 4 handshake #
        ###############
        elif self.close_connection:
            if r_FIN and self.STATUS == 2:
                print(Fore.YELLOW + "send_fragment->2send ACK\n")
                self.flags = ACK

                temp_ack = self.ack_num
                self.ack_num = self.seq_num + 1
                self.seq_num = temp_ack

                header = self.create_protocol_header()
                message = header + self.data.encode('utf-8')
                self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))

                print(Fore.YELLOW + "send_fragment->3send FIN\n")
                self.send_FIN()
                return
            elif s_FIN and self.STATUS == 1:
                print(Fore.YELLOW + "send_fragment->4send ACK\n")
                self.send_ACK_handshake()

                self.connection = False
                self.close_connection = False
                self.global_var_set_None()
                return
            else:
                # reverse seq_num and ack_num ??
                temp_seq = self.seq_num
                self.seq_num = self.ack_num
                self.ack_num = temp_seq

                print(Fore.LIGHTYELLOW_EX + "send_fragment->1send FIN\n")
                self.send_FIN()
                return

        else:  # connection == True, send data

            if file_transmission:

                seq_num = self.seq_num  # seq_num not depend on fill
                self.base = seq_num

                count_of_fragments = math.ceil(os.path.getsize(self.file_path) / self.config.FRAGMENT_SIZE)  # to get round up

                if self.wrong_data:
                    num_wrong_fragments = max(1, int(count_of_fragments * self.config.error_rate))

                    population_size = int(count_of_fragments)
                    sample_size = min(num_wrong_fragments, population_size)

                    wrong_indices = random.sample(
                        range(seq_num, seq_num + population_size),
                        sample_size
                    )
                else:
                    wrong_indices = []

                try:
                    fragment_count = 0
                    last_fragment_size = 0
                    file_name_size = len(os.path.basename(self.file_path))

                    file_name = os.path.basename(self.file_path)
                    self.store_sent_packet(seq_num, file_name.encode('utf-8'))

                    """~~~send_first_fragment~~~"""
                    """~~~first_fragment_is_file_name~~~"""
                    self.flags = file_flag
                    self.flags |= First_Fragment
                    data = self.sent_packets[seq_num]
                    self.checksum = self.calculate_checksum(data)

                    if self.config.show_sequence_number_control:
                        print(Fore.GREEN + f"\nSend  seq. num. {self.seq_num}")

                    if isinstance(data, str):
                        data = data.encode('utf-8')
                    header = self.create_protocol_header()
                    message = header + data
                    self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))

                    seq_num += 1  # update seq_num for next fragment
                    self.seq_num += 1
                    time.sleep(0.1)
                    self.flags = file_flag
                    with open(self.file_path, 'rb') as f:
                        while True:
                            file_seg = f.read(self.config.FRAGMENT_SIZE)
                            if not file_seg:
                                break

                            self.store_sent_packet(seq_num, file_seg)  # to control

                            """"tracing information"""
                            fragment_count += 1
                            last_fragment_size = len(file_seg)

                            flags = file_flag
                            checksum = self.calculate_checksum(file_seg)

                            """Checking if it is the last fragment"""
                            if not f.read(1):
                                flags |= Last_Fragment
                            else:
                                f.seek(-1, 1)

                            if self.wrong_data:
                                if seq_num in wrong_indices:
                                    if self.config.show_crc_check_control:
                                        print(
                                            Fore.YELLOW + f"\nData is encoded wrong in fragment {seq_num}, seq num {self.seq_num}.")
                                    file_seg = self.create_wrong_fragment(file_seg)

                            if self.config.show_sequence_number_control:
                                print(Fore.GREEN + f"\nSend  seq. num. {self.seq_num}")

                            """" in future add timeout for waiting ACK and resend!!!"""
                            while True:
                                if seq_num < self.base + self.window_size:  # next segment is in window
                                    self.send_file_fragment(file_seg, seq_num, checksum, flags)
                                    break
                                else:
                                    if not self.wait_for_acks():
                                        print("Timeout expired. Resending fragments.")
                                        self.check_timeouts()

                            seq_num += 1  # seq_num for next fragment

                    """"Check if all fragments are received correctly"""
                    while self.base != seq_num:

                        if not self.wait_for_acks():
                            print("Timeout expired. Resending fragments.")
                            self.check_timeouts()

                    """"Send manage fragment, for end of message/file transmission"""
                    self.flags = 0b11111111
                    self.data = ''
                    self.checksum = 0
                    self.seq_num = 0
                    self.ack_num = 0

                    header = self.create_protocol_header()
                    self.client_socket.sendto(header, (self.config.REMOTE_IP, self.config.OUT_PORT))

                    """Information about file after transmission"""
                    print(Fore.GREEN + f"\nTotal fragments: {fragment_count} in file.")
                    print(Fore.GREEN + f"\n{fragment_count - 1} fragments with size {self.config.FRAGMENT_SIZE} bytes.")

                    if last_fragment_size < self.config.FRAGMENT_SIZE:
                        print(Fore.GREEN + f"Last fragment in file, size: {last_fragment_size} bytes")
                    else:
                        print(Fore.GREEN + f"All fragment in file is the same size: {self.config.FRAGMENT_SIZE} bytes")

                    print(Fore.GREEN + f"First fragment is file name, size {len(file_name)} bytes.")
                    print(Fore.GREEN + f"Total file size: {os.path.getsize(self.file_path)} bytes")

                    print(Fore.LIGHTRED_EX + f"Count of wrong fragments: {len(wrong_indices)}")
                    print(Fore.LIGHTGREEN_EX + f"Biggest  fragment size: {self.config.FRAGMENT_SIZE} bytes")

                    if last_fragment_size < file_name_size:
                        print(Fore.LIGHTGREEN_EX + f"Smallest fragment size: {last_fragment_size} bytes")
                    else:  # Not manage fragment with size 0
                        print(Fore.LIGHTGREEN_EX + f"Smallest fragment size: {file_name_size} bytes")

                except Exception as e:
                    print(Fore.RED + f"Error: {e}")
                    return

                """Reset flags"""
                self.flags = 0
                if self.wrong_data:
                    self.wrong_data = False

                print(Fore.LIGHTGREEN_EX + "All fragments received.")
                self.seq_num = random.randint(0, 2 ** 16 - 1)
                self.ack_num = 0
                file_transmission = False
                return

            """Send message"""
            if len(self.data) > self.config.FRAGMENT_SIZE:
                fragments = [self.data[i:i + self.config.FRAGMENT_SIZE] for i in range(0, len(self.data), self.config.FRAGMENT_SIZE)]

                print(Fore.YELLOW + f"Text size: {len(self.data)} bytes")
                print(Fore.YELLOW + f"Count of fragments: {len(fragments)}")
                print(Fore.YELLOW + f"Fragment size: {self.config.FRAGMENT_SIZE} bytes")
                if len(fragments[-1]) < self.config.FRAGMENT_SIZE:
                    print(Fore.YELLOW + f"Last fragment size: {len(fragments[-1])} bytes")
                    print(Fore.YELLOW + f"Last fragment is smallest fragment, teda: {len(fragments[-1])} bytes")
                    print(Fore.YELLOW + f"Biggest fragment size: {self.config.FRAGMENT_SIZE} bytes") # najvetši fragment
                else:
                    print(Fore.YELLOW + f"All fragments are the same, that is, we do not have the smallest and the largest fragment, fragments have size: {self.config.FRAGMENT_SIZE} bytes")
                    print(Fore.YELLOW + f"The smallest fragment has the size as the largest")

                wrong_indices = []
                if self.wrong_data:
                    num_wrong_fragments = max(1, int(len(fragments) * self.config.error_rate))
                    population_size = max(1, len(fragments) - 1)
                    sample_size = min(num_wrong_fragments, population_size)
                    if sample_size > 0:
                        if len(fragments) <= 1:
                            sample_size = 1
                        if len(fragments) > 2 or len(fragments) == 1:
                            wrong_indices = random.sample(range(1, population_size), sample_size)
                        else:
                            wrong_indices = []

                print(Fore.LIGHTRED_EX + f"Count of wrong fragments: {len(wrong_indices)}")

                seq_num = self.seq_num  # seq_num not depend on fill
                self.base = seq_num

                for i, fragment in enumerate(fragments):
                    self.store_sent_packet(seq_num, fragment)

                    self.flags = massage_flag  # set the massage_flag bit

                    if i == len(fragments) - 1:
                        self.flags |= Last_Fragment

                    self.checksum = self.calculate_checksum(fragment)

                    if self.wrong_data:
                        if i in wrong_indices:
                            if self.config.show_crc_check_control:
                                print(Fore.YELLOW + f"\nData is encoded wrong in fragment {i}, seq num {self.seq_num}.")
                            fragment = self.create_wrong_fragment(fragment)

                    if self.config.show_sequence_number_control:
                        print(Fore.GREEN + f"\nSend  seq. num. {self.seq_num}")

                    # self.send_fragment(fragment, self.flags)

                    """" in future add timeout for waiting ACK and resend!!!"""
                    while True:
                        if seq_num < self.base + self.window_size:  # next segment is in window
                            self.send_fragment(fragment, self.flags)
                            break
                        else:
                            if not self.wait_for_acks():
                                print("Timeout expired. Resending fragments.")
                                self.check_timeouts()

                    seq_num += 1

                """"Check if all fragments are received correctly"""
                while self.base != seq_num:
                    if not self.wait_for_acks():
                        print("Timeout expired. Resending fragments.")
                        self.check_timeouts()

                """"Send manage fragment, for end of message/file transmission"""
                self.flags = 0b11111111
                self.data = ''
                self.checksum = 0
                self.seq_num = 0
                self.ack_num = 0

                header = self.create_protocol_header()
                self.client_socket.sendto(header, (self.config.REMOTE_IP, self.config.OUT_PORT))

                """Reset flags"""
                self.flags = 0
                if self.wrong_data:
                    self.wrong_data = False

                print(Fore.LIGHTGREEN_EX + "All fragments received.")
                self.seq_num = random.randint(0, 2 ** 16 - 1)
                self.ack_num = 0
            else:
                """Single fragment send"""
                self.checksum = self.calculate_checksum(self.data)
                self.store_sent_packet(self.seq_num, self.data)

                if self.wrong_data:
                    if self.config.show_crc_check_control:
                        print(Fore.LIGHTRED_EX + "Data is encoded wrong")
                    self.data = self.create_wrong_fragment(self.data)
                    print(Fore.LIGHTGREEN_EX + "Send 1 wrong fragment")
                    self.wrong_data = False
                else:
                    print(Fore.LIGHTGREEN_EX + "Data is encoded correctly, no wrong fragment.")

                print(Fore.LIGHTGREEN_EX + f"Text size: {len(self.data)} bytes")
                print(Fore.LIGHTGREEN_EX + "Count of fragments: 1")
                print(Fore.LIGHTGREEN_EX + f"Fragment size: {len(self.data)} bytes")
                print(Fore.LIGHTGREEN_EX + f"We sent 1 fragment, not the biggest nor the smallest, so the size is: {len(self.data)} bytes")

                #print(Fore.LIGHTGREEN_EX + f"Najmensij fragment size: {len(self.data)} bytes")

                print(Fore.LIGHTGREEN_EX + f"Send single syn. fragment {self.seq_num}")
                self.send_fragment(self.data, massage_flag | First_Fragment | Last_Fragment)

    def wait_for_acks(self):
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if all(seq in self.ack_received for seq in range(self.base, self.seq_num)):
                return True
            time.sleep(self.config.check_ack_interval)
        return False

    def check_timeouts(self):
        for seq_num in range(self.base, self.seq_num):
            if seq_num not in self.ack_received:
                data = self.retrieve_data_for_seq_num(seq_num)
                if data is not None:
                    self.checksum = self.calculate_checksum(data)
                    self.seq_num = seq_num
                    self.send_fragment(data, self.flags)

    def send_file_fragment(self, fragment, seq_num, checksum, flags):
        if isinstance(fragment, str):
            fragment = fragment.encode('utf-8')
        header = struct.pack('!IIBHH', seq_num, 0, flags, self.window_size, checksum)
        message = header + fragment
        self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))
        self.seq_num += 1

    def send_fragment(self, fragment, flags):
        if fragment is None:
            print(Fore.RED + "Error: fragment is None.")
            return

        self.flags = flags
        if isinstance(fragment, str):
            fragment = fragment.encode('utf-8')
        header = self.create_protocol_header()
        message = header + fragment
        self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))
        self.seq_num += 1

    def create_wrong_fragment(self, fragment):

        if len(fragment) == 1:  # revers don't work
            fragment = bytearray(fragment.encode('utf-8'))
            fragment[0] = (fragment[0] + 1) % 256
            return bytes(fragment)

        if isinstance(fragment, str):
            fragment = ''.join(reversed(fragment))
        elif isinstance(fragment, (bytes, bytearray)):
            fragment = type(fragment)(reversed(fragment))
        else:
            raise TypeError(Fore.RED + "Data must be a string, bytes, or bytearray")
        return fragment


    def receive_data(self):
        global r_SYN, r_SYN_ACK, r_ACK, r_FIN, file_transmission, \
            last_received_time, end_file_transmission, count_of_inc_receive_data, min_size_of_fragment, max_size_of_fragment

        self.last_received_time = time.time()

        data, addr = self.client_socket.recvfrom(1472)

        header = data[:13]
        temp_seq_num, temp_ack_num, temp_flags, temp_window_size, temp_checksum = struct.unpack('!IIBHH', header)

        if temp_flags == keep_alive_flag:
            if self.config.show_keepalive_activity_control:
                print(Fore.LIGHTYELLOW_EX + "Keepalive probe received.")
            return

        if temp_flags == 0b11111111:
            end_file_transmission = True
            return

        # 3 handshake
        if not self.connection:
            self.seq_num, self.ack_num, self.flags, self.window_size, self.checksum = struct.unpack('!IIBHH', header)

            if (self.flags & SYN) and (self.flags & ACK):  # self.flags == SYN + ACK
                print(Fore.BLUE + "2receive SYN-ACK")
                r_SYN_ACK = True

                self.send_message()
                return

            elif self.flags == SYN:  # pre send SYN-ACK
                print(Fore.BLUE + "1receive SYN")
                self.flags = SYN | ACK
                r_SYN = True
                self.send_message()  # send SYN_ACK wait to receive ACK

                while True:
                    try:
                        data, addr = self.client_socket.recvfrom(1472)
                    except Exception as e:
                        print(f"Error receiving data: {e}")
                    header = data[:13]
                    self.seq_num, self.ack_num, self.flags, self.window_size, self.checksum = struct.unpack('!IIBHH',
                                                                                                            header)

                    if self.flags == ACK:
                        print(Fore.BLUE + "3receive ACK")
                        # FRAGMENT_SIZE = int((data[13:]).decode('utf-8'))
                        r_ACK = True
                        self.connection = True
                        # Start keep alive thread
                        self.keep_alive_thread = threading.Thread(target=self.keep_alive)
                        self.keep_alive_thread.daemon = True
                        self.keep_alive_thread.start()

                        return
        else:
            # receive 4 handshake
            if temp_flags == 0b10000000 and self.STATUS == 0:
                print(Fore.LIGHTYELLOW_EX + "1Receive FIN")
                self.STATUS = 2
                r_FIN = True
                self.close_connection = True

                self.seq_num = temp_seq_num
                self.ack_num = temp_ack_num

                self.send_message()
                return
            elif temp_flags == 0b00001000 and self.STATUS == 1 and s_FIN:
                print(Fore.LIGHTYELLOW_EX + "2Receive Ack")
                return
            elif temp_flags == 0b10000000 and self.STATUS == 1 and s_FIN:
                print(Fore.LIGHTYELLOW_EX + "3Receive FIN")
                self.seq_num = temp_seq_num
                self.ack_num = temp_ack_num

                self.send_ACK_handshake()

                self.connection = False
                self.close_connection = False
                self.global_var_set_None()
                return
            elif temp_flags == 0b00001000 and self.STATUS == 2:
                print(Fore.LIGHTYELLOW_EX + "4Receive Ack")
                self.connection = False
                self.close_connection = False
                self.global_var_set_None()
                print(Fore.RED + "Connection closed")
                return
            # end 4 handshake

            if temp_flags == NACK:  # receive NACK
                # if show_receive_control:
                if self.config.show_receive_control:
                    print(Fore.LIGHTRED_EX + f"Receive NACK, num {temp_ack_num}\n")

                missing_seq_num = temp_ack_num

                # add logic to send missing data again
                # print(self.sent_packets)
                # for i in self.sent_packets:
                #     print(f"have seq num: {i}")

                if missing_seq_num in self.sent_packets:
                    # self.seq_num = missing_seq_num
                    # self.ack_num = temp_seq_num
                    self.data = self.retrieve_data_for_seq_num(missing_seq_num)

                    if self.config.show_crc_check_control:
                        if file_transmission:
                            print(Fore.LIGHTRED_EX + f"Missing data for seq num {missing_seq_num}\n")
                        else:
                            print(Fore.LIGHTRED_EX + f"Missing data for seq num {missing_seq_num}: {self.data}")

                        print(Fore.LIGHTGREEN_EX + f"Resending missing data for seq num {missing_seq_num}.")

                    if not file_transmission:
                        self.flags = massage_flag
                    else:
                        self.flags = file_flag

                    header = struct.pack('!IIBHH', missing_seq_num, self.ack_num, self.flags, self.window_size,
                                         self.calculate_checksum(self.data))

                    message = header + (self.data if isinstance(self.data, bytes) else self.data.encode('utf-8'))

                    self.client_socket.sendto(message, (self.config.REMOTE_IP, self.config.OUT_PORT))

                    return
                return

            if temp_flags == ACK:  # receive ACK 1/11/2024 | del sent segment form list
                # pick up fragment from sent packets
                if temp_ack_num in self.sent_packets:
                    del self.sent_packets[temp_ack_num]
                    self.ack_received.add(temp_ack_num)

                while self.base in self.ack_received:
                    self.base += 1

                if self.config.show_receive_control:
                    print(Fore.LIGHTYELLOW_EX
                          + f"\nWe receive ACK {temp_ack_num}, count of segments in process {len(self.sent_packets)}")

                # temp_ack = self.ack_num swap seq_num and ack_num
                return

            else:  # receive message/file
                global first_segment, first_segment_time, NACK_for_single_incorrect_fragment

                if not first_segment:
                    first_segment_time = time.time()
                    first_segment = True

                if temp_flags & file_flag:  # receive file
                    file_transmission = True

                message_data = data[13:]

                self.checksum = temp_checksum
                check_crc = self.verify_checksum(data[13:])

                if self.config.show_sequence_number_control:
                    print(Fore.LIGHTGREEN_EX + f"Received fragment with seq. num. {temp_seq_num}.")

                if min_size_of_fragment < len(message_data) < max_size_of_fragment:
                    min_size_of_fragment = len(message_data)
                if len(message_data) > max_size_of_fragment:
                    max_size_of_fragment = len(message_data)

                """Processing data and responding ACK or NACK"""
                if check_crc:
                    if self.config.show_crc_check_control:
                        print(Fore.GREEN + "Data is correct, checksum is correct.")

                    """Receive single fragment"""
                    if temp_flags & massage_flag and temp_flags & First_Fragment and temp_flags & Last_Fragment or \
                            NACK_for_single_incorrect_fragment:
                        print(Fore.MAGENTA + f"Received {len(message_data)} bytes.")
                        print(Fore.MAGENTA + f"Received message: {message_data.decode('utf-8')}")
                        print(Fore.MAGENTA + f"Count of incorrect received fragment: {count_of_inc_receive_data}")
                        count_of_inc_receive_data = 0
                        self.send_ACK(temp_ack_num, temp_seq_num)

                        self.received_packets.clear()
                        self.received_seq_numbers.clear()
                        self.ack_received.clear()
                        NACK_for_single_incorrect_fragment = False

                        first_segment = False
                        return

                    """Receive basic fragment"""
                    if temp_flags & massage_flag or temp_flags & file_flag:
                        """Check if First_Fragment of file is received"""
                        if temp_flags & file_flag and temp_flags & First_Fragment:
                            self.ack_received.clear()
                            self.sent_packets.clear()
                            self.received_seq_numbers.clear()

                            file_name = message_data.decode('utf-8', errors='ignore')
                            self.file_path = os.path.join(self.config.STORAGE_PATH, file_name)

                            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                            try:
                                print(Fore.LIGHTGREEN_EX + f"Received file name: {message_data.decode('utf-8')}")
                            except UnicodeDecodeError:
                                print(Fore.LIGHTRED_EX + "Error decoding file name.")

                                print("file_name")
                                print(file_name)
                            if os.path.exists(self.file_path):
                                print(Fore.LIGHTRED_EX + "File already exists. It will be overwritten.")
                                with open(self.file_path, 'wb') as f:
                                    f.write(b'')
                            self.store_received_packet(temp_seq_num, message_data)
                            self.send_ACK(temp_ack_num, temp_seq_num)
                            return

                        """Check if Last_Fragment bit is set and type of message"""
                        """Receive all fragments?"""
                        if temp_flags & Last_Fragment:
                            self.send_ACK(temp_ack_num, temp_seq_num)
                            self.store_received_packet(temp_seq_num, message_data)
                            print(Fore.LIGHTGREEN_EX + f"Received last fragment {temp_seq_num}.")

                            threading.Thread(target=self.check_end_of_transmission, args=(first_segment_time,)).start()
                        else:
                            """Receive fragment"""
                            self.store_received_packet(temp_seq_num, message_data)
                            self.send_ACK(temp_ack_num, temp_seq_num)

                            if file_transmission:
                                if len(self.received_packets) >= 5 * self.window_size:
                                    self.save_part_of_file()
                                    self.clear_used_fragments()
                            return
                        return
                    return
                else:
                    """Incorrect data"""
                    if not check_crc:
                        if self.config.show_crc_check_control:
                            print(Fore.RED + f"Incorrect data received from sequence number {temp_seq_num}. Send NACK.")
                        expected_seq_num = temp_seq_num

                        if temp_flags & massage_flag and temp_flags & First_Fragment and temp_flags & Last_Fragment:
                            NACK_for_single_incorrect_fragment = True

                        count_of_inc_receive_data += 1

                        """Data is not correct, send NACK"""
                        self.send_NACK(expected_seq_num)
                        return

    def check_end_of_transmission(self, first_segment_time):
        global first_segment, end_file_transmission, file_transmission, count_of_inc_receive_data, min_size_of_fragment, max_size_of_fragment

        min_seq_num = min(self.received_packets.keys())
        max_seq_num = max(self.received_packets.keys())

        check_end_of_transmission = False
        while not check_end_of_transmission:
            if end_file_transmission:
                last_segment_time = time.time()

                print(Fore.LIGHTCYAN_EX + f"Received min fragment size: {min_size_of_fragment} bytes.")
                print(Fore.LIGHTCYAN_EX + f"Received max fragment size: {max_size_of_fragment} bytes.")
                min_size_of_fragment = 2500
                max_size_of_fragment = 0
                """End of file transmission"""
                if file_transmission:
                    print(
                        Fore.LIGHTCYAN_EX +
                        f"Transition time: {last_segment_time - first_segment_time}s.")

                    print(Fore.MAGENTA + f"Count of incorrect received fragment: {count_of_inc_receive_data}")
                    count_of_inc_receive_data = 0

                    self.save_file()
                else:
                    """End of message transmission"""
                    print(Fore.MAGENTA + "All fragments received, message:")
                    for i in range(min_seq_num, max_seq_num + 1):
                        print(f"{self.received_packets[i].decode('utf-8')}", end='')

                    print(
                        Fore.LIGHTGREEN_EX + f"\nReceived {len(self.received_packets)} fragments.")
                    print(
                        Fore.LIGHTGREEN_EX +
                        f"Transition time: {last_segment_time - first_segment_time}s.")

                    print(Fore.LIGHTGREEN_EX + f"Count of incorrect received fragment: {count_of_inc_receive_data}")
                    count_of_inc_receive_data = 0

                first_segment = False
                self.seq_num = random.randint(0, 2 ** 16 - 1)
                self.ack_num = 0
                self.received_packets.clear()
                self.received_seq_numbers.clear()
                self.ack_received.clear()
                end_file_transmission = False
                check_end_of_transmission = True

                if len(self.received_packets) != 0:
                    print(Fore.YELLOW + f"Received {len(self.received_packets)} "
                                        f"fragments. Not all fragments received.")

                if file_transmission:
                    print(Fore.LIGHTMAGENTA_EX + "End file transmission")
                    file_transmission = False
                else:
                    print(Fore.LIGHTMAGENTA_EX + "End message transmission")
            else:
                time.sleep(0.5)


    def save_part_of_file(self):
        os.makedirs('files', exist_ok=True)

        with open(self.file_path, 'ab') as f:
            sorted_keys = sorted(self.received_packets.keys())
            first_seq_num = min(sorted_keys)
            half_index = len(sorted_keys) // 4
            for seq_num in sorted_keys[:half_index]:
                if seq_num == first_seq_num:  # Skip the first fragment (file name)
                    continue
                f.write(self.received_packets[seq_num])

    def clear_used_fragments(self):
        sorted_keys = sorted(self.received_packets.keys())
        first_seq_num = min(sorted_keys)
        half_index = len(sorted_keys) // 4
        for seq_num in sorted_keys[:half_index]:
            if seq_num == first_seq_num:  # Skip the first fragment (file name)
                continue
            del self.received_packets[seq_num]

    def save_file(self):
        global file_transmission
        try:
            self.received_packets = dict(sorted(self.received_packets.items()))
            first_seq_num = min(self.received_packets.keys())
            file_name = self.received_packets[first_seq_num].decode('utf-8')
            file_path = os.path.join(self.config.STORAGE_PATH, file_name)

            print(Fore.LIGHTCYAN_EX + f"File name: {file_name}")
            print(Fore.LIGHTCYAN_EX + f"File path: {file_path}")

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            os.makedirs(self.config.STORAGE_PATH, exist_ok=True)

            total_size = 0
            fragment_size = 0
            last_fragment_size = 0
            with open(file_path, 'ab') as f:
                for seq_num in sorted(self.received_packets.keys()):
                    if seq_num != first_seq_num:
                        fragment = self.received_packets[seq_num]
                        f.write(fragment)
                        total_size += len(fragment)
                        fragment_size = len(fragment)
                        last_fragment_size = len(fragment)

            print(Fore.LIGHTCYAN_EX + f"File saved to: {os.path.abspath(file_path)}")

            total_size = os.path.getsize(file_path)
            print(Fore.LIGHTCYAN_EX + f"Total file size: {total_size} bytes")
            print(
                Fore.LIGHTCYAN_EX + f"Total fragments received: {len(self.received_seq_numbers)} (including file name)")
            print(Fore.LIGHTCYAN_EX + f"Last fragment size: {last_fragment_size} bytes")
            print(Fore.LIGHTCYAN_EX + f"First fragment is file name, size {len(file_name)} bytes.")
            print(Fore.LIGHTCYAN_EX + f"{len(self.received_seq_numbers) - 2} fragments with size "
                                      f"{fragment_size} bytes.")
            self.received_packets.clear()
            file_transmission = False

        except Exception as e:
            print(Fore.RED + f"Error saving file: {str(e)}")

    def wrong_data_next_send(self):
        self.wrong_data = True

    def send_file(self, file_path):
        global file_transmission

        self.seq_num = random.randint(0, 2 ** 16 - 1)
        self.ack_num = 0
        self.base = self.seq_num
        self.ack_received.clear()
        self.sent_packets.clear()
        self.received_seq_numbers.clear()

        file_transmission = True

        self.file_path = file_path
        self.send_message()

        time.sleep(0.8)

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        num_fragments = (file_size + self.config.FRAGMENT_SIZE - 1) // self.config.FRAGMENT_SIZE

        print(Fore.CYAN + f"Sending file: {file_name}")
        print(Fore.YELLOW + f"File size: {file_size} bytes")
        print(Fore.YELLOW + f"Number of fragments: {num_fragments + 1}")
        print(Fore.YELLOW + f"Fragment size: {self.config.FRAGMENT_SIZE} bytes")

        if len(self.sent_packets) == 0:
            print(Fore.LIGHTGREEN_EX + "File transfer complete.")

            file_transmission = False