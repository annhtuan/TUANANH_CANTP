# TUANANH_CANTP
Simulation CANTP
# CanTP Simulation with Python

This project simulates how the CAN Transport Protocol (CanTP) works by using the `python-can` library. The simulation represents a receiving node that handles CanTP messages and processes the received data following the protocol's requirements.

## Features
- **CAN Node Simulation**: The program simulates a CAN node that receives CanTP messages.
- **Message Handling**: Handles incoming messages with the correct data length and flow control to prevent flow control timeouts.
- **Flow Control**: Sends flow control messages to the transmitter to manage the transmission.
- **Bit Padding Removal**: Removes padding bits if present in the incoming message.
- **Byte Array Assembly**: Combines the received bytearray into a complete string.
- **Send CAN STANDARD and CAN FD**: Send and receive both CAN STANDARD and CAN FD.

  
## Requirements
To run this simulation, you need the following dependencies:
- `python-can` library
- Python 3.9
- Two ValueCAN 4.0 devices
- Install the following Python libraries:
  - `python-can`
  - `python_ics`
  - `filelock`
##-Additionally, you need to install the **RP1210 J2534 API Install Kit** driver, which can be downloaded from the following link:  
[RP1210 J2534 API Install Kit](https://intrepidcs.com/products/software/vehicle-spy/vehicle-spy-evaluation/)
## Example: Switching Between CAN Standard and CAN FD
To switch between sending CAN Standard and CAN FD, you can modify the second parameter in the following code:
```python
cantp.send_data(data, SEND_MESSAGE_TYPE.FLEXCAN)
