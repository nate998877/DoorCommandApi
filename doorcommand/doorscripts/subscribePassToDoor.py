import socket
import sys
import time
import time



class Controller:
    def __init__(self, serial_number, address_byte='00'):
        self.serial_number = int(serial_number, 16).to_bytes(2, byteorder='little').hex()
        self.address_byte = int(address_byte, 16).to_bytes(2, byteorder='little').hex() #I don't know what this is for
        self.function_bytes_dict = {
            "amend_directive":'F410',
            "get_latest_index":'108C',
            "read_command":'F110',
            "read_operation_status":'8110',
            "l_door_open":'9D10',
            "set_time":'8B10',
            "set_door_control_param":'8F10',
            "clear_domain":'9310',
            "read_domain":'9510',
            "tail_plus_permissions":'9B10',
            "modify_permissions":'0711',
            "delete_an_authority":'0811',
            "read_control_time":'9610',
            "modificaiton_time":'9710',
            "read_record":'8D10',
            "remove_record":'8E10',
            "ip_search":'0111',
        }



    def construct_command(self, **kwargs):
        local_vars = locals()
        del local_vars['self']
        return self._construct_command(local_vars['kwargs'])



    def construct_extended_command(self, **kwargs):
        """kwargs should be input as a=03 b=00 page=xx c=04' abc are for other commands, but I don't understand how they work

        Returns:
            [string] -- [524 byte length]
        """
        local_vars = locals()
        del local_vars['self']
        user_list = []

        for user in local_vars['kwargs']['users']:
            user_list.append(self._construct_userframe(user))
        del local_vars['kwargs']['users']
        return self._construct_extended_command(local_vars['kwargs'], user_list)



    def _construct_userframe(self, user):
        padded_pass = int(user[5], 16).to_bytes(2,byteorder='little').hex()
        return f"{''.join(user[:4])}{padded_pass}000000"



    #? local_vars is order specific. Kwargs might be way to further simplify?
    def _construct_command(self, local_vars):
        frame = self.serial_number + ''.join(local_vars.values())
        frame = self._fill_frame(frame)
        checksum = self._checksum(frame)
        return '7E'+frame+checksum+'0D'



    def _construct_extended_command(self, local_vars, userarr, fill_char='F', frame_length=1040):
        """constructs a 524 byte long dataframe

        Args:
            local_vars ([type]): [description]
            userarr ([type]): [description]
            fill_char (str, optional): [description]. Defaults to 'F'.
            frame_length (int, optional): [description]. Defaults to 1040.

        Returns:
            [type]: [description]
        """
        frame = self.serial_number +'F910'+ ''.join(local_vars.values())
        frame = frame + userarr[0]
        frame = self._fill_frame(frame, fill_char, frame_length)
        checksum = self._checksum(userarr[0])
        return '7E'+frame+checksum+'0D'



    def _fill_frame(self, unf_frame, fill_char='0', frame_length=60):
        """pads dataframes with fill_char

        Args:
        
            unf_frame str -- 'frame to pad'
            fill_char str, optional -- 'character frame is padded with'. Defaults to '0'.
            frame_length int, optional -- 'total length after padding'. Defaults to 60.

        Returns:
        
            str -- 'padded frame'
        """
        return unf_frame.ljust(frame_length, fill_char)



    def _checksum(self, frame):
        """Generates a 2 hex long checksum for dataframes

        Args:
        
            frame str -- 'frame containing all data except for capping bytes & checksum'

        Returns:
        
            str -- 'checksum'
        """
        
        frame_sum = sum(bytes.fromhex(frame))
        checksum = frame_sum.to_bytes(2, byteorder='little')
        return checksum.hex()


    def ymd_to_hex(self, year, month, day):
        """converts ymd as ints to a 4 byte long hex string

        Args:
        
            year int -- 'value between 0-199 representing years relative to 2000. Eg. 20 = 2020'
            month int -- 'value between 1-12 represents months'
            day int -- 'value between 1-31 represents days in month'

        Returns:
        
            str -- '4 bytes long'
        """
        b_year = format(year, '07b') # 0 is padding, 7 is length, b is byte for byte.
        b_month = format(month, '04b')
        b_day = format(day, '05b')

        return format(int(b_year+b_month+b_day, 2), 'x') # x is lowercase hex


    def hms_to_hex(self, hour, minute, second):
        """converts hms as ints to a 4 byte long hex string

        Args:
        
            hour int -- 'value between 0-23'
            minute int -- 'value between 0-59'
            second int -- 'value between 0-29 as 2 second interval'

        Returns:
        
            str -- '4 bytes long'
        """
        b_hour = format(hour, '05b') 
        b_minute = format(minute, '06b')
        b_second = format(second, '05b')

        return format(int(b_hour+b_minute+b_second, 2), 'x') 




