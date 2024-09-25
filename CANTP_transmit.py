import can
import time
import random
from enum import Enum
import sys
class SEND_MESSAGE_TYPE(Enum):
    STANDARD = False
    FLEXCAN = True

class CanTpTransmit:
    #constructor
    def __init__(self,  message_type = SEND_MESSAGE_TYPE.STANDARD):
        self.bs = 0  # Block Size (Number of CFs to send before waiting for the next FC)
        self.stmin = 0  # Separation Time Minimum (Delay between CF transmissions)
        self.message_type = message_type
        self.wrong_flow = False
        self.flag_overflow = False
        self.bus = can.Bus(channel = 1 , bitrate = 500000, interface = 'neovi',fd = True,receive_own_message = False)

    #deconstructor
    def __del__(self):
        self.bus.shutdown()
    def send_data(self, data,send_message_type):
        self.message_type = send_message_type
        #send flexcan
        if self.message_type == SEND_MESSAGE_TYPE.FLEXCAN :
                if len(data) <= 7 :
                    self.send_single_frame(data)
                    if(send_message_type == True):
                        print("Transmit all FD CAN data <= 7")
                elif len(data) >=8 and self.message_type == SEND_MESSAGE_TYPE.FLEXCAN and len(data) <=62: 
                    self.send_single_frame_FD(data)
                    print("Transmit all FD CAN data in (8,63) ")
                else:
                    # Send the First Frame
                    self.send_first_frame_flexcan(data)
                    try : 
                    # Wait for the first FlowControl message
                        self.wait_for_flow_control()
                        if self.flag_overflow == True:
                            print("stop sending")
                            self.flag_overflow = False
                    # Once flow control is received, start sending consecutive frames
                        else:
                            self.send_consecutive_frames_flexcan( data)
                            print("Transmit all")
                    except TimeoutError as e:
                        print(e);
        elif self.message_type == SEND_MESSAGE_TYPE.STANDARD:
                if len(data) <= 7 :
                    self.send_single_frame(data)
                    print("Transmit all STANDARD CAN ")
                else:
                    # Send the First Frame
                    self.send_first_frame_standard(data)
                    try : 
                    # Wait for the first FlowControl message
                        self.wait_for_flow_control()
                        if self.flag_overflow == True:
                            print("stop sending")
                            self.flag_overflow = False

                    # Once flow control is received, start sending consecutive frames
                        self.send_consecutive_frames_standard(data)
                        print("Transmit all")
                    except TimeoutError as e:
                        print(e);
    def send_first_frame_flexcan(self, data):
        total_length = len(data)
        if total_length <= 4095:
            # First case: FF_DL <= 4095
            first_frame = [0x10 | ((total_length >> 8) & 0x0F), total_length & 0xFF]
            first_frame += data[:62]  # First 62 bytes of data
        else:
            # Second case: FF_DL > 4095
            first_frame = [0x10, 0x00]  # FF_DL > 4095 uses extended length
            ff_dl_extended = total_length.to_bytes(4, byteorder='big')  # 4-byte length
            first_frame += list(ff_dl_extended)[:4]  # Append the first 4 bytes of extended length
            first_frame += data[:58]  # Only 58 bytes of data can fit

        # Add padding if necessary to make the frame 8 bytes
        first_frame += [0x00] * (64 - len(first_frame))
        
        print(f"Sending First Frame FD: {first_frame}")
        self.transmit( first_frame)

    #function to send CF of flexcan
    def send_consecutive_frames_flexcan(self, data):
        sn = 1  # Sequence Number
        num_cf_sent = 0  # Track how many CFs have been sent
        time.sleep(0.1)
        for i in range(62, len(data), 63):
            if num_cf_sent == self.bs:
                # Block size reached, wait for next FlowControl
                print(f"Waiting for next FlowControl after sending {self.bs} CFs")
                self.wait_for_flow_control()
                num_cf_sent = 0  # Reset counter for the next block

            cf_frame = [0x20 | (sn & 0x0F)] + data[i:i + 63]
            padding_fd_number = 0
            if len(cf_frame) <8 :
                padding_fd_number = 8
            elif len(cf_frame) <12 and len(cf_frame) >=8:
                padding_fd_number = 12
            elif len(cf_frame) <16  and len(cf_frame) >=12 :
                padding_fd_number = 16
            elif len(cf_frame) <20  and len(cf_frame) >=16:
                padding_fd_number = 24
            elif len(cf_frame) <32  and len(cf_frame) >=20:
                padding_fd_number = 32
            elif len(cf_frame) <48  and len(cf_frame) >=32:
                padding_fd_number = 48
            elif len(cf_frame) <64 and len(cf_frame) >=48:
                padding_fd_number = 64
            cf_frame += [0x00] * (padding_fd_number - len(cf_frame))  # Padding
            print(f"Sending Consecutive Frame FLEXCAN {sn}: {cf_frame}")
            self.transmit( cf_frame)
            time.sleep(0.1)  # Apply STmin delay (convert ms to seconds)
            
            sn += 1
            num_cf_sent += 1

            if sn > 15:
                sn = 0

    #function to send single frame FD
    def send_single_frame_FD (self,data):
        sf_dl = len(data)
        frame = [0x00] + [sf_dl] + data
        if(len(frame)) < 12 :
            frame += [0x00]*(12-len(frame))
            print(f"Sending single frame : {frame}")
        elif (len(frame)) >= 12 and (len(frame)) < 16 :
            frame += [0x00]*(16-len(frame))
            print(f"Sending single frame : {frame}")
        elif (len(frame)) >= 12 and (len(frame)) < 16 :
            frame += [0x00]*(16-len(frame))
            print(f"Sending single frame : {frame}")
        elif (len(frame)) >= 16 and (len(frame)) < 20 :
            frame += [0x00]*(20-len(frame))
            print(f"Sending single frame : {frame}")
        elif (len(frame)) >= 20 and (len(frame)) < 24 :
            frame += [0x00]*(24-len(frame))
            print(f"Sending single frame : {frame}")
        elif (len(frame)) >= 24 and (len(frame)) < 32:
            frame += [0x00]*(32-len(frame))
            print(f"Sending single frame : {frame}")
        elif (len(frame)) >= 32 and (len(frame)) < 48 :
            frame += [0x00]*(48-len(frame))
            print(f"Sending single frame : {frame}")
        elif (len(frame)) >= 48 and (len(frame)) < 64 :
            frame += [0x00]*(64-len(frame))
            print(f"Sending single frame : {frame}")
        self.transmit(frame)
    def send_single_frame(self, data):
        sf_dl = len(data)
        frame = [0x00 | sf_dl] + data
        if len(frame) < 8:
            frame += [0x00] * (8 - len(frame))  # Padding
        if self.message_type == SEND_MESSAGE_TYPE.FLEXCAN:
            print(f"Sending single frame FD data <8 : {frame}")
        elif self.message_type == SEND_MESSAGE_TYPE.STANDARD:
            print(f"Sending single frame STANDARE data <8 : {frame}")
        self.transmit(frame)

    #function to send first frame standard
    def send_first_frame_standard(self,  data):
        total_length = len(data)
        print(f"length data = {len(data)}")
        if total_length <= 4095:
            # First case: FF_DL <= 4095
            first_frame = [0x10 | ((total_length >> 8) & 0x0F), total_length & 0xFF]
            first_frame += data[:6]  # First 6 bytes of data
        else:
            # Second case: FF_DL > 4095
            first_frame = [0x10, 0x00]  # FF_DL > 4095 uses extended length
            ff_dl_extended = total_length.to_bytes(4, byteorder='big')  # 4-byte length
            first_frame += list(ff_dl_extended)[:4]  # Append the first 4 bytes of extended length
            first_frame += data[:2]  # Only 3 bytes of data can fit

        # Add padding if necessary to make the frame 8 bytes
        first_frame += [0x00] * (8 - len(first_frame))
        
        print(f"Sending First Frame: {first_frame}")
        self.transmit(first_frame)

    #function to send CF standard
    def send_consecutive_frames_standard(self, data):
        sn = 1  # Sequence Number
        num_cf_sent = 0  # Track how many CFs have been sent
        time.sleep(0.1)
        for i in range(6, len(data), 7):
            if num_cf_sent == self.bs:
                # Block size reached, wait for next FlowControl
                print(f"Waiting for next FlowControl after sending {self.bs} CFs")
                self.wait_for_flow_control()
                num_cf_sent = 0  # Reset counter for the next block

            cf_frame = [0x20 | (sn & 0x0F)] + data[i:i + 7]
            cf_frame += [0x00] * (8 - len(cf_frame))  # Padding
            print(f"Sending Consecutive Frame {sn}: {cf_frame}")
            self.transmit(cf_frame)
            time.sleep(0.15)  # Apply STmin delay (convert ms to seconds)
            
            sn += 1
            num_cf_sent += 1

            if sn > 15:
                sn = 0

    #funciton to transmit message
    def transmit(self, frame):
        if self.message_type == SEND_MESSAGE_TYPE.FLEXCAN:
            can_msg = can.Message(arbitration_id=0x123, data=frame, is_extended_id=False,is_fd= True)
        else:
            can_msg = can.Message(arbitration_id=0x123, data=frame, is_extended_id=False,is_fd= False)
        
        try:
            self.bus.send(can_msg)
        except can.CanError as e:
            print(f"CAN message NOT sent: {e}")

    #funciton to wait flow control
    def wait_for_flow_control(self):
        """
        Function that waits for the FlowControl frame containing BS and StMin.
        """
        start_time = time.time()
        
        while True:
                recv_msg = self.bus.recv(timeout=1)
                elapsed_time = time.time() - start_time
                if recv_msg and recv_msg.arbitration_id == 0x789:  # Example FC arbitration ID
                    data = recv_msg.data
                    if data[0] == 0x30:
                        self.bs = data[1]
                        self.stmin = data[2]
                        print("                ")
                        print(f"Received Flow Control CTS: BS={self.bs}")
                        print("                ")
                        break
                    elif data[0] == 0x31:
                        print("                ")
                        print(f"Received Flow Control WAIT")
                        time.sleep(0.5)
                        continue
                    elif data[0] == 0x32:
                        self.flag_overflow = True
                        print("                ")
                        print(f"Received Flow Control OVERFLOW")
                    #if data[0] >> 4 == 0x3:  # Check if it's a FlowControl frame (PCI type = 0x3)
                        break
                    else:
                        print("WRONG FLOW CONTROL STRUCTURE")
                        self.wrong_flow = True
                        break
                # Notify the user every second about the waiting status
                if elapsed_time % 1 < 0.1:  # Check every second
                    print(f"Waiting for Flow Control... {int(elapsed_time)} seconds elapsed")
            
            # Check if the timeout has been reached
                if elapsed_time > 5:
                    print("Timeout: No Flow Control received. Ending data transmission.")
                    raise TimeoutError("Flow Control not received within 5 seconds.") 
                time.sleep(0.2)

