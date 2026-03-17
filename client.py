import socket

HOST = "127.0.0.1"
PORT = 9999
BUFFER_SIZE = 1024
QUIT_COMMAND = "/quit"

print("Client: Starting...")
try:
    client_socket = socket.socket()
    print("Client: Socket created.")

    server_address = (HOST, PORT)
    print(f"Client: Connecting to {server_address[0]}:{server_address[1]}...")
    client_socket.connect(server_address)
    print("Client: Connected!")
    print(f"Client: Type a message and press Enter. Use {QUIT_COMMAND} to exit.")

    while True:
        message = input("You: ").strip()
        if not message:
            print("Client: Empty message not sent.")
            continue

        client_socket.sendall(message.encode("utf-8"))

        if message == QUIT_COMMAND:
            print("Client: Closing chat.")
            break

        data_received = client_socket.recv(BUFFER_SIZE)
        if not data_received:
            print("Client: Server disconnected.")
            break

        response = data_received.decode("utf-8").strip()
        print(f"Server: {response}")

        if response == QUIT_COMMAND:
            print("Client: Server ended the chat.")
            break

    client_socket.close()
    print("Client: Socket closed.")

except socket.error as err:
    print(f"Client: Failed to connect or send. Is server running? Error: {err}")
except Exception as e:
    print(f"Client: An error occurred: {e}")
