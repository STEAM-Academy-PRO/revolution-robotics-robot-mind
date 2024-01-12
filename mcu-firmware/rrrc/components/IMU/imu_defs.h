/*
 * imu_defs.h
 *
 * Register description of the ST Microelectronics LSM5DS3 IMU.
 * Note: description was mostly done on a need-to-do basis, so registers and fields may be missing.
 *
 * Created: 2019. 08. 14. 11:23:31
 *  Author: D�niel Buga
 */


#ifndef LSM6DS3_DEFS_H_
#define LSM6DS3_DEFS_H_

#define LSM6DS3_WHOAMI_VALUES ((uint8_t) 0x6Au), ((uint8_t) 0x69u)

/* ---------- register addresses ---------- */
/* r/w registers */
#define LSM6DS3_REGISTER_ADDRESS_FUNC_CFG_ACCESS        ((uint8_t) 0x01u)
#define LSM6DS3_REGISTER_ADDRESS_SENSOR_SYNC_TIME_FRAME ((uint8_t) 0x04u)
#define LSM6DS3_REGISTER_ADDRESS_SENSOR_SYNC_RES_RATIO  ((uint8_t) 0x05u)
#define LSM6DS3_REGISTER_ADDRESS_FIFO_CTRL1             ((uint8_t) 0x06u)
#define LSM6DS3_REGISTER_ADDRESS_FIFO_CTRL2             ((uint8_t) 0x07u)
#define LSM6DS3_REGISTER_ADDRESS_FIFO_CTRL3             ((uint8_t) 0x08u)
#define LSM6DS3_REGISTER_ADDRESS_FIFO_CTRL4             ((uint8_t) 0x09u)
#define LSM6DS3_REGISTER_ADDRESS_FIFO_CTRL5             ((uint8_t) 0x0Au)
#define LSM6DS3_REGISTER_ADDRESS_DRDY_PULSE_CFG_G       ((uint8_t) 0x0Bu)
#define LSM6DS3_REGISTER_ADDRESS_INT1_CTRL              ((uint8_t) 0x0Du)
#define LSM6DS3_REGISTER_ADDRESS_INT2_CTRL              ((uint8_t) 0x0Eu)
#define LSM6DS3_REGISTER_ADDRESS_CTRL1_XL               ((uint8_t) 0x10u)
#define LSM6DS3_REGISTER_ADDRESS_CTRL2_G                ((uint8_t) 0x11u)
#define LSM6DS3_REGISTER_ADDRESS_CTRL3_C                ((uint8_t) 0x12u)
#define LSM6DS3_REGISTER_ADDRESS_CTRL4_C                ((uint8_t) 0x13u)
#define LSM6DS3_REGISTER_ADDRESS_CTRL5_C                ((uint8_t) 0x14u)
#define LSM6DS3_REGISTER_ADDRESS_CTRL6_C                ((uint8_t) 0x15u)
#define LSM6DS3_REGISTER_ADDRESS_CTRL7_G                ((uint8_t) 0x16u)
#define LSM6DS3_REGISTER_ADDRESS_CTRL8_XL               ((uint8_t) 0x17u)
#define LSM6DS3_REGISTER_ADDRESS_CTRL9_XL               ((uint8_t) 0x18u)
#define LSM6DS3_REGISTER_ADDRESS_CTRL10_C               ((uint8_t) 0x19u)
#define LSM6DS3_REGISTER_ADDRESS_MASTER_CONFIG          ((uint8_t) 0x1Au)

#define LSM6DS3_REGISTER_ADDRESS_X_OFS_USR              ((uint8_t) 0x73u)
#define LSM6DS3_REGISTER_ADDRESS_Y_OFS_USR              ((uint8_t) 0x74u)
#define LSM6DS3_REGISTER_ADDRESS_Z_OFS_USR              ((uint8_t) 0x75u)

/* read only registers */
#define LSM6DS3_REGISTER_ADDRESS_WHOAMI                 ((uint8_t) 0x0Fu)
#define LSM6DS3_REGISTER_ADDRESS_WAKE_UP_SRC            ((uint8_t) 0x1Bu)
#define LSM6DS3_REGISTER_ADDRESS_TAP_SRC                ((uint8_t) 0x1Cu)
#define LSM6DS3_REGISTER_ADDRESS_D6D_SRC                ((uint8_t) 0x1Du)
#define LSM6DS3_REGISTER_ADDRESS_STATUS                 ((uint8_t) 0x1Eu)

