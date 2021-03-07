import socket
# import sys
import time
# import argparse
# import threading
# import re
import datetime

# TODO: document/explain hardcoded and/or unique non-passed variables.
# TODO: Ensure hardcode values are actually hardcoded. Some values change after specifc events
# TODO: add unit tests.

# BEWARE HERE BE SERPENTS, HEX, BINARY, HARDCODED NONSENSE, AND THE RAMBLINGS OF A MADMAN!


class Command_Constructor:
    class Function_Bytes:
        amend_directive = 'F410'
        get_latest_index = '108C'
        read_command = 'F110'
        read_operation_status = '8110'
        l_door_open = '9D10'
        set_time = '8B10'
        set_door_control_param = '8F10'
        clear_domain = '9310'
        read_domain = '9510'
        tail_plus_permissions = '9B10'
        modify_permissions = '0711'
        delete_an_authority = '0811'
        read_control_time = '9610'
        modificaiton_time = '9710'
        read_latest_record = '8D10'
        remove_record = '8E10'
        ip_search = '0111'
        read_records = 'F810'

    def __init__(self, serial_number, address_byte):
        """Init Command Constructor

        Args:
            serial_number (Str): Controller ID, located on PCB
            address_byte (Str): I don't know it's use yet, but it's here.
        """
        self.function_bytes = self.Function_Bytes()
        self.serial_number = self._to_little_endian(serial_number)
        self.address_byte = self._to_little_endian(address_byte)

    def construct_command(self, **kwargs):
        """ !!@!! WARNING: ORDER OF INPUT VARIABLES IS IMPORTANT TO PROPER COMMAND CREATION !!@!! """
        """Constructs a door controller command

        Returns:
            command (Str): A command ready to be sent to door controller
        """
        print(kwargs)
        if 'password' in kwargs:
            kwargs['password'] = self._password_to_hex(kwargs['password'])
        print(kwargs)

        frame = self.serial_number + ''.join(kwargs.values())
        frame = self._fill_frame(frame)
        checksum = self._checksum(frame)
        return '7E'+frame+checksum+'0D'

    def construct_extended_command(self, **kwargs):
        """ !!@!!WARNING: ORDER OF INPUT VARIABLES IS IMPORTANT TO PROPER COMMAND CREATION !!@!! """
        """kwargs should be input as a=XX b=XX c=XX d=XX
        Depending on command being executed.

        Returns:
            extended_command (Str): A command ready to be sent to door controller
        """

        if 'users' in kwargs:
            kwargs['users'] = list(map(self._construct_userframe, kwargs['users']))

        if 'passwords' in kwargs:
            p_list = list(map(self._password_to_hex, kwargs['passwords']))
            kwargs['passwords'] = ''.join(p_list).ljust(16, 'f') * 4

        return self._construct_extended_command(**kwargs)

    def ymd_to_hex(self, year, month, day):
        """Encodes provided YMD into a 4hex value

        Args:
            year (Int): 'value between 0-199 representing years relative to 2000. Eg. 20 = 2020'
            month (Int): 'value between 1-12 represents months'
            day (Int): 'value between 1-31 represents days in month'

        Returns:
            ymd_hex (Str): '4 hex long encoded YMD'
        """
        b_year = format(year, '07b')  # 0 is padding, 7 is length, b is for byte.
        b_month = format(month, '04b')
        b_day = format(day, '05b')

        return format(int(b_year+b_month+b_day, 2), '04x')  # x is lowercase hex

    def hms_to_hex(self, hour, minute, second):
        """Converts hms as ints to a 4 hex long string

        Args:
            hour (Int): 'value between 0-23'
            minute (Int): 'value between 0-59'
            second (Int): 'value between 0-29 as 2 second interval'

        Returns:
            hms_hex(Str): 'length of 8 character representation of HMS'
        """
        b_hour = format(hour, '05b')
        b_minute = format(minute, '06b')
        b_second = format(second, '05b')

        return format(int(b_hour+b_minute+b_second, 2), '04x')

    def _construct_userframe(self, user_data):
        """Formats and appends the required data for adding users

        Args:
            user_data (List): list containing card, door, start_date, end_date,
            Permission, password

        Returns:
            user_frame (Str): subframe containing user's information
        """
        user_data[5] = self._password_to_hex(user_data[5])
        return f"{''.join(user_data)}000000"

    def _construct_extended_command(self, fill_char='F', frame_length=1040, **kwargs):
        """constructs a 524 hex long dataframe

        Args:
            fill_char (Str, optional): Character frame is padded with. Defaults to 'F'.
            frame_length (Int, optional): Length of the completed subframe. Defaults to 1040.

        Returns:
            frame (Str): A completed frame including checksum & endcap bytes
        """
        # all extended commands seem to use F910
        frame = self.serial_number + 'F910' + ''.join(kwargs.values())
        frame = self._fill_frame(frame, fill_char, frame_length)
        if kwargs['user_list']:
            checksum = self._checksum(kwargs['user_list'][0])  # TODO: double check this gives correct checksum
        else:
            checksum = self._checksum(frame[0:598])
        return f'7E{frame}{checksum}0D'

    def _password_to_hex(self, password):
        """Convert int password to valid hex

        Args:
            password (Int): value between 1000-65534

        Returns:
            password (Str): Hex(Str) with little endianness
        """

        x = format(int(password), '04x')
        return self._to_little_endian(x)

    def _to_little_endian(self, val):
        """Converts Val to little endian

        Args:
            val (Str): A hex(Str) to be converted

        Returns:
            endianed (Str): val with little endianness
        """

        return int(val, 16).to_bytes(
            2, byteorder='little').hex()

    def _card_to_hex(self, card):
        card = card.zfill(8)
        area_id = card[:3]
        card_id = card[3:]

        y = int(area_id).to_bytes(1, byteorder='little').hex()
        x = int(card_id).to_bytes(2, byteorder='little').hex()
        return x+y


    def _fill_frame(self, unf_frame, fill_char='0', frame_length=60):
        """Pads a frame with fill_char to length frame_length

        Args:
            unf_frame (Str): 'frame to pad'
            fill_char (Str): 'character frame is padded with'. Defaults to '0'.
            frame_length (Int): 'total length after padding'. Defaults to 60.

        Returns:
            p_frame (Str): 'a padded frame'
        """
        return unf_frame.ljust(frame_length, fill_char)

    def _checksum(self, frame):
        """Generates a 2 hex long checksum for dataframes

        Args:
            frame (Str): 'frame containing all data except for capping bytes & checksum'

        Returns:
            checksum (Str): 'checksum'
        """

        frame_sum = sum(bytes.fromhex(frame))
        checksum = frame_sum.to_bytes(2, byteorder='little')
        return checksum.hex()




