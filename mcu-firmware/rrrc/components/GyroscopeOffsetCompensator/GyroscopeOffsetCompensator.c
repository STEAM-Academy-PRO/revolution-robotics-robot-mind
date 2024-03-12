#include "GyroscopeOffsetCompensator.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include <stdbool.h>
#include <stdint.h>
#include <math.h>

static bool offsetCalibrated;
static Vector3D_t averageAngularSpeed;
static Vector3D_t sumAngularSpeed;
static uint32_t averageAngularSpeedSamples;

#define AVERAGE_NUM_SAMPLES ((uint32_t)1000u)

/**
 * Restart the averaging process.
 *
 * Does not affect signal output: compensates using the old average until new one is calculated.
 */
static void restart_averaging(void)
{
    /* start a new calibration immediately */
    averageAngularSpeedSamples = 0u;

    /* only reset sum, average will be used for compensation */
    sumAngularSpeed = (Vector3D_t){0.0f, 0.0f, 0.0f};
}
/* End User Code Section: Declarations */

void GyroscopeOffsetCompensator_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    offsetCalibrated = false;

    restart_averaging();

    Vector3D_t angularSpeed;
    while (GyroscopeOffsetCompensator_Read_AngularSpeeds(&angularSpeed) != QueueStatus_Empty)
        ;

    averageAngularSpeed = (Vector3D_t){0.0f, 0.0f, 0.0f};
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void GyroscopeOffsetCompensator_Run_Update(void)
{
    /* Begin User Code Section: Update:run Start */
    Vector3D_t angularSpeed;
    while (GyroscopeOffsetCompensator_Read_AngularSpeeds(&angularSpeed) != QueueStatus_Empty)
    {
        if (GyroscopeOffsetCompensator_Read_IsMoving())
        {
            restart_averaging();
        }
        else
        {
            // Continuously collect samples if the brain is not moving. Start updating the average
            // once we have enough samples.
            if (averageAngularSpeedSamples < AVERAGE_NUM_SAMPLES)
            {
                ++averageAngularSpeedSamples;
            }
            else
            {
                // If our buffer is full, we remove the average. This has a similar effect to
                // removing the oldest sample, albeit turns the averaging into an estimation.
                // Still, it's better to track changes continuously instead of
                // once every 2.5 seconds.
                sumAngularSpeed.x -= averageAngularSpeed.x;
                sumAngularSpeed.y -= averageAngularSpeed.y;
                sumAngularSpeed.z -= averageAngularSpeed.z;
            }

            sumAngularSpeed.x += angularSpeed.x;
            sumAngularSpeed.y += angularSpeed.y;
            sumAngularSpeed.z += angularSpeed.z;

            if (averageAngularSpeedSamples == AVERAGE_NUM_SAMPLES)
            {
                averageAngularSpeed.x = sumAngularSpeed.x / AVERAGE_NUM_SAMPLES;
                averageAngularSpeed.y = sumAngularSpeed.y / AVERAGE_NUM_SAMPLES;
                averageAngularSpeed.z = sumAngularSpeed.z / AVERAGE_NUM_SAMPLES;

                offsetCalibrated = true;
            }
        }

        if (offsetCalibrated)
        {
            const Vector3D_t output = (Vector3D_t) {
                .x = angularSpeed.x - averageAngularSpeed.x,
                .y = angularSpeed.y - averageAngularSpeed.y,
                .z = angularSpeed.z - averageAngularSpeed.z,
            };

            GyroscopeOffsetCompensator_Write_CompensatedAngularSpeeds(&output);
        }
    }
    /* End User Code Section: Update:run Start */
    /* Begin User Code Section: Update:run End */

    /* End User Code Section: Update:run End */
}

__attribute__((weak))
void GyroscopeOffsetCompensator_Write_CompensatedAngularSpeeds(const Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: CompensatedAngularSpeeds:write Start */

    /* End User Code Section: CompensatedAngularSpeeds:write Start */
    /* Begin User Code Section: CompensatedAngularSpeeds:write End */

    /* End User Code Section: CompensatedAngularSpeeds:write End */
}

__attribute__((weak))
QueueStatus_t GyroscopeOffsetCompensator_Read_AngularSpeeds(Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: AngularSpeeds:read Start */

    /* End User Code Section: AngularSpeeds:read Start */
    /* Begin User Code Section: AngularSpeeds:read End */

    /* End User Code Section: AngularSpeeds:read End */
    return QueueStatus_Empty;
}

__attribute__((weak))
bool GyroscopeOffsetCompensator_Read_IsMoving(void)
{
    /* Begin User Code Section: IsMoving:read Start */

    /* End User Code Section: IsMoving:read Start */
    /* Begin User Code Section: IsMoving:read End */

    /* End User Code Section: IsMoving:read End */
    return false;
}
