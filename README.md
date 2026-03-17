# Wazzap

Simple terminal chat app built with Python sockets.

## Run Locally

Start the server:

```bash
python server.py
```

Start the client in another terminal:

```bash
python client.py 127.0.0.1 9999
```

## Test Between Host and Kali

1. On Kali, find the IP address:

```bash
ip addr show
```

or

```bash
hostname -I
```

2. On Kali, start the server:

```bash
python3 server.py 0.0.0.0 9999
```

3. On your host machine, connect with the Kali IP:

```bash
python client.py <KALI_IP> 9999
```

4. Type messages in either terminal.
5. Use `/quit` to close the chat cleanly.

## Notes

- The server listens on all network interfaces by default.
- The client defaults to `127.0.0.1 9999` if you do not provide arguments.
- On Linux and Kali, the app uses `select` with both the socket and `stdin`.
- On Windows, console `stdin` is not directly selectable, so a small input thread is used while `select` still handles the socket.