#define LSM6DS3_REGISTER_ADDRESS_FIFO_STATUS1           ((uint8_t) 0x3Au)
#define LSM6DS3_REGISTER_ADDRESS_FIFO_STATUS2           ((uint8_t) 0x3Bu)
#define LSM6DS3_REGISTER_ADDRESS_FIFO_STATUS3           ((uint8_t) 0x3Cu)
#define LSM6DS3_REGISTER_ADDRESS_FIFO_STATUS4           ((uint8_t) 0x3Du)
#define LSM6DS3_REGISTER_ADDRESS_FIFO_DATA_OUT_L        ((uint8_t) 0x3Eu)
#define LSM6DS3_REGISTER_ADDRESS_FIFO_DATA_OUT_H        ((uint8_t) 0x3Fu)

/* first of 6 output registers */
#define LSM6DS3_ACCEL_REGISTERS  ((uint8_t) 0x28u)

/* first of 6 output registers */
#define LSM6DS3_GYRO_REGISTERS   ((uint8_t) 0x22u)

/* ---------- register values ---------- */

/* FUNC_CFG_ACCESS (01h) */
#define LSM6DS3_FIELD_FUNC_CFG_EN_SIZE          ((uint8_t) 3u)
#define LSM6DS3_FIELD_FUNC_CFG_EN_POS           ((uint8_t) 5u)

#define LSM6DS3_VALUE_FUNC_CFG_EN_DISABLED      ((uint8_t) 0u)
#define LSM6DS3_VALUE_FUNC_CFG_EN_A             ((uint8_t) 1u)
#define LSM6DS3_VALUE_FUNC_CFG_EN_B             ((uint8_t) 5u)

/* SENSOR_SYNC_TIME_FRAME (04h) */
#define LSM6DS3_FIELD_TPH_SIZE                  ((uint8_t) 4u)
#define LSM6DS3_FIELD_TPH_POS                   ((uint8_t) 0u)

/* SENSOR_SYNC_RES_RATIO (05h) */
#define LSM6DS3_FIELD_RR_SIZE                   ((uint8_t) 2u)
#define LSM6DS3_FIELD_RR_POS                    ((uint8_t) 0u)

#define LSM6DS3_VALUE_RR_2_11                   ((uint8_t) 0u)
#define LSM6DS3_VALUE_RR_2_12                   ((uint8_t) 1u)
#define LSM6DS3_VALUE_RR_2_13                   ((uint8_t) 2u)
#define LSM6DS3_VALUE_RR_2_14                   ((uint8_t) 3u)

/* FIFO_CTRL1 (06h) */
#define LSM6DS3_FIELD_FTH_L_SIZE                ((uint8_t) 8u)
#define LSM6DS3_FIELD_FTH_L_POS                 ((uint8_t) 0u)

/* FIFO_CTRL2 (07h) */
#define LSM6DS3_FIELD_FTH_H_SIZE                ((uint8_t) 3u)
#define LSM6DS3_FIELD_FTH_H_POS                 ((uint8_t) 0u)

#define LSM6DS3_FIELD_FIFO_TEMP_EN_SIZE         ((uint8_t) 1u)
#define LSM6DS3_FIELD_FIFO_TEMP_EN_POS          ((uint8_t) 3u)

#define LSM6DS3_FIELD_TIMER_PEDO_FIFO_DRDY_SIZE ((uint8_t) 1u)
#define LSM6DS3_FIELD_TIMER_PEDO_FIFO_DRDY_POS  ((uint8_t) 6u)

#define LSM6DS3_FIELD_TIMER_PEDO_FIFO_EN_SIZE   ((uint8_t) 1u)
#define LSM6DS3_FIELD_TIMER_PEDO_FIFO_EN_POS    ((uint8_t) 7u)

/* FIFO_CTRL3 (08h) */
#define LSM6DS3_FIELD_DEC_FIFO_XL_SIZE          ((uint8_t) 3u)
#define LSM6DS3_FIELD_DEC_FIFO_XL_POS           ((uint8_t) 0u)

#define LSM6DS3_FIELD_DEC_FIFO_GYRO_SIZE        ((uint8_t) 3u)
#define LSM6DS3_FIELD_DEC_FIFO_GYRO_POS         ((uint8_t) 3u)

#define LSM6DS3_VALUE_DEC_FIFO_XL_NOT_PRESENT   ((uint8_t) 0u)
#define LSM6DS3_VALUE_DEC_FIFO_XL_NO            ((uint8_t) 1u)
#define LSM6DS3_VALUE_DEC_FIFO_XL_2             ((uint8_t) 2u)
#define LSM6DS3_VALUE_DEC_FIFO_XL_3             ((uint8_t) 3u)
#define LSM6DS3_VALUE_DEC_FIFO_XL_4             ((uint8_t) 4u)
#define LSM6DS3_VALUE_DEC_FIFO_XL_8             ((uint8_t) 5u)
#define LSM6DS3_VALUE_DEC_FIFO_XL_16            ((uint8_t) 6u)
#define LSM6DS3_VALUE_DEC_FIFO_XL_32            ((uint8_t) 7u)

