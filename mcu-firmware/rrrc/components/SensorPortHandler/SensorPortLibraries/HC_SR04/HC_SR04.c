#include "HC_SR04.h"
#include <hal_delay.h>
#include <string.h>
#include <math.h>
#include "FreeRTOS.h"

#define HCSR05_MEDIAN_FITLER_SIZE ((uint8_t)3u)
#define OVER_VALID_DISTANCE (1000u)

#define TEST_SENSOR_ON_PORT_STATE_NONE 0
#define TEST_SENSOR_ON_PORT_STATE_WAIT_IRQ 1
#define TEST_SENSOR_ON_PORT_STATE_IRQ_TRIGGERED 2
#define TEST_SENSOR_ON_PORT_TIMEOUT 100

typedef struct
{
    uint16_t start_time;
    uint16_t end_time;
    bool sample_valid;
    uint32_t distanceBuffer[HCSR05_MEDIAN_FITLER_SIZE - 1];
    uint32_t distanceBufferWriteIdx;
} SensorLibrary_HC_SR04_Data_t;

static int hc_sr04_test_sensor_on_port_state = TEST_SENSOR_ON_PORT_STATE_NONE;
static int hc_sr04_test_sensor_on_port_timeout = 0;

static uint32_t _get_cm(uint32_t distance_tick)
{
    float distance_ms = SensorPortHandler_Call_ConvertTicksToMs(distance_tick);

    return (uint32_t)lroundf(distance_ms * 17.0f);
}

static inline void swap_uint32(uint32_t *a, uint32_t *b)
{
    uint32_t t = *a;
    *a = *b;
    *b = t;
}

static uint32_t update_filtered_distance(SensorLibrary_HC_SR04_Data_t *sens_data)
{
    uint32_t distance;
    if (sens_data->sample_valid) {
        uint16_t start = sens_data->start_time;
        uint16_t end = sens_data->end_time;
        distance = end - start;
    } else {
        distance = OVER_VALID_DISTANCE;
    }

    // Copy the previous samples into a temporary buffer
    uint32_t ordered[HCSR05_MEDIAN_FITLER_SIZE];
    memcpy(&ordered[0], &sens_data->distanceBuffer[0], sizeof(sens_data->distanceBuffer));
    ordered[HCSR05_MEDIAN_FITLER_SIZE - 1] = distance;

    sens_data->distanceBuffer[sens_data->distanceBufferWriteIdx] = distance;
    sens_data->distanceBufferWriteIdx = (sens_data->distanceBufferWriteIdx + 1) % ARRAY_SIZE(sens_data->distanceBuffer);

    for (uint32_t i = 0; i < HCSR05_MEDIAN_FITLER_SIZE - 1; i++)
    {
        for (uint32_t j = i + 1; j < HCSR05_MEDIAN_FITLER_SIZE; j++)
        {
            if (ordered[i] > ordered[j])
            {
                swap_uint32(&ordered[i], &ordered[j]);
            }
        }
    }

    return ordered[HCSR05_MEDIAN_FITLER_SIZE / 2];
}

SensorLibraryStatus_t HC_SR04_Load(SensorPort_t *sensorPort)
{
    SensorPortHandler_Call_UpdateStatusSlotSize(4u);

    SensorLibrary_HC_SR04_Data_t *libdata = SensorPortHandler_Call_Allocate(sizeof(SensorLibrary_HC_SR04_Data_t));

    libdata->start_time = 0u;
    libdata->end_time = 0u;
    libdata->sample_valid = false;
    libdata->distanceBufferWriteIdx = 0u;
    memset(&libdata->distanceBuffer[0], 0, sizeof(libdata->distanceBuffer));

    sensorPort->libraryData = libdata;
    SensorPort_SetGreenLed(sensorPort, true);

    SensorPort_SetVccIo(sensorPort, Sensor_VccIo_5V);
    SensorPort_ConfigureGpio0_Output(sensorPort);
    SensorPort_ConfigureGpio1_Interrupt(sensorPort);

    return SensorLibraryStatus_Ok;
}

