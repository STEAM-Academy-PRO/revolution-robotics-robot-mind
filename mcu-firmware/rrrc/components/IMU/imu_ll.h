/*
 * imu_ll.h
 *
 * Created: 2019. 08. 12. 18:22:51
 *  Author: Dániel Buga
 */ 


#ifndef IMU_LL_H_
#define IMU_LL_H_

#include <stdint.h>
#include <stdio.h>
#include <stdbool.h>

void _imu_write_registers(uint8_t reg, uint8_t* pData, size_t data_count);
void _imu_read_registers(uint8_t reg, uint8_t* pData, size_t data_count);
void _imu_write_register(uint8_t reg, uint8_t data);
uint8_t _imu_read_register(uint8_t reg);
bool imu_axl_data_ready(void);
bool imu_gyro_data_ready(void);

void IMU_Call_LowLevelInit(void);

#endif /* IMU_LL_H_ */
