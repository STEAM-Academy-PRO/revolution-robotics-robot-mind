#include "DcMotor.h"
#include "CommonLibraries/log.h"

#include "CommonLibraries/converter.h"
#include "CommonLibraries/functions.h"
#include "libraries/controller/pid.h"
#include "libraries/interpolation/linear_interpolate.h"
#include "utils.h"

#include <compiler.h>
#include <string.h>
#include <math.h>

#define MOTOR_CONTROL_PWM               ((uint8_t) 0u)
#define MOTOR_CONTROL_SPEED             ((uint8_t) 1u)
#define MOTOR_CONTROL_POSITION          ((uint8_t) 2u)
#define MOTOR_CONTROL_POSITION_RELATIVE ((uint8_t) 3u)

typedef enum {
    DcMotorStatus_Normal = 0u,
    DcMotorStatus_Blocked = 1u,
    DcMotorStatus_GoalReached = 2u,
} __attribute__((packed)) DcMotorStatus_t;

#define DRIVE_CONTSTRAINED_POWER    ((uint8_t) 0u)
#define DRIVE_CONTSTRAINED_SPEED    ((uint8_t) 1u)

/* The time it takes to realize that the motors can't move */
#define MOTOR_TIMEOUT_THRESHOLD     ((uint16_t) 10u)  /** < 100ms @ 10ms update */

/* The time it takes to realize we can't get closer to a position target */
#define POSITION_TIMEOUT            ((uint16_t) 50u)  /** < 0.5s @ 10ms update */

// #define DOUBLE_ENCODER_RESOLUTION

#ifdef DOUBLE_ENCODER_RESOLUTION
const float pulses_per_encoder_slit = 4.0f;
#else
const float pulses_per_encoder_slit = 2.0f;
#endif

typedef enum {
    PositionBreakpointKind_Degrees,
    PositionBreakpointKind_Relative
} PositionBreakpointKind_t;

typedef struct
{
    /* configuration */
    bool isEmulated; /** < Disconnects driver from the motor driver IC and enables a digital twin */
    PidConfig_t slowPositionConfig;
    PidConfig_t fastPositionConfig;
    float positionBreakpoint; /** < in the unit specified by positionBreakpointKind, relative to the distance from the goal */
    PositionBreakpointKind_t positionBreakpointKind;
    PID_t positionController;
    PID_t speedController;
    float resolution;
    uint16_t atLeastOneDegree;  /** < encoder ticks in a degree, or 1 if resolution <= 360 */
    LUT_t nonlinearity;
    float nonlinearity_xs[10];
    float nonlinearity_ys[10];

    /**
    If drive request does not have limits (i.e. they are set to 0), we use the limits we received
    during port configuration.
    */
    float positionControllerLowerLimit;
    float positionControllerUpperLimit;
    float speedControllerLowerLimit;
    float speedControllerUpperLimit;

    float maxAcceleration;
    float maxDeceleration;

    DriveRequest_t currentRequest;

    /* last status */
    DcMotorStatus_t motorStatus;
    int32_t lastPosition;
    int32_t prevPosDiff;
    float currentSpeed; /** < rpm */
    uint16_t motorTimeout;
    uint8_t lastCreatedCommandVersion;
    uint32_t minPositionDistance;
    uint16_t minPositionTimeout;

    /* current status */
    int32_t position;
    float emulatedSpeed;
    float emulatedPosition;
} MotorLibrary_Dc_Data_t;

typedef struct
{
    DcMotorStatus_t status;
    uint8_t pwm;
    int32_t position;
    float speed;
    uint8_t version;
} __attribute__((packed)) DcMotorStatusSlot_t;

// assert that the struct is packed
_Static_assert(sizeof(DcMotorStatusSlot_t) == 11u);

static void emulator_reset(MotorLibrary_Dc_Data_t* libdata)
{
    libdata->emulatedSpeed = 0.0f;
    libdata->emulatedPosition = 0.0f;
}

/**
 * Based on PWM and motor model, calculates a new position.
 */