#define LSM6DS3_VALUE_DEC_FIFO_GYRO_NOT_PRESENT ((uint8_t) 0u)
#define LSM6DS3_VALUE_DEC_FIFO_GYRO_NO          ((uint8_t) 1u)
#define LSM6DS3_VALUE_DEC_FIFO_GYRO_2           ((uint8_t) 2u)
#define LSM6DS3_VALUE_DEC_FIFO_GYRO_3           ((uint8_t) 3u)
#define LSM6DS3_VALUE_DEC_FIFO_GYRO_4           ((uint8_t) 4u)
#define LSM6DS3_VALUE_DEC_FIFO_GYRO_8           ((uint8_t) 5u)
#define LSM6DS3_VALUE_DEC_FIFO_GYRO_16          ((uint8_t) 6u)
#define LSM6DS3_VALUE_DEC_FIFO_GYRO_32          ((uint8_t) 7u)

/* FIFO_CTRL4 (09h) */
#define LSM6DS3_FIELD_DEC_FIFO_DS3_SIZE         ((uint8_t) 3u)
#define LSM6DS3_FIELD_DEC_FIFO_DS3_POS          ((uint8_t) 0u)

#define LSM6DS3_FIELD_DEC_FIFO_DS4_SIZE         ((uint8_t) 3u)
#define LSM6DS3_FIELD_DEC_FIFO_DS4_POS          ((uint8_t) 3u)

#define LSM6DS3_FIELD_ONLY_HIGH_DATA_SIZE       ((uint8_t) 1u)
#define LSM6DS3_FIELD_ONLY_HIGH_DATA_POS        ((uint8_t) 6u)

#define LSM6DS3_FIELD_STOP_ON_FTH_SIZE          ((uint8_t) 1u)
#define LSM6DS3_FIELD_STOP_ON_FTH_POS           ((uint8_t) 7u)

#define LSM6DS3_VALUE_DEC_FIFO_DS3_NOT_PRESENT  ((uint8_t) 0u)
#define LSM6DS3_VALUE_DEC_FIFO_DS3_NO           ((uint8_t) 1u)
#define LSM6DS3_VALUE_DEC_FIFO_DS3_2            ((uint8_t) 2u)
#define LSM6DS3_VALUE_DEC_FIFO_DS3_3            ((uint8_t) 3u)
#define LSM6DS3_VALUE_DEC_FIFO_DS3_4            ((uint8_t) 4u)
#define LSM6DS3_VALUE_DEC_FIFO_DS3_8            ((uint8_t) 5u)
#define LSM6DS3_VALUE_DEC_FIFO_DS3_16           ((uint8_t) 6u)
#define LSM6DS3_VALUE_DEC_FIFO_DS3_32           ((uint8_t) 7u)

#define LSM6DS3_VALUE_DEC_FIFO_DS4_NOT_PRESENT  ((uint8_t) 0u)
#define LSM6DS3_VALUE_DEC_FIFO_DS4_NO           ((uint8_t) 1u)
#define LSM6DS3_VALUE_DEC_FIFO_DS4_2            ((uint8_t) 2u)
#define LSM6DS3_VALUE_DEC_FIFO_DS4_3            ((uint8_t) 3u)
#define LSM6DS3_VALUE_DEC_FIFO_DS4_4            ((uint8_t) 4u)
#define LSM6DS3_VALUE_DEC_FIFO_DS4_8            ((uint8_t) 5u)
#define LSM6DS3_VALUE_DEC_FIFO_DS4_16           ((uint8_t) 6u)
#define LSM6DS3_VALUE_DEC_FIFO_DS4_32           ((uint8_t) 7u)

/* FIFO_CTRL5 (0Ah) */
#define LSM6DS3_FIELD_FIFO_MODE_SIZE            ((uint8_t) 3u)
#define LSM6DS3_FIELD_FIFO_MODE_POS             ((uint8_t) 0u)

#define LSM6DS3_FIELD_FIFO_ODR_SIZE             ((uint8_t) 4u)
#define LSM6DS3_FIELD_FIFO_ODR_POS              ((uint8_t) 3u)