SensorLibraryUnloadStatus_t HC_SR04_Unload(SensorPort_t* sensorPort)
{
    SensorPort_SetVccIo(sensorPort, Sensor_VccIo_3V3);
    SensorPort_ConfigureGpio0_Input(sensorPort);
    SensorPort_ConfigureGpio1_Input(sensorPort);

    SensorPort_SetOrangeLed(sensorPort, false);
    SensorPort_SetGreenLed(sensorPort, false);
    SensorPortHandler_Call_Free(&sensorPort->libraryData);

    return SensorLibraryUnloadStatus_Done;
}

SensorLibraryStatus_t HC_SR04_Update(SensorPort_t *sensorPort)
{
    SensorLibrary_HC_SR04_Data_t *libdata = (SensorLibrary_HC_SR04_Data_t *)sensorPort->libraryData;

    uint32_t filtered = update_filtered_distance(libdata);
    uint32_t cm = _get_cm(filtered);
    SensorPortHandler_Call_UpdatePortStatus(sensorPort->port_idx, (ByteArray_t){
        .bytes = (uint8_t *)&cm,
        .count = sizeof(cm),
    });

    libdata->sample_valid = false;
    portENTER_CRITICAL();
    SensorPort_SetGpio0_Output(sensorPort, true);
    delay_us(30);
    SensorPort_SetGpio0_Output(sensorPort, false);
    portEXIT_CRITICAL();

    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t HC_SR04_UpdateConfiguration(SensorPort_t *sensorPort, const uint8_t *data, uint8_t size)
{
    (void)sensorPort;
    (void)data;
    (void)size;

    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t HC_SR04_UpdateAnalogData(SensorPort_t *sensorPort, uint8_t rawValue)
{
    (void)sensorPort;
    (void)rawValue;

    return SensorLibraryStatus_Ok;
}

SensorLibraryStatus_t HC_SR04_InterruptCallback(SensorPort_t *sensorPort, bool status)
{
    SensorLibrary_HC_SR04_Data_t *libdata = (SensorLibrary_HC_SR04_Data_t *)sensorPort->libraryData;
    if (status)
    {
        libdata->start_time = SensorPortHandler_Call_ReadCurrentTicks();
    }
    else
    {
        libdata->end_time = SensorPortHandler_Call_ReadCurrentTicks();
        libdata->sample_valid = true;
    }

    SensorPort_SetOrangeLed(sensorPort, status);
    return SensorLibraryStatus_Ok;
}

void HC_SR04_ReadSensorInfo(SensorPort_t *sensorPort, uint8_t page, uint8_t *buffer, uint8_t size, uint8_t *count)
{
    (void)sensorPort;
    (void)page;
    (void)buffer;
    (void)size;

    *count = 0u;
}

static void HC_SR04_test_sensor_callback(void* user_data)
{
    (void)user_data;

    if (hc_sr04_test_sensor_on_port_state == TEST_SENSOR_ON_PORT_STATE_WAIT_IRQ)
    {
        /*
         * When testing sensor presense we are not interested in measuring
         * signal trip time only the fact of it.
         * Also libraryData is not set, so return early.
         */
        hc_sr04_test_sensor_on_port_state = TEST_SENSOR_ON_PORT_STATE_IRQ_TRIGGERED;
    }
}

/*
 * Distance sensor validation routine. This is only possible under conditions.
 * Main of which is some valid obstacle that can bounce of sensor's wave and
 * trigger interrupt. In that case we detect 'sensor is present' status.
 * If timeout is received before interrupt handler is called, we detect
 * 'sensor presense unknown' status, as we can not reliably tell if sensor
 * is absent or there is no solid obstacle in front of the robot.
 * Returns true if test is done and result holds outcome of validation logic
 * Returns false if test is not finished yet.
 */
static bool HC_SR04_TestSensorOnPort(SensorPort_t *sensorPort, SensorOnPortStatus_t *result)
{
  if (hc_sr04_test_sensor_on_port_state == TEST_SENSOR_ON_PORT_STATE_NONE)
  {
    hc_sr04_test_sensor_on_port_state = TEST_SENSOR_ON_PORT_STATE_WAIT_IRQ;
    SensorPort_SetGreenLed(sensorPort, true);
    SensorPort_SetVccIo(sensorPort, Sensor_VccIo_5V);
    SensorPort_ConfigureGpio0_Output(sensorPort);

    portENTER_CRITICAL();
    SensorPort_ConfigureGpio1_CustomInterrupt(sensorPort,
        HC_SR04_test_sensor_callback);

    /*
     * After configuring gpio1 to INPUT/INTERRUPT, we should immediately clear
     * pending interrupts. Here is why:
     * - EIC->CONFIG.SENSE is setup as edge-triggered (both ways)
     * - If gpio pin level is low, EIC does not detect edge-trigger
     * - If gpio pin is high, EIC will detect low-to-high trigger and
     *   will set an interrupt
     * - This interrupt will trigger execution of HC_SR04_test_sensor_callback
     *   right after portEXIT_CRITICAL, which will break the detection logic
     * - To see this - observe EIC->INTFLAG and NVIC->ISPR on debug of this code
     */
    SensorPort_ConfigureGpio1_ClearPendingInterrupt(sensorPort);

    if (SensorPort_Read_Gpio1(sensorPort))
    {
      /* Normally gpio1 should not be 1 on a distance sensor, so it's not it */
      *result = SensorOnPortStatus_NotPresent;
      portEXIT_CRITICAL();
      goto test_completed;
    }

    /*
     * Fire a distance ray according to datasheet and wait for interrupt on gpio1
     * pin
     */
    SensorPort_SetGpio0_Output(sensorPort, true);
    delay_us(30);
    SensorPort_SetGpio0_Output(sensorPort, false);
    hc_sr04_test_sensor_on_port_timeout = 100;
    portEXIT_CRITICAL();
    return false;
  }

  if (hc_sr04_test_sensor_on_port_state == TEST_SENSOR_ON_PORT_STATE_WAIT_IRQ)
  {
    if (!hc_sr04_test_sensor_on_port_timeout)
    {
        /* timeout has passed, ray not returned */
        *result = SensorOnPortStatus_Unknown;
        goto test_completed;
    }

    hc_sr04_test_sensor_on_port_timeout--;
  }
  else
  {
    /* state is TEST_SENSOR_ON_PORT_STATE_IRQ_TRIGGERED */
    *result = SensorOnPortStatus_Present;
    goto test_completed;
  }

  /* test not completed */
  return false;

test_completed:
  portENTER_CRITICAL();

  SensorPort_SetVccIo(sensorPort, Sensor_VccIo_3V3);
  SensorPort_ConfigureGpio0_Input(sensorPort);
  SensorPort_ConfigureGpio1_Input(sensorPort);
  SensorPort_SetGreenLed(sensorPort, false);

  hc_sr04_test_sensor_on_port_state = TEST_SENSOR_ON_PORT_STATE_NONE;
  portEXIT_CRITICAL();
  /* test is done */
  return true;
}

const SensorLibrary_t sensor_library_hc_sr04 = {
    .Name                = "HC_SR04",
    .Load                = &HC_SR04_Load,
    .Unload              = &HC_SR04_Unload,
    .Update              = &HC_SR04_Update,
    .UpdateConfiguration = &HC_SR04_UpdateConfiguration,
    .UpdateAnalogData    = &HC_SR04_UpdateAnalogData,
    .InterruptHandler    = &HC_SR04_InterruptCallback,
    .ReadSensorInfo      = &HC_SR04_ReadSensorInfo,
    .TestSensorOnPort    = &HC_SR04_TestSensorOnPort
};
