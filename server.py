import argparse
import os
import queue
import select
import socket
import sys
import threading

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 9999
BUFFER_SIZE = 1024
QUIT_COMMAND = "/quit"
LEET_COMMAND = "/leet"
VIRUS_COMMAND = "/virus"
CONTROL_PREFIX = "__CTRL__:"
VIRUS_SIGNAL = f"{CONTROL_PREFIX}VIRUS"
USERNAME_PREFIX = f"{CONTROL_PREFIX}USERNAME:"

LEET_MAP = str.maketrans({
    "a": "4",
    "A": "4",
    "e": "3",
    "E": "3",
    "i": "1",
    "I": "1",
    "o": "0",
    "O": "0",
    "s": "5",
    "S": "5",
    "t": "7",
    "T": "7",
    "g": "6",
    "G": "6",
})


def parse_args():
    parser = argparse.ArgumentParser(description="Run the Wazzap chat server.")
    parser.add_argument("host", nargs="?", default=DEFAULT_HOST, help="Host/IP to bind to.")
    parser.add_argument(
        "port",
        nargs="?",
        type=int,
        default=DEFAULT_PORT,
        help="TCP port to listen on.",
    )
    return parser.parse_args()


def prompt():
    print("> ", end="", flush=True)


def to_leetspeak(message):
    return message.translate(LEET_MAP)


def start_input_reader():
    input_queue = queue.Queue()

    def read_lines():
        for line in sys.stdin:
            input_queue.put(line.rstrip("\r\n"))

    threading.Thread(target=read_lines, daemon=True).start()
    return input_queue


def send_line(connection, message):
    connection.sendall(f"{message}\n".encode("utf-8"))


def safe_send(connection, message):
    try:
        send_line(connection, message)
        return True
    except OSError:
        return False


def broadcast(clients, sender_socket, message):
    disconnected = []
    for client_socket in list(clients):
        if sender_socket is not None and client_socket is sender_socket:
            continue
        if not safe_send(client_socket, message):
            disconnected.append(client_socket)
    return disconnected


def remove_client(client_socket, clients, client_buffers, watched_inputs):
    client_name = clients.pop(client_socket, None)
    client_buffers.pop(client_socket, None)
    if client_socket in watched_inputs:
        watched_inputs.remove(client_socket)
    try:
        client_socket.close()
    except OSError:
        pass
    return client_name


def handle_server_input(message, clients, leet_enabled):
    message = message.strip()
    if not message:
        prompt()
        return False, leet_enabled

    if message == LEET_COMMAND:
        leet_enabled = not leet_enabled
        state = "enabled" if leet_enabled else "disabled"
        print(f"\nServer: Leet mode {state}.")
        prompt()
        return False, leet_enabled

    if message == VIRUS_COMMAND:
        disconnected = broadcast(clients, None, VIRUS_SIGNAL)
        for client_socket in disconnected:
            remove_client(client_socket, clients, client_buffers, watched_inputs)
        print("\nServer: Virus payload sent.")
        prompt()
        return False, leet_enabled

    if message == QUIT_COMMAND:
        print("\nServer: Shutting down.")
        return True, leet_enabled

    outgoing_message = to_leetspeak(message) if leet_enabled else message
    disconnected = broadcast(clients, None, f"Server: {outgoing_message}")
    for client_socket in disconnected:
        client_name = remove_client(client_socket, clients, client_buffers, watched_inputs)
        if client_name:
            broadcast(clients, None, f"* {client_name} disconnected.")
    prompt()
    return False, leet_enabled