#define LSM6DS3_VALUE_FIFO_MODE_DISABLED                ((uint8_t) 0u)
#define LSM6DS3_VALUE_FIFO_MODE_FIFO                    ((uint8_t) 1u)
#define LSM6DS3_VALUE_FIFO_MODE_CONTINUOUS_TO_FIFO      ((uint8_t) 3u)
#define LSM6DS3_VALUE_FIFO_MODE_BYPASS_TO_CONTINUOUS    ((uint8_t) 4u)
#define LSM6DS3_VALUE_FIFO_MODE_CONTINUOUS              ((uint8_t) 6u)

#define LSM6DS3_VALUE_FIFO_ODR_DISABLED         ((uint8_t) 0u)
#define LSM6DS3_VALUE_FIFO_ODR_12_5             ((uint8_t) 1u)
#define LSM6DS3_VALUE_FIFO_ODR_26               ((uint8_t) 2u)
#define LSM6DS3_VALUE_FIFO_ODR_52               ((uint8_t) 3u)
#define LSM6DS3_VALUE_FIFO_ODR_104              ((uint8_t) 4u)
#define LSM6DS3_VALUE_FIFO_ODR_208              ((uint8_t) 5u)
#define LSM6DS3_VALUE_FIFO_ODR_416              ((uint8_t) 6u)
#define LSM6DS3_VALUE_FIFO_ODR_833              ((uint8_t) 7u)
#define LSM6DS3_VALUE_FIFO_ODR_1666             ((uint8_t) 8u)
#define LSM6DS3_VALUE_FIFO_ODR_3332             ((uint8_t) 9u)
#define LSM6DS3_VALUE_FIFO_ODR_6664             ((uint8_t) 10u)

/* DRDY_PULSE_CONFIG_G (0Bh) */
#define LSM6DS3_FIELD_DRDY_MODE_SIZE            ((uint8_t) 1u)
#define LSM6DS3_FIELD_DRDY_MODE_POS             ((uint8_t) 7u)

#define LSM6DS3_INT2_WRIST_TILT_SIZE            ((uint8_t) 1u)
#define LSM6DS3_INT2_WRIST_TILT_POS             ((uint8_t) 0u)

#define LSM6DS3_VALUE_DRDY_MODE_LATCHED         ((uint8_t) 0u)
#define LSM6DS3_VALUE_DRDY_MODE_PULSED          ((uint8_t) 1u)

/* INT1_CTRL (0Dh) */
#define LSM6DS3_FIELD_INT1_STEP_DETECTOR_SIZE   ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT1_STEP_DETECTOR_POS    ((uint8_t) 7u)

#define LSM6DS3_FIELD_INT1_SIGN_MOT_SIZE        ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT1_SIGN_MOT_POS         ((uint8_t) 6u)

#define LSM6DS3_FIELD_INT1_FULL_FLAG_SIZE       ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT1_FULL_FLAG_POS        ((uint8_t) 5u)

#define LSM6DS3_FIELD_INT1_FIFO_OVR_SIZE        ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT1_FIFO_OVR_POS         ((uint8_t) 4u)

#define LSM6DS3_FIELD_INT1_FTH_SIZE             ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT1_FTH_POS              ((uint8_t) 3u)

#define LSM6DS3_FIELD_INT1_BOOT_SIZE            ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT1_BOOT_POS             ((uint8_t) 2u)

#define LSM6DS3_FIELD_INT1_DRDY_G_SIZE          ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT1_DRDY_G_POS           ((uint8_t) 1u)

#define LSM6DS3_FIELD_INT1_DRDY_XL_SIZE         ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT1_DRDY_XL_POS          ((uint8_t) 0u)

/* INT2_CTRL (0Eh) */
#define LSM6DS3_FIELD_INT2_STEP_DELTA_SIZE      ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT2_STEP_DELTA_POS       ((uint8_t) 7u)

#define LSM6DS3_FIELD_INT2_STEP_COUNT_OV_SIZE   ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT2_STEP_COUNT_OV_POS    ((uint8_t) 6u)

#define LSM6DS3_FIELD_INT2_FULL_FLAG_SIZE       ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT2_FULL_FLAG_POS        ((uint8_t) 5u)

#define LSM6DS3_FIELD_INT2_FIFO_OVR_SIZE        ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT2_FIFO_OVR_POS         ((uint8_t) 4u)

#define LSM6DS3_FIELD_INT2_FTH_SIZE             ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT2_FTH_POS              ((uint8_t) 3u)

#define LSM6DS3_FIELD_INT2_DRDY_TEMP_SIZE       ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT2_DRDY_TEMP_POS        ((uint8_t) 2u)

#define LSM6DS3_FIELD_INT2_DRDY_G_SIZE          ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT2_DRDY_G_POS           ((uint8_t) 1u)

#define LSM6DS3_FIELD_INT2_DRDY_XL_SIZE         ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT2_DRDY_XL_POS          ((uint8_t) 0u)