static void emulator_tick(MotorLibrary_Dc_Data_t* libdata, int16_t pwm, float dt)
{
    const float MIN_SPEED = 0.1f; /** < in encoder ticks per second */
    // TODO re-identify the motors to get a more realistic characteristic.
    const float K = 50.0f; // RPM / %PWM
    libdata->emulatedSpeed = K * (float) pwm;

    if (fabsf(libdata->emulatedSpeed) < MIN_SPEED)
    {
        libdata->emulatedSpeed = 0.0f;
    }

    /* Apply calculated speed to the position counter. We use a float intermediary to reduce error */
    libdata->emulatedPosition += dt * libdata->emulatedSpeed;
    libdata->position = (int32_t) lroundf(libdata->emulatedPosition);
}

static void _reset_timeout(uint16_t* timer)
{
    *timer = 0u;
}

static void _tick_timeout(uint16_t* timer, uint16_t timeout)
{
    if (*timer < timeout)
    {
        *timer += 1u;
    }
}

static bool _has_timeout_elapsed(const uint16_t* timer, uint16_t timeout)
{
    return *timer >= timeout;
}

static bool _is_motor_blocked(MotorLibrary_Dc_Data_t* libdata, float u)
{
    if (libdata->prevPosDiff != 0)
    {
        return false;
    }
    if (libdata->speedController.config.LowerLimit < u && u < libdata->speedController.config.UpperLimit)
    {
        return false;
    }

    return true;
}

static int32_t degrees_to_ticks(const MotorLibrary_Dc_Data_t* libdata, float degrees)
{
    return (int32_t) lroundf(map(degrees, 0.0f, 360.0f, 0.0f, fabsf(libdata->resolution)));
}

static int32_t ticks_to_degrees(const MotorLibrary_Dc_Data_t* libdata, float value)
{
    return (int32_t) lroundf(map(value, 0.0f, fabsf(libdata->resolution), 0.0f, 360.0f));
}

static void _update_status_data(const MotorPort_t* motorPort, int16_t pwm)
{
    MotorLibrary_Dc_Data_t* libdata = (MotorLibrary_Dc_Data_t*) motorPort->libraryData;

    DcMotorStatusSlot_t status_struct = (DcMotorStatusSlot_t) {
        .status = libdata->motorStatus,
        .pwm = (uint8_t) (pwm/2), // Divide by 2 to map 0..200 (physical timer config) to 0..100 (%)
        .position = ticks_to_degrees(libdata, libdata->lastPosition),
        .speed = libdata->currentSpeed,
        .version = libdata->currentRequest.version
    };

    MotorPortHandler_Call_UpdatePortStatus(motorPort->port_idx, (ByteArray_t) {
        .bytes = (uint8_t*) &status_struct,
        .count = sizeof(status_struct)
    });
}

/* Clears motor status when configuration or drive command is changed */
void _reset_motor_status(MotorPort_t* motorPort)
{
    MotorLibrary_Dc_Data_t* libdata = (MotorLibrary_Dc_Data_t*) motorPort->libraryData;

    libdata->motorStatus = DcMotorStatus_Normal;
    _reset_timeout(&libdata->motorTimeout);
    _update_status_data(motorPort, 0);
}

/**
 * Take the last drive requests version and set an empty request with that version. This
 * makes the driver ignore the last command that was issued before configuration.
 */
static void ignore_last_drive_request(MotorPort_t* motorPort)
{
    MotorLibrary_Dc_Data_t* libdata = (MotorLibrary_Dc_Data_t*) motorPort->libraryData;

    /* read last request to get the version */
    DriveRequest_t driveRequest;
    MotorPortHandler_Read_DriveRequest(motorPort->port_idx, &driveRequest);

    driveRequest.request_type = DriveRequest_RequestType_Power;
    driveRequest.request.power = 0;

    driveRequest.speed_limit = 0.0f;
    driveRequest.power_limit = 0.0f;

    /* set this dummy request as active */
    libdata->currentRequest = driveRequest;
}