print("Server: Starting...")
try:
    args = parse_args()
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Server: Socket created.")

    server_address = (args.host, args.port)
    print(f"Server: Binding to {server_address[0]}:{server_address[1]}...")
    server_socket.bind(server_address)

    server_socket.listen()
    print(f"Server: Listening on port {server_address[1]}...")
    print(f"Server: Chat room is live. Type messages anytime. Use {QUIT_COMMAND} to exit.")
    print(f"Server: Use {LEET_COMMAND} to toggle leetspeak for future outgoing messages.")

    watched_inputs = [server_socket]
    input_queue = None
    if os.name == "nt":
        input_queue = start_input_reader()
    else:
        watched_inputs.append(sys.stdin)

    clients = {}
    client_buffers = {}
    client_counter = 0
    leet_enabled = False
    prompt()

    while True:
        readable, _, _ = select.select(watched_inputs, [], [], 0.2)
        should_exit = False

        for source in readable:
            if source is server_socket:
                client_connection, client_address = server_socket.accept()
                client_counter += 1
                client_name = f"Guest-{client_counter}"
                clients[client_connection] = client_name
                client_buffers[client_connection] = ""
                watched_inputs.append(client_connection)
                print(f"\nServer: {client_name} connected from {client_address[0]}:{client_address[1]}")
                safe_send(
                    client_connection,
                    f"* Connected to Wazzap chat room as {client_name}. {QUIT_COMMAND} to leave.",
                )
                prompt()
                continue

            if source is sys.stdin:
                typed_message = sys.stdin.readline()
                if typed_message == "":
                    typed_message = QUIT_COMMAND
                should_exit, leet_enabled = handle_server_input(
                    typed_message,
                    clients,
                    leet_enabled,
                )
                if should_exit:
                    break
                continue

            data_received = source.recv(BUFFER_SIZE)
            if not data_received:
                client_name = remove_client(source, clients, client_buffers, watched_inputs)
                if client_name:
                    print(f"\nServer: {client_name} disconnected.")
                    broadcast(clients, None, f"* {client_name} left the chat.")
                    prompt()
                continue

            receive_buffer = client_buffers[source] + data_received.decode("utf-8")

            while "\n" in receive_buffer:
                message, receive_buffer = receive_buffer.split("\n", 1)
                message = message.rstrip("\r")
                if not message:
                    continue

                client_name = clients.get(source, "Unknown")
                if message.startswith(USERNAME_PREFIX):
                    new_name = message[len(USERNAME_PREFIX):].strip()
                    if new_name:
                        old_name = client_name
                        clients[source] = new_name
                        print(f"\nServer: {old_name} is now {new_name}.")
                        safe_send(source, f"* You are now known as {new_name}.")
                        broadcast(clients, source, f"* {new_name} joined the chat.")
                        prompt()
                    continue

                if message == QUIT_COMMAND:
                    remove_client(source, clients, client_buffers, watched_inputs)
                    print(f"\nServer: {client_name} left the chat.")
                    broadcast(clients, None, f"* {client_name} left the chat.")
                    prompt()
                    break

                if message == VIRUS_SIGNAL:
                    print(f"\nServer: {client_name} triggered /virus.")
                    disconnected = broadcast(clients, source, VIRUS_SIGNAL)
                    for client_socket in disconnected:
                        removed_name = remove_client(client_socket, clients, client_buffers, watched_inputs)
                        if removed_name:
                            broadcast(clients, None, f"* {removed_name} disconnected.")
                    prompt()
                    continue

                print(f"\n{client_name}: {message}")
                disconnected = broadcast(clients, source, f"{client_name}: {message}")
                for client_socket in disconnected:
                    removed_name = remove_client(client_socket, clients, client_buffers, watched_inputs)
                    if removed_name:
                        broadcast(clients, None, f"* {removed_name} disconnected.")
                prompt()

            client_buffers[source] = receive_buffer

        if input_queue is not None:
            while True:
                try:
                    typed_message = input_queue.get_nowait()
                except queue.Empty:
                    break

                should_exit, leet_enabled = handle_server_input(
                    typed_message,
                    clients,
                    leet_enabled,
                )
                if should_exit:
                    break

        if should_exit:
            break

    broadcast(clients, None, "* Server is shutting down.")
    for client_socket in list(clients):
        remove_client(client_socket, clients, client_buffers, watched_inputs)

    server_socket.close()
    print("Server: Server socket closed.")

except socket.error as err:
    print(f"Server: Socket error: {err}")
except Exception as e:
    print(f"Server: An error occurred: {e}")
