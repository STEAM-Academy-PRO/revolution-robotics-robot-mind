#include "rrrc_hal.h"
#include "rrrc_worklogic.h"

static MotorPort_t motorPorts[] =
{
    {
        .port_idx = 0u
    },
    {
        .port_idx = 1u
    },
    {
        .port_idx = 2u
    },
    {
        .port_idx = 3u
    },
    {
        .port_idx = 4u
    },
    {
        .port_idx = 5u
    }
};

#define MOTOR_DRIVER_INIT(i)                              \
{                                                         \
    .idx = i,                                             \
                                                          \
    .fault = MOTOR_DRIVER_## i ## _FAULT,                 \
    .n_sleep = MOTOR_DRIVER_## i ## _EN,                  \
                                                          \
    .pwm_a = {                                            \
        .timer = MOTOR_DRIVER_## i ##_CH_A_PWM_TIMER,     \
        .ch1 = MOTOR_DRIVER_## i ##_CH_A_PWM0_CH,         \
        .ch2 = MOTOR_DRIVER_## i ##_CH_A_PWM1_CH,         \
        .pin1 = MOTOR_DRIVER_## i ##_CH_A_PWM0_PIN,       \
        .pin2 = MOTOR_DRIVER_## i ##_CH_A_PWM1_PIN,       \
     },                                                   \
    .pwm_b = {                                            \
        .timer = MOTOR_DRIVER_## i ##_CH_B_PWM_TIMER,     \
        .ch2 = MOTOR_DRIVER_## i ##_CH_B_PWM1_CH,         \
        .ch1 = MOTOR_DRIVER_## i ##_CH_B_PWM0_CH,         \
        .pin1 = MOTOR_DRIVER_## i ##_CH_B_PWM0_PIN,       \
        .pin2 = MOTOR_DRIVER_## i ##_CH_B_PWM1_PIN,       \
    }                                                     \
}

static MotorDriver_8833_t motorDrivers[] = {
    MOTOR_DRIVER_INIT(0),
    MOTOR_DRIVER_INIT(1),
    MOTOR_DRIVER_INIT(2)
};

static SensorPort_t sensorPorts[] =
{
    {
        .port_idx = 0u,
        .led0 = S3_LED_GREEN,
        .led1 = S3_LED_YELLOW,
        .gpio0 = S3_GPIO_OUT,
        .gpio1 = S3_GPIO_IN,
        .vccio = S3_IOVCC,
        .comm_hw = SENSOR_3_SERCOM,
        .comm_pin0 = {
            .pin = SENSOR_3_SDApin,
            .function = SENSOR_3_SDApin_function
        },
        .comm_pin1 = {
            .pin = SENSOR_3_SCLpin,
            .function = SENSOR_3_SCLpin_function
        }
    },
    {
        .port_idx = 1u,
        .led0 = S2_LED_GREEN,
        .led1 = S2_LED_YELLOW,
        .gpio0 = S2_GPIO_OUT,
        .gpio1 = S2_GPIO_IN,
        .vccio = S2_IOVCC,
        .comm_hw = SENSOR_2_SERCOM,
        .comm_pin0 = {
            .pin = SENSOR_2_SDApin,
            .function = SENSOR_2_SDApin_function
        },
        .comm_pin1 = {
            .pin = SENSOR_2_SCLpin,
            .function = SENSOR_2_SCLpin_function
        }
    },
    {
        .port_idx = 2u,
        .led0 = S1_LED_GREEN,
        .led1 = S1_LED_YELLOW,
        .gpio0 = S1_GPIO_OUT,
        .gpio1 = S1_GPIO_IN,
        .vccio = S1_IOVCC,
        .comm_hw = SENSOR_1_SERCOM,
        .comm_pin0 = {
            .pin = SENSOR_1_SDApin,
            .function = SENSOR_1_SDApin_function
        },
        .comm_pin1 = {
            .pin = SENSOR_1_SCLpin,
            .function = SENSOR_1_SCLpin_function
        }
    },
    {
        .port_idx = 3u,
        .led0 = S0_LED_GREEN,
        .led1 = S0_LED_YELLOW,
        .gpio0 = S0_GPIO_OUT,
        .gpio1 = S0_GPIO_IN,
        .vccio = S0_IOVCC,
        .comm_hw = SENSOR_0_SERCOM,
        .comm_pin0 = {
            .pin = SENSOR_0_SDApin,
            .function = SENSOR_0_SDApin_function
        },
        .comm_pin1 = {
            .pin = SENSOR_0_SCLpin,
            .function = SENSOR_0_SCLpin_function
        }
    }
};

static void ProcessTasks_1ms(void)
{
    Runtime_RaiseEvent_1ms();
}

static void ProcessTasks_10ms(uint8_t offset)
{
    switch (offset)
    {
        case 0u:
            Runtime_RaiseEvent_10ms_offset0();
            break;

        case 1u:
            Runtime_RaiseEvent_10ms_offset1();
            break;

        case 2u:
            Runtime_RaiseEvent_10ms_offset2();
            MotorDriver_8833_Run_OnUpdate(&motorDrivers[0]);
            break;

        case 3u:
            Runtime_RaiseEvent_10ms_offset3();
            MotorDriver_8833_Run_OnUpdate(&motorDrivers[2]);
            break;

        case 4u:
            Runtime_RaiseEvent_10ms_offset4();
            MotorDriver_8833_Run_OnUpdate(&motorDrivers[1]);
            break;

        case 5u:
            Runtime_RaiseEvent_10ms_offset5();
            break;

        case 6u:
            Runtime_RaiseEvent_10ms_offset6();
            break;

        case 7u:
            Runtime_RaiseEvent_10ms_offset7();
            break;

        case 8u:
            Runtime_RaiseEvent_10ms_offset8();
            break;

        case 9u:
            Runtime_RaiseEvent_10ms_offset9();
            break;
    }
}

