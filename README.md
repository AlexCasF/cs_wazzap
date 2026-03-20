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
python client.py 192.168.106.128 9999
```

4. Type messages in either terminal.
5. Use `/quit` to close the chat cleanly.

## Notes

- The server listens on all network interfaces by default.
- The client defaults to `127.0.0.1 9999` if you do not provide arguments.
- On Linux and Kali, the app uses `select` with both the socket and `stdin`.
- On Windows, console `stdin` is not directly selectable, so a small input thread is used while `select` still handles the socket.

## Project Summary

### What the App Does

Wazzap is a terminal-based chat application built with Python sockets. The server runs on the Kali VM and listens for one client connection, while the client runs on the Windows host machine and connects to the server using either the Kali IP address or a Pinggy TCP tunnel. Both sides can send and receive messages in real time.

### Pinggy Setup

Pinggy TCP tunneling worked at the beginning of testing and allowed the client to connect to the Kali-hosted server over the internet. After the initial success, later attempts were inconsistent because the server only handles one client session at a time and has to be restarted after each completed chat. For this report, no Pinggy screenshot is included.

### Features Added

- Real-time two-way chat using Python sockets
- Simultaneous send and receive behavior using `select`
- Configurable host and port arguments for both server and client
- `/quit` command for a clean shutdown
- `/leet` command to toggle leetspeak for future outgoing messages
- `/virus` command to trigger a prank warning screen and glitch animation on the other side

### What I Learned and Challenges I Overcame

- I learned how client/server socket communication works in Python.
- I learned how to use `select` so the chat can send and receive without blocking.
- I learned how to connect a host machine to a Kali VM over a local network using the VM's IP address.
- I learned how to use `scp` to copy files from Windows to Kali and how to expose a local TCP service with Pinggy.
- One challenge was that the client and server initially had mismatched ports, which prevented them from connecting.
- Another challenge was that Windows console input does not behave the same way as Linux `stdin` with `select`, so the program needed a small compatibility fallback.
- Pinggy testing was also tricky because the current server accepts one client session and then exits, which means the server must be restarted before reconnecting.