static void initialize_driver(MotorPort_t* motorPort, bool isEmulated)
{
    LOG("MotorPort %d: Initialize DC motor driver\n");
    MotorPortHandler_Call_UpdateStatusSlotSize(11u);

    MotorLibrary_Dc_Data_t* libdata = MotorPortHandler_Call_Allocate(sizeof(MotorLibrary_Dc_Data_t));

    libdata->isEmulated = isEmulated;
    emulator_reset(libdata);

    pid_initialize(&libdata->positionController);
    pid_initialize(&libdata->speedController);

    libdata->positionControllerLowerLimit = 0.0f;
    libdata->positionControllerUpperLimit = 0.0f;

    libdata->speedControllerLowerLimit = 0.0f;
    libdata->speedControllerUpperLimit = 0.0f;

    libdata->maxAcceleration = 0.0f;
    libdata->maxDeceleration = 0.0f;

    libdata->resolution = 360.0f;
    libdata->position = 0;
    libdata->prevPosDiff = 0;
    libdata->currentSpeed = 0.0f;
    libdata->lastPosition = 0;
    libdata->minPositionDistance = UINT32_MAX;
    _reset_timeout(&libdata->minPositionTimeout);

    /* use linear characteristic by default */
    libdata->nonlinearity_xs[0] = 0.0f;
    libdata->nonlinearity_xs[1] = 100.0f;
    libdata->nonlinearity_ys[0] = 0.0f;
    libdata->nonlinearity_ys[1] = 100.0f;
    libdata->nonlinearity.size = 2u;
    libdata->nonlinearity.xs = &libdata->nonlinearity_xs[0];
    libdata->nonlinearity.ys = &libdata->nonlinearity_ys[0];

    motorPort->libraryData = libdata;
    MotorPort_EnableExti0(motorPort);
#ifdef DOUBLE_ENCODER_RESOLUTION
    MotorPort_EnableExti1(motorPort);
#endif
    MotorPort_SetGreenLed(motorPort, true);

    _reset_motor_status(motorPort);

    // Initializes `currentRequest` to a dummy request that will be ignored by the driver.
    // Also sets the version to the last created command version to make sure the driver
    // will ignore the last command that was issued before configuration.
    ignore_last_drive_request(motorPort);

    // Make sure we generate a request that will not get immediately ignored by
    // the above call to `ignore_last_drive_request`.
    libdata->lastCreatedCommandVersion = libdata->currentRequest.version;
}

MotorLibraryStatus_t DcMotor_Load(MotorPort_t* motorPort)
{
    initialize_driver(motorPort, false);

    return MotorLibraryStatus_Ok;
}

/**
 * Initialize driver in DC motor emulation mode to support HIL-testing higher level control.
 *
 * This driver variant provides the same interface as DcMotor, without driving an actual motor. The
 * driver maintains and updates a virual position counter.
 *
 * TODO: the driver should implement a characteristic close to the identified motors for it to act
 * as a proper digital twin. The DcMotor driver should also be refactored to reuse code. The emulator
 * driver needs to periodically react to the requested PWM and somehow apply position counter changes
 * to the encoder input signals, everything else should be the same.
 */
MotorLibraryStatus_t DcMotorEmulator_Load(MotorPort_t* motorPort)
{
    initialize_driver(motorPort, true);

    return MotorLibraryStatus_Ok;
}

MotorLibraryStatus_t DcMotor_Unload(MotorPort_t* motorPort)
{
    MotorPort_SetDriveValue(motorPort, 0);
    MotorPort_SetGreenLed(motorPort, false);
    MotorPort_DisableExti0(motorPort);
    MotorPort_DisableExti1(motorPort);
    MotorPort_WriteMaxCurrent(motorPort, 0.0f);
    MotorPortHandler_Call_Free(&motorPort->libraryData);

    return MotorLibraryStatus_Ok;
}

/**
 * Calculates motor speed from the tracked encoder pulse count.
 */
static void _update_current_speed(MotorLibrary_Dc_Data_t* libdata)
{
    /* Calculate current speed (no need to lock here, int32 copy is atomic and lastPosition is only written on one thread) */
    int32_t current_position = libdata->position * sgn_int32(libdata->resolution);
    int32_t posDiff = current_position - libdata->lastPosition;
    int32_t lastPosDiff = libdata->prevPosDiff;
    libdata->prevPosDiff = posDiff;
    libdata->lastPosition = current_position;

    /*
     * Calculate speed - 10ms cycle time, 2 consecutive samples (so 0.02s total window width)
     * one complete revolution in one tick means 100 revolutions in a second, or 6000 RPM.
     *
     * speed = dPos / dt, dt = 0.02s -> x50, result unit is RPM
     */
    //bool was_moving = (int)libdata->currentSpeed != 0;
    libdata->currentSpeed = map(posDiff + lastPosDiff, 0.0f, fabsf(libdata->resolution), 0.0f, 3000.0f);
    //bool is_moving = (int)libdata->currentSpeed != 0;
    //if (was_moving || is_moving){
    //    LOG("Motor speed: %d\n", (int)libdata->currentSpeed);
    //}
}

