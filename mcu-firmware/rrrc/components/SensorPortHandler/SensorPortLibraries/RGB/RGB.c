#include "RGB.h"
#include "utils.h"
#include "CommonLibraries/color.h"
#include <hal_delay.h>
#include <string.h>

/*
----------------------------
|  nono  |  I2C0  |  nono  |
|  nono  |  LED0  |  nono  |
----------------------------
|  I2C2  |  I2C3  |  I2C1  |
|  LED2  |  LED3  |  LED1  |
----------------------------
*/

typedef struct
{
    uint16_t clear;
    uint16_t red;
    uint16_t green;
    uint16_t blue;
    uint16_t ir;
} veml3328_colors_t;

typedef struct
{
    int32_t R;
    int32_t G;
    int32_t B;
} color_coef_t;

typedef enum
{
    SENS_STATE_RESET = 0,
    SENS_STATE_OPERATIONAL,
    SENS_STATE_ERROR,
    SENS_STATE_STOP,
} sensor_state_t;

typedef enum
{
    SENS_DEINIT_STATE_NONE = 0,
    SENS_DEINIT_STATE_IN_PROGRESS,
    SENS_DEINIT_STATE_COMPLETED,
    SENS_DEINIT_STATE_ERROR
} deinit_state_t;

typedef enum
{
    I2C_DIR_RAW_WRITE = 0,
    I2C_DIR_RAW_READ_CONTINUE,
} i2c_direction_t;

typedef enum
{
    COLOR_SENSOR_TEST_STATE_NONE = 0,
    COLOR_SENSOR_TEST_STATE_I2C_READ,
    COLOR_SENSOR_TEST_STATE_DONE,
} color_sensor_test_state_t;

typedef struct
{
    i2c_direction_t dir;
    uint8_t address;
    uint8_t data_sz;
    uint8_t* data;
} i2c_command_t;

typedef struct {
    sensor_state_t state;
    deinit_state_t deinit_state;
    uint8_t sequence_idx;
    uint8_t deinit_num_retries;
    uint8_t orange_led;
    color_sensor_test_state_t test_state;
    SensorOnPortStatus_t test_result;
    bool transferring;
    color_coef_t coef;
    veml3328_colors_t sens_color[4];
    i2c_command_t readcolor_sequence[28];
} SensorLibrary_RGB_Data_t;

static void i2c_txrx_complete(I2CMasterInstance_t* instance, size_t transferred);
static void rgb_read_sensor(SensorPort_t* sensorPort);
static void rgb_init_sensor(SensorPort_t* sensorPort);

#define DEFAULT_COEF_R (210)
#define DEFAULT_COEF_G (140)
#define DEFAULT_COEF_B (280)

#define SENS_DEINIT_MAX_RETRIES 5
/* I2C device addresses, left shifted to include the R/W bit */
#define	VEML3328_ADDR            (0x10 << 1)
#define PCA9633TK_ADDR           (0x62 << 1)
#define PCA9546APW_ADDR          (0x70 << 1)

/* veml3328 command code */
#define	VEML3328_CONF            0x00
#define VEML3328_R_DATA          0x05
#define VEML3328_G_DATA          0x06
#define VEML3328_B_DATA          0x07
#define VEML3328_C_DATA	         0x04
#define VEML3328_IR_DATA         0x08

#define VEML3328_CONF_AF         (1 << 3)
#define VEML3328_CONF_TRIG       (1 << 2)
#define VEML3328_CONF_SENS_LOW   (1 << 6)
#define VEML3328_CONF_IT_50MS    (0 << 4)
#define VEML3328_CONF_IT_100MS   (1 << 4)
#define VEML3328_CONF_IT_200MS   (2 << 4)
#define VEML3328_CONF_IT_400MS   (3 << 4)

#define VEML3328_CONF_DG_X1      (0 << 12)
#define VEML3328_CONF_DG_X2      (1 << 12)
#define VEML3328_CONF_DG_X4      (2 << 12)

#define VEML3328_CONF_GAIN_HALF  (3 << 10)
#define VEML3328_CONF_GAIN_X1    (0 << 10)
#define VEML3328_CONF_GAIN_X2    (1 << 10)
#define VEML3328_CONF_GAIN_X4    (2 << 10)

