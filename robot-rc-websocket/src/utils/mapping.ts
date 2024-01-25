
export function mapAnalogNormal(val: number) {
    return mapValue(val, -1, 1, 0, 255)
}

export function mapValue(value: number, inMin: number, inMax: number, outMin: number, outMax: number) {
    // Map the value from the input range to the output range
    const mappedValue = (value - inMin) * (outMax - outMin) / (inMax - inMin) + outMin;

    // Round the mapped value
    return Math.floor(mappedValue);
}

export function clamp(value: number, min: number, max: number): number {
    return Math.min(Math.max(value, min), max);
}


export function toByte(boolArray: boolean[]) {
    let byteValue = 0;
    for (let i = 0; i < 8; i++) {
        // Use bitwise OR to set the bit at the i-th position if the boolean is true
        byteValue |= (boolArray[i] ? 1 : 0) << i;
    }
    return byteValue
}