static void _process_new_request(MotorPort_t* motorPort, MotorLibrary_Dc_Data_t* libdata, const DriveRequest_t* driveRequest)
{
    DriveRequest_RequestType_t last_request_type = libdata->currentRequest.request_type;

    const char* request_kind;
    switch (driveRequest->request_type)
    {
        case DriveRequest_RequestType_Power:
            request_kind = "power";
            break;
        case DriveRequest_RequestType_Speed:
            request_kind = "speed";
            break;
        case DriveRequest_RequestType_Position:
            libdata->minPositionDistance = UINT32_MAX;
            _reset_timeout(&libdata->minPositionTimeout);
            request_kind = "position";
            break;
        default:
            request_kind = "unknown";
            break;
    }

    LOG("Motor %u: new %s request: %u\n", motorPort->port_idx, request_kind, driveRequest->version);

    if (last_request_type != driveRequest->request_type)
    {
        pid_reset(&libdata->speedController);
        pid_reset(&libdata->positionController);
    }

    libdata->currentRequest = *driveRequest;
    _reset_motor_status(motorPort);

    if (libdata->currentRequest.request_type != DriveRequest_RequestType_Power)
    {
        /* set up limits */
        if (libdata->currentRequest.speed_limit == 0.0f)
        {
            /* speed limits, already converted from dps to ticks per sec */
            libdata->positionController.config.LowerLimit = libdata->positionControllerLowerLimit;
            libdata->positionController.config.UpperLimit = libdata->positionControllerUpperLimit;
        }
        else
        {
            libdata->positionController.config.LowerLimit = -libdata->currentRequest.speed_limit;
            libdata->positionController.config.UpperLimit = libdata->currentRequest.speed_limit;
        }

        if (libdata->currentRequest.power_limit == 0.0f)
        {
            /* default power limits [as speed limits before static linearization] */
            libdata->speedController.config.LowerLimit = libdata->speedControllerLowerLimit;
            libdata->speedController.config.UpperLimit = libdata->speedControllerUpperLimit;
        }
        else
        {
            /*
            Create inverse table (map from ys to xs, the swap is not a typo)

            This maps the power limits to appropriate output limits of the speed controller, taking
            motor characteristics into account.

            // FIXME: this needs to be revisited, something is not quite right around these limits
            or the linearization implementation.
            */
            float xs[libdata->nonlinearity.size];
            for (size_t i = 0u; i < libdata->nonlinearity.size; i++)
            {
                xs[i] = fabsf(libdata->nonlinearity_ys[i]);
            }

            LUT_t inv = {
                .xs = xs,
                .ys = libdata->nonlinearity_xs,
                .size = libdata->nonlinearity.size
            };

            // rescale power_limit from -100..100 to -200..200 before lookup
            float power_limit = linear_interpolate(inv, 2.0f * libdata->currentRequest.power_limit);
            libdata->speedController.config.LowerLimit = -power_limit;
            libdata->speedController.config.UpperLimit = power_limit;
        }
    }
}

static void select_pid(PID_t* controller, const PidConfig_t* coefficients)
{
    controller->config.P = coefficients->P;
    controller->config.I = coefficients->I;
    controller->config.D = coefficients->D;
}

