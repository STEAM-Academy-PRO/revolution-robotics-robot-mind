/*
 * ColorSensor.c
 *
 * Created: 2022. 03. 31. 12:48:20
 *  Author: Vladimir Yakovlev
 */

#include "RGB.h"
#include "utils.h"
#include "utils/color.h"
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

#define COLOR_SENSOR_TEST_STATE_NONE 0
#define COLOR_SENSOR_TEST_STATE_I2C_READ 1
#define COLOR_SENSOR_TEST_STATE_DONE 2
static bool color_sensor_test_state_result = false;
static int color_sensor_test_state = COLOR_SENSOR_TEST_STATE_NONE;

typedef struct _veml3328_colors
{
    uint16_t clear;
    uint16_t red;
    uint16_t green;
    uint16_t blue;
    uint16_t ir;
} __attribute__((packed)) veml3328_colors_t;

typedef struct{
    int Rcoef;//    = 210;
    int Gcoef;//    = 140;
    int Bcoef;//    = 280;
}__attribute__((packed)) color_coef_t;


enum {
    SENS_STATE_RESET = 0,
    SENS_STATE_OPERATIONAL = 1,
    SENS_STATE_ERROR = 2,
    SENS_STATE_STOP = 3,
};

enum {
    SENS_DEINIT_STATE_NONE = 0,
    SENS_DEINIT_STATE_REQUESTED = 1,
    SENS_DEINIT_STATE_IN_PROGRESS = 2,
    SENS_DEINIT_STATE_COMPLETED = 3,
    SENS_DEINIT_STATE_DEINITIALIZED = 4,
    SENS_DEINIT_STATE_ERROR = 5
};

typedef enum
{
    I2C_DIR_RAW_READ = 1,
    I2C_DIR_RAW_WRITE = 2,
    I2C_DIR_RAW_READ_CONTINUE = 3,
    I2C_DIR_RAW_WRITE_CONTINUE = 4,
}i2c_direction_t;

typedef struct
{
    i2c_direction_t dir;
    uint8_t address;
    uint8_t* data;
    uint8_t data_sz;
}__attribute__((packed)) i2c_command_t;

typedef struct {
    uint8_t state;
    uint8_t init_sequence_idx;
    uint8_t deinit_sequence_idx;
    OnDeInitCompletedCb deinit_completion_cb;
    uint8_t deinit_state;
    uint8_t deinit_num_retries;

    uint8_t readcolor_sequence_idx;
    i2c_command_t readcolor_sequence[40];
    bool transfering;
    int32_t orangeled;
    color_coef_t coef;
    veml3328_colors_t sens_color[4];
    rgb_t color[4];
} __attribute__((packed)) SensorLibrary_RGB_Data_t;

static int Rcoef_default = 210;
static int Gcoef_default = 140;
static int Bcoef_default = 280;

#define SENS_DEINIT_MAX_RETRIES 5
#define	VEML3328_ADDR            0x10

/* veml3328 command code */
#define	VEML3328_CONF            0x00
#define VEML3328_R_DATA          0x05
#define VEML3328_G_DATA          0x06
#define VEML3328_B_DATA          0x07
#define VEML3328_C_DATA	         0x04
#define VEML3328_IR_DATA         0x08

#define VEML3328_DEVICE_ID_REG   0x0C
#define VEML3328_DEVICE_ID_VAL   0x28

/* veml3328 CONF command code */
#define VEML3328_CONF_SD         0x8001
#define VEML3328_CONF_SD_MASK    0x7FFE

#define VEML3328_CONF_AF         (1 << 3)
#define VEML3328_CONF_TRIG       (1 << 2)
#define VEML3328_CONF_SENS_LOW   (1 << 6)
#define VEML3328_CONF_IT_50MS    (0 << 4)
#define VEML3328_CONF_IT_100MS   (1 << 4)
#define VEML3328_CONF_IT_200MS   (2 << 4)
#define VEML3328_CONF_IT_400MS   (3 << 4)