/* CTRL1_XL (10h) */
#define LSM6DS3_FIELD_ODR_XL_SIZE       ((uint8_t) 4u)
#define LSM6DS3_FIELD_ODR_XL_POS        ((uint8_t) 4u)

#define LSM6DS3_FIELD_FS_XL_SIZE        ((uint8_t) 2u)
#define LSM6DS3_FIELD_FS_XL_POS         ((uint8_t) 2u)

#define LSM6DS3_FIELD_LPF1_BW_SEL_SIZE  ((uint8_t) 1u)
#define LSM6DS3_FIELD_LPF1_BW_SEL_POS   ((uint8_t) 1u)

#define LSM6DS3_FIELD_BW0_XL_SIZE       ((uint8_t) 1u)
#define LSM6DS3_FIELD_BW0_XL_POS        ((uint8_t) 0u)

#define LSM6DS3_VALUE_BW0_XL_1500       ((uint8_t) 0u)
#define LSM6DS3_VALUE_BW0_XL_400        ((uint8_t) 1u)

#define LSM6DS3_VALUE_FS_XL_2g          ((uint8_t) 0u)
#define LSM6DS3_VALUE_FS_XL_16g         ((uint8_t) 1u)
#define LSM6DS3_VALUE_FS_XL_4g          ((uint8_t) 2u)
#define LSM6DS3_VALUE_FS_XL_8g          ((uint8_t) 3u)

#define LSM6DS3_VALUE_ODR_XL_DISABLED   ((uint8_t) 0u)
#define LSM6DS3_VALUE_ODR_XL_1_6        ((uint8_t) 11u) /* 0b1011 */
#define LSM6DS3_VALUE_ODR_XL_12_5       ((uint8_t) 1u)
#define LSM6DS3_VALUE_ODR_XL_26         ((uint8_t) 2u)
#define LSM6DS3_VALUE_ODR_XL_52         ((uint8_t) 3u)
#define LSM6DS3_VALUE_ODR_XL_104        ((uint8_t) 4u)
#define LSM6DS3_VALUE_ODR_XL_208        ((uint8_t) 5u)
#define LSM6DS3_VALUE_ODR_XL_416        ((uint8_t) 6u)
#define LSM6DS3_VALUE_ODR_XL_833        ((uint8_t) 7u)
#define LSM6DS3_VALUE_ODR_XL_1666       ((uint8_t) 8u)
#define LSM6DS3_VALUE_ODR_XL_3332       ((uint8_t) 9u)
#define LSM6DS3_VALUE_ODR_XL_6664       ((uint8_t) 10u)

/* CTRL2_G (11h) */
#define LSM6DS3_FIELD_ODR_G_SIZE       ((uint8_t) 4u)
#define LSM6DS3_FIELD_ODR_G_POS        ((uint8_t) 4u)

#define LSM6DS3_FIELD_FS_G_SIZE        ((uint8_t) 3u)
#define LSM6DS3_FIELD_FS_G_POS         ((uint8_t) 1u)

#define LSM6DS3_VALUE_FS_G_125         ((uint8_t) 1u)
#define LSM6DS3_VALUE_FS_G_245         ((uint8_t) 0u)
#define LSM6DS3_VALUE_FS_G_500         ((uint8_t) 2u)
#define LSM6DS3_VALUE_FS_G_1000        ((uint8_t) 4u)
#define LSM6DS3_VALUE_FS_G_2000        ((uint8_t) 6u)

#define LSM6DS3_VALUE_ODR_G_DISABLED   ((uint8_t) 0u)
#define LSM6DS3_VALUE_ODR_G_12_5       ((uint8_t) 1u)
#define LSM6DS3_VALUE_ODR_G_26         ((uint8_t) 2u)
#define LSM6DS3_VALUE_ODR_G_52         ((uint8_t) 3u)
#define LSM6DS3_VALUE_ODR_G_104        ((uint8_t) 4u)
#define LSM6DS3_VALUE_ODR_G_208        ((uint8_t) 5u)
#define LSM6DS3_VALUE_ODR_G_416        ((uint8_t) 6u)
#define LSM6DS3_VALUE_ODR_G_833        ((uint8_t) 7u)
#define LSM6DS3_VALUE_ODR_G_1666       ((uint8_t) 8u)
#define LSM6DS3_VALUE_ODR_G_3332       ((uint8_t) 9u)
#define LSM6DS3_VALUE_ODR_G_6664       ((uint8_t) 10u)