static int16_t _run_motor_control(MotorPort_t* motorPort, MotorLibrary_Dc_Data_t* libdata)
{
    if (libdata->currentRequest.request_type == DriveRequest_RequestType_Power)
    {
        return libdata->currentRequest.request.power;
    }

    float reqSpeed = 0.0f;
    if (libdata->currentRequest.request_type == DriveRequest_RequestType_Speed)
    {
        /* requested speed is given, already converted from si */
        reqSpeed = libdata->currentRequest.request.speed;

        /* acceleration limiting */
        if (libdata->currentSpeed > 0.0f)
        {
            reqSpeed = constrain_f32(reqSpeed, libdata->currentSpeed - libdata->maxDeceleration, libdata->currentSpeed + libdata->maxAcceleration);
        }
        else
        {
            reqSpeed = constrain_f32(reqSpeed, libdata->currentSpeed - libdata->maxAcceleration, libdata->currentSpeed + libdata->maxDeceleration);
        }
    }
    else
    {
        uint32_t distanceFromGoal = (uint32_t)abs_int32(libdata->lastPosition - libdata->currentRequest.request.position);
        if (distanceFromGoal < libdata->currentRequest.positionBreakpoint)
        {
            select_pid(&libdata->positionController, &libdata->slowPositionConfig);
        }
        else
        {
            select_pid(&libdata->positionController, &libdata->fastPositionConfig);
        }

        /* update status if goal is reached */
        if (distanceFromGoal < libdata->atLeastOneDegree)
        {
            if (libdata->motorStatus != DcMotorStatus_GoalReached) {
                LOG("Motor %u: request %u: goal reached\n", motorPort->port_idx, libdata->currentRequest.version);
                libdata->motorStatus = DcMotorStatus_GoalReached;
            }
        }
        else
        {
            /*
            Keep track of the minimum distance and apply a timeout. If we can't get closer to
            the goal, we shouldn't wait forever in a misguided hope.
            */
            if (distanceFromGoal < libdata->minPositionDistance)
            {
                libdata->minPositionDistance = distanceFromGoal;
                _reset_timeout(&libdata->minPositionTimeout);
            }
            else if (!_has_timeout_elapsed(&libdata->minPositionTimeout, POSITION_TIMEOUT))
            {
                _tick_timeout(&libdata->minPositionTimeout, POSITION_TIMEOUT);
                if (_has_timeout_elapsed(&libdata->minPositionTimeout, POSITION_TIMEOUT))
                {
                    LOG("Motor %u: request %u: timeout\n", motorPort->port_idx, libdata->currentRequest.version);
                    libdata->motorStatus = DcMotorStatus_GoalReached;
                }
            }
        }
        /* calculate speed to reach requested position */
        reqSpeed = pid_update(&libdata->positionController, libdata->currentRequest.request.position, libdata->lastPosition);
    }

    /* calculate drive value to control speed */
    const float u = pid_update(&libdata->speedController, reqSpeed, libdata->currentSpeed);

    if (_is_motor_blocked(libdata, u))
    {
        if (!_has_timeout_elapsed(&libdata->motorTimeout, MOTOR_TIMEOUT_THRESHOLD))
        {
            _tick_timeout(&libdata->motorTimeout, MOTOR_TIMEOUT_THRESHOLD);
            if (_has_timeout_elapsed(&libdata->motorTimeout, MOTOR_TIMEOUT_THRESHOLD))
            {
                LOG("Motor %u: stuck\n", motorPort->port_idx);
                libdata->motorStatus = DcMotorStatus_Blocked;
                return 0;
            }
        }
    }
    else
    {
        _reset_timeout(&libdata->motorTimeout);
    }

    int16_t pwm;

    pwm = lroundf(linear_interpolate_symmetrical(libdata->nonlinearity, u));

    /* physical limits */
    pwm = constrain_int16(pwm, -200, 200);

    return pwm;
}

MotorLibraryStatus_t DcMotor_Update(MotorPort_t* motorPort)
{
    MotorLibrary_Dc_Data_t* libdata = (MotorLibrary_Dc_Data_t*) motorPort->libraryData;

    DriveRequest_t driveRequest;
    MotorPortHandler_Read_DriveRequest(motorPort->port_idx, &driveRequest);

    _update_current_speed(libdata);

    /* do we have a new drive command? */
    if (driveRequest.version != libdata->currentRequest.version)
    {
        _process_new_request(motorPort, libdata, &driveRequest);
    }

    /* control the motor */
    int16_t pwm = _run_motor_control(motorPort, libdata);

    if (libdata->isEmulated)
    {
        // TODO: emulator should probably be implemented in a different Update function
        // to avoid wasting CPU in normal operation.
        emulator_tick(libdata, pwm, 0.01); // 10ms tick rate
    }
    else
    {
        MotorPort_SetDriveValue(motorPort, pwm);
    }

    _update_status_data(motorPort, pwm);

    return MotorLibraryStatus_Ok;
}