#define VEML3328_CONF_DG_X1   (0 << 12)
#define VEML3328_CONF_DG_X2   (1 << 12)
#define VEML3328_CONF_DG_X4   (2 << 12)

#define VEML3328_CONF_GAIN_HALF (3 << 10)
#define VEML3328_CONF_GAIN_X1   (0 << 10)
#define VEML3328_CONF_GAIN_X2   (1 << 10)
#define VEML3328_CONF_GAIN_X4   (2 << 10)

#define VEML3328_AUTO_GAIN_HALF  (VEML3328_CONF_DG_X1 | VEML3328_CONF_GAIN_HALF)
#define VEML3328_CONF_GAIN_2     (VEML3328_CONF_DG_X2 | VEML3328_CONF_GAIN_X1)
#define VEML3328_CONF_GAIN_8     (VEML3328_CONF_DG_X4 | VEML3328_CONF_GAIN_X2)
#define VEML3328_CONF_GAIN_12     (VEML3328_CONF_DG_X4 | VEML3328_CONF_GAIN_X4)

#define VEML3328_CONF_GAIN_MASK  0xC3FF

#define PCA9633TK_ADDR              0x62
#define PCA9633TK_REG_MODE1			0x00
#define PCA9633TK_REG_MODE2			0x01
#define PCA9633TK_REG_PWM0			0x02
#define PCA9633TK_REG_PWM1			0x03
#define PCA9633TK_REG_PWM2			0x04
#define PCA9633TK_REG_PWM3			0x05
#define PCA9633TK_REG_GRPPWM		0x06
#define PCA9633TK_REG_GRPFREQ		0x07
#define PCA9633TK_REG_LEDOUT		0x08
#define PCA9633TK_REG_SUBADR1		0x09
#define PCA9633TK_REG_SUBADR2		0x0A
#define PCA9633TK_REG_SUBADR3		0x0B
#define PCA9633TK_REG_ALLCALLADR	0x0C

#define PCA9546APW_ADDR             0x70

static uint8_t pca9633tk_init_sequence[] =
{
    /*0x00, */0x91, /* PCA9633TK_REG_MODE1	   */
    /*0x01, */0x01, /* PCA9633TK_REG_MODE2	   */
    /*0x02, */0x5A, /* PCA9633TK_REG_PWM0	   */
    /*0x03, */0x5A, /* PCA9633TK_REG_PWM1	   */
    /*0x04, */0x5A, /* PCA9633TK_REG_PWM2	   */
    /*0x05, */0x5A, /* PCA9633TK_REG_PWM3	   */
    /*0x06, */0xFF, /* PCA9633TK_REG_GRPPWM	   */
    /*0x07, */0x00, /* PCA9633TK_REG_GRPFREQ	   */
    /*0x08, */0xAA, /* PCA9633TK_REG_LEDOUT	   */
    /*0x09, */0xE2, /* PCA9633TK_REG_SUBADR1	   */
    /*0x0A, */0xE4, /* PCA9633TK_REG_SUBADR2	   */
    /*0x0B, */0xE8, /* PCA9633TK_REG_SUBADR3	   */
    /*0x0C, */0xE0, /* PCA9633TK_REG_ALLCALLADR */
    /*0x00, */0x81, /* PCA9633TK_REG_MODE1	   */
};

static uint8_t pca9633tk_deinit_sequence[] =
{
    /*0x00, */0x91, /* PCA9633TK_REG_MODE1	   */
    /*0x01, */0x02, /* PCA9633TK_REG_MODE2	   */
    /*0x02, */0x00, /* PCA9633TK_REG_PWM0	   */
    /*0x03, */0x00, /* PCA9633TK_REG_PWM1	   */
    /*0x04, */0x00, /* PCA9633TK_REG_PWM2	   */
    /*0x05, */0x00, /* PCA9633TK_REG_PWM3	   */
};

