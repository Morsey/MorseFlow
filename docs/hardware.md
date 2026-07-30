# Morseboard Hardware Contract

## Reserved Pins

| Function | GPIO |
| --- | --- |
| DFPlayer UART TX to DFPlayer RX | GPIO0 |
| DFPlayer UART RX from DFPlayer TX | GPIO1 |
| Switched 5V prop power enable | GPIO15 |
| W5500 MISO | GPIO16 |
| W5500 CS | GPIO17 |
| W5500 SCK | GPIO18 |
| W5500 MOSI | GPIO19 |
| W5500 RESET | GPIO20 |
| W5500 INT | GPIO21 |
| Optional onboard relay | GPIO22 |

GPIO16-GPIO21 are reserved for W5500 Ethernet and must not be used by props.
Onboard buttons are not used.

## Prop Ports

Each Morseboard has eight RJ45 prop ports. Each cable carries:

- GND
- Switched 5V
- Always-live 12V
- Signal A
- Signal B

| Port | Signal A | Signal B |
| --- | --- | --- |
| 1 | GPIO2 | GPIO3 |
| 2 | GPIO4 | GPIO5 |
| 3 | GPIO6 | GPIO7 |
| 4 | GPIO8 | GPIO9 |
| 5 | GPIO10 | GPIO11 |
| 6 | GPIO12 | GPIO26 |
| 7 | GPIO13 | GPIO27 |
| 8 | GPIO14 | GPIO28 |

## Example PIB Pattern

A simple Prop Interface Board can map:

- Signal A: solenoid driver input.
- Signal B: NeoPixel or indicator control input.

Smart PIBs may use a small RP2040-class board. For RFID PIBs, prefer simple
status outputs:

- No card.
- Correct card present.
- Incorrect card present.

Serial RFID PIB mode should be used only when Node-RED needs the actual card ID.

