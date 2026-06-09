#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Unittest for testing TCPServer functions of umodbus"""

import mpy_unittest as unittest
from umodbus.tcp import TCPServer


class FakeClientSocket(object):
    def __init__(self, recv_data):
        self._recv_data = recv_data
        self.sent_data = []
        self.closed = False
        self.timeout = None

    def settimeout(self, timeout):
        self.timeout = timeout

    def recv(self, size):
        if self._recv_data:
            return self._recv_data.pop(0)
        raise OSError(11)

    def send(self, data):
        self.sent_data.append(data)

    def close(self):
        self.closed = True


class FakeServerSocket(object):
    def __init__(self, client_socks):
        self._client_socks = client_socks
        self.timeout = None

    def settimeout(self, timeout):
        self.timeout = timeout

    def accept(self):
        if self._client_socks:
            return self._client_socks.pop(0), ('127.0.0.1', 502)
        raise OSError(11)


class TestTcpServer(unittest.TestCase):
    def setUp(self) -> None:
        """Run before every test method"""
        self._request = b'\x00\x01\x00\x00\x00\x06\x0a\x01\x00\x7b\x00\x01'

    def test_get_request_multiple_clients(self) -> None:
        """Test processing requests from multiple clients"""
        first_client = FakeClientSocket([self._request])
        second_client = FakeClientSocket([self._request])

        server = TCPServer()
        server._sock = FakeServerSocket([first_client, second_client])
        server._max_connections = 2

        request = server.get_request(timeout=0)
        request.send_response([True])

        self.assertFalse(first_client.closed)
        self.assertEqual(len(first_client.sent_data), 1)
        self.assertEqual(len(second_client.sent_data), 0)

        request = server.get_request(timeout=0)
        request.send_response([True])

        self.assertFalse(second_client.closed)
        self.assertEqual(len(first_client.sent_data), 1)
        self.assertEqual(len(second_client.sent_data), 1)

    def test_get_request_max_connections(self) -> None:
        """Test rejecting clients above maximum active connections"""
        first_client = FakeClientSocket([self._request])
        second_client = FakeClientSocket([self._request])

        server = TCPServer()
        server._sock = FakeServerSocket([first_client, second_client])
        server._max_connections = 1

        request = server.get_request(timeout=0)
        request.send_response([True])

        self.assertFalse(first_client.closed)
        self.assertFalse(second_client.closed)

        request = server.get_request(timeout=0)

        self.assertIsNone(request)
        self.assertFalse(first_client.closed)
        self.assertTrue(second_client.closed)


if __name__ == '__main__':
    unittest.main()