static uint8_t PCA9546_port0 = 1<<0;
static uint8_t PCA9546_port1 = 1<<1;
static uint8_t PCA9546_port2 = 1<<2;
static uint8_t PCA9546_port3 = 1<<3;
static uint8_t PCA9546_port_off = 0;

static const uint16_t val_init  = (uint16_t)(VEML3328_CONF_IT_50MS | VEML3328_CONF_SENS_LOW | VEML3328_CONF_DG_X1 | VEML3328_CONF_GAIN_X1);
static uint8_t veml3328_init_sequence[3] = {VEML3328_CONF, val_init&0xFF, val_init>>8 };
static const uint16_t val_deinit  = (uint16_t)(VEML3328_CONF_SD);
static uint8_t veml3328_deinit_sequence[3] = {VEML3328_CONF, val_deinit&0xFF, val_deinit>>8 };

static const i2c_command_t init_sequence[] =
{
    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port0, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&veml3328_init_sequence[0], 3},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port1, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&veml3328_init_sequence[0], 3},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port2, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&veml3328_init_sequence[0], 3},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port3, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&veml3328_init_sequence[0], 3},

//    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port_off, .data_sz=1},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9633TK_ADDR<<1, .data=pca9633tk_init_sequence, .data_sz=ARRAY_SIZE(pca9633tk_init_sequence)},
};

static const i2c_command_t deinit_sequence[] =
{
    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port0, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&veml3328_deinit_sequence[0], 3},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port1, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&veml3328_deinit_sequence[0], 3},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port2, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&veml3328_deinit_sequence[0], 3},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port3, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&veml3328_deinit_sequence[0], 3},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port_off, .data_sz=1},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9633TK_ADDR<<1, .data=pca9633tk_deinit_sequence, .data_sz=ARRAY_SIZE(pca9633tk_deinit_sequence)},
};

static uint8_t VEML3328_colorR = VEML3328_R_DATA;
static uint8_t VEML3328_colorG = VEML3328_G_DATA;
static uint8_t VEML3328_colorB = VEML3328_B_DATA;

static const i2c_command_t readcolors_sequence[] =
{
    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port0, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorR, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorG, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorB, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port1, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorR, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorG, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorB, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port2, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorR, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorG, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorB, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},

    {.dir=I2C_DIR_RAW_WRITE, .address=PCA9546APW_ADDR<<1, .data=&PCA9546_port3, .data_sz=1},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorR, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorG, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},
    {.dir=I2C_DIR_RAW_WRITE, .address=VEML3328_ADDR<<1, .data=&VEML3328_colorB, .data_sz=1},
    {.dir=I2C_DIR_RAW_READ_CONTINUE, .address=VEML3328_ADDR<<1, .data=NULL, .data_sz=2},
};
/************************************************************************************************************************************/

#define minRGB(R,G,B)    (R < G ? (R < B ? R : B) : (G < B ? G : B))
#define maxRGB(R,G,B)    (R > G ? (R > B ? R : B) : (G > B ? G : B))

static int normalize_colors(SensorLibrary_RGB_Data_t* libdata)
{
    for (uint8_t idx=0; idx<4; idx++) {
        libdata->sens_color[idx].red = (libdata->sens_color[idx].red * libdata->coef.Rcoef)/1000u;
        libdata->sens_color[idx].green = (libdata->sens_color[idx].green * libdata->coef.Gcoef)/1000u;
        libdata->sens_color[idx].blue = (libdata->sens_color[idx].blue * libdata->coef.Bcoef)/1000u;
    }
    return 0;
}

