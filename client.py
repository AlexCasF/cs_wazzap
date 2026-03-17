import argparse
import os
import queue
import select
import socket
import sys
import threading

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9999
BUFFER_SIZE = 1024
QUIT_COMMAND = "/quit"


def parse_args():
    parser = argparse.ArgumentParser(description="Run the Wazzap chat client.")
    parser.add_argument(
        "host",
        nargs="?",
        default=DEFAULT_HOST,
        help="Server IP or hostname to connect to.",
    )
    parser.add_argument(
        "port",
        nargs="?",
        type=int,
        default=DEFAULT_PORT,
        help="Server TCP port to connect to.",
    )
    return parser.parse_args()


def prompt():
    print("You: ", end="", flush=True)


def start_input_reader():
    input_queue = queue.Queue()

    def read_lines():
        for line in sys.stdin:
            input_queue.put(line.rstrip("\r\n"))
        input_queue.put(None)

    threading.Thread(target=read_lines, daemon=True).start()
    return input_queue


def send_message(connection, message):
    connection.sendall(f"{message}\n".encode("utf-8"))


def handle_outgoing_message(connection, message):
    message = message.strip()
    if not message:
        prompt()
        return False, False

    try:
        send_message(connection, message)
    except OSError as err:
        print(f"\nClient: Connection lost while sending: {err}")
        return True, True

    if message == QUIT_COMMAND:
        try:
            connection.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        print("\nClient: Closing your side of the chat. Waiting for server...")
        return True, False

    prompt()
    return False, False


def handle_incoming_data(receive_buffer, data_received, local_input_closed):
    receive_buffer += data_received.decode("utf-8")

    while "\n" in receive_buffer:
        message, receive_buffer = receive_buffer.split("\n", 1)
        message = message.rstrip("\r")
        if not message:
            continue

        print(f"\nServer: {message}")
        if message == QUIT_COMMAND:
            print("Client: Server ended the chat.")
            return receive_buffer, True

        if not local_input_closed:
            prompt()

    return receive_buffer, False


print("Client: Starting...")
try:
    args = parse_args()
    client_socket = socket.socket()
    print("Client: Socket created.")

    server_address = (args.host, args.port)
    print(f"Client: Connecting to {server_address[0]}:{server_address[1]}...")
    client_socket.connect(server_address)
    print("Client: Connected!")
    print(f"Client: Chat is live. Type messages anytime. Use {QUIT_COMMAND} to exit.")

    watched_inputs = [client_socket]
    input_queue = None
    if os.name == "nt":
        input_queue = start_input_reader()
    else:
        watched_inputs.append(sys.stdin)

    receive_buffer = ""
    local_input_closed = False
    prompt()

    while True:
        readable, _, _ = select.select(watched_inputs, [], [], 0.2)
        should_exit = False

        for source in readable:
            if source is client_socket:
                data_received = client_socket.recv(BUFFER_SIZE)
                if not data_received:
                    print("\nClient: Server disconnected.")
                    should_exit = True
                    break

                receive_buffer, should_exit = handle_incoming_data(
                    receive_buffer,
                    data_received,
                    local_input_closed,
                )
            else:
                typed_message = sys.stdin.readline()
                if typed_message == "":
                    typed_message = QUIT_COMMAND
                local_input_closed, should_exit = handle_outgoing_message(
                    client_socket,
                    typed_message,
                )
                if local_input_closed:
                    watched_inputs = [client_socket]

            if should_exit:
                break

        if should_exit:
            break

        if input_queue is not None and not local_input_closed:
            while True:
                try:
                    typed_message = input_queue.get_nowait()
                except queue.Empty:
                    break

                if typed_message is None:
                    typed_message = QUIT_COMMAND

                local_input_closed, should_exit = handle_outgoing_message(
                    client_socket,
                    typed_message,
                )
                if local_input_closed:
                    input_queue = None
                    watched_inputs = [client_socket]
                    break

                if should_exit:
                    break

        if should_exit:
            break

    client_socket.close()
    print("Client: Socket closed.")

except socket.error as err:
    print(f"Client: Failed to connect or send. Is server running? Error: {err}")
except Exception as e:
    print(f"Client: An error occurred: {e}")