void DcMotor_Gpio0Callback(void* port)
{
    MotorPort_t* motorPort = (MotorPort_t*) port;
    MotorLibrary_Dc_Data_t* libdata = (MotorLibrary_Dc_Data_t*) motorPort->libraryData;
    bool pin0state = MotorPort_Read_Enc0(motorPort);
    bool pin1state = MotorPort_Read_Enc1(motorPort);

    /* ps0 ps1 out
         0   0   1
         0   1  -1
         1   0  -1
         1   1   1
    */
    if (pin0state == pin1state)
    {
        libdata->position += 1u;
    }
    else
    {
        libdata->position -= 1u;
    }
}

void DcMotor_Gpio1Callback(void* port)
{
    MotorPort_t* motorPort = (MotorPort_t*) port;
    MotorLibrary_Dc_Data_t* libdata = (MotorLibrary_Dc_Data_t*) motorPort->libraryData;
    bool pin0state = MotorPort_Read_Enc0(motorPort);
    bool pin1state = MotorPort_Read_Enc1(motorPort);

    /* ps0 ps1 out
         0   0  -1
         0   1   1
         1   0   1
         1   1  -1
    */
    if (pin0state == pin1state)
    {
        libdata->position -= 1u;
    }
    else
    {
        libdata->position += 1u;
    }
}

static void dc_motor_read_pid_config(PidConfig_t* config, const uint8_t* buffer)
{
    config->P = get_float(&buffer[0]);
    config->I = get_float(&buffer[4]);
    config->D = get_float(&buffer[8]);
    config->LowerLimit = get_float(&buffer[12]);
    config->UpperLimit = get_float(&buffer[16]);
}

MotorLibraryStatus_t DcMotor_UpdateConfiguration(MotorPort_t* motorPort, const uint8_t* data, uint8_t size)
{
    MotorLibrary_Dc_Data_t* libdata = (MotorLibrary_Dc_Data_t*) motorPort->libraryData;
    const size_t header_size = 81u;
    /* Do we have the required data? */
    if (size < header_size)
    {
        LOG("DcMotor_UpdateConfiguration: expected at least %u bytes, got %u\n", header_size, size);
        return MotorLibraryStatus_InputError;
    }
    /* Linearity table is optional but must be 8 bytes per entry */
    if ((size - header_size) % 8 != 0u)
    {
        LOG("DcMotor_UpdateConfiguration: linearity table size error\n");
        return MotorLibraryStatus_InputError;
    }
    size_t nNonlinearityPoints = (size - header_size) / 8u;
    if (nNonlinearityPoints > 9u) /** < 1 point is reserved for (0, 0) */
    {
        LOG("DcMotor_UpdateConfiguration: linearity table too large: %u elements\n", nNonlinearityPoints);
        return MotorLibraryStatus_InputError;
    }

    /* reset controller states & coefficients */
    pid_initialize(&libdata->positionController);
    pid_initialize(&libdata->speedController);

    /* read parameters */
    float encoder_slits = get_float(&data[0]);

    dc_motor_read_pid_config(&libdata->slowPositionConfig, &data[4]);
    dc_motor_read_pid_config(&libdata->fastPositionConfig, &data[24]);
    switch (data[44])
    {
        case 0: libdata->positionBreakpointKind = PositionBreakpointKind_Degrees; break;
        case 1: libdata->positionBreakpointKind = PositionBreakpointKind_Relative; break;
        default:
            LOG("DcMotor_UpdateConfiguration: invalid positionBreakpointKind: %u\n", data[44]);
            return MotorLibraryStatus_InputError;
    }
    libdata->positionBreakpoint = get_float(&data[45]);
    dc_motor_read_pid_config(&libdata->speedController.config, &data[49]);

    libdata->maxDeceleration = get_float(&data[69]);
    libdata->maxAcceleration = get_float(&data[73]);

    Current_t maxCurrent = get_float(&data[77]);

    /* calculate misc values */
    libdata->resolution = pulses_per_encoder_slit * encoder_slits;
    libdata->atLeastOneDegree = lroundf(fabsf(libdata->resolution) / 360.0f);
    if (libdata->atLeastOneDegree == 0u)
    {
        libdata->atLeastOneDegree = 1u;
    }

    libdata->positionControllerLowerLimit = libdata->slowPositionConfig.LowerLimit;
    libdata->positionControllerUpperLimit = libdata->slowPositionConfig.UpperLimit;

    libdata->speedControllerLowerLimit = libdata->speedController.config.LowerLimit;
    libdata->speedControllerUpperLimit = libdata->speedController.config.UpperLimit;

    MotorPort_WriteMaxCurrent(motorPort, maxCurrent);

    /* read nonlinearity LUT data */
    libdata->nonlinearity_xs[0u] = 0.0f;
    libdata->nonlinearity_ys[0u] = 0.0f;

    if (nNonlinearityPoints == 0u)
    {
        libdata->nonlinearity_xs[1u] = 1.0f;
        libdata->nonlinearity_ys[1u] = 1.0f;
        libdata->nonlinearity.size = 2u;
    }
    else
    {
        for (size_t i = 0u; i < nNonlinearityPoints; i++)
        {
            libdata->nonlinearity_xs[i + 1u] = get_float(&data[header_size + i * 8u]);
            libdata->nonlinearity_ys[i + 1u] = get_float(&data[header_size + i * 8u + 4u]) * sgn_float(libdata->resolution);
        }
        libdata->nonlinearity.size = nNonlinearityPoints + 1u;
    }

    /* Make sure motor is stopped */
    if (!libdata->isEmulated)
    {
        MotorPort_SetDriveValue(motorPort, 0);
    }

    /* reset states */
    libdata->lastPosition = 0;
    libdata->position = 0;
    libdata->currentSpeed = 0.0f;
    _reset_motor_status(motorPort);
    emulator_reset(libdata);

    ignore_last_drive_request(motorPort);

    return MotorLibraryStatus_Ok;
}