static void ProcessTasks_20ms(uint8_t offset)
{
    switch (offset)
    {
        case 0u:
            Runtime_RaiseEvent_20ms_offset0();
            break;

        case 1u:
            Runtime_RaiseEvent_20ms_offset1();
            break;

        case 2u:
            Runtime_RaiseEvent_20ms_offset2();
            break;

        case 3u:
            Runtime_RaiseEvent_20ms_offset3();
            break;

        case 4u:
            Runtime_RaiseEvent_20ms_offset4();
            break;

        case 5u:
            Runtime_RaiseEvent_20ms_offset5();
            break;

        case 6u:
            Runtime_RaiseEvent_20ms_offset6();
            break;

        case 7u:
            Runtime_RaiseEvent_20ms_offset7();
            break;

        case 8u:
            Runtime_RaiseEvent_20ms_offset8();
            break;

        case 9u:
            Runtime_RaiseEvent_20ms_offset9();
            break;

        case 10u:
            Runtime_RaiseEvent_20ms_offset10();
            break;

        case 11u:
            Runtime_RaiseEvent_20ms_offset11();
            break;

        case 12u:
            Runtime_RaiseEvent_20ms_offset12();
            break;

        case 13u:
            Runtime_RaiseEvent_20ms_offset13();
            break;

        case 14u:
            Runtime_RaiseEvent_20ms_offset14();
            break;

        case 15u:
            Runtime_RaiseEvent_20ms_offset15();
            break;

        case 16u:
            Runtime_RaiseEvent_20ms_offset16();
            break;

        case 17u:
            Runtime_RaiseEvent_20ms_offset17();
            break;

        case 18u:
            Runtime_RaiseEvent_20ms_offset18();
            break;

        case 19u:
            Runtime_RaiseEvent_20ms_offset19();
            break;

        default:
            break;
    }
}

void RRRC_ProcessLogic_Init(void)
{
    system_init();

    MasterCommunication_Run_OnInit();
    Runtime_RaiseEvent_OnInit();

    MotorPortHandler_Run_OnInit(&motorPorts[0], ARRAY_SIZE(motorPorts));
    SensorPortHandler_Run_OnInit(&sensorPorts[0], ARRAY_SIZE(sensorPorts));

    MotorDriver_8833_Run_OnDriverInit(motorDrivers, ARRAY_SIZE(motorDrivers));

    Runtime_RaiseEvent_OnInitDone();
}

//*********************************************************************************************
void RRRC_ProcessLogic_xTask(void* user)
{
    (void) user;

    TickType_t xLastWakeTime = xTaskGetTickCount();
    for (uint8_t cycleCounter = 0u;;)
    {
        ProcessTasks_1ms();

        ProcessTasks_10ms(cycleCounter % 10);
        ProcessTasks_20ms(cycleCounter % 20);
        if (cycleCounter == 99u)
        {
            Runtime_RaiseEvent_100ms();
            cycleCounter = 0u;
        }
        else
        {
            cycleCounter++;
        }

        vTaskDelayUntil(&xLastWakeTime, 1u);
    }
}

static int16_t driveValues[ARRAY_SIZE(motorPorts)] = {0};

void MotorDerating_Write_DeratedControlValue(uint32_t index, const int16_t value)
{
    driveValues[index] = value;
}

#define MOTOR_DRIVER_CHANNEL_A 0
#define MOTOR_DRIVER_CHANNEL_B 1

void MotorDriver_8833_GetMotorPortDriver(int motor_port_idx,
    int *motor_driver_idx, int *motor_driver_channel_idx)
{
  switch (motor_port_idx)
  {
    case 0: *motor_driver_idx = 1; *motor_driver_channel_idx = MOTOR_DRIVER_CHANNEL_A;
        break;
    case 1: *motor_driver_idx = 0; *motor_driver_channel_idx = MOTOR_DRIVER_CHANNEL_A;
        break;
    case 2: *motor_driver_idx = 0; *motor_driver_channel_idx = MOTOR_DRIVER_CHANNEL_B;
        break;
    case 3: *motor_driver_idx = 2; *motor_driver_channel_idx = MOTOR_DRIVER_CHANNEL_A;
        break;
    case 4: *motor_driver_idx = 2; *motor_driver_channel_idx = MOTOR_DRIVER_CHANNEL_B;
        break;
    case 5: *motor_driver_idx = 1; *motor_driver_channel_idx = MOTOR_DRIVER_CHANNEL_B;
        break;
    default:
        break;
  }
}

int16_t MotorDriver_8833_Read_DriveRequest_ChannelA(MotorDriver_8833_t* driver)
{
    switch (driver->idx)
    {
        case 0u: return driveValues[4];
        case 1u: return driveValues[3];
        case 2u: return driveValues[2];

        default:
            ASSERT(0);
            return 0;
    }
}

int16_t MotorDriver_8833_Read_DriveRequest_ChannelB(MotorDriver_8833_t* driver)
{
    switch (driver->idx)
    {
        case 0u: return driveValues[5];
        case 1u: return driveValues[0];
        case 2u: return driveValues[1];

        default:
            ASSERT(0);
            return 0;
    }
}

void MasterCommunicationInterface_Read_Configuration(MasterCommunicationInterface_Config_t* dst)
{
    dst->rx_timeout = 100u;

    dst->default_response = MasterCommunication_Constant_DefaultResponse();
    dst->rx_overflow_response = MasterCommunication_Constant_LongRxErrorResponse();
}
