import socket
from urllib.parse import urlparse


def default_action_fun(url, flag=''):
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = 40050
    message = str(parsed_url.port) + ', ' + flag

    # 创建套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到服务器
        client_socket.connect((host, port))
        # 发送消息
        client_socket.sendall(message.encode())
        # 接收响应
        response = client_socket.recv(1024).decode()
        # 打印响应
        return response
    finally:
        client_socket.close()

res = default_action_fun('http://43.136.237.143:40030/Less-6/', '10.2.26-MariaDB-log')
print(res)