static MotorLibraryStatus_t _create_pwm_request(const MotorLibrary_Dc_Data_t* libdata, const uint8_t* data, uint8_t size, DriveRequest_t* driveRequest)
{
    (void) libdata;
    if (size != 2u)
    {
        LOG("_create_pwm_request: got %d bytes, expected 2\n", size);
        return MotorLibraryStatus_InputError;
    }

    int8_t pwm = data[1];
    if (pwm < -100 || pwm > 100)
    {
        LOG("_create_pwm_request: invalid pwm %d\n", pwm);
        return MotorLibraryStatus_InputError;
    }

    /* direct power request, no need to set limits */
    driveRequest->request_type = DriveRequest_RequestType_Power;

    /* pwm value directly given in the -100...100 range, scale it to -200...200 */
    driveRequest->request.power = 2 * (int16_t) pwm;

    return MotorLibraryStatus_Ok;
}

static MotorLibraryStatus_t _create_speed_request(const MotorLibrary_Dc_Data_t* libdata, const uint8_t* data, uint8_t size, DriveRequest_t* driveRequest)
{
    (void) libdata;
    /* direct power request, no need to set limits for position controller */
    if (size == 5u)
    {
        /* reset speed controller limits */
        driveRequest->power_limit = 0.0f;
    }
    else if (size == 9u)
    {
        /* constrained drive command - power constraint */
        driveRequest->power_limit = get_float(&data[5]);
    }
    else
    {
        LOG("_create_speed_request input error: got %d bytes\n", size);
        return MotorLibraryStatus_InputError;
    }

    driveRequest->request_type = DriveRequest_RequestType_Speed;
    driveRequest->request.speed = get_float(&data[1]);

    return MotorLibraryStatus_Ok;
}