if __name__ == "__main__":
    cantp = CanTpTransmit()  # Use vcan0, replace with real channel for actual CAN
    # x = 5000# Example: number of elements
    # data = [random.randint(0x00, 0xFF) for _ in range(x)]
    # print(f"do dai data = {len(data)}")
    # Z = "ABCDE"
    # y = """A study from the University of South Australia has found that babies born to mothers with a high-fat,.
    # high-sugar diet may face an increased risk of heart disease and diabetes later in life. Researchers studied baboons,.
    # feeding pregnant females unhealthy diets and comparing the heart tissues of their offspring to those born from mothers.
    # on healthy diets. They found that the unhealthy diet led to reduced levels of the thyroid hormone T3, essential for .
    # proper heart development, potentially leading to long-term cardiovascular and metabolic issues, even if babies were .
    # born at a normal weight.The findings suggest that the effects of poor maternal nutrition may persist into adulthood,.
    # increasing the risk of heart problems and insulin resistance, conditions that contribute to diabetes. The researchers recommend early .
    # cardiometabolic health screening for babies born to mothers with such diets to detect potential health risks.
    # This study, published in *The Journal of Physiology*, highlights the long-term impact of maternal diet on fetal development and future health outcomes."""
    # #data = [ord(char) for char in Z]
    # cantp.send_data(data,SEND_MESSAGE_TYPE.STANDARD)
    while True:
        # Nhập chuỗi từ bàn phím
        print("enter your string (press enter to abort)")
        input_string = input("Nhập chuỗi dữ liệu (nhấn Enter để thoát): ")
        
        # Nếu chuỗi rỗng (người dùng chỉ nhấn Enter), thoát vòng lặp
        if input_string == "":
            print("Hủy truyền tin nhắn.")
            break
        
        # Chuyển đổi chuỗi thành mảng số nguyên (dựa trên mã ASCII của các ký tự)
        data = list(input_string.encode('utf-32'))
        print(f"do dai data = {len(data)}")
        
        # Gửi dữ liệu qua CAN
        cantp.send_data(data, SEND_MESSAGE_TYPE.FLEXCAN)

    
        
