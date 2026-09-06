"""Check UDP DNS through the temporary SOCKS test client."""
import socket
import struct

with socket.create_connection(("127.0.0.1", 10809), timeout=15) as control:
    control.sendall(b"\x05\x01\x00")
    assert control.recv(2) == b"\x05\x00", "SOCKS authentication failed"
    control.sendall(b"\x05\x03\x00\x01" + bytes(6))
    response = b""
    while len(response) < 10:
        part = control.recv(10 - len(response))
        assert part, "SOCKS connection closed"
        response += part
    assert response[:4] == b"\x05\x00\x00\x01", response
    relay = (socket.inet_ntoa(response[4:8]), int.from_bytes(response[8:10], "big"))
    query = struct.pack("!6H", 0x7619, 0x100, 1, 0, 0, 0)
    query += b"\x07example\x03com\x00\x00\x01\x00\x01"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.settimeout(15)
        udp.sendto(b"\x00\x00\x00\x01" + socket.inet_aton("1.1.1.1") + b"\x00\x35" + query, relay)
        reply = udp.recv(4096)
    assert reply[:4] == b"\x00\x00\x00\x01", reply
    ident, flags, _, answers, _, _ = struct.unpack("!6H", reply[10:22])
    assert ident == 0x7619 and flags & 0x8000 and flags & 15 == 0 and answers > 0
    print(f"UDP DNS passed: {answers} answers through Wi-Fi endpoint and SSH")