static void sRgbToRgb888(SensorLibrary_RGB_Data_t* libdata)
{
    for (uint8_t idx=0; idx<4; idx++) {
        int div = (maxRGB(libdata->sens_color[idx].red, libdata->sens_color[idx].green, libdata->sens_color[idx].blue)/256) + 1;
        libdata->color[idx].R = libdata->sens_color[idx].red/div;
        libdata->color[idx].G = libdata->sens_color[idx].green/div;
        libdata->color[idx].B = libdata->sens_color[idx].blue/div;
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

static void RgbReadSensor(SensorPort_t* sensorPort);
static void RgbInitSensor(SensorPort_t* sensorPort);

static void i2c_txrx_complete(I2CMasterInstance_t* instance, size_t transferred)
{
    SensorPort_t *sensorPort = CONTAINER_OF(instance, SensorPort_t, sercom.i2cm.sercom_instance);
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    if (color_sensor_test_state == COLOR_SENSOR_TEST_STATE_I2C_READ)
    {
        color_sensor_test_state = COLOR_SENSOR_TEST_STATE_DONE;
        if (transferred)
        {
            color_sensor_test_state_result = true;
        }
        else
        {
            color_sensor_test_state_result = false;
        }
        return;
    }

    if (transferred > 0u)
    {
        libdata->orangeled++;
        if ((libdata->orangeled % 25) == 0)
            SensorPort_ToggleOrangeLed(sensorPort);

        switch (libdata->state) {
        case SENS_STATE_RESET:
            RgbInitSensor(sensorPort);
            break;
        case SENS_STATE_OPERATIONAL:
            RgbReadSensor(sensorPort);
            break;
        }

    }else {
        set_sensor_state(sensorPort, SENS_STATE_ERROR);
        libdata->transfering = false;
        return;
    }
}

static void RgbReadSensor(SensorPort_t* sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    libdata->transfering = true;
    if (libdata->readcolor_sequence_idx>=ARRAY_SIZE(readcolors_sequence))
    {
        normalize_colors(libdata);
        sRgbToRgb888(libdata);
        SensorPortHandler_Call_UpdatePortStatus(sensorPort->port_idx, (ByteArray_t){
            .bytes = (uint8_t*)&libdata->color[0],
            .count = 4*sizeof(rgb_t)
        });
        libdata->transfering = false;
        libdata->readcolor_sequence_idx = 0;
        return;
    }

    if (libdata->readcolor_sequence[libdata->readcolor_sequence_idx].dir == I2C_DIR_RAW_WRITE)
    {
        if (sensorPort->sercom.i2cm.sercom_instance.in_handler == false)
        {
            SensorPort_I2C_StartWrite(sensorPort,
                                      libdata->readcolor_sequence[libdata->readcolor_sequence_idx].address,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data_sz,
                    &i2c_txrx_complete);
        } else {
            SensorPort_I2C_StartWriteFromISR(sensorPort,
                                      libdata->readcolor_sequence[libdata->readcolor_sequence_idx].address,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data_sz,
                    &i2c_txrx_complete);
        }
    }
    else if (libdata->readcolor_sequence[libdata->readcolor_sequence_idx].dir == I2C_DIR_RAW_READ)
    {
        if (sensorPort->sercom.i2cm.sercom_instance.in_handler == false)
        {
            SensorPort_I2C_StartRead(sensorPort,
                                      libdata->readcolor_sequence[libdata->readcolor_sequence_idx].address,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data_sz,
                    &i2c_txrx_complete);
        } else {
            SensorPort_I2C_StartReadFromISR(sensorPort,
                                      libdata->readcolor_sequence[libdata->readcolor_sequence_idx].address,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data_sz,
                    &i2c_txrx_complete);
        }
    }


    else if (libdata->readcolor_sequence[libdata->readcolor_sequence_idx].dir == I2C_DIR_RAW_WRITE_CONTINUE)
    {
        if (sensorPort->sercom.i2cm.sercom_instance.in_handler == true)
        {
            SensorPort_I2C_ContinueWriteFromISR(sensorPort,
                                      libdata->readcolor_sequence[libdata->readcolor_sequence_idx].address,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data_sz,
                    &i2c_txrx_complete);
        }
    }
    else if (libdata->readcolor_sequence[libdata->readcolor_sequence_idx].dir == I2C_DIR_RAW_READ_CONTINUE)
    {
        if (sensorPort->sercom.i2cm.sercom_instance.in_handler == true)
        {
            SensorPort_I2C_ContinueReadFromISR(sensorPort,
                                      libdata->readcolor_sequence[libdata->readcolor_sequence_idx].address,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data,
                    libdata->readcolor_sequence[libdata->readcolor_sequence_idx].data_sz,
                    &i2c_txrx_complete);
        }
    }

    else
    {
        libdata->transfering = false;
    }

    libdata->readcolor_sequence_idx++;
    return;
}

static void RgbInitSensor(SensorPort_t* sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    libdata->transfering = true;

    if (libdata->init_sequence_idx>=ARRAY_SIZE(init_sequence))
    {
        set_sensor_state(sensorPort, SENS_STATE_OPERATIONAL);
        libdata->transfering = false;
        return;
    }

    if (init_sequence[libdata->init_sequence_idx].dir == I2C_DIR_RAW_WRITE)
    {
        if (sensorPort->sercom.i2cm.sercom_instance.in_handler == false)
        {
            SensorPort_I2C_StartWrite(sensorPort,
                                        init_sequence[libdata->init_sequence_idx].address,
                                        init_sequence[libdata->init_sequence_idx].data,
                                        init_sequence[libdata->init_sequence_idx].data_sz,
                                        &i2c_txrx_complete);
        }else
        {
            SensorPort_I2C_StartWriteFromISR(sensorPort,
                                        init_sequence[libdata->init_sequence_idx].address,
                                        init_sequence[libdata->init_sequence_idx].data,
                                        init_sequence[libdata->init_sequence_idx].data_sz,
                                        &i2c_txrx_complete);
        }
    }else {
        libdata->transfering = false;
    }

    libdata->init_sequence_idx++;
    return;
}

/* Called from ISR */
static void deinit_i2c_cb_from_isr(I2CMasterInstance_t* instance, size_t transferred)
{
    const i2c_command_t *cmd;
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
            cmd = &deinit_sequence[libdata->deinit_sequence_idx];
            SensorPort_I2C_StartWriteFromISR(sensorPort, cmd->address, cmd->data,
                cmd->data_sz, deinit_i2c_cb_from_isr);
        }
        return;
    }

    if (libdata->deinit_sequence_idx>=ARRAY_SIZE(deinit_sequence))
    {
        libdata->deinit_state = SENS_DEINIT_STATE_COMPLETED;
        libdata->transfering = false;
        return;
    }

    cmd = &deinit_sequence[libdata->deinit_sequence_idx++];
    SensorPort_I2C_StartWriteFromISR(sensorPort,cmd->address, cmd->data, cmd->data_sz,
        deinit_i2c_cb_from_isr);
}

