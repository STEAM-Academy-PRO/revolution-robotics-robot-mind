#include "MasterStatusObserver.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include <compiler.h>

#define MSO_UPDATE_PERIOD       ((uint32_t)100u)

static uint32_t updateTimeout;
static uint32_t startupTimeout;

static void start_update(void)
{
    updateTimeout = MasterStatusObserver_Read_UpdateTimeout();

    MasterStatusObserver_Write_MasterStatus(MasterStatus_Updating);
    MasterStatusObserver_Write_EnableCommunicationObserver(false);
}

static void stop_updating(void)
{
    updateTimeout = 0u;
    startupTimeout = 0u;
}

static bool countdown(uint32_t* timer, uint32_t increment)
{
    bool elapsed = false;

    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    if (*timer != 0u)
    {
        if (*timer <= increment)
        {
            *timer = 0u;
            elapsed = true;
        }
        else
        {
            *timer -= increment;
        }
    }
    __set_PRIMASK(primask);

    return elapsed;
}
/* End User Code Section: Declarations */

void MasterStatusObserver_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    if (MasterStatusObserver_Read_IsColdStart())
    {
        startupTimeout = MasterStatusObserver_Read_ExpectedStartupTime();
    }
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void MasterStatusObserver_Run_Update(void)
{
    /* Begin User Code Section: Update:run Start */
    if (countdown(&startupTimeout, MSO_UPDATE_PERIOD))
    {
        start_update();
    }
    else if (countdown(&updateTimeout, MSO_UPDATE_PERIOD))
    {
        MasterStatusObserver_Write_MasterStatus(MasterStatus_Unknown);
    }
    /* End User Code Section: Update:run Start */
    /* Begin User Code Section: Update:run End */

    /* End User Code Section: Update:run End */
}

Comm_Status_t MasterStatusObserver_Run_Command_SetMasterStatus_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetMasterStatus_Start:run Start */
    (void) response;
    (void) responseCount;

    Comm_Status_t status = Comm_Status_Ok;
    if  (commandPayload.count != 1u)
    {
        status = Comm_Status_Error_PayloadLengthError;
    }
    else
    {
        switch (commandPayload.bytes[0])
        {
            case 0u:
                stop_updating();
                MasterStatusObserver_Write_MasterStatus(MasterStatus_Unknown);
                MasterStatusObserver_Write_EnableCommunicationObserver(false);
                break;

            case 1u:
                stop_updating();
                MasterStatusObserver_Write_MasterStatus(MasterStatus_NotConfigured);
                MasterStatusObserver_Write_EnableCommunicationObserver(true);
                break;

            case 2u:
                stop_updating();
                MasterStatusObserver_Write_MasterStatus(MasterStatus_Operational);
                MasterStatusObserver_Write_EnableCommunicationObserver(true);
                break;

            case 3u:
                stop_updating();
                MasterStatusObserver_Write_MasterStatus(MasterStatus_Controlled);
                MasterStatusObserver_Write_EnableCommunicationObserver(true);
                break;

            case 4u:
                stop_updating();
                MasterStatusObserver_Write_MasterStatus(MasterStatus_Configuring);
                MasterStatusObserver_Write_EnableCommunicationObserver(true);
                break;

            case 5u:
                start_update();
                break;

            default:
                status = Comm_Status_Error_CommandError;
                break;
        }
    }

    return status;
    /* End User Code Section: Command_SetMasterStatus_Start:run Start */
    /* Begin User Code Section: Command_SetMasterStatus_Start:run End */

    /* End User Code Section: Command_SetMasterStatus_Start:run End */
}

__attribute__((weak))
void MasterStatusObserver_Write_EnableCommunicationObserver(bool value)
{
    (void) value;
    /* Begin User Code Section: EnableCommunicationObserver:write Start */

    /* End User Code Section: EnableCommunicationObserver:write Start */
    /* Begin User Code Section: EnableCommunicationObserver:write End */

    /* End User Code Section: EnableCommunicationObserver:write End */
}

__attribute__((weak))
void MasterStatusObserver_Write_MasterStatus(MasterStatus_t value)
{
    (void) value;
    /* Begin User Code Section: MasterStatus:write Start */

    /* End User Code Section: MasterStatus:write Start */
    /* Begin User Code Section: MasterStatus:write End */

    /* End User Code Section: MasterStatus:write End */
}

__attribute__((weak))
uint32_t MasterStatusObserver_Read_ExpectedStartupTime(void)
{
    /* Begin User Code Section: ExpectedStartupTime:read Start */

    /* End User Code Section: ExpectedStartupTime:read Start */
    /* Begin User Code Section: ExpectedStartupTime:read End */

    /* End User Code Section: ExpectedStartupTime:read End */
    return 10000;
}

__attribute__((weak))
bool MasterStatusObserver_Read_IsColdStart(void)
{
    /* Begin User Code Section: IsColdStart:read Start */

    /* End User Code Section: IsColdStart:read Start */
    /* Begin User Code Section: IsColdStart:read End */

    /* End User Code Section: IsColdStart:read End */
    return false;
}

__attribute__((weak))
uint32_t MasterStatusObserver_Read_UpdateTimeout(void)
{
    /* Begin User Code Section: UpdateTimeout:read Start */

    /* End User Code Section: UpdateTimeout:read Start */
    /* Begin User Code Section: UpdateTimeout:read End */

    /* End User Code Section: UpdateTimeout:read End */
    return 30000;
}
