import socket

print("Client: Starting...")
try:
    # Create a socket
    client_socket = socket.socket()
    print("Client: Socket created.")

    # Server address (localhost means this computer) and port
    # This must match the port used by server.py.
    server_address = ("127.0.0.1", 9999)

    print(f"Client: Connecting to {server_address[0]}:{server_address[1]}...")
    # Connect to the server
    client_socket.connect(server_address)
    print("Client: Connected!")

    # Send a message (must be encoded to bytes)
    message = "Hi server!"
    client_socket.sendall(message.encode('utf-8'))
    print(f"Client: Sent: '{message}'")

    # Close the socket
    client_socket.close()
    print("Client: Socket closed.")

except socket.error as err:
    print(f"Client: Failed to connect or send. Is server running? Error: {err}")
except Exception as e:
    print(f"Client: An error occurred: {e}")