class Door_Controller:
    # !README
    """ !!@!!WARNING: ORDER OF INPUT VARIABLES IS IMPORTANT TO PROPER COMMAND CREATION !!@!!
        REFERENCE EXISTING COMMANDS ORDER, ANY DOCS YOU CAN FIND, CONTACT NATE, 
        WIRESHARK IT YOURSELF IF YOU HAVE A PCB, OR CRY """
    def __init__(self, controller_id, address_byte='00', host='', port=62000):
        self.c = Command_Constructor(controller_id, address_byte)
        self.HOST = host
        self.PORT = port

    def upload_card_perms(self, card, password, permission='01'):
        """Updates/uploads a user to the door controller

        Args:
            card (Int): User's card number 
            password (Str): password
            permission (Str, optional): The time profile. Defaults to '01'.

        Returns:
            Str: Constructed Command
        """
        now = datetime.datetime.now()
        command = {
            'functionbytes': self.c.function_bytes.modify_permissions,
            'e': '0100',  # Hardcoded
            'card': card,
            'doorNum': '01',  # Hardcoded : check if value is 01 at cyberia
            'startYMD': self.c.ymd_to_hex((now.year % 100), 1, 1),
            'endYMD': self.c.ymd_to_hex(22, 12, 10),
            'time': permission,
            'password': password
        }
        # (functionbytes=c.function_bytes_dict['modify_permissions'], e='0100', card=card, doorNum='01', startYMD='2108', endYMD=c.ymd_to_hex(22, 12, 10), time=permission, password=passw)

        x = self.c.construct_command(**command)
        self.execute_command(x)

    def upload_one_time_passwords(self, passwords):
        # x & y are hardcoded settings. I haven't bothered to understand what they're doing they don't need to change.
        x = f"{'0'*4}1e{'0'*14}03{'0'*22}01{'0'*24}fa0064000155{'0'*8}70{'0'*56}8494"
        y = f"{'0'*110}0d{'0'*116}ff{'0'*66}0cc4c3e0f929001000fcffffff0f{'0'*12}fff10f0000300044{'0'*12}"

        command = {
            'a': '03',
            'b': '00',
            'page': '01',
            'c': '01',
            'x': x,
            'passwords': passwords,
            'y': y,
            'fill_char': '0'
        }

        return self.c.construct_extended_command(**command)

    def delete_everything_off_controller_are_you_sure_of_yourself(self):
    # This hard-resets all settings on the controller, except history which cannot be modified!
        command = {
            'functionbytes': self.c.function_bytes.clear_domain
        }
        command = self.c.construct_command(**command)
        return self.execute_command(command)

    def listen_for_card(self, known_cards):
        command = self.c.construct_command(functionbytes=self.c.function_bytes.read_operation_status)
            
        def card_check(card):
            card = card[34:40]
            print(card, known_cards)
            print((card not in known_cards))
            if(card not in known_cards and card != '050000'):
                return True

        # return self.execute_command(command) # [34:40]
        self.execute_command_until(command, card_check, 1)

    def listen_for_admin_code(self): #not done
        command = self.c.construct_command(functionbytes=self.c.function_bytes.read_operation_status)

        def code_check(code):
            """There's no way to check the specific code, so instead we're checking for built-in the super_admin user"""
            code = code[34:40]
            if(code == '050000'):
                return True

        return self.execute_command_until(command, code_check, 24)

    def upload_card_times(self, users):
        """Uploads times user's are permitted through door

        Args:
            card (Int): User's access card
            door (Str): Door user has access to. Default
            start_date ([type]): [description]
            end_date ([type]): [description]
            perm ([type]): [description]
            password ([type]): [description]

        Returns:
            [type]: [description]
        """
        final = [users[i * 32:(i + 1) * 32] for i in range((len(users) + 32 - 1) // 32 )] #split into list of list with len 32
        for i, chunk in enumerate(final):
            page = format(0, '02x')
            command = self.c.construct_extended_command(a='03', b='00', page=page, c='04', users=users)
            self.execute_command(command)

    def execute_command(self, command):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind((self.HOST, self.PORT))

            sock.sendto(bytearray.fromhex(command), ('255.255.255.255', 60000))
            return sock.recv(1024).hex()

    def execute_command_until(self, command, until, hours_to_run):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind((self.HOST, self.PORT)) 

            # setup for listen_for_card. Not sure if other commands will need
            sock.sendto(bytearray.fromhex(command), ('255.255.255.255', 60000))
            untilVal = None
            now = datetime.datetime.now()

            while(not untilVal):
                try:
                    if(((datetime.datetime.now() - now).seconds/3600) >= hours_to_run):
                        return None
                except:
                    pass

                sock.sendto(bytearray.fromhex(command), ('255.255.255.255', 60000))
                scanned = sock.recv(1024).hex()
                print(scanned)
                untilVal = until(scanned)
                time.sleep(5)
        return untilVal


c = Door_Controller('e63a')
