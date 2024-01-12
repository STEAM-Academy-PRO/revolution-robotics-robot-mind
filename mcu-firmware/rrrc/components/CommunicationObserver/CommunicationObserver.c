#include "CommunicationObserver.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include <stdint.h>

#define ERROR_COUNTER_MAX              ((uint8_t) 4u)
#define ERROR_COUNTER_INCREMENT        ((uint8_t) 2u)

static uint8_t errorCounter;
static bool wasEnabled;
static bool firstMessageIndicated;

static inline uint8_t min_uint8(uint8_t a, uint8_t b)
{
    if (a < b)
    {
        return a;
    }
    else
    {
        return b;
    }
}
/* End User Code Section: Declarations */

void CommunicationObserver_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    wasEnabled = false;
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void CommunicationObserver_Run_OnMessageMissed(void)
{
    /* Begin User Code Section: OnMessageMissed:run Start */
    bool isEnabled = CommunicationObserver_Read_IsEnabled();

    if (wasEnabled != isEnabled)
    {
        if (!wasEnabled)
        {
            errorCounter = ERROR_COUNTER_MAX;
            firstMessageIndicated = false;
        }

        wasEnabled = isEnabled;
    }

    if (errorCounter > 0u)
    {
        --errorCounter;
    }
    if (errorCounter == 0u && isEnabled)
    {
        CommunicationObserver_RaiseEvent_ErrorLimitReached();
    }
    /* End User Code Section: OnMessageMissed:run Start */
    /* Begin User Code Section: OnMessageMissed:run End */

    /* End User Code Section: OnMessageMissed:run End */
}

void CommunicationObserver_Run_OnMessageReceived(void)
{
    /* Begin User Code Section: OnMessageReceived:run Start */
    bool isEnabled = CommunicationObserver_Read_IsEnabled();

    if (wasEnabled != isEnabled)
    {
        if (!wasEnabled)
        {
            errorCounter = ERROR_COUNTER_MAX;
            firstMessageIndicated = false;
        }

        wasEnabled = isEnabled;
    }

    if (isEnabled)
    {
        errorCounter = min_uint8(errorCounter + ERROR_COUNTER_INCREMENT, ERROR_COUNTER_MAX);

        if (!firstMessageIndicated)
        {
            CommunicationObserver_RaiseEvent_FirstMessageReceived();
            firstMessageIndicated = true;
        }
    }
    /* End User Code Section: OnMessageReceived:run Start */
    /* Begin User Code Section: OnMessageReceived:run End */

    /* End User Code Section: OnMessageReceived:run End */
}

__attribute__((weak))
void CommunicationObserver_RaiseEvent_ErrorLimitReached(void)
{
    /* Begin User Code Section: ErrorLimitReached:run Start */

    /* End User Code Section: ErrorLimitReached:run Start */
    /* Begin User Code Section: ErrorLimitReached:run End */

    /* End User Code Section: ErrorLimitReached:run End */
}

__attribute__((weak))
void CommunicationObserver_RaiseEvent_FirstMessageReceived(void)
{
    /* Begin User Code Section: FirstMessageReceived:run Start */

    /* End User Code Section: FirstMessageReceived:run Start */
    /* Begin User Code Section: FirstMessageReceived:run End */

    /* End User Code Section: FirstMessageReceived:run End */
}

__attribute__((weak))
bool CommunicationObserver_Read_IsEnabled(void)
{
    /* Begin User Code Section: IsEnabled:read Start */

    /* End User Code Section: IsEnabled:read Start */
    /* Begin User Code Section: IsEnabled:read End */

    /* End User Code Section: IsEnabled:read End */
    return false;
}
