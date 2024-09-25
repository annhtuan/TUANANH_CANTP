import can
import time
from enum import Enum
OVER_FLOW_BUFFER = 20000


class FC_FLAG(Enum):
    #clear to send
    CTS = 0
    #wait status
    WAIT = 1
    #overflow status
    OVFLW = 2

class CanTpReceiver:
    #constructor
    def __init__(self):
        self.received_data = []  # List để lưu trữ dữ liệu đã nhận
        self.total_length = None  # Tổng chiều dài dữ liệu
        self.received_length = 0  # Chiều dài dữ liệu đã nhận
        self.bs = 15  # Block Size mặc định
        self.stmin = 0  # Separation Time Minimum
        self.cf_count = 0  # Đếm số lượng Consecutive Frames đã nhận
        self.bus = can.Bus(channel = 1 , bitrate = 500000, interface = 'neovi',fd = True,receive_own_message = False)
        self.buffer = 0
        self.CURRENT_BUFFER = 50
    #deconstructor
    def __del__(self):
        self.bus.shutdown()
        
    def send_flow_control(self,flag):
        """
        Hàm gửi Flow Control Frame với giá trị BS và STmin.
        """
        # Flow Control Frame với PCI type là 0x30 (Flow Control), BS và STmin
        FC = None
        case = None
        if flag == FC_FLAG.CTS :
            FC = can.Message(arbitration_id=0x789, data=[0x30, self.bs, self.stmin, 0, 0, 0, 0, 0], is_extended_id=False)
            case = "Continue to Send"
        elif flag == FC_FLAG.WAIT:
            FC = can.Message(arbitration_id=0x789, data=[0x31, self.bs, self.stmin, 0, 0, 0, 0, 0], is_extended_id=False)
            case = "Wait"
        elif flag == FC_FLAG.OVFLW:
            FC = can.Message(arbitration_id=0x789, data=[0x32, self.bs, self.stmin, 0, 0, 0, 0, 0], is_extended_id=False)               
            case = "OVERFLOW"
        try:
            self.bus.send(FC)
            print("            ")
            print(f"Sent Flow Control " + case + f" message: Data={list(FC.data)}")
        except can.CanError:
            print("Failed to send flow control frame")

    #function to receive message
    def receive_frame(self):
        """
        Hàm nhận từng frame từ CAN bus, phân tích và ghép lại dữ liệu.
        """
        #with can.ThreadSafeBus(interface='socketcan', channel='vcan0', bitrate=500000,fd = True) as bus:
        try:
            recv_msg = self.bus.recv(timeout=0.2)  # Đợi tối đa 0.2 giây để nhận tin nhắn
            if recv_msg:
                arbitration_id =  hex(recv_msg.arbitration_id)
                # Ignore Flow Control messages with arbitration ID 0x789 (or whatever ID you use)
                if recv_msg.arbitration_id == 0x789:
                    return None  # Skip this message
                
                #RECEIVE STANDARD CAN
                elif not recv_msg.is_fd and len(recv_msg.data)==8:
                    data = recv_msg.data
                    
                    # Kiểm tra loại frame dựa trên byte đầu tiên (PCI Type)
                    pci_type = data[0] >> 4  # PCI type là 4 bit cao của byte đầu tiên
                    byte_2 = data[1]
                    if pci_type == 0x0:
                        # Single Frame (PCI type = 0x0)
                        print("Received a Single Frame, no flow control sent.")
                        sf_dl = data[0] & 0x0F  # Lấy SF_DL (4 bit thấp)
                        print(f"sfdl = {sf_dl}")
                        self.received_data += list(data[1:1+sf_dl])  # Lưu dữ liệu từ Single Frame
                        print(f"Data received: {self.received_data}")
                        print(f"All data received: {''.join(chr(byte) for byte in self.received_data[0:len(self.received_data)])}")
                        self.reset_receiver()
                    elif pci_type == 0x1 and byte_2 !=0 :
                        # First Frame (PCI type = 0x1)
                        print("Received a First Frame <4095, sending Flow Control Frame.")
                        ff_dl = ((data[0] & 0x0F) << 8) + data[1]  # Lấy FF_DL (12 bit)
                        print(f"ff_dl = {ff_dl}")
                        self.total_length = ff_dl  # Tổng chiều dài dữ liệu
                        self.received_data += list(data[2:])  # Lưu 6 byte từ First Frame
                        self.received_length = len(self.received_data)
                        self.cf_count = 0  # Đặt lại bộ đếm Consecutive Frames
                        self.buffer = self.CURRENT_BUFFER - 6
                        if self.total_length > OVER_FLOW_BUFFER:
                            print("overflow occur , come here")
                            self.send_flow_control(FC_FLAG.OVFLW)  # Gửi Flow Control với BS = 4, STmin = 0
                            self.reset_receiver()
                        else:
                            print("overflow don't occur")
                            time.sleep(1)
                            self.send_flow_control(FC_FLAG.CTS)
                    elif pci_type == 0x1 and byte_2 == 0 :
                        # First Frame (PCI type = 0x1)
                        print("Received a First Frame >4095, sending Flow Control Frame.")
                        #ff_dl = ((data[0] & 0x0F) << 8) + data[1]  # Lấy FF_DL (12 bit)
                        ff_dl = (data[2] << 24) | (data[3] << 16) | (data[4] << 8) | data[5]
                        print(f"ff_dl = {ff_dl}")                  
                        self.total_length = ff_dl  # Tổng chiều dài dữ liệu
                        self.received_data += list(data[6:])  # Lưu 2 byte từ First Frame
                        self.received_length = len(self.received_data)
                        self.cf_count = 0  # Đặt lại bộ đếm Consecutive Frames
                        self.buffer = self.CURRENT_BUFFER - 2
                        if self.total_length > OVER_FLOW_BUFFER:
                            print("overflow occur")
                            time(1)
                            self.send_flow_control(FC_FLAG.OVFLW)  # Gửi Flow Control với BS = 4, STmin = 0 
                            self.reset_receiver()
                        else:
                            print("overflow don't occur")
                            self.send_flow_control(FC_FLAG.CTS) 
                    elif pci_type == 0x2:
                        # Consecutive Frame (PCI type = 0x2)
                        sn = data[0] & 0x0F  # Sequence Number (4 bit thấp)
                        #print(f"Received a Consecutive Frame, SN={sn}")

                        self.received_data += list(data[1:])  # Lưu dữ liệu từ Consecutive Frame
                        self.received_length = len(self.received_data)
                        self.cf_count += 1  # Tăng bộ đếm CF
                        
                        # Kiểm tra nếu đã nhận đủ toàn bộ dữ liệu
                        if self.received_length >= self.total_length:
                            time.sleep(1.5)
                            print(f"All data received: {''.join(chr(byte) for byte in self.received_data[0:self.total_length])}")
                            #print(f"All data received: {self.received_data[0:self.total_length]}")
                            self.reset_receiver()


                        # Nếu đã nhận đủ số lượng CF theo Block Size (BS)
                        if self.cf_count >= self.bs:
                            self.buffer -= 7* self.bs
                            print("           ")
                            print(f"Received {self.bs} Consecutive Frames, sending new Flow Control.")
                            print("                   ")
                            while self.buffer < 7*self.bs:
                                self.send_flow_control(FC_FLAG.WAIT)  # Gửi Flow Control mới
                                time.sleep(0.5)
                                self.CURRENT_BUFFER= self.CURRENT_BUFFER *2
                                self.buffer = self.CURRENT_BUFFER 
                                time.sleep(1)
                            self.send_flow_control(FC_FLAG.CTS)
                            self.cf_count = 0  # Đặt lại bộ đếm CF
                    else:
                        print(f"Received another frame type: PCI type {pci_type}")
                    
                    return recv_msg
                #Handle can fd
                elif recv_msg.is_fd and len(recv_msg.data) in {8,12,16,20,24,32,48,64} :
                    #print("receive fd frame")
                    data = recv_msg.data
                    #print(f"Received message FD : ID={arbitration_id}, Data={data}")
                    
                    # Kiểm tra loại frame dựa trên byte đầu tiên (PCI Type)
                    pci_type = data[0] >> 4  # PCI type là 4 bit cao của byte đầu tiên
                    byte_1 = data[0]
                    byte_2 = data[1]
                    if pci_type == 0x0 and len(recv_msg.data) == 8:
                        # Single Frame (PCI type = 0x0)
                        print("Received a Single Frame FD, data < 7 , no flow control sent.")
                        sf_dl = data[0] & 0x0F  # Lấy SF_DL (4 bit thấp)
                        self.received_data += list(data[1:1+sf_dl])  # Lưu dữ liệu từ Single Frame
                        print(f"Data received: {self.received_data}")
                        print(f"All data received: {''.join(chr(byte) for byte in self.received_data[0:self.total_length])}")

                        self.reset_receiver()
                    elif byte_1 == 0x00  and len(recv_msg.data) in {12,20,24,32,48,64}:
                        print("Received Single Frame FD data >=8 and <=62 ,no flow control send ")
                        sf_dl = byte_2
                        self.received_data += list(data[2:2+sf_dl])
                        print(f"Data received: {self.received_data}")
                        print(f"All data received: {''.join(chr(byte) for byte in self.received_data[0:self.total_length])}")
                        self.reset_receiver()
                    elif pci_type == 0x1 and byte_2 !=0  and len(recv_msg.data) == 64:
                        # First Frame (PCI type = 0x1)
                        print("Received a First Frame FD < 4095, sending Flow Control Frame.")
                        ff_dl = ((data[0] & 0x0F) << 8) + data[1]  # Lấy FF_DL (12 bit)
                        print(f"ff_dl = {ff_dl}")
                        self.total_length = ff_dl  # Tổng chiều dài dữ liệu
                        self.received_data += list(data[2:])  # Lưu 6 byte từ First Frame
                        self.received_length = len(self.received_data)
                        self.cf_count = 0  # Đặt lại bộ đếm Consecutive Frames
                        self.buffer = self.CURRENT_BUFFER-62
                        if self.total_length > OVER_FLOW_BUFFER:
                            print("overflow occur")
                            self.send_flow_control(FC_FLAG.OVFLW)  # Gửi Flow Control với BS = 4, STmin = 0
                            self.reset_receiver()
                        else:
                            print("overflow don't occur")
                            time.sleep(1)
                            self.send_flow_control(FC_FLAG.CTS)
                    elif pci_type == 0x1 and byte_2 == 0 and len(recv_msg.data) == 64 :
                        # First Frame (PCI type = 0x1)
                        print("Received a First Frame FD > 4095, sending Flow Control Frame.")
                        #ff_dl = ((data[0] & 0x0F) << 8) + data[1]  # Lấy FF_DL (12 bit)
                        ff_dl = (data[2] << 24) | (data[3] << 16) | (data[4] << 8) | data[5]
                        print(f"ff_dl = {ff_dl}")                  
                        self.total_length = ff_dl  # Tổng chiều dài dữ liệu
                        self.received_data += list(data[6:])  # Lưu 2 byte từ First Frame
                        self.received_length = len(self.received_data)
                        self.cf_count = 0  # Đặt lại bộ đếm Consecutive Frames
                        self.buffer = self.CURRENT_BUFFER - 58
                        if self.total_length > OVER_FLOW_BUFFER :
                            print("overflow occur")
                            self.send_flow_control(FC_FLAG.OVFLW)  # Gửi Flow Control với BS = 4, STmin = 0  
                            self.reset_receiver()
                        else:
                            print("overflow don't occur")
                            time.sleep(1)
                            self.send_flow_control(FC_FLAG.CTS)
                    elif pci_type == 0x2:
                        # Consecutive Frame (PCI type = 0x2)
                        sn = data[0] & 0x0F  # Sequence Number (4 bit thấp)
                        #print(f"Received a Consecutive Frame, SN={sn}")

                        self.received_data += list(data[1:])  # Lưu dữ liệu từ Consecutive Frame
                        self.received_length = len(self.received_data)
                        self.cf_count += 1  # Tăng bộ đếm CF

                        # Kiểm tra nếu đã nhận đủ toàn bộ dữ liệu
                        if self.received_length >= self.total_length:
                            time.sleep(1.5)
                            print(f"All data received: {''.join(chr(byte) for byte in self.received_data[0:self.total_length])}")
                            #print(f"All data FD received: {self.received_data[0:self.total_length]}")
                            self.reset_receiver()
                        
                        # Nếu đã nhận đủ số lượng CF theo Block Size (BS)
                        if self.cf_count >= self.bs:
                            print(f"Received {self.bs} Consecutive Frames FD, sending new Flow Control.")
                            self.buffer -= 63*self.bs
                            while self.buffer < 63* self.bs:
                                self.send_flow_control(FC_FLAG.WAIT)  # Gửi Flow Control mới
                                time.sleep(0.3)
                                self.CURRENT_BUFFER = self.CURRENT_BUFFER *2
                                self.buffer = self.CURRENT_BUFFER 
                            self.send_flow_control(FC_FLAG.CTS)
                            self.cf_count = 0  # Đặt lại bộ đếm CF
                    else:
                        print(f"Received another frame type: PCI type {pci_type}")
                    
                    return recv_msg
                else:
                    print("Length is wrong")
                    return None 
            else:
                return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    
    def reset_receiver(self):
        """
        Đặt lại các biến để sẵn sàng nhận một chuỗi mới.
        """
        self.received_data = []
        self.total_length = None
        self.received_length = 0
        self.cf_count = 0
        self.buffer = 0
        CURRENT_BUFFER = 200

if __name__ == "__main__":
    receiver = CanTpReceiver()
    
    try:
        print("Waiting to receive messages...")
        while True:
            new_msg = receiver.receive_frame()
    except KeyboardInterrupt:
        print("Process interrupted")
