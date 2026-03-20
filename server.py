import argparse
import os
import queue
import random
import select
import shutil
import socket
import sys
import threading
import time

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 9999
BUFFER_SIZE = 1024
QUIT_COMMAND = "/quit"
LEET_COMMAND = "/leet"
VIRUS_COMMAND = "/virus"
CONTROL_PREFIX = "__CTRL__:"
VIRUS_SIGNAL = f"{CONTROL_PREFIX}VIRUS"

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
    print("You: ", end="", flush=True)


def to_leetspeak(message):
    return message.translate(LEET_MAP)


def clear_screen():
    print("\033[2J\033[H", end="", flush=True)


def glitch_text(text):
    glitch_chars = "@#$%&*?!~=+<>/\\|[]{};:.,^_"
    mojibake_chars = "XO01Il/\\\\[]{}<>~^_-+="
    transformed = []

    for char in text:
        roll = random.random()
        if char != " " and roll < 0.18:
            transformed.append("")
        elif char != " " and roll < 0.52:
            transformed.append(random.choice(glitch_chars))
        elif char != " " and roll < 0.72:
            transformed.append(random.choice(mojibake_chars))
        else:
            transformed.append(char)

    return "".join(transformed)


def run_virus_effect(remote_label):
    width = shutil.get_terminal_size((80, 24)).columns
    messages = [
        "SYSTEM BREACH DETECTED",
        "BOOT SECTOR CORRUPTED",
        "ENCRYPTING CHAT LOGS",
        "SCRAMBLING MEMORY",
        "PAYLOAD DEPLOYED",
        "SIGNAL INJECTION",
        "TERMINAL MELTDOWN",
        "RECOVERING FRAGMENTS",
    ]

    end_time = time.time() + 10
    while time.time() < end_time:
        clear_screen()
        print(glitch_text("!!! WAZZAP VIRUS ALERT !!!").center(width))
        print()

        for _ in range(8):
            print(glitch_text(random.choice(messages)).center(width))

        print()
        print(glitch_text(f"{remote_label} infected your terminal").center(width))
        time.sleep(0.08)

    clear_screen()
    print("Terminal recovered.")


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


def handle_outgoing_message(connection, message, leet_enabled):
    message = message.strip()
    if not message:
        prompt()
        return False, False, leet_enabled

    if message == LEET_COMMAND:
        leet_enabled = not leet_enabled
        state = "enabled" if leet_enabled else "disabled"
        print(f"\nServer: Leet mode {state}.")
        prompt()
        return False, False, leet_enabled

    if message == VIRUS_COMMAND:
        try:
            send_message(connection, VIRUS_SIGNAL)
        except OSError as err:
            print(f"\nServer: Connection lost while sending: {err}")
            return True, True, leet_enabled
        print("\nServer: Virus payload sent.")
        prompt()
        return False, False, leet_enabled

    outgoing_message = to_leetspeak(message) if leet_enabled and message != QUIT_COMMAND else message

    try:
        send_message(connection, outgoing_message)
    except OSError as err:
        print(f"\nServer: Connection lost while sending: {err}")
        return True, True, leet_enabled

    if message == QUIT_COMMAND:
        try:
            connection.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        print("\nServer: Closing your side of the chat. Waiting for client...")
        return True, False, leet_enabled

    prompt()
    return False, False, leet_enabled


def handle_incoming_data(receive_buffer, data_received, local_input_closed):
    receive_buffer += data_received.decode("utf-8")

    while "\n" in receive_buffer:
        message, receive_buffer = receive_buffer.split("\n", 1)
        message = message.rstrip("\r")
        if not message:
            continue

        if message == VIRUS_SIGNAL:
            print("\nClient: Triggered /virus.")
            run_virus_effect("Client")
            if not local_input_closed:
                prompt()
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
    args = parse_args()
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Server: Socket created.")

    server_address = (args.host, args.port)
    print(f"Server: Binding to {server_address[0]}:{server_address[1]}...")
    server_socket.bind(server_address)

    server_socket.listen(1)
    print(f"Server: Listening on port {server_address[1]}...")

    client_connection, client_address = server_socket.accept()
    print(f"Server: Connection accepted from {client_address[0]}:{client_address[1]}")
    print(f"Server: Chat is live. Type messages anytime. Use {QUIT_COMMAND} to exit.")
    print(f"Server: Use {LEET_COMMAND} to toggle leetspeak for future outgoing messages.")
    print(f"Server: Use {VIRUS_COMMAND} to prank the other side for 10 seconds.")

    watched_inputs = [client_connection]
    input_queue = None
    if os.name == "nt":
        input_queue = start_input_reader()
    else:
        watched_inputs.append(sys.stdin)

    receive_buffer = ""
    local_input_closed = False
    leet_enabled = False
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
                local_input_closed, should_exit, leet_enabled = handle_outgoing_message(
                    client_connection,
                    typed_message,
                    leet_enabled,
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

                local_input_closed, should_exit, leet_enabled = handle_outgoing_message(
                    client_connection,
                    typed_message,
                    leet_enabled,
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
