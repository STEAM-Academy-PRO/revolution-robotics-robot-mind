#ifndef COMPONENT_MOTOR_DRIVER_8833_H_
#define COMPONENT_MOTOR_DRIVER_8833_H_

#include <stdio.h>
#include <stdbool.h>

typedef struct {
    uint8_t timer;
    uint32_t ch1;
    uint32_t ch2;
    uint8_t pin1;
    uint8_t pin2;

    int16_t prev_speed;
} MotorDriver_8833_Channel_t;

typedef struct {
    uint8_t idx;

    uint8_t fault;
    uint8_t n_sleep;

    MotorDriver_8833_Channel_t pwm_a;
    MotorDriver_8833_Channel_t pwm_b;

    bool has_fault;
} MotorDriver_8833_t;

#ifndef COMPONENT_TYPES_MOTOR_DRIVER_8833_H_
#define COMPONENT_TYPES_MOTOR_DRIVER_8833_H_

#endif /* COMPONENT_TYPES_MOTOR_DRIVER_8833_H_ */

void MotorDriver_8833_Run_OnInit(void);
void MotorDriver_8833_Run_Start(void);

void MotorDriver_8833_Run_OnDriverInit(MotorDriver_8833_t* drivers,
    int num_drivers);

void MotorDriver_8833_Run_OnUpdate(MotorDriver_8833_t* driver);

void MotorDriver_8833_Call_OnFault(MotorDriver_8833_t* driver);
void MotorDriver_8833_Run_FaultCleared(MotorDriver_8833_t* driver);

int16_t MotorDriver_8833_Read_DriveRequest_ChannelA(MotorDriver_8833_t* driver);
int16_t MotorDriver_8833_Read_DriveRequest_ChannelB(MotorDriver_8833_t* driver);
bool MotorDriver_8833_TestLoadStart(int driver_index, int driver_channel, uint8_t test_power);
bool MotorDriver_8833_TestLoadStop(int driver_index, int driver_channel);
void MotorDriver_8833_GetMotorPortDriver(int motor_port_idx,
    int *motor_driver_idx, int *motor_driver_channel_idx);
void MotorDriver_8833_Run_StartISR(void);

#endif /* COMPONENT_MOTOR_DRIVER_8833_H_ */