# card needs to be converted to int version first. This might be extra steps if we don't care about displaying user ids
def upload_card_perms(c, card, permission, password):
    x = format(password, 'x')
    passw = x[2:]+x[:2]
    return c.construct_command(functionbytes=c.function_bytes_dict['modify_permissions'], e='0100', card=card, doorNum='01', startYMD='2108', endYMD=c.ymd_to_hex(22, 12, 10), time=permission, password=passw)


#This hard-resets all settings on the controller!
def clear_controller(c):
    return c.construct_command(functionbytes=c.function_bytes_dict['clear_domain'])


def upload_card_times(c, card, door, start_date, end_date, perm, password):
    users = [[card, door, start_date, end_date, perm, format(password, 'x') ]]
    return c.construct_extended_command(a='03', b='00', page='00', c='04', users=users)
    


def listen_for_card(c, sock):
    command = c.construct_command(functionbytes=c.function_bytes_dict['read_operation_status'])
    sock.sendto(bytearray.fromhex(command), ('255.255.255.255', 60000))
    
    init_card = sock.recv(1024).hex()[34:40] # [34:40] is location in string that contains last scanned card num
    scanned_card = init_card
    
    #poll for new card. Needs an async way to break out 
    while scanned_card == init_card:
        sock.sendto(bytearray.fromhex(command), ('255.255.255.255', 60000))
        scanned = sock.recv(1024).hex()
        scanned_card = scanned[34:40]
        time.sleep(1)

    # sc = [scanned_card[i:i+2] for i in range(0,len(scanned_card),2)]
    # return int(f"{int(sc[2], 16)}{int(sc[1]+sc[0], 16)}")# return the unfuckulated scanned card
    return scanned_card


def clearr(c, sock):
    cmd = clear_controller(c)
    sock.sendto(bytearray.fromhex(cmd), ('255.255.255.255', 60000))
    print(sock.recv(1024).hex())


def main():
    HOST, PORT = "localhost", 62000
    c = Controller('e63a')
    card = ''
    # with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
    #     sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #     sock.bind(('', PORT))
        
        # clearr(c, sock)
        
            #7e3ae6 07110100 8fbe 78 01 2108 9f29 01 40e2 0100000000000000000000000014050d
        # cmd='7e3ae6 07110100 8fbe 78 01 2108 9f29 01 40e2 0100000000000000000000000014050d'
        # sock.sendto(bytearray.fromhex(cmd), ('255.255.255.255', 62000))
        # sock.recv(1024).hex()
        
        # card = listen_for_card(c, sock)

        # cmd = upload_card_perms(c, card, '01', 5151)
        # sock.sendto(bytearray.fromhex(cmd), ('255.255.255.255', 60000))
        # print(sock.recv(1024).hex())
        
        # cmd = upload_card_times(c, card, '01', c.ymd_to_hex(20,1,1), c.ymd_to_hex(20,6,5), '01', 1234) 
        # sock.sendto(bytearray.fromhex(cmd), ('255.255.255.255', 62000))
        # print(sock.recv(1024).hex())



if __name__ == "__main__":
    main()











#FIXME: Several functions have hardcoded or unique non-passed variables that need to be accounted for.
#TODO: test each of these to ensure they work properly
