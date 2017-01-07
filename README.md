# Simple Multicast Test Tool

For detailed description see: [http://soar.name/tag/multicast](http://soar.name/tag/multicast)

## Usage:

```bash
smt.py [-h] --group GROUP --port PORT [--bind BIND] [--ttl TTL]
```

* `-h`, `--help` - show this help message and exit
* `--group GROUP` - Multicast group to join/send data, for example `224.1.1.1`
* `--port PORT` - Multicast group port to join/send data, for example `12345`
* `--bind BIND` - Bind to IP address (not required), optional, for example `192.168.1.1`
* `--ttl TTL` - TTL for multicast packets, optional, for example `10`
