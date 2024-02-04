#include "RingLedDisplay.h"
#include "utils.h"
#include "utils_assert.h"

/* Begin User Code Section: Declarations */
#include "RingLedDisplay_private.h"

#include <string.h>

static RingLedScenario_t current_scenario;
static const indication_handler_t* current_scenario_handler;
static uint32_t time_since_startup;
static bool master_ready;

static ssize_t copy_ring_led_scenario_name(const char* name, ByteArray_t destination)
{
    size_t length = strlen(name);

    if (length > destination.count)
    {
        return -1;
    }

    memcpy(destination.bytes, name, length);
    return (ssize_t)length;
}

/* End User Code Section: Declarations */

void RingLedDisplay_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    master_ready = !RingLedDisplay_Read_WaitForMasterStartup();

    bool display_default_animation = !master_ready;

    time_since_startup = 0u;
    if (display_default_animation)
    {
        /* current_scenario will be set to a "to-be-changed" value if default animation ends */
        current_scenario_handler = &startup_indicator_scenario;
    }
    else
    {
        current_scenario = RingLedDisplay_Read_Scenario();
        current_scenario_handler = &public_scenario_handlers[current_scenario];
    }

    if (current_scenario_handler->init)
    {
        current_scenario_handler->init(current_scenario_handler->userData);
    }
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void RingLedDisplay_Run_Update(void)
{
    /* Begin User Code Section: Update:run Start */
    RingLedScenario_t requested_scenario = RingLedDisplay_Read_Scenario();

    bool display_default_animation = !master_ready
                                     && (time_since_startup < RingLedDisplay_Read_ExpectedStartupTime());

    if (display_default_animation)
    {
        time_since_startup += 20u;

        if (time_since_startup >= RingLedDisplay_Read_ExpectedStartupTime())
        {
            /* force switch to requested scenario */
            current_scenario = requested_scenario + 1u;
            display_default_animation = false;
        }
    }

    if (!display_default_animation)
    {
        MasterStatus_t master_status = RingLedDisplay_Read_MasterStatus();

        if (master_status == MasterStatus_Unknown)
        {
            requested_scenario = RingLedScenario_BusyIndicator;
        }

        if (current_scenario != requested_scenario)
        {
            if (current_scenario_handler->DeInit)
            {
                current_scenario_handler->DeInit(current_scenario_handler->userData);
            }

            current_scenario = requested_scenario;
            current_scenario_handler = &public_scenario_handlers[current_scenario];

            ASSERT(current_scenario_handler);
            ASSERT(current_scenario_handler->handler);

            if (current_scenario_handler->init)
            {
                current_scenario_handler->init(current_scenario_handler->userData);
            }
        }
    }

    current_scenario_handler->handler(current_scenario_handler->userData);
    /* End User Code Section: Update:run Start */
    /* Begin User Code Section: Update:run End */

    /* End User Code Section: Update:run End */
}

void RingLedDisplay_Run_OnMasterStarted(void)
{
    /* Begin User Code Section: OnMasterStarted:run Start */
    master_ready = true;
    /* End User Code Section: OnMasterStarted:run Start */
    /* Begin User Code Section: OnMasterStarted:run End */

    /* End User Code Section: OnMasterStarted:run End */
}

ssize_t RingLedDisplay_Run_ReadScenarioName(RingLedScenario_t scenario, ByteArray_t destination)
{
    /* Begin User Code Section: ReadScenarioName:run Start */
    switch (scenario)
    {
        case RingLedScenario_Off: return copy_ring_led_scenario_name("RingLedOff", destination);
        case RingLedScenario_UserFrame: return copy_ring_led_scenario_name("UserFrame", destination);
        case RingLedScenario_ColorWheel: return copy_ring_led_scenario_name("ColorWheel", destination);
        case RingLedScenario_RainbowFade: return copy_ring_led_scenario_name("RainbowFade", destination);
        case RingLedScenario_BusyIndicator: return copy_ring_led_scenario_name("BusyRing", destination);
        case RingLedScenario_BreathingGreen: return copy_ring_led_scenario_name("BreathingGreen", destination);

        /* these are not listed */
        case RingLedScenario_Siren: return 0;
        case RingLedScenario_TrafficLight: return 0;

        default: return -2;
    }
    /* End User Code Section: ReadScenarioName:run Start */
    /* Begin User Code Section: ReadScenarioName:run End */

    /* End User Code Section: ReadScenarioName:run End */
}

size_t RingLedDisplay_Constant_ScenarioCount(void)
{
    /* Begin User Code Section: ScenarioCount:constant Start */

    /* End User Code Section: ScenarioCount:constant Start */
    /* Begin User Code Section: ScenarioCount:constant End */

    /* End User Code Section: ScenarioCount:constant End */
    return ARRAY_SIZE(public_scenario_handlers);
}

__attribute__((weak))
void RingLedDisplay_Write_LedColor(uint32_t index, rgb_t value)
{
    (void) value;
    ASSERT(index < 12);
    /* Begin User Code Section: LedColor:write Start */

    /* End User Code Section: LedColor:write Start */
    /* Begin User Code Section: LedColor:write End */

    /* End User Code Section: LedColor:write End */
}

__attribute__((weak))
uint32_t RingLedDisplay_Read_ExpectedStartupTime(void)
{
    /* Begin User Code Section: ExpectedStartupTime:read Start */

    /* End User Code Section: ExpectedStartupTime:read Start */
    /* Begin User Code Section: ExpectedStartupTime:read End */

    /* End User Code Section: ExpectedStartupTime:read End */
    return 0u;
}

__attribute__((weak))
MasterStatus_t RingLedDisplay_Read_MasterStatus(void)
{
    /* Begin User Code Section: MasterStatus:read Start */

    /* End User Code Section: MasterStatus:read Start */
    /* Begin User Code Section: MasterStatus:read End */

    /* End User Code Section: MasterStatus:read End */
    return MasterStatus_Unknown;
}

__attribute__((weak))
RingLedScenario_t RingLedDisplay_Read_Scenario(void)
{
    /* Begin User Code Section: Scenario:read Start */

    /* End User Code Section: Scenario:read Start */
    /* Begin User Code Section: Scenario:read End */

    /* End User Code Section: Scenario:read End */
    return RingLedScenario_Off;
}

__attribute__((weak))
rgb_t RingLedDisplay_Read_UserColors(uint32_t index)
{
    ASSERT(index < 12);
    /* Begin User Code Section: UserColors:read Start */

    /* End User Code Section: UserColors:read Start */
    /* Begin User Code Section: UserColors:read End */

    /* End User Code Section: UserColors:read End */
    return (rgb_t){0, 0, 0};
}

__attribute__((weak))
bool RingLedDisplay_Read_WaitForMasterStartup(void)
{
    /* Begin User Code Section: WaitForMasterStartup:read Start */

    /* End User Code Section: WaitForMasterStartup:read Start */
    /* Begin User Code Section: WaitForMasterStartup:read End */

    /* End User Code Section: WaitForMasterStartup:read End */
    return false;
}