#define VEML3328_CONF_INIT   (VEML3328_CONF_IT_50MS | VEML3328_CONF_SENS_LOW | VEML3328_CONF_DG_X1 | VEML3328_CONF_GAIN_X1)
#define VEML3328_CONF_DEINIT ((uint16_t)0x8001u)

static uint8_t pca9633tk_init_sequence[] =
{
    0x91, /* PCA9633TK_REG_MODE1      */
    0x01, /* PCA9633TK_REG_MODE2      */
    0x5A, /* PCA9633TK_REG_PWM0       */
    0x5A, /* PCA9633TK_REG_PWM1       */
    0x5A, /* PCA9633TK_REG_PWM2       */
    0x5A, /* PCA9633TK_REG_PWM3       */
    0xFF, /* PCA9633TK_REG_GRPPWM     */
    0x00, /* PCA9633TK_REG_GRPFREQ    */
    0xAA, /* PCA9633TK_REG_LEDOUT     */
    0xE2, /* PCA9633TK_REG_SUBADR1    */
    0xE4, /* PCA9633TK_REG_SUBADR2    */
    0xE8, /* PCA9633TK_REG_SUBADR3    */
    0xE0, /* PCA9633TK_REG_ALLCALLADR */
    0x81, /* PCA9633TK_REG_MODE1      */
};

static uint8_t pca9633tk_deinit_sequence[] =
{
    0x91, /* PCA9633TK_REG_MODE1 */
    0x02, /* PCA9633TK_REG_MODE2 */
    0x00, /* PCA9633TK_REG_PWM0  */
    0x00, /* PCA9633TK_REG_PWM1  */
    0x00, /* PCA9633TK_REG_PWM2  */
    0x00, /* PCA9633TK_REG_PWM3  */
};

static uint8_t PCA9546_port_0   = 1 << 0;
static uint8_t PCA9546_port_1   = 1 << 1;
static uint8_t PCA9546_port_2   = 1 << 2;
static uint8_t PCA9546_port_3   = 1 << 3;
static uint8_t PCA9546_port_off = 0;

#define PORT_SWITCH(port) { .dir = I2C_DIR_RAW_WRITE, .address = PCA9546APW_ADDR, .data = &PCA9546_port_##port, .data_sz = 1 }

static uint8_t veml3328_init_sequence[3]   = { VEML3328_CONF, VEML3328_CONF_INIT   & 0xFF, VEML3328_CONF_INIT   >> 8 };
static uint8_t veml3328_deinit_sequence[3] = { VEML3328_CONF, VEML3328_CONF_DEINIT & 0xFF, VEML3328_CONF_DEINIT >> 8 };

#define INIT_PORT()   { .dir = I2C_DIR_RAW_WRITE, .address = VEML3328_ADDR,   .data = &veml3328_init_sequence[0],   .data_sz = ARRAY_SIZE(veml3328_init_sequence) }
#define DEINIT_PORT() { .dir = I2C_DIR_RAW_WRITE, .address = VEML3328_ADDR,   .data = &veml3328_deinit_sequence[0], .data_sz = ARRAY_SIZE(veml3328_deinit_sequence) }

static uint8_t VEML3328_colorR = VEML3328_R_DATA;
static uint8_t VEML3328_colorG = VEML3328_G_DATA;
static uint8_t VEML3328_colorB = VEML3328_B_DATA;

#define READ_PORT(port) \
    { .dir = I2C_DIR_RAW_WRITE,         .address=VEML3328_ADDR, .data = &VEML3328_colorR, .data_sz = 1 }, \
    { .dir = I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR, .data = NULL,             .data_sz = 2 }, \
    { .dir = I2C_DIR_RAW_WRITE,         .address=VEML3328_ADDR, .data = &VEML3328_colorG, .data_sz = 1 }, \
    { .dir = I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR, .data = NULL,             .data_sz = 2 }, \
    { .dir = I2C_DIR_RAW_WRITE,         .address=VEML3328_ADDR, .data = &VEML3328_colorB, .data_sz = 1 }, \
    { .dir = I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR, .data = NULL,             .data_sz = 2 }

static const i2c_command_t init_sequence[] =
{
    PORT_SWITCH(0),
    INIT_PORT(),
    PORT_SWITCH(1),
    INIT_PORT(),
    PORT_SWITCH(2),
    INIT_PORT(),
    PORT_SWITCH(3),
    INIT_PORT(),

    { .dir = I2C_DIR_RAW_WRITE, .address = PCA9633TK_ADDR,  .data = pca9633tk_init_sequence,    .data_sz = ARRAY_SIZE(pca9633tk_init_sequence) },
};