static void OnDeInitCompleted(SensorPort_t *sensorPort, bool success)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;
    SensorPort_SetGreenLed(sensorPort, false);
    SensorPort_SetOrangeLed(sensorPort, false);
    SensorPort_SetVccIo(sensorPort, Sensor_VccIo_3V3);
    SensorPort_I2C_Disable(sensorPort);
    SensorPortHandler_Call_Free(&sensorPort->libraryData);
    if (libdata->deinit_completion_cb)
    {
        libdata->deinit_completion_cb(sensorPort, success);
        libdata->deinit_completion_cb = NULL;
    }
}

static void ProcessDeinitCompleted(SensorPort_t* sensorPort, bool success)
{
  SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

  /* For debug */
  ASSERT(success);

  libdata->deinit_state = SENS_DEINIT_STATE_DEINITIALIZED;
  OnDeInitCompleted(sensorPort, success);
}

static void ProcessDeinitRequested(SensorPort_t* sensorPort)
{
    const i2c_command_t *cmd;
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;
    libdata->deinit_num_retries = 0;
    libdata->transfering = true;
    cmd = &deinit_sequence[0];
    libdata->deinit_sequence_idx = 1;
    libdata->deinit_state = SENS_DEINIT_STATE_IN_PROGRESS;
    SensorPort_I2C_StartWrite(sensorPort, cmd->address, cmd->data, cmd->data_sz,
        deinit_i2c_cb_from_isr);
}

