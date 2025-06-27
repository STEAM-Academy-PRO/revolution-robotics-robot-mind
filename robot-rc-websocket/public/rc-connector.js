let connecting = false
let device, server, ip = localStorage.getItem('brainIp') || null;

const liveMessageServiceUUID = 'd2d5558c-5b9d-11e9-8647-d663bd873d93';

const revvyBleWlanServiceUUID = "12345678-1234-5678-1234-56789abcdef0";
const lanIpServiceUUID = '12345678-1234-5678-1234-56789abcdef2';
const wlanCredentialsServiceUUID = '12345678-1234-5678-1234-56789abcdef3'
const networkStatusCharacteristicUUID = '12345678-1234-5678-1234-56789abcdef5';

const connectButton = document.getElementById('connectBtn');
const manualConnectBtn = document.getElementById('manualConnectBtn');
const PORT_SSL = 8433

const wifiCredentials = JSON.parse(localStorage.getItem('wifiCredentialsList') || '{}');

async function sendDownWlanCredentials(ssid){
    if (!device) {
        if (!await connectBluetooth()){
            statusLog('Cancelled.')
            return;
        }
    }
    try{
        if (device) {
            statusLog('Connected to device, sending WLAN credentials...');

            // Send SSID and password to the BLE device
            const ssid = document.getElementById('wifiSsid').value.trim();
            const password = document.getElementById('wifiPassword').value.trim();

            wifiCredentials[ssid] = password;
            localStorage.setItem('wifiCredentialsList', JSON.stringify(wifiCredentials));

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

async function connectButtonHandler(){
    // If we're already connected and have a  valid IP, navigate to the brain.
    if (device && device.gatt.connected && ip) {
        return navigateToBrainRcButton(ip);
    }

    // Otherwise, try to connect.
    await connectBluetooth();

    if (device && device.gatt.connected) {
        statusLog('Connected to device, getting IP address...');
        ip = await getIp();
        if (ip) {
            statusLog(`Your RR Brain's IP is ${ip}. Click again to open remote!`);
            manualConnectBtn.innerHTML = `
                <span class="brain-id">Open RC of ${device.name || 'unknown-brain'}...</span>
            `;
            manualConnectBtn.onclick = () => navigateToBrainRcButton(ip);
        }
    }
}

async function subscribeToIpChanges() {
    try {
        const service = await server.getPrimaryService(revvyBleWlanServiceUUID);
        const ipCharacteristic = await service.getCharacteristic(lanIpServiceUUID);
        await ipCharacteristic.startNotifications();
        console.log('Subscribed to IP address changes');
        ipCharacteristic.addEventListener('characteristicvaluechanged', (event) => {
            const value = event.target.value;
            const decoder = new TextDecoder('utf-8');
            const newIp = decoder.decode(value);
            localStorage.setItem('brainIp', newIp);
            statusLog(`IP address changed to: ${newIp}`);
            ip = newIp;

            // Update the manual connect button
            const brainId = device.name || 'unknown-brain';
            manualConnectBtn.innerHTML = `
                <span class="brain-id">Open RC of ${brainId}...</span>
                `
        });
    } catch (err) {
        console.error('Failed to subscribe to IP changes:', err);
        error(`Failed to subscribe to IP changes.<br> ${err.message} <br>`);
    }
}

function createConnectToPreviousWifiButtons(){
    if (Object.keys(wifiCredentials).length) {
        document.getElementById('previous-wifi-access-points').innerHTML = `
        <h3>Connect to previous WiFi access points:</h3><div id="previous-wifi-access-point-buttons"></div>`;
    }

    Object.keys(wifiCredentials).forEach(ssid => {
        const button = document.createElement('button');
        button.className = 'btn2';
        button.innerHTML = ssid;
        button.onclick = async () => {
            document.getElementById('wifiSsid').value = ssid;
            document.getElementById('wifiPassword').value = wifiCredentials[ssid];
            await sendDownWlanCredentials();
            await getIp();
        };
        document.getElementById('previous-wifi-access-point-buttons').append(button);
    })
}

async function getIpAsync(ipCharacteristic) {
    const ipEncoded = await ipCharacteristic.readValue();
    const decoder = new TextDecoder('utf-8');
    return decoder.decode(ipEncoded);
}

async function getIp(){
    statusLog('Getting IP address...');

    const service = await server.getPrimaryService(revvyBleWlanServiceUUID);
    const ipCharacteristic = await service.getCharacteristic(lanIpServiceUUID);

    ip = await getIpAsync(ipCharacteristic);

    localStorage.setItem('brainIp', ip);


    statusLog(`Your RR Brain's IP is ${ip}. Click again to open remote!`)

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

        localStorage.setItem('brainId', device.name);

        await subscribeToNetworkStatusChanges();
        await subscribeToIpChanges();
        document.getElementById('logo').classList.add('connected');
        return true;
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
    console.warn(message);
    document.getElementById('info').innerHTML = message
}

async function navigateToBrainRcButton(brainIp){
    brainIp = brainIp || ip;
    if (device){
        await device.gatt.disconnect();
        device = null;
    }
    location.href = `https://${brainIp}:${PORT_SSL}?address=${brainIp}`;
}

window.addEventListener('DOMContentLoaded', function() {
    // Restore brainId
    // const brainId = localStorage.getItem('brainId');
    // if (brainId) {
    //     document.getElementById('brainIdInput').value = brainId;
    // }

    // Restore WiFi SSID and password
    const ssid = localStorage.getItem('wifiSsid');
    const pwd = localStorage.getItem('wifiPassword');
    if (ssid) document.getElementById('wifiSsid').value = ssid;
    if (pwd) document.getElementById('wifiPassword').value = pwd;

    // I am using this here, so that the old brains are also visible.
    if (ip){
        document.getElementById('lastBrain').innerHTML = `
            <button class="btn2" id="manualConnectBtn" onclick="navigateToBrainRcButton()">
                Open RC of
                <span class="brain-id">${localStorage.getItem('brainId') || 'Unknown Brain'}</span>
                ...
            </button>
        `;
    }

    createConnectToPreviousWifiButtons()
});

// Save WiFi SSID and password on change
document.getElementById('wifiSsid').addEventListener('input', function(e) {
    localStorage.setItem('wifiSsid', e.target.value);
});
document.getElementById('wifiPassword').addEventListener('input', function(e) {
    localStorage.setItem('wifiPassword', e.target.value);
});

document.getElementById('sendWifiBtn').addEventListener('click', sendDownWlanCredentials);
document.getElementById('connectBtn').addEventListener('click',  connectButtonHandler);

document.getElementById('firstTimeSetupBtn').addEventListener('click', function() {
    const toggleContainer = document.getElementById('toggleContainer');
    if (toggleContainer) {
        toggleContainer.style.display = (toggleContainer.style.display === 'none' || !toggleContainer.style.display) ? 'block' : 'none';
    }
})