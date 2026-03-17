import os
import queue
import select
import socket
import sys
import threading

HOST = "0.0.0.0"
PORT = 9999
BUFFER_SIZE = 1024
QUIT_COMMAND = "/quit"


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
        print(f"\nServer: Connection lost while sending: {err}")
        return True, True

    if message == QUIT_COMMAND:
        try:
            connection.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        print("\nServer: Closing your side of the chat. Waiting for client...")
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

        print(f"\nClient: {message}")
        if message == QUIT_COMMAND:
            print("Server: Client ended the chat.")
            return receive_buffer, True

        if not local_input_closed:
            prompt()

    return receive_buffer, False


print("Server: Starting...")
try:
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Server: Socket created.")

    server_address = (HOST, PORT)
    print(f"Server: Binding to {server_address[0]}:{server_address[1]}...")
    server_socket.bind(server_address)

    server_socket.listen(1)
    print(f"Server: Listening on port {server_address[1]}...")

    client_connection, client_address = server_socket.accept()
    print(f"Server: Connection accepted from {client_address[0]}:{client_address[1]}")
    print(f"Server: Chat is live. Type messages anytime. Use {QUIT_COMMAND} to exit.")

    watched_inputs = [client_connection]
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
            if source is client_connection:
                data_received = client_connection.recv(BUFFER_SIZE)
                if not data_received:
                    print("\nServer: Client disconnected.")
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
                    client_connection,
                    typed_message,
                )
                if local_input_closed:
                    watched_inputs = [client_connection]

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
                    client_connection,
                    typed_message,
                )
                if local_input_closed:
                    input_queue = None
                    watched_inputs = [client_connection]
                    break

                if should_exit:
                    break

        if should_exit:
            break

    client_connection.close()
    print("Server: Client connection closed.")

    server_socket.close()
    print("Server: Server socket closed.")

except socket.error as err:
    print(f"Server: Socket error: {err}")
except Exception as e:
    print(f"Server: An error occurred: {e}")