static MotorLibraryStatus_t _create_position_request(const MotorLibrary_Dc_Data_t* libdata, const uint8_t* data, uint8_t size, DriveRequest_t* driveRequest)
{
    if (size == 5u)
    {
        /* reset controller limits */
        driveRequest->power_limit = 0.0f;
        driveRequest->speed_limit = 0.0f;
    }
    else if (size == 10u)
    {
        /* constrained drive command */
        switch (data[5])
        {
            case DRIVE_CONTSTRAINED_POWER:
                driveRequest->power_limit = get_float(&data[6]);
                driveRequest->speed_limit = 0.0f;
                break;

            case DRIVE_CONTSTRAINED_SPEED:
                driveRequest->power_limit = 0.0f;
                driveRequest->speed_limit = get_float(&data[6]);
                break;

            default:
                LOG("_create_position_request input error: unknown limit type %d\n", data[5]);
                return MotorLibraryStatus_InputError;
        }
    }
    else if (size == 13u)
    {
        driveRequest->speed_limit = get_float(&data[5]);
        driveRequest->power_limit = get_float(&data[9]);
    }
    else
    {
        LOG("_create_position_request input error: got %d bytes\n", size);
        return MotorLibraryStatus_InputError;
    }

    int32_t requested_position = degrees_to_ticks(libdata, get_int32(&data[1]));
    if (data[0] == MOTOR_CONTROL_POSITION_RELATIVE)
    {
        requested_position = requested_position + libdata->lastPosition;
    }

    driveRequest->request_type = DriveRequest_RequestType_Position;
    driveRequest->request.position = requested_position;

    switch (libdata->positionBreakpointKind) {
        case PositionBreakpointKind_Degrees:
            driveRequest->positionBreakpoint = (uint32_t) degrees_to_ticks(libdata, libdata->positionBreakpoint);
            break;
        case PositionBreakpointKind_Relative: {
            float distanceTicks = fabsf((float)(libdata->lastPosition - requested_position));
            driveRequest->positionBreakpoint = (uint32_t) lroundf(libdata->positionBreakpoint * distanceTicks);
            break;
        }
        default:
            /* should not happen, we check for invalid values when reading the configuration */
            break;
    }

    return MotorLibraryStatus_Ok;
}

MotorLibraryStatus_t DcMotor_CreateDriveRequest(const MotorPort_t* motorPort, const uint8_t* data, uint8_t size, DriveRequest_t* driveRequest)
{
    if (size == 0u)
    {
        LOG("DcMotor_CreateDriveRequest: empty request\n");
        return MotorLibraryStatus_InputError;
    }

    MotorLibrary_Dc_Data_t* libdata = (MotorLibrary_Dc_Data_t*) motorPort->libraryData;

    /* make sure the request won't get ignored if the caller decides to apply it */
    libdata->lastCreatedCommandVersion += 1u;
    driveRequest->version = libdata->lastCreatedCommandVersion;

    switch (data[0])
    {
        case MOTOR_CONTROL_PWM:
            return _create_pwm_request(libdata, data, size, driveRequest);

        case MOTOR_CONTROL_SPEED:
            return _create_speed_request(libdata, data, size, driveRequest);

        case MOTOR_CONTROL_POSITION:
        case MOTOR_CONTROL_POSITION_RELATIVE:
            return _create_position_request(libdata, data, size, driveRequest);

        default:
            LOG("DcMotor_CreateDriveRequest: unknown control mode %d\n", data[0]);
            return MotorLibraryStatus_InputError;
    }
}

const MotorLibrary_t motor_library_dc =
{
    .Name                = "DcMotor",
    .Load                = &DcMotor_Load,
    .Unload              = &DcMotor_Unload,
    .Update              = &DcMotor_Update,
    .Gpio0Callback       = &DcMotor_Gpio0Callback,
    .Gpio1Callback       = &DcMotor_Gpio1Callback,
    .UpdateConfiguration = &DcMotor_UpdateConfiguration,
    .CreateDriveRequest  = &DcMotor_CreateDriveRequest
};

const MotorLibrary_t motor_library_dc_emulator =
{
    .Name                = "DcMotorEmulator",
    .Load                = &DcMotorEmulator_Load,
    .Unload              = &DcMotor_Unload,
    .Update              = &DcMotor_Update,
    .Gpio0Callback       = NULL,
    .Gpio1Callback       = NULL,
    .UpdateConfiguration = &DcMotor_UpdateConfiguration,
    .CreateDriveRequest  = &DcMotor_CreateDriveRequest
};
