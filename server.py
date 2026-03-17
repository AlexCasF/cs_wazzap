import socket

HOST = "0.0.0.0"
PORT = 9999
BUFFER_SIZE = 1024
QUIT_COMMAND = "/quit"

print("Server: Starting...")
try:
    # Create a socket and allow quick restarts while we are testing.
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
    print(f"Server: Type a reply after each client message. Use {QUIT_COMMAND} to exit.")

    while True:
        data_received = client_connection.recv(BUFFER_SIZE)
        if not data_received:
            print("Server: Client disconnected.")
            break

        message = data_received.decode("utf-8").strip()
        print(f"Client: {message}")

        if message == QUIT_COMMAND:
            print("Server: Client ended the chat.")
            break

        reply = input("You: ").strip()
        if not reply:
            print("Server: Empty message not sent.")
            continue

        client_connection.sendall(reply.encode("utf-8"))

        if reply == QUIT_COMMAND:
            print("Server: Closing chat.")
            break

    client_connection.close()
    print("Server: Client connection closed.")

    server_socket.close()
    print("Server: Server socket closed.")

except socket.error as err:
    print(f"Server: Socket error: {err}")
except Exception as e:
    print(f"Server: An error occurred: {e}")
