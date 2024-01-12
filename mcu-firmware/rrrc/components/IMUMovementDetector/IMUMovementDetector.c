#include "IMUMovementDetector.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include <math.h>

#define IDLE_SENSITIVITY ((float)2.0f)
#define IDLE_NUM_SAMPLES ((uint32_t)200u)
#define IGNORE_SAMPLES ((uint32_t)200u)

static Vector3D_t currentMidValue;
static uint32_t samplesInCurrentBand;
static uint32_t ignored_samples;

static bool is_close_to(const Vector3D_t vector, const Vector3D_t reference, float threshold)
{
    return fabsf(vector.x - reference.x) <= threshold && fabsf(vector.y - reference.y) <= threshold && fabsf(vector.z - reference.z) <= threshold;
}

/* End User Code Section: Declarations */

void IMUMovementDetector_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    samplesInCurrentBand = 0u;
    currentMidValue = (Vector3D_t){0.0f, 0.0f, 0.0f};
    ignored_samples = IGNORE_SAMPLES;

    Vector3D_t angularSpeed;
    while (IMUMovementDetector_Read_AngularSpeeds(&angularSpeed) != QueueStatus_Empty)
        ;
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void IMUMovementDetector_Run_OnUpdate(void)
{
    /* Begin User Code Section: OnUpdate:run Start */
    Vector3D_t angularSpeed;
    while (IMUMovementDetector_Read_AngularSpeeds(&angularSpeed) != QueueStatus_Empty)
    {
        if (ignored_samples > 0)
        {
            ignored_samples -= 1;
            continue;
        }
        if (is_close_to(angularSpeed, currentMidValue, IDLE_SENSITIVITY))
        {
            if (samplesInCurrentBand < IDLE_NUM_SAMPLES)
            {
                samplesInCurrentBand++;
                if (samplesInCurrentBand == IDLE_NUM_SAMPLES)
                {
                    IMUMovementDetector_Write_IsMoving(false);
                }
            }
        }
        else
        {
            samplesInCurrentBand = 0u;
            currentMidValue = angularSpeed;
            IMUMovementDetector_Write_IsMoving(true);
        }
    }
    /* End User Code Section: OnUpdate:run Start */
    /* Begin User Code Section: OnUpdate:run End */

    /* End User Code Section: OnUpdate:run End */
}

__attribute__((weak))
void IMUMovementDetector_Write_IsMoving(bool value)
{
    (void) value;
    /* Begin User Code Section: IsMoving:write Start */

    /* End User Code Section: IsMoving:write Start */
    /* Begin User Code Section: IsMoving:write End */

    /* End User Code Section: IsMoving:write End */
}

__attribute__((weak))
QueueStatus_t IMUMovementDetector_Read_Acceleration(Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: Acceleration:read Start */

    /* End User Code Section: Acceleration:read Start */
    /* Begin User Code Section: Acceleration:read End */

    /* End User Code Section: Acceleration:read End */
    return QueueStatus_Empty;
}

__attribute__((weak))
QueueStatus_t IMUMovementDetector_Read_AngularSpeeds(Vector3D_t* value)
{
    ASSERT(value != NULL);
    /* Begin User Code Section: AngularSpeeds:read Start */

    /* End User Code Section: AngularSpeeds:read Start */
    /* Begin User Code Section: AngularSpeeds:read End */

    /* End User Code Section: AngularSpeeds:read End */
    return QueueStatus_Empty;
}