/* CTRL3_C (12h) */
#define LSM6DS3_FIELD_BOOT_SIZE         ((uint8_t) 1u)
#define LSM6DS3_FIELD_BOOT_POS          ((uint8_t) 7u)

#define LSM6DS3_FIELD_BDU_SIZE          ((uint8_t) 1u)
#define LSM6DS3_FIELD_BDU_POS           ((uint8_t) 6u)

#define LSM6DS3_FIELD_H_LACTIVE_SIZE    ((uint8_t) 1u)
#define LSM6DS3_FIELD_H_LACTIVE_POS     ((uint8_t) 5u)

#define LSM6DS3_FIELD_PP_OD_SIZE        ((uint8_t) 1u)
#define LSM6DS3_FIELD_PP_OD_POS         ((uint8_t) 4u)

#define LSM6DS3_FIELD_SIM_SIZE          ((uint8_t) 1u)
#define LSM6DS3_FIELD_SIM_POS           ((uint8_t) 3u)

#define LSM6DS3_FIELD_IF_INC_SIZE       ((uint8_t) 1u)
#define LSM6DS3_FIELD_IF_INC_POS        ((uint8_t) 2u)

#define LSM6DS3_FIELD_BLE_SIZE          ((uint8_t) 1u)
#define LSM6DS3_FIELD_BLE_POS           ((uint8_t) 1u)

#define LSM6DS3_FIELD_SW_RESET_SIZE     ((uint8_t) 1u)
#define LSM6DS3_FIELD_SW_RESET_POS      ((uint8_t) 0u)

/* CTRL4_C (13h) */
#define LSM6DS3_FIELD_DEN_XL_EN_SIZE        ((uint8_t) 1u)
#define LSM6DS3_FIELD_DEN_XL_EN_POS         ((uint8_t) 7u)

#define LSM6DS3_FIELD_SLEEP_SIZE            ((uint8_t) 1u)
#define LSM6DS3_FIELD_SLEEP_POS             ((uint8_t) 6u)

#define LSM6DS3_FIELD_INT2_on_INT1_SIZE     ((uint8_t) 1u)
#define LSM6DS3_FIELD_INT2_on_INT1_POS      ((uint8_t) 5u)

#define LSM6DS3_FIELD_DEN_DRDY_INT1_SIZE    ((uint8_t) 1u)
#define LSM6DS3_FIELD_DEN_DRDY_INT1_POS     ((uint8_t) 4u)

#define LSM6DS3_FIELD_DRDY_MASK_SIZE        ((uint8_t) 1u)
#define LSM6DS3_FIELD_DRDY_MASK_POS         ((uint8_t) 3u)

#define LSM6DS3_FIELD_I2C_disable_SIZE      ((uint8_t) 1u)
#define LSM6DS3_FIELD_I2C_disable_POS       ((uint8_t) 2u)

#define LSM6DS3_FIELD_LPF1_SEL_G_SIZE       ((uint8_t) 1u)
#define LSM6DS3_FIELD_LPF1_SEL_G_POS        ((uint8_t) 1u)

/* CTRL5_XL (14h) */
#define LSM6DS3_FIELD_ROUNDING_SIZE     ((uint8_t) 3u)
#define LSM6DS3_FIELD_ROUNDING_POS      ((uint8_t) 5u)

#define LSM6DS3_FIELD_DEN_LH_SIZE       ((uint8_t) 1u)
#define LSM6DS3_FIELD_DEN_LH_POS        ((uint8_t) 4u)

#define LSM6DS3_FIELD_ST_G_SIZE         ((uint8_t) 2u)
#define LSM6DS3_FIELD_ST_G_POS          ((uint8_t) 2u)

#define LSM6DS3_FIELD_ST_XL_SIZE        ((uint8_t) 2u)
#define LSM6DS3_FIELD_ST_XL_POS         ((uint8_t) 0u)

#define LSM6DS3_VALUE_ROUNDING_NO       ((uint8_t) 0u)

#define LSM6DS3_VALUE_ST_G_NORMAL       ((uint8_t) 0u)
#define LSM6DS3_VALUE_ST_G_POSITIVE     ((uint8_t) 1u)
#define LSM6DS3_VALUE_ST_G_NEGATIVE     ((uint8_t) 3u)

#define LSM6DS3_VALUE_ST_XL_NORMAL      ((uint8_t) 0u)
#define LSM6DS3_VALUE_ST_XL_POSITIVE    ((uint8_t) 1u)
#define LSM6DS3_VALUE_ST_XL_NEGATIVE    ((uint8_t) 2u)

/* CTRL6_XL (15h) */
#define LSM6DS3_FIELD_TRIG_MODE_SIZE    ((uint8_t) 3u)
#define LSM6DS3_FIELD_TRIG_MODE_POS     ((uint8_t) 5u)