static const i2c_command_t deinit_sequence[] =
{
    PORT_SWITCH(0),
    DEINIT_PORT(),
    PORT_SWITCH(1),
    DEINIT_PORT(),
    PORT_SWITCH(2),
    DEINIT_PORT(),
    PORT_SWITCH(3),
    DEINIT_PORT(),
    PORT_SWITCH(off),

    { .dir = I2C_DIR_RAW_WRITE, .address = PCA9633TK_ADDR,  .data = pca9633tk_deinit_sequence, .data_sz = ARRAY_SIZE(pca9633tk_deinit_sequence)},
};

static const i2c_command_t readcolors_sequence[] =
{
    PORT_SWITCH(0),
    READ_PORT(),
    PORT_SWITCH(1),
    READ_PORT(),
    PORT_SWITCH(2),
    READ_PORT(),
    PORT_SWITCH(3),
    READ_PORT(),
};

static bool execute_i2c_command(SensorPort_t* sensorPort, const i2c_command_t* command)
{
    SensorPort_I2C_Status_t i2c_status = SensorPort_I2C_Error;
    if (command->dir == I2C_DIR_RAW_WRITE)
    {
        if (!sensorPort->sercom.i2cm.sercom_instance.in_handler)
        {
            i2c_status = SensorPort_I2C_StartWrite(
                sensorPort,
                command->address,
                command->data,
                command->data_sz,
                &i2c_txrx_complete
            );
        } else {
            i2c_status = SensorPort_I2C_StartWriteFromISR(
                sensorPort,
                command->address,
                command->data,
                command->data_sz,
                &i2c_txrx_complete
            );
        }
    }
    else if (command->dir == I2C_DIR_RAW_READ_CONTINUE)
    {
        i2c_status = SensorPort_I2C_ContinueReadFromISR(
            sensorPort,
            command->address,
            command->data,
            command->data_sz,
            &i2c_txrx_complete
        );
    }

    return (i2c_status == SensorPort_I2C_Success);
}
/************************************************************************************************************************************/

static void normalize_colors(SensorLibrary_RGB_Data_t* libdata)
{
    for (size_t idx = 0u; idx < 4u; idx++) {
        libdata->sens_color[idx].red   = (libdata->sens_color[idx].red   * libdata->coef.R) / 1000u;
        libdata->sens_color[idx].green = (libdata->sens_color[idx].green * libdata->coef.G) / 1000u;
        libdata->sens_color[idx].blue  = (libdata->sens_color[idx].blue  * libdata->coef.B) / 1000u;
    }
}

static void srgb_to_rgb888(SensorLibrary_RGB_Data_t* libdata, rgb_t *colors)
{
    #define MAX(A, B)   ((A) > (B) ? (A) : (B))
    #define MAX3(R,G,B) MAX(MAX((R), (G)), (B))

    for (size_t idx = 0; idx < 4u; idx++) {
        uint16_t max_color = MAX3(libdata->sens_color[idx].red, libdata->sens_color[idx].green, libdata->sens_color[idx].blue);
        uint16_t div = max_color / 256 + 1;
        colors[idx].R = libdata->sens_color[idx].red   / div;
        colors[idx].G = libdata->sens_color[idx].green / div;
        colors[idx].B = libdata->sens_color[idx].blue  / div;
    }
}

static void set_sensor_state(SensorPort_t* sensorPort, uint8_t state)
{
    SensorLibrary_RGB_Data_t* libdata = (SensorLibrary_RGB_Data_t*) sensorPort->libraryData;

    libdata->state = state;

    SensorPortHandler_Call_UpdatePortStatus(sensorPort->port_idx, (ByteArray_t) {
        .bytes = (uint8_t*)&libdata->state,
        .count = 1u
    });
}