static void try_init_port(SensorPort_t* sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = (SensorLibrary_RGB_Data_t*) sensorPort->libraryData;

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
    libdata->readcolor_sequence_idx = 0;
    libdata->init_sequence_idx = 0;
    libdata->transfering = false;
}

static SensorLibraryStatus_t ColorSensor_Init(SensorPort_t *sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = SensorPortHandler_Call_Allocate(sizeof(SensorLibrary_RGB_Data_t));
    sensorPort->libraryData = libdata;

    SensorPort_SetVccIo(sensorPort, Sensor_VccIo_3V3);
    SensorPort_ConfigureGpio0_Output(sensorPort);

    try_init_port(sensorPort);
    libdata->deinit_state = SENS_DEINIT_STATE_NONE;
    libdata->deinit_num_retries = 0;

    libdata->coef.Rcoef = Rcoef_default;
    libdata->coef.Gcoef = Gcoef_default;
    libdata->coef.Bcoef = Bcoef_default;

    memcpy(libdata->readcolor_sequence, readcolors_sequence, sizeof(readcolors_sequence));

    libdata->readcolor_sequence[2].data = (uint8_t*)&libdata->sens_color[0].red;
    libdata->readcolor_sequence[4].data = (uint8_t*)&libdata->sens_color[0].green;
    libdata->readcolor_sequence[6].data = (uint8_t*)&libdata->sens_color[0].blue;

    libdata->readcolor_sequence[9].data = (uint8_t*)&libdata->sens_color[1].red;
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

static void ColorSensor_DeInit(SensorPort_t *sensorPort, OnDeInitCompletedCb cb)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    /*
     * Early exit with failure if DeInit already requested and
     * not finished
     */
    if (libdata->deinit_state != SENS_DEINIT_STATE_NONE)
    {
      cb(sensorPort, false);
    }

    libdata->deinit_state = SENS_DEINIT_STATE_REQUESTED;
    libdata->deinit_completion_cb  = cb;
}

static void ProcessDeinitState(SensorPort_t *sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    switch (libdata->deinit_state) {
    case SENS_DEINIT_STATE_NONE:
        break;
    case SENS_DEINIT_STATE_REQUESTED:
        ProcessDeinitRequested(sensorPort);
        break;
    case SENS_DEINIT_STATE_IN_PROGRESS:
        break;
    case SENS_DEINIT_STATE_COMPLETED:
        ProcessDeinitCompleted(sensorPort, true);
        break;
    case SENS_DEINIT_STATE_ERROR:
        ProcessDeinitCompleted(sensorPort, false);
        break;
    default:
        break;
    }
}

static SensorLibraryStatus_t ColorSensor_Update(SensorPort_t *sensorPort)
{
    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    if (libdata->transfering == true)
        return SensorLibraryStatus_Ok;

    switch (libdata->state) {
    case SENS_STATE_RESET:
        libdata->init_sequence_idx = 0;
        RgbInitSensor(sensorPort);
        break;
    case SENS_STATE_OPERATIONAL:
        if (libdata->deinit_state != SENS_DEINIT_STATE_NONE)
        {
           ProcessDeinitState(sensorPort);
        }
        else
        {
           libdata->readcolor_sequence_idx = 0;
           RgbReadSensor(sensorPort);
        }
        break;
    case SENS_STATE_ERROR:
        try_init_port(sensorPort);
        break;
    default:
        break;
    }

    return SensorLibraryStatus_Ok;
}