#define LSM6DS3_FIELD_XL_HM_MODE_SIZE   ((uint8_t) 1u)
#define LSM6DS3_FIELD_XL_HM_MODE_POS    ((uint8_t) 4u)

#define LSM6DS3_FIELD_USR_OFF_W_SIZE    ((uint8_t) 1u)
#define LSM6DS3_FIELD_USR_OFF_W_POS     ((uint8_t) 3u)

#define LSM6DS3_FIELD_FTYPE_SIZE        ((uint8_t) 2u)
#define LSM6DS3_FIELD_FTYPE_POS         ((uint8_t) 0u)

#define LSM6DS3_VALUE_TRIG_MODE_EDGE            ((uint8_t) 4u)
#define LSM6DS3_VALUE_TRIG_MODE_LEVEL           ((uint8_t) 2u)
#define LSM6DS3_VALUE_TRIG_MODE_LEVEL_LATCHED   ((uint8_t) 3u)
#define LSM6DS3_VALUE_TRIG_MODE_LEVEL_FIFO      ((uint8_t) 6u)

#define LSM6DS3_VALUE_FTYPE_0                   ((uint8_t) 2u)
#define LSM6DS3_VALUE_FTYPE_1                   ((uint8_t) 1u)
#define LSM6DS3_VALUE_FTYPE_2                   ((uint8_t) 0u)
#define LSM6DS3_VALUE_FTYPE_3                   ((uint8_t) 3u)

/* CTRL7_G (16h) */
#define LSM6DS3_FIELD_G_HM_MODE_SIZE        ((uint8_t) 1u)
#define LSM6DS3_FIELD_G_HM_MODE_POS         ((uint8_t) 7u)

#define LSM6DS3_FIELD_HP_EN_G_SIZE          ((uint8_t) 1u)
#define LSM6DS3_FIELD_HP_EN_G_POS           ((uint8_t) 6u)

#define LSM6DS3_FIELD_HPM_G_SIZE            ((uint8_t) 2u)
#define LSM6DS3_FIELD_HPM_G_POS             ((uint8_t) 4u)

#define LSM6DS3_FIELD_ROUNDING_STATUS_SIZE  ((uint8_t) 1u)
#define LSM6DS3_FIELD_ROUNDING_STATUS_POS   ((uint8_t) 2u)

#define LSM6DS3_VALUE_HPM_G_16m             ((uint8_t) 0u)
#define LSM6DS3_VALUE_HPM_G_65m             ((uint8_t) 1u)
#define LSM6DS3_VALUE_HPM_G_260m            ((uint8_t) 2u)
#define LSM6DS3_VALUE_HPM_G_1040m           ((uint8_t) 3u)

/* CTRL8_XL (17h) */
#define LSM6DS3_FIELD_LPF2_XL_EN_SIZE       ((uint8_t) 1u)
#define LSM6DS3_FIELD_LPF2_XL_EN_POS        ((uint8_t) 7u)

#define LSM6DS3_FIELD_HPCF_XL_SIZE          ((uint8_t) 2u)
#define LSM6DS3_FIELD_HPCF_XL_POS           ((uint8_t) 5u)

#define LSM6DS3_FIELD_HP_REF_MODE_SIZE      ((uint8_t) 2u)
#define LSM6DS3_FIELD_HP_REF_MODE_POS       ((uint8_t) 4u)

#define LSM6DS3_FIELD_INPUT_COMPOSITE_SIZE  ((uint8_t) 1u)
#define LSM6DS3_FIELD_INPUT_COMPOSITE_POS   ((uint8_t) 3u)

#define LSM6DS3_FIELD_HP_SLOPE_XL_EN_SIZE   ((uint8_t) 1u)
#define LSM6DS3_FIELD_HP_SLOPE_XL_EN_POS    ((uint8_t) 2u)

#define LSM6DS3_FIELD_LOW_PASS_ON_6D_SIZE   ((uint8_t) 1u)
#define LSM6DS3_FIELD_LOW_PASS_ON_6D_POS    ((uint8_t) 0u)

/* CTRL9_XL (18h) */
#define LSM6DS3_FIELD_DEN_X_SIZE            ((uint8_t) 1u)
#define LSM6DS3_FIELD_DEN_X_POS             ((uint8_t) 7u)

#define LSM6DS3_FIELD_DEN_Y_SIZE            ((uint8_t) 1u)
#define LSM6DS3_FIELD_DEN_Y_POS             ((uint8_t) 6u)

