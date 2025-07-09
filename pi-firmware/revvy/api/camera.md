# Raspberry pi camera streaming for Revvy

Hook up WIFI - follow docs.

Restore the package installer:

```bash
sudo mkdir -p /var/lib/dpkg
sudo touch /var/lib/dpkg/status
```

Install dependencies:
```bash
sudo apt install -y raspberrypi-kernel git gcc g++ cmake libjpeg62-turbo-dev libuvc-dev v4l-utils nginx
```

For now, our kernel does not load UVCWebcam module, as we do not have it in production.
That's why we need the `raspberrypi-kernel` to be installed.
(when asked, omit useradd script replacement.)


```bash
git clone https://github.com/jacksonliam/mjpg-streamer.git
cd mjpg-streamer/mjpg-streamer-experimental/

```

We need to have `nginx` wrap the stream around, as we need https.

Create the file

`sudo nano /etc/nginx/sites-available/stream`

Add:

```bash
server {
    listen 8083 ssl;
    server_name _;

    ssl_certificate     /home/pi/cert/cert.pem;
    ssl_certificate_key /home/pi/cert/key.pem;

    location / {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
Then

```bash
sudo ln -s /etc/nginx/sites-available/stream /etc/nginx/sites-enabled/
```

Note that due to logging disabled, I needed to add the following to `serial.sh`:

```bash
sudo mkdir -p /var/lib/nginx/body
sudo mkdir -p /var/log/nginx
sudo systemctl start nginx

```

This way it actually loads on reboot.