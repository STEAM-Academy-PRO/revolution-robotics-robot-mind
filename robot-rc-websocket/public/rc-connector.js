let connecting = false
let device, server;

const liveMessageServiceUUID = 'd2d5558c-5b9d-11e9-8647-d663bd873d93';

const revvyBleWlanServiceUUID = "12345678-1234-5678-1234-56789abcdef0";
const lanIpServiceUUID = '12345678-1234-5678-1234-56789abcdef2';
const wlanCredentialsServiceUUID = '12345678-1234-5678-1234-56789abcdef3'
const networkStatusCharacteristicUUID = '12345678-1234-5678-1234-56789abcdef5';

// I am using this here, so that the old brains are also visible.

async function sendDownWlanCredentials(){
    if (!device) {
        await connectBluetooth()
    }
    try{
        if (device && device.gatt.connected) {

            statusLog('Connected to device, sending WLAN credentials...');

            // Send SSID and password to the BLE device
            const ssid = localStorage.getItem('wifiSsid') || '';
            const password = localStorage.getItem('wifiPassword') || '';

            const credentialsService = await server.getPrimaryService(revvyBleWlanServiceUUID);
            const credentialsCharacteristic = await credentialsService.getCharacteristic(wlanCredentialsServiceUUID);

            // Format: SSID and password separated by a null byte
            const encoder = new TextEncoder();
            const credentialsData = encoder.encode(`${ssid}\0${password}`);
            await credentialsCharacteristic.writeValue(credentialsData);
            statusLog('Sent WiFi credentials over BLE.');
        }
    } catch (err) {
        console.error('Failed to send WLAN credentials:', err);
        error(`Failed to send WLAN credentials.<br> ${err.message} <br>`)
    }
}

async function connectButton(){
    await connectBluetooth();
    if (device && device.gatt.connected) {
        statusLog('Connected to device, getting IP address...');
        await getIp()
    }
}

async function getIp(){
    statusLog('Getting IP address...');
    const service = await server.getPrimaryService(revvyBleWlanServiceUUID);
    const ipCharacteristic = await service.getCharacteristic(lanIpServiceUUID);
    const ipEncoded = await ipCharacteristic.readValue();
    const decoder = new TextDecoder('utf-8');
    const ip = decoder.decode(ipEncoded);

    statusLog(`Your RR Brain's IP is ${ip}, redirecting...`)

    return ip
}

async function connectBluetooth() {
    if (connecting) return; // Prevent multiple clicks
    connecting = true;
    document.getElementById('logo').classList.add('pulse-bg');

    document.getElementById('error').innerHTML = '';

    if (!navigator.bluetooth) {
        document.getElementById('error').innerHTML = 'Bluetooth not supported in this browser.';
        return;
    }
    try {
        statusLog('Connecting to the Brain...');
        device = await navigator.bluetooth.requestDevice({
            filters: [{services: [liveMessageServiceUUID]}],
            optionalServices: [revvyBleWlanServiceUUID]
        });

        server = await device.gatt.connect();

        await subscribeToNetworkStatusChanges();
    } catch (err) {
        // User cancelled or error
        if (err.code === 8){
            statusLog('Cancelled. Click to try again!');
            return
        }
        console.error('Bluetooth connection failed:', err);
        error(`Failed to connect to Bluetooth device.<br> ${err.message} <br>`)
    }
    finally {
        connecting = false;
        document.getElementById('logo').classList.remove('pulse-bg');
    }
}

async function subscribeToNetworkStatusChanges(){
    try{
        const service = await server.getPrimaryService(revvyBleWlanServiceUUID);

        // 3. Get the characteristic with notify
        const characteristic = await service.getCharacteristic(networkStatusCharacteristicUUID);

        // 4. Subscribe to notifications
        await characteristic.startNotifications();
        characteristic.addEventListener('characteristicvaluechanged', (event) => {
            const value = event.target.value;
            const decoder = new TextDecoder('utf-8');
            const status = decoder.decode(value);
            const deviceName = device.name || 'Unknown Device';
            statusLog(`[${deviceName}] ${status}`);
        });
    }
    catch (e){
        error(`Failed to subscribe to network status changes.<br> ${e.message} <br>`);
    }
}

function error(message){
    document.getElementById('error').innerHTML = `
        <div style="color: red; font-size: 1.5rem; text-align: center;">
            <strong>Error:</strong> ${message}
        </div>
    `;
}

function statusLog(message){
    console.log(message);
    document.getElementById('info').innerHTML = message
}

window.addEventListener('DOMContentLoaded', function() {
    // Restore brainId
    const brainId = localStorage.getItem('brainId');
    if (brainId) {
        document.getElementById('brainIdInput').value = brainId;
    }

    // Restore WiFi SSID and password
    const ssid = localStorage.getItem('wifiSsid');
    const pwd = localStorage.getItem('wifiPassword');
    if (ssid) document.getElementById('wifiSsid').value = ssid;
    if (pwd) document.getElementById('wifiPassword').value = pwd;
});

// Save WiFi SSID and password on change
document.getElementById('wifiSsid').addEventListener('input', function(e) {
    localStorage.setItem('wifiSsid', e.target.value);
});
document.getElementById('wifiPassword').addEventListener('input', function(e) {
    localStorage.setItem('wifiPassword', e.target.value);
});

// document.getElementById('brainIdInput').addEventListener('input', function(e) {
//     const val = e.target.value.trim();
//     if (val.length === e.target.maxLength) {
//         localStorage.setItem('brainId', val);
//         window.location.href = `http://${val}-rr.local:8000`;
//     }
// });

document.getElementById('manualConnectBtn').addEventListener('click', function() {
    const input = document.getElementById('brainIdInput');
    const val = input.value.trim();
    if (val) {
        localStorage.setItem('brainId', val);
        window.location.href = `http://${val}-rr.local:8000`;
    }
});

document.getElementById('sendWifiBtn').addEventListener('click', sendDownWlanCredentials);
document.getElementById('connectBtn').addEventListener('click',  connectButton);

document.getElementById('firstTimeSetupBtn').addEventListener('click', function() {
    const toggleContainer = document.getElementById('toggleContainer');
    if (toggleContainer) {
        toggleContainer.style.display = (toggleContainer.style.display === 'none' || !toggleContainer.style.display) ? 'block' : 'none';
    }
})