static SensorLibraryStatus_t ColorSensor_UpdateConfiguration(
    SensorPort_t *sensorPort, const uint8_t *data, uint8_t size)
{
    (void)sensorPort;
    (void)data;
    (void)size;

    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;
    if (size == sizeof(libdata->coef))
    {
        memcpy(&libdata->coef, data, sizeof(libdata->coef));
    }else {
        return SensorLibraryStatus_LengthError;
    }

    return SensorLibraryStatus_Ok;
}

static SensorLibraryStatus_t ColorSensor_UpdateAnalogData(
    SensorPort_t* sensorPort, uint8_t rawValue)
{
    (void) sensorPort;
    (void) rawValue;
    return SensorLibraryStatus_Ok;
}

static SensorLibraryStatus_t ColorSensor_InterruptCallback(
    SensorPort_t* sensorPort, bool status)
{
    (void) sensorPort;
    (void) status;
    return SensorLibraryStatus_Ok;
}

static void ColorSensor_ReadSensorInfo(SensorPort_t *sensorPort, uint8_t page,
    uint8_t *buffer, uint8_t size, uint8_t *count)
{
    (void)sensorPort;
    (void)page;
    (void)buffer;
    (void)size;

    SensorLibrary_RGB_Data_t* libdata = sensorPort->libraryData;

    if (page == 0)
    {
        memcpy(&buffer[0], &libdata->coef, sizeof(libdata->coef));
    }else {
        *count = 0u;
    }
}

static bool ColorSensor_TestSensorOnPort(SensorPort_t *sensorPort, SensorOnPortStatus_t *result)
{
  SensorPort_I2C_Status_t i2c_status;

  if (color_sensor_test_state == COLOR_SENSOR_TEST_STATE_NONE)
  {
    color_sensor_test_state = COLOR_SENSOR_TEST_STATE_I2C_READ;
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
      goto out_completed;
    }

    SensorPort_SetGreenLed(sensorPort, true);

    i2c_status = SensorPort_I2C_StartWrite(sensorPort, PCA9633TK_ADDR<<1,
      &PCA9546_port_off, 1, i2c_txrx_complete);

    if (i2c_status != SensorPort_I2C_Success)
    {
      *result = SensorOnPortStatus_Error;
      goto out_completed;
    }

    return false;
  }

  if (color_sensor_test_state == COLOR_SENSOR_TEST_STATE_I2C_READ)
  {
    return false;
  }

  if (color_sensor_test_state == COLOR_SENSOR_TEST_STATE_DONE)
  {
    if (color_sensor_test_state_result)
    {
        *result = SensorOnPortStatus_Present;
    }
    else
    {
        *result = SensorOnPortStatus_NotPresent;
    }
    color_sensor_test_state_result = false;
    goto out_completed;
  }

  *result = SensorOnPortStatus_Error;

out_completed:
  SensorPort_SetGreenLed(sensorPort, false);
  SensorPort_I2C_Disable(sensorPort);
  SensorPort_ConfigureGpio0_Input(sensorPort);
  color_sensor_test_state = COLOR_SENSOR_TEST_STATE_NONE;
  return true;
}

const SensorLibrary_t sensor_library_rgb = {
    .name = "RGB",
    .Init = &ColorSensor_Init,
    .DeInit = &ColorSensor_DeInit,
    .Update = &ColorSensor_Update,
    .UpdateConfiguration = &ColorSensor_UpdateConfiguration,
    .UpdateAnalogData = &ColorSensor_UpdateAnalogData,
    .InterruptHandler = &ColorSensor_InterruptCallback,
    .ReadSensorInfo = &ColorSensor_ReadSensorInfo,
    .TestSensorOnPort = &ColorSensor_TestSensorOnPort
};
