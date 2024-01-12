#include "BluetoothStatusObserver.h"
#include "utils.h"

/* Begin User Code Section: Declarations */

/* End User Code Section: Declarations */

void BluetoothStatusObserver_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    BluetoothStatusObserver_Write_ConnectionStatus(BluetoothStatus_Inactive);
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

Comm_Status_t BluetoothStatusObserver_Run_Command_SetBluetoothStatus_Start(ConstByteArray_t commandPayload, ByteArray_t response, uint8_t* responseCount)
{
    /* Begin User Code Section: Command_SetBluetoothStatus_Start:run Start */
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
                BluetoothStatusObserver_Write_ConnectionStatus(BluetoothStatus_NotConnected);
                break;

            case 1u:
                BluetoothStatusObserver_Write_ConnectionStatus(BluetoothStatus_Connected);
                break;

            default:
                status = Comm_Status_Error_CommandError;
                break;
        }
    }

    return status;
    /* End User Code Section: Command_SetBluetoothStatus_Start:run Start */
    /* Begin User Code Section: Command_SetBluetoothStatus_Start:run End */

    /* End User Code Section: Command_SetBluetoothStatus_Start:run End */
}

__attribute__((weak))
void BluetoothStatusObserver_Write_ConnectionStatus(BluetoothStatus_t value)
{
    (void) value;
    /* Begin User Code Section: ConnectionStatus:write Start */

    /* End User Code Section: ConnectionStatus:write Start */
    /* Begin User Code Section: ConnectionStatus:write End */

    /* End User Code Section: ConnectionStatus:write End */
}
