# Raspberry pi camera streaming for Revvy

Hook up WIFI - follow docs.

Restore the package installer:

```bash
sudo mkdir -p /var/lib/dpkg
sudo touch /var/lib/dpkg/status
```

Install dependencies:
```bash
sudo apt install -y gcc g++ cmake libjpeg62-turbo-dev git libuvc-dev v4l-utils
```


```bash
git clone https://github.com/jacksonliam/mjpg-streamer.git
cd mjpg-streamer/mjpg-streamer-experimental/

```

...or just grab the binary from 