static void i2c_txrx_complete(I2CMasterInstance_t* instance, size_t transferred)
{
    SensorPort_t *sensorPort = CONTAINER_OF(instance, SensorPort_t, sercom.i2cm.sercom_instance);
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    if (libdata->test_state == COLOR_SENSOR_TEST_STATE_I2C_READ)
    {
        libdata->test_state = COLOR_SENSOR_TEST_STATE_DONE;
        if (transferred > 0)
        {
            libdata->test_result = SensorOnPortStatus_Present;
        }
        else
        {
            libdata->test_result = SensorOnPortStatus_NotPresent;
        }
    }
    else if (transferred > 0u)
    {
        libdata->orange_led++;
        if ((libdata->orange_led % 25) == 0)
        {
            libdata->orange_led = 0u;
            SensorPort_ToggleOrangeLed(sensorPort);
        }

        switch (libdata->state) {
            case SENS_STATE_RESET:
                rgb_init_sensor(sensorPort);
                break;

            case SENS_STATE_OPERATIONAL:
                rgb_read_sensor(sensorPort);
                break;

            default:
                ASSERT(0);
        }
    }
    else
    {
        set_sensor_state(sensorPort, SENS_STATE_ERROR);
        libdata->transferring = false;
    }
}

static void rgb_read_sensor(SensorPort_t* sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    if (libdata->sequence_idx >= ARRAY_SIZE(readcolors_sequence))
    {
        rgb_t color[4];
        normalize_colors(libdata);
        srgb_to_rgb888(libdata, &color[0]);
        SensorPortHandler_Call_UpdatePortStatus(sensorPort->port_idx, (ByteArray_t){
            .bytes = (uint8_t*)&color[0],
            .count = sizeof(color)
        });
        libdata->transferring = false;
        libdata->sequence_idx = 0;
        return;
    }

    libdata->transferring = execute_i2c_command(sensorPort, &libdata->readcolor_sequence[libdata->sequence_idx]);
    libdata->sequence_idx++;
}

static void rgb_init_sensor(SensorPort_t* sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    if (libdata->sequence_idx >= ARRAY_SIZE(init_sequence))
    {
        set_sensor_state(sensorPort, SENS_STATE_OPERATIONAL);
        libdata->transferring = false;
        return;
    }

    libdata->transferring = execute_i2c_command(sensorPort, &init_sequence[libdata->sequence_idx]);
    libdata->sequence_idx++;
}

/* Called from ISR */
static void deinit_i2c_cb_from_isr(I2CMasterInstance_t* instance, size_t transferred)
{
    SensorPort_t *sensorPort = CONTAINER_OF(instance, SensorPort_t, sercom.i2cm.sercom_instance);
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;
    if (transferred == 0)
    {
        /*  SERCOM_I2CM_STATUS_RXNACK received */
        if (libdata->deinit_num_retries > SENS_DEINIT_MAX_RETRIES)
        {
            libdata->deinit_state = SENS_DEINIT_STATE_ERROR;
        }
        else
        {
            libdata->deinit_num_retries++;
            const i2c_command_t *cmd = &deinit_sequence[libdata->sequence_idx];
            SensorPort_I2C_StartWriteFromISR(sensorPort, cmd->address, cmd->data,
                cmd->data_sz, deinit_i2c_cb_from_isr);
        }
    }
    else if (libdata->sequence_idx >= ARRAY_SIZE(deinit_sequence))
    {
        libdata->deinit_state = SENS_DEINIT_STATE_COMPLETED;
        libdata->transferring = false;
    }
    else
    {
        const i2c_command_t *cmd = &deinit_sequence[libdata->sequence_idx++];
        SensorPort_I2C_StartWriteFromISR(sensorPort,cmd->address, cmd->data, cmd->data_sz,
            deinit_i2c_cb_from_isr);
    }
}

static void ProcessDeinitCompleted(SensorPort_t* sensorPort)
{
    SensorPort_SetGreenLed(sensorPort, false);
    SensorPort_SetOrangeLed(sensorPort, false);
    SensorPort_SetVccIo(sensorPort, Sensor_VccIo_3V3);
    SensorPort_I2C_Disable(sensorPort);
    SensorPortHandler_Call_Free(&sensorPort->libraryData);
}

static void ProcessDeinitRequested(SensorPort_t* sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;
    libdata->deinit_num_retries = 0;
    libdata->transferring = true;
    const i2c_command_t *cmd = &deinit_sequence[0];
    libdata->sequence_idx = 1;
    libdata->deinit_state = SENS_DEINIT_STATE_IN_PROGRESS;
    SensorPort_I2C_StartWrite(sensorPort, cmd->address, cmd->data, cmd->data_sz,
        deinit_i2c_cb_from_isr);
}

