
import asyncio
from scapy.sendrecv import AsyncSniffer
from scapy.layers.dhcp import DHCP
from scapy.layers.l2 import Ether

FILTER = "udp and (port 67 or 68)"

_sniffer = None
REQUESTED_ADDR = "requested_addr"
MESSAGE_TYPE = "message-type"
HOSTNAME = "hostname"
MAC_ADDRESS = "macaddress"
IP_ADDRESS = "ip"
DHCP_REQUEST = 3


def format_mac(mac: str) -> str:
    """Format the mac address string for entry into dev reg."""
    to_test = mac

    if len(to_test) == 17 and to_test.count(":") == 5:
        return to_test.lower()

    if len(to_test) == 17 and to_test.count("-") == 5:
        to_test = to_test.replace("-", "")
    elif len(to_test) == 14 and to_test.count(".") == 2:
        to_test = to_test.replace(".", "")

    if len(to_test) == 12:
        # no : included
        return ":".join(to_test.lower()[i : i + 2] for i in range(0, 12, 2))

    # Not sure how formatted, return original
    return mac

def _format_mac(mac_address):
    """Format a mac address for matching."""
    return format_mac(mac_address).replace(":", "")

def _decode_dhcp_option(dhcp_options, key):
    """Extract and decode data from a packet option."""
    for option in dhcp_options:
        if len(option) < 2 or option[0] != key:
            continue

        value = option[1]
        if value is None or key != HOSTNAME:
            return value

        # hostname is unicode
        try:
            return value.decode()
        except (AttributeError, UnicodeDecodeError):
            return None


def handle_dhcp_packet( packet):
    """Process a dhcp packet."""
    if DHCP not in packet:
        return
    print('----received')

    options = packet[DHCP].options

    request_type = _decode_dhcp_option(options, MESSAGE_TYPE)
    if request_type != DHCP_REQUEST:
        # DHCP request
        return

    ip_address = _decode_dhcp_option(options, REQUESTED_ADDR)
    hostname = _decode_dhcp_option(options, HOSTNAME)
    mac_address = _format_mac(packet[Ether].src)

    if ip_address is None or hostname is None or mac_address is None:
        return

async def start():

    _sniffer = AsyncSniffer(
        #filter=FILTER,
        #started_callback=self._started.set,
        prn=handle_dhcp_packet,
        store=0,
    )

    _sniffer.start()
    print("OK")

async def b():
    p = input()
    print('input:',p)
    _sniffer.stop()

async def main():
    await asyncio.gather(start(),b())
    
asyncio.run(main())