#include <atmel_start.h>

static void enable_brownout_detector(void)
{
    // We can maybe write the NVM user row to auto-enable the brown-out detector.
    // The user row can be erased but a power-off event will leave it in inconsistent state, so
    // these modifications should not be done in runtime, but by external tools that can back the
    // values up first. Maybe we can make this part of the factory setup.
    // For now, we just enable the brown-out detector here.

    // Set up BOD and wait for power supply to settle
    // Disable BOD33 before changing the configuration
    SUPC->BOD33.bit.ENABLE = 0;
    while (!SUPC->STATUS.bit.B33SRDY) {};

    // Datasheet 19.8.5, 3.3V Brown-Out Detector (BOD33) Control:
    // VBOD- = 1.5 + LEVEL[7:0] x VBOD33_LEVEL_STEP
    // VBOD+ = VBOD- + N x VBOD33_HYST_STEP

    // According to datasheet, Table 54-19:
    // VBOD33_LEVEL_STEP = 6mV
    // VBOD33_HYST_STEP = 6mV

    // Requirement: VBOD33(max): LEVEL[7:0] value < 255 - HYST[3:0]
    // To set a 300mV hysteresis: HYST*6 = 300 -> HYST = 300/6 = 50
    // Hysteresis limits the max LEVEL to 205. 205 gives us
    // VBOD- = 1500 + 205*6 = 2730 mV
    // VBOD+ = VBOD- + HYST = 3030 mV

    SUPC->BOD33.reg = (
        // Set BOD threshold level (BOD33.LEVEL)
        SUPC_BOD33_LEVEL(205) |
        // Set BOD hysteresis level (BOD33.HYST)
        SUPC_BOD33_HYST(50) |
        // Enable in Standby mode (configured to normal mode)
        SUPC_BOD33_STDBYCFG |
        // Select no action while we wait for the voltage to settle
        SUPC_BOD33_ACTION_NONE
    );

    // Enable BOD33
    SUPC->BOD33.bit.ENABLE = 1;
    while (!SUPC->STATUS.bit.BOD33RDY) {};

    // Wait for voltage to settle. BOD33DET is set to 0 when the voltage is above the threshold.
    while (SUPC->STATUS.bit.BOD33DET) {}

    // Set up BOD to reset if supply voltage drops
    SUPC->BOD33.bit.ENABLE = 0;
    while (!SUPC->STATUS.bit.B33SRDY) {};

    SUPC->BOD33.reg |= SUPC_BOD33_ACTION_RESET;
    SUPC->BOD33.bit.ENABLE = 1;

    // We don't have to wait for synchronization here as we are not planning to write more bits
}

/**
 * Initializes MCU, drivers and middleware in the project
 **/
void atmel_start_init(void)
{
    enable_brownout_detector();
    system_init();
}
