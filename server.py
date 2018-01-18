# _*_ coding:utf-8 _*_
__author__ = 'douge'

import socket
import threading
import sys
import base64
import hashlib
import struct
import select
import threadpool
import time

# ====== config ======
HOST = 'localhost'
PORT = 123456
MAGIC_STRING = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
HANDSHAKE_STRING = "HTTP/1.1 101 Switching Protocols\r\n" \
                   "Upgrade:websocket\r\n" \
                   "Connection: Upgrade\r\n" \
                   "Sec-WebSocket-Accept: {1}\r\n" \
                   "WebSocket-Location: ws://{2}/chat\r\n" \
                   "WebSocket-Protocol:chat\r\n\r\n"

inputConn = []


class Th(threading.Thread):
    def __init__(self, connection, ):
        threading.Thread.__init__(self)
        self.con = connection

    def run(self):
        while True:
            try:
                pass
            except:
                pass
        self.con.close()

    def recv_data(self, num):
        try:
            all_data = self.con.recv(num)
            if not len(all_data):
                return False
        except TypeError:
            return False
        else:
            print("haha")
            print(all_data)
            code_len = all_data[1] & 0x7f
            if code_len == 0x7e:
                masks = all_data[4:8]
                data = all_data[8:]
            elif code_len == 0x7f:
                masks = all_data[10:14]
                data = all_data[14:]
            else:
                masks = all_data[2:6]
                data = all_data[6:]
            raw_str = ""
            i = 0
            for d in data:
                raw_str += chr(d ^ masks[i % 4])
                i += 1
            print("--begin--")
            print(raw_str)
            print("--end--")
            return raw_str

    # send data
    def send_data(self, data):
        # 先编码--中文乱码
        data = str(data).encode('utf-8')

        msgLen = len(data)
        backMsgList = [struct.pack('B', 129)]

        if msgLen <= 125:
            backMsgList.append(struct.pack('b', msgLen))
        elif msgLen <= 65535:
            backMsgList.append(struct.pack('b', 126))
            backMsgList.append(struct.pack('>h', msgLen))
        elif msgLen <= (2 ^ 64 - 1):
            backMsgList.append(struct.pack('b', 127))
            backMsgList.append(struct.pack('>h', msgLen))
        else:
            print("the message is too long to send in a time")
            return
        message_byte = bytes()
        # print(type(backMsgList[0]))
        for c in backMsgList:
            message_byte += c
        # message_byte += bytes(data, encoding="utf8")

        message_byte += data
        self.con.send(message_byte)

        return True


def recv_data_glo(con):
    try:
        all_data = con.recv(1024)
        if not len(all_data):
            return False
    except TypeError:
        return False
    else:
        print("haha")
        print(all_data)
        code_len = all_data[1] & 0x7f
        if code_len == 0x7e:
            masks = all_data[4:8]
            data = all_data[8:]
        elif code_len == 0x7f:
            masks = all_data[10:14]
            data = all_data[14:]
        else:
            masks = all_data[2:6]
            data = all_data[6:]
        raw_str = ""
        i = 0
        for d in data:
            raw_str += chr(d ^ masks[i % 4])
            i += 1
        print("--begin--")
        print(raw_str)
        # print(thread.GetCurrentThreadId())
        print("--end--")
        return raw_str


# handshake
def handshake(con):
    headers = {}
    shake = con.recv(1024)

    shake = shake.decode()
    if not len(shake):
        return False

    try:
        print(shake.split('\r\n\r\n'))
        header, data = shake.split('\r\n\r\n', 1)
    except TypeError as e:
        print(e)
    for line in header.split('\r\n')[1:]:
        key, val = line.split(': ', 1)
        headers[key] = val

    if 'Sec-WebSocket-Key' not in headers:
        print('This socket is not websocket, client close.')
        con.close()
        return False

    headers["Location"] = "ws://{2}/chat".replace("{2}", HOST + ':' + str(PORT))
    key = headers['Sec-WebSocket-Key']
    token = base64.b64encode(hashlib.sha1(str.encode(str(key + MAGIC_STRING))).digest())

    handshake = "HTTP/1.1 101 Switching Protocols\r\n" \
                "Upgrade: websocket\r\n" \
                "Connection: Upgrade\r\n" \
                "Sec-WebSocket-Accept: " + bytes.decode(token) + "\r\n" \
                                                                 "WebSocket-Origin: " + str(headers["Origin"]) + "\r\n" \
                                                                                                                 "WebSocket-Location: " + str(
        headers["Location"]) + "\r\n\r\n"

    con.send(str.encode(str(handshake)))

    return True


def new_service():
    """start a service socket and listen
    when coms a connection, start a new thread to handle it"""
    global inputConn
    #线程池
    pool = threadpool.ThreadPool(10)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', 3368))
        sock.listen(1000)
        print("listen 1000")
        # 链接队列大小
        print("bind 3368,ready to use")
    except:
        print("Server is already running,quit")
        sys.exit()
    inputConn.append(sock)
    conDict = {}
    while True:
        rs, ws, es = select.select(inputConn, [], [])
        rsCons = []
        for r in rs:
            if sock == r:
                connection, address = sock.accept()
                # 返回元组（socket,add），accept调用时会进入waite状态
                print("Got connection from ", address)
                if handshake(connection):
                    print("handshake success")
                    t = Th(connection)
                    conDict[connection] = t
                    inputConn.append(connection)
                    t.start()
                    t.send_data("hahhfdsgbdfgfdahah")
                    print('new thread for client ...')
            else:
                rsCons.append(r)
                # try:
                #     data = conDict[r].recv_data(1024)
                #     disconnected = not data
                #     conDict[r].send_data("收到了")
                # except socket.error:
                #     disconnected = True
                #
                # if disconnected:
                #     print(r.getpeername(), 'disconnected')
                #     inputConn.remove(r)
                # else:
                #     print(data)
            requests = threadpool.makeRequests(recv_data_glo, rsCons)
            for req in requests:
                pool.putRequest(req)
            pool.wait()


if __name__ == '__main__':
    new_service()