static void try_init_port(SensorPort_t* sensorPort)
{
    SensorPort_SetGpio0_Output(sensorPort, false);
    SensorPort_I2C_Disable(sensorPort);
    SensorPort_SetOrangeLed(sensorPort, false);

    delay_ms(10);

    SensorPort_SetGpio0_Output(sensorPort, true);
    if (SensorPort_I2C_Enable(sensorPort, 400) == SensorPort_I2C_Success)
    {
        SensorPort_SetGreenLed(sensorPort, true);
        set_sensor_state(sensorPort, SENS_STATE_RESET);
    }
    else
    {
        SensorPort_SetGreenLed(sensorPort, false);
        set_sensor_state(sensorPort, SENS_STATE_ERROR);
    }
}

static SensorLibraryStatus_t ColorSensor_Load(SensorPort_t *sensorPort)
{
    SensorPortHandler_Call_UpdateStatusSlotSize(sizeof(rgb_t[4]));

    SensorLibrary_RGB_Data_t* libdata = SensorPortHandler_Call_Allocate(sizeof(SensorLibrary_RGB_Data_t));
    sensorPort->libraryData = libdata;

    libdata->test_result = SensorOnPortStatus_NotPresent;
    libdata->transferring = false;
    libdata->sequence_idx = 0u;

    SensorPort_SetVccIo(sensorPort, Sensor_VccIo_3V3);
    SensorPort_ConfigureGpio0_Output(sensorPort);

    try_init_port(sensorPort);
    libdata->deinit_state = SENS_DEINIT_STATE_NONE;
    libdata->deinit_num_retries = 0;

    libdata->coef.R = DEFAULT_COEF_R;
    libdata->coef.G = DEFAULT_COEF_G;
    libdata->coef.B = DEFAULT_COEF_B;

    memcpy(libdata->readcolor_sequence, readcolors_sequence, sizeof(readcolors_sequence));

    libdata->readcolor_sequence[2].data = (uint8_t*)&libdata->sens_color[0].red;
    libdata->readcolor_sequence[4].data = (uint8_t*)&libdata->sens_color[0].green;
    libdata->readcolor_sequence[6].data = (uint8_t*)&libdata->sens_color[0].blue;

    libdata->readcolor_sequence[9].data  = (uint8_t*)&libdata->sens_color[1].red;
    libdata->readcolor_sequence[11].data = (uint8_t*)&libdata->sens_color[1].green;
    libdata->readcolor_sequence[13].data = (uint8_t*)&libdata->sens_color[1].blue;

    libdata->readcolor_sequence[16].data = (uint8_t*)&libdata->sens_color[2].red;
    libdata->readcolor_sequence[18].data = (uint8_t*)&libdata->sens_color[2].green;
    libdata->readcolor_sequence[20].data = (uint8_t*)&libdata->sens_color[2].blue;

    libdata->readcolor_sequence[23].data = (uint8_t*)&libdata->sens_color[3].red;
    libdata->readcolor_sequence[25].data = (uint8_t*)&libdata->sens_color[3].green;
    libdata->readcolor_sequence[27].data = (uint8_t*)&libdata->sens_color[3].blue;

    return SensorLibraryStatus_Ok;
}

static SensorLibraryUnloadStatus_t ColorSensor_Unload(SensorPort_t *sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    switch (libdata->deinit_state) {
        case SENS_DEINIT_STATE_NONE:
            ProcessDeinitRequested(sensorPort);
            break;

        case SENS_DEINIT_STATE_IN_PROGRESS:
            break;

        case SENS_DEINIT_STATE_COMPLETED:
            ProcessDeinitCompleted(sensorPort);
            return SensorLibraryUnloadStatus_Done;

        case SENS_DEINIT_STATE_ERROR:
            ProcessDeinitCompleted(sensorPort);
            return SensorLibraryUnloadStatus_Done;

        default:
            ASSERT(0);
    }

    return SensorLibraryUnloadStatus_Pending;
}