#define LSM6DS3_FIELD_DEN_Z_SIZE            ((uint8_t) 1u)
#define LSM6DS3_FIELD_DEN_Z_POS             ((uint8_t) 5u)

#define LSM6DS3_FIELD_DEN_XL_G_SIZE         ((uint8_t) 1u)
#define LSM6DS3_FIELD_DEN_XL_G_POS          ((uint8_t) 4u)

#define LSM6DS3_FIELD_SOFT_EN_SIZE          ((uint8_t) 1u)
#define LSM6DS3_FIELD_SOFT_EN_POS           ((uint8_t) 2u)

/* CTRL10_C (19h) */
#define LSM6DS3_FIELD_WRIST_TILT_EN_SIZE    ((uint8_t) 1u)
#define LSM6DS3_FIELD_WRIST_TILT_EN_POS     ((uint8_t) 7u)

#define LSM6DS3_FIELD_TIMER_EN_SIZE         ((uint8_t) 1u)
#define LSM6DS3_FIELD_TIMER_EN_POS          ((uint8_t) 5u)

#define LSM6DS3_FIELD_PEDO_EN_SIZE          ((uint8_t) 1u)
#define LSM6DS3_FIELD_PEDO_EN_POS           ((uint8_t) 4u)

#define LSM6DS3_FIELD_TILT_EN_SIZE          ((uint8_t) 1u)
#define LSM6DS3_FIELD_TILT_EN_POS           ((uint8_t) 3u)

#define LSM6DS3_FIELD_FUNC_EN_SIZE          ((uint8_t) 1u)
#define LSM6DS3_FIELD_FUNC_EN_POS           ((uint8_t) 2u)

#define LSM6DS3_FIELD_PEDO_RST_STEP_SIZE    ((uint8_t) 1u)
#define LSM6DS3_FIELD_PEDO_RST_STEP_POS     ((uint8_t) 1u)

#define LSM6DS3_FIELD_SIGN_MOTION_EN_SIZE   ((uint8_t) 1u)
#define LSM6DS3_FIELD_SIGN_MOTION_EN_POS    ((uint8_t) 0u)

/* MASTER_CONFIG (1Ah) */
#define LSM6DS3_FIELD_DRDY_ON_INT1_SIZE         ((uint8_t) 1u)
#define LSM6DS3_FIELD_DRDY_ON_INT1_POS          ((uint8_t) 7u)

#define LSM6DS3_FIELD_DATA_VALID_SEL_FIFO_SIZE  ((uint8_t) 1u)
#define LSM6DS3_FIELD_DATA_VALID_SEL_FIFO_POS   ((uint8_t) 6u)

#define LSM6DS3_FIELD_START_CONFIG_SIZE         ((uint8_t) 1u)
#define LSM6DS3_FIELD_START_CONFIG_POS          ((uint8_t) 4u)

#define LSM6DS3_FIELD_PULL_UP_EN_SIZE           ((uint8_t) 1u)
#define LSM6DS3_FIELD_PULL_UP_EN_POS            ((uint8_t) 3u)

#define LSM6DS3_FIELD_PASS_THROUGH_MODE_SIZE    ((uint8_t) 1u)
#define LSM6DS3_FIELD_PASS_THROUGH_MODE_POS     ((uint8_t) 2u)

#define LSM6DS3_FIELD_IRON_EN_SIZE              ((uint8_t) 1u)
#define LSM6DS3_FIELD_IRON_EN_POS               ((uint8_t) 1u)

#define LSM6DS3_FIELD_MASTER_ON_SIZE            ((uint8_t) 1u)
#define LSM6DS3_FIELD_MASTER_ON_POS             ((uint8_t) 0u)

/* helper macros */

#define LSM6DS3_REG(x)                      (LSM6DS3_REGISTER_ADDRESS_ ## x)
#define LSM6DS3_FIELD_VALUE(field, value)   (( ((value) & ((1u << (LSM6DS3_FIELD_ ## field ## _SIZE)) - 1u)) << (LSM6DS3_FIELD_ ## field ## _POS)))
#define LSM6DS3_FIELD_MASK(field)           LSM6DS3_FIELD_VALUE(field, 0xFFu)
#define LSM6DS3_FIELD_ENABLE(field)         LSM6DS3_FIELD_VALUE(field, 0x01u)
#define LSM6DS3_FIELD_NAMED(field, name)    LSM6DS3_FIELD_VALUE(field, LSM6DS3_VALUE_ ## field ## _ ## name)
#define LSM6DS3_GET_FIELD(var, field)       ((var & LSM6DS3_FIELD_MASK(field)) >> (LSM6DS3_FIELD_ ## field ## _POS))

#endif /* LSM6DS3_DEFS_H_ */
