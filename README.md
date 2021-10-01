# TuxPay

#### Manual Installation

Install system dependencies

```
sudo apt install python3-pip libsecp256k1-dev npm wkhtmltopdf
```

Optionally install `tor` to connect to .onion electrumx servers.

Create virtual environment & Install dependencies. Note that sqlite is installed by default, but if you are using an
external database server you will need to install the appropriate RDBMS package separately,
e.g. `pip3 install databases[mysql]` or `databases[postgresql]`

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Build the JS SDK

```
cd sdk
npm install
npm run build
cd ..
```

Build the Admin front-end

```
cd admin
npm install
npm run generate
cd ..
```

Run the initial setup wizard (this generates all of the wallet roots and sets up currencies - rerun the wizard to
change/overwrite the existing config)

```
python3 setup.py
```

To set up the system service you will first need to edit `tuxpay.service` and fill out the templated fields with the
path of the install location. The specified user needs to have read access of the directory (and write access to at
least the `data` folder), so permissions will need to be set appropriately, or the `user` will need to be changed.

```
cp tuxpay.service /etc/systemd/system/tuxpay.service
sudo systemctl daemon-reload
sudo service tuxpay enable && sudo service tuxpay start
```

#### Installation (docker)

```
# Builds container
docker-compose build

# Runs the setup script - see the configuration file for additional options afterwards
docker run -it -v "[ABSOLUTE PATH TO ./data/]:/tuxpay/data/" tuxpay python3 setup.py

# Runs the container as a service (will auto-restart as long as docker daemon is running)
docker-compose up -d 
```