static SensorLibraryStatus_t ColorSensor_Update(SensorPort_t *sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    if (libdata->transferring)
    {
        return SensorLibraryStatus_Ok;
    }

    switch (libdata->state) {
        case SENS_STATE_RESET:
            libdata->sequence_idx = 0;
            rgb_init_sensor(sensorPort);
            break;

        case SENS_STATE_OPERATIONAL:
            libdata->sequence_idx = 0;
            rgb_read_sensor(sensorPort);
            break;

        case SENS_STATE_ERROR:
            libdata->sequence_idx = 0;
            try_init_port(sensorPort);
            break;

        default:
            break;
    }

    return SensorLibraryStatus_Ok;
}

static SensorLibraryStatus_t ColorSensor_UpdateConfiguration(SensorPort_t *sensorPort, const uint8_t *data, uint8_t size)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;
    if (size != sizeof(libdata->coef))
    {
        return SensorLibraryStatus_LengthError;
    }

    memcpy(&libdata->coef, data, sizeof(libdata->coef));
    return SensorLibraryStatus_Ok;
}

static SensorLibraryStatus_t ColorSensor_UpdateAnalogData(SensorPort_t* sensorPort, uint8_t rawValue)
{
    (void) sensorPort;
    (void) rawValue;
    return SensorLibraryStatus_Ok;
}

static SensorLibraryStatus_t ColorSensor_InterruptCallback(SensorPort_t* sensorPort, bool status)
{
    (void) sensorPort;
    (void) status;
    return SensorLibraryStatus_Ok;
}

static void ColorSensor_ReadSensorInfo(SensorPort_t *sensorPort, uint8_t page,
    uint8_t *buffer, uint8_t size, uint8_t *count)
{
    (void)size;

    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    if (page == 0u)
    {
        memcpy(&buffer[0], &libdata->coef, sizeof(libdata->coef));
    }
    else
    {
        *count = 0u;
    }
}

static void on_test_done(SensorPort_t *sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;
    SensorPort_SetGreenLed(sensorPort, false);
    SensorPort_I2C_Disable(sensorPort);
    SensorPort_ConfigureGpio0_Input(sensorPort);
    libdata->test_state = COLOR_SENSOR_TEST_STATE_NONE;
}

static bool ColorSensor_TestSensorOnPort(SensorPort_t *sensorPort, SensorOnPortStatus_t *result)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    switch (libdata->test_state)
    {
        case COLOR_SENSOR_TEST_STATE_NONE:
            libdata->test_result = SensorOnPortStatus_NotPresent;
            libdata->test_state = COLOR_SENSOR_TEST_STATE_I2C_READ;
            SensorPort_SetVccIo(sensorPort, Sensor_VccIo_3V3);
            SensorPort_ConfigureGpio0_Output(sensorPort);

            SensorPort_SetGpio0_Output(sensorPort, false);
            SensorPort_I2C_Disable(sensorPort);
            SensorPort_SetOrangeLed(sensorPort, false);

            delay_ms(10);

            SensorPort_SetGpio0_Output(sensorPort, true);
            if (SensorPort_I2C_Enable(sensorPort, 400) != SensorPort_I2C_Success)
            {
                *result = SensorOnPortStatus_Error;
                on_test_done(sensorPort);
                return true;
            }

            SensorPort_SetGreenLed(sensorPort, true);

            SensorPort_I2C_Status_t i2c_status = SensorPort_I2C_StartWrite(sensorPort, PCA9633TK_ADDR,
                &PCA9546_port_off, 1, i2c_txrx_complete);

            if (i2c_status != SensorPort_I2C_Success)
            {
                *result = SensorOnPortStatus_Error;
                on_test_done(sensorPort);
                return true;
            }

            return false;

        case COLOR_SENSOR_TEST_STATE_I2C_READ:
            return false;

        case COLOR_SENSOR_TEST_STATE_DONE:
            *result = libdata->test_result;
            on_test_done(sensorPort);
            return true;

        default:
            ASSERT(0);
    }
}

const SensorLibrary_t sensor_library_rgb = {
    .Name                = "RGB",
    .Load                = &ColorSensor_Load,
    .Unload              = &ColorSensor_Unload,
    .Update              = &ColorSensor_Update,
    .UpdateConfiguration = &ColorSensor_UpdateConfiguration,
    .UpdateAnalogData    = &ColorSensor_UpdateAnalogData,
    .InterruptHandler    = &ColorSensor_InterruptCallback,
    .ReadSensorInfo      = &ColorSensor_ReadSensorInfo,
    .TestSensorOnPort    = &ColorSensor_TestSensorOnPort
};
