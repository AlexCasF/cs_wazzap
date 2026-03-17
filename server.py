import socket

print("Server: Starting...")
try:
    # Create a socket
    server_socket = socket.socket()
    print("Server: Socket created.")

    # Address to listen on ('0.0.0.0' means all available interfaces) and port
    server_address = ("0.0.0.0", 9999)

    print(f"Server: Binding to {server_address[0]}:{server_address[1]}...")
    # Attach the socket to the address and port
    server_socket.bind(server_address)

    # Start listening for incoming connections (allow 1 waiting connection)
    server_socket.listen(1)
    print(f"Server: Listening on port {server_address[1]}...")

    # Wait for a client to connect (this stops the program until connection)
    client_connection, client_address = server_socket.accept()
    print(f"Server: Connection accepted from {client_address[0]}:{client_address[1]}")

    # Receive data (up to 1024 bytes)
    data_received = client_connection.recv(1024)
    # Decode the bytes back into a string
    message = data_received.decode('utf-8')
    print(f"Server: Received: '{message}'")

    # Close the connection with the client
    client_connection.close()
    print("Server: Client connection closed.")

    # Close the server's listening socket
    server_socket.close()
    print("Server: Server socket closed.")

except socket.error as err:
    print(f"Server: Socket error: {err}")
except Exception as e:
    print(f"Server: An error occurred: {e}")