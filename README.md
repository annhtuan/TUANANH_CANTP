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

## Requirements
To run this simulation, you need the following dependencies:
- `python-can` library
- Python 3.6 or higher

You can install the required libraries using `pip`:
```bash
pip install python-can
