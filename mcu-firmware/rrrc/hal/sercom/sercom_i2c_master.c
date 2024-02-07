#include "sercom_i2c_master.h"
#include <math.h>

/**
 * Low-level asynchronous i2c master implementation to support reconfigurable interfaces.
 * This implementation assumes 24MHz clock and settings that are configured in the Pi firmware.
 */

#define I2CM_INT_HANDLER_MASTER_BUS  0 /**< Data transmitted */
#define I2CM_INT_HANDLER_SLAVE_BUS   1 /**< Data received */
#define I2CM_INT_HANDLER_ERROR       3

static void i2c_slave_bus_callback(void* data);
static void i2c_master_bus_callback(void* data);

static void i2c_master_send_stop(I2CMasterInstance_t* instance);
static void i2c_master_abort_transaction(I2CMasterInstance_t* instance);
static void i2c_master_continue_tx_transaction(I2CMasterInstance_t* instance);

#define CMD_SEND_REPEATED_START (1u)
#define CMD_SEND_ACK            (2u)
#define CMD_SEND_STOP_CONDITION (3u)

typedef enum {
    ReadWithAck = 0,
    ReadWithNack = 1
} ReadResponse_t;

static void i2c_master_command(I2CMasterInstance_t* instance, uint8_t command)
{
    hri_sercomi2cm_set_CTRLB_CMD_bf(instance->hw, command);
}

static void i2c_master_send_ack(I2CMasterInstance_t* instance)
{
    hri_sercomi2cm_clear_CTRLB_ACKACT_bit(instance->hw);
    i2c_master_command(instance, CMD_SEND_ACK);
}

static void i2c_master_send_stop(I2CMasterInstance_t* instance)
{
    hri_sercomi2cm_set_CTRLB_ACKACT_bit(instance->hw);
    i2c_master_command(instance, CMD_SEND_STOP_CONDITION);
}

static bool i2c_master_start_transaction(I2CMasterInstance_t* instance)
{
    instance->current_transfer_count = 0u;

    sercom_set_interrupt_handler(instance, I2CM_INT_HANDLER_MASTER_BUS, &i2c_master_bus_callback);
    uint8_t address = instance->current_transaction.slave_addr & 0xFEu;

    switch (instance->current_transaction.type)
    {
        case I2CTransaction_Read:
            sercom_set_interrupt_handler(instance, I2CM_INT_HANDLER_SLAVE_BUS, &i2c_slave_bus_callback);
            address = address | 0x01u;
            break;

        case I2CTransaction_Write:
            break;

        default:
            return false;
    }

    hri_sercomi2cm_write_ADDR_reg(instance->hw, address);
    return true;
}

static void i2c_master_cleanup_transaction(I2CMasterInstance_t* instance)
{
    /* no continue request, allow starting a new transaction */
    i2c_master_send_stop(instance);

    sercom_set_interrupt_handler(instance, I2CM_INT_HANDLER_MASTER_BUS, NULL);
    sercom_set_interrupt_handler(instance, I2CM_INT_HANDLER_SLAVE_BUS, NULL);

    instance->current_transaction.type = I2CTransaction_None;
}

/**
 * Call the transaction end callback
 *
 * @return true if continuation was requested
 */
static bool i2c_master_handle_end_of_transaction(I2CMasterInstance_t* instance)
{
    size_t transferred = instance->current_transfer_count;
    I2CTransactionCallback_t callback = instance->current_transaction.callback;

    if (callback == NULL)
    {
        return false;
    }

    /* can't modify transaction type because continue_* functions depend on it */
    instance->current_transaction.buffer = NULL;
    instance->current_transfer_count = 0u;
    instance->continue_transaction = false;

    bool was_in_handler = instance->in_handler;
    instance->in_handler = true;
    callback(instance, transferred);
    instance->in_handler = was_in_handler;

    return instance->current_transaction.buffer != NULL;
}

static void i2c_master_abort_transaction(I2CMasterInstance_t* instance)
{
    if (!i2c_master_handle_end_of_transaction(instance))
    {
        /* no continuation, send STOP */
        i2c_master_cleanup_transaction(instance);
        return;
    }

    /*
    TODO: this code does not:

    - send repeated start conditions
    - send a start condition if transaction type changes (read <-> write)

    This modification was made by Softeq, and it's not clear if it's correct.
    */
    if (instance->continue_transaction == false)
    {
        i2c_master_send_stop(instance);

        /*
        At the risk of breaking the color sensors, I've removed the start condition from here.
        If we don't have to continue, don't start a new transaction.
        */
    }
    else
    {
        if (!i2c_master_start_transaction(instance))
        {
            i2c_master_cleanup_transaction(instance);
        }
    }
}

static void i2c_master_continue_tx_transaction(I2CMasterInstance_t* instance)
{
    uint32_t byte_to_send = (uint32_t) instance->current_transaction.buffer[instance->current_transfer_count];
    ++instance->current_transfer_count;

    /* send byte */
    hri_sercomi2cm_write_DATA_reg(instance->hw, byte_to_send);
}

static void i2c_master_bus_callback(void* data)
{
    I2CMasterInstance_t* instance = (I2CMasterInstance_t*) data;

    hri_sercomi2cm_clear_interrupt_MB_bit(instance->hw);
    uint16_t status = hri_sercomi2cm_read_STATUS_reg(instance->hw);

    if (status & (SERCOM_I2CM_STATUS_ARBLOST | SERCOM_I2CM_STATUS_RXNACK | SERCOM_I2CM_STATUS_BUSERR))
    {
        i2c_master_abort_transaction(instance);
    }
    else if (instance->current_transfer_count == instance->current_transaction.count)
    {
        /* last byte was transmitted before this interrupt request */
        i2c_master_abort_transaction(instance);
    }
    else
    {
        /* handle transmission */
        i2c_master_continue_tx_transaction(instance);
    }
}

static void i2c_slave_bus_callback(void* data)
{
    I2CMasterInstance_t* instance = (I2CMasterInstance_t*) data;

    hri_sercomi2cm_clear_interrupt_SB_bit(instance->hw);

    /* byte received, store it */
    instance->current_transaction.buffer[instance->current_transfer_count] = (uint8_t) hri_sercomi2cm_read_DATA_reg(instance->hw);
    instance->current_transfer_count++;

    if (instance->current_transfer_count == instance->current_transaction.count)
    {
        /* buffer full, abort */
        i2c_master_abort_transaction(instance);
    }
    else
    {
        i2c_master_send_ack(instance);
    }
}

I2CResult_t sercom_i2c_master_init(I2CMasterInstance_t* instance, const I2CMasterConfig_t* config)
{
    if (instance->hw != NULL)
    {
        return I2CResult_Busy;
    }

    if (sercom_init(config->hw, instance) != SercomResult_Ok)
    {
        return I2CResult_Error;
    }

    instance->hw = config->hw;
    instance->in_handler = false;
    instance->current_transfer_count = 0u;
    instance->continue_transaction = false;

    instance->current_transaction.count = 0u;
    instance->current_transaction.buffer = NULL;

    hri_sercomi2cm_set_CTRLA_SWRST_bit(instance->hw);

    /**
     * CTRLA:
     * - don't run in standby mode
     * - no Slave SCL Low Extend Time-Out
     * - no Master SCL Low Extended Time-Out
     * - no inactive timeout
     * - standard or fast mode
     * - 300-600ns SDA hold time
     * - no 4-wire mode
     * - clock stretch before ack
     */
    uint32_t ctrl_a = SERCOM_I2CM_CTRLA_MODE(0x05)
                    | SERCOM_I2CM_CTRLA_SDAHOLD(0x02);

    /**
     * CTRLB:
     * - smart mode disabled
     * - quick command disabled
     */
    uint32_t ctrl_b = 0u;

    /**
     * CTRLC:
     * no 32bit extension
     */
    uint32_t ctrl_c = 0u;

    hri_sercomi2cm_write_CTRLA_reg(instance->hw, ctrl_a);
    hri_sercomi2cm_write_CTRLB_reg(instance->hw, ctrl_b);
    hri_sercomi2cm_write_CTRLC_reg(instance->hw, ctrl_c);

    /* assuming standard or fast mode */
    const uint32_t clkrate = 24000u; /**< in kHz */
    const uint32_t baudrate = config->clock_frequency;
    const float trise = config->trise * 0.000000001f;
    uint32_t baud = (uint32_t)lroundf(((clkrate - 10 * baudrate - baudrate * clkrate * trise)
                        / (2 * baudrate)));
    hri_sercomi2cm_write_BAUD_BAUD_bf(instance->hw, baud);

    hri_sercomi2cm_set_INTEN_MB_bit(instance->hw);
    hri_sercomi2cm_set_INTEN_SB_bit(instance->hw);

    return I2CResult_Ok;
}

I2CResult_t sercom_i2c_master_enable(I2CMasterInstance_t* instance)
{
    hri_sercomi2cm_set_CTRLA_ENABLE_bit(instance->hw);

    for (uint32_t retries = 0u; retries < 5u; retries++)
    {
        hri_sercomi2cm_clear_STATUS_reg(instance->hw, SERCOM_I2CM_STATUS_BUSSTATE(0x01));
        for (uint32_t timeout = 0u; timeout < 128u; timeout++)
        {
            if (hri_sercomi2cm_read_STATUS_BUSSTATE_bf(instance->hw) == 0x01)
            {
                return I2CResult_Ok;
            }
        }
    }

    return I2CResult_Error;
}

I2CResult_t sercom_i2c_master_deinit(I2CMasterInstance_t* instance)
{
    if (sercom_deinit(instance) != SercomResult_Ok)
    {
        return I2CResult_Error;
    }

    hri_sercomi2cm_set_CTRLA_SWRST_bit(instance->hw);
    instance->hw = NULL;

    return I2CResult_Ok;
}

I2CResult_t sercom_i2c_master_transfer(I2CMasterInstance_t* instance, const I2CTransaction_t* transaction)
{
    ASSERT(transaction != NULL);
    ASSERT(transaction->buffer != NULL);
    ASSERT(transaction->count != 0u);

    if (instance->in_handler)
    {
        return I2CResult_Error;
    }

    if (instance->current_transaction.type != I2CTransaction_None)
    {
        return I2CResult_Busy;
    }
    instance->current_transaction = *transaction;

    /* data transmission is handled in the interrupt handlers, only set up address here */
    hri_sercomi2cm_clear_CTRLB_ACKACT_bit(instance->hw); // setup to send ACKs on read
    if (!i2c_master_start_transaction(instance))
    {
        instance->current_transaction.type = I2CTransaction_None;

        sercom_set_interrupt_handler(instance, I2CM_INT_HANDLER_MASTER_BUS, NULL);
        sercom_set_interrupt_handler(instance, I2CM_INT_HANDLER_SLAVE_BUS, NULL);

        return I2CResult_Error;
    }

    return I2CResult_Ok;
}

static I2CResult_t _i2c_master_continue(I2CMasterInstance_t* instance, I2CTransactionType_t type, uint8_t* buffer, size_t size, I2CTransactionCallback_t callback, bool continue_transaction)
{
    ASSERT(buffer != NULL);
    if (!instance->in_handler)
    {
        return I2CResult_Error;
    }

    instance->current_transaction.type = type;
    instance->continue_transaction = continue_transaction;

    instance->current_transaction.buffer = buffer;
    instance->current_transaction.count = size;
    instance->current_transaction.callback = callback;

    return I2CResult_Ok;
}

I2CResult_t sercom_i2c_master_continue_read(I2CMasterInstance_t* instance, uint8_t* buffer, size_t size, I2CTransactionCallback_t callback, bool continue_transaction)
{
    return _i2c_master_continue(instance, I2CTransaction_Read, buffer, size, callback, continue_transaction);
}

I2CResult_t sercom_i2c_master_continue_write(I2CMasterInstance_t* instance, uint8_t* buffer, size_t count, I2CTransactionCallback_t callback, bool continue_transaction)
{
    return _i2c_master_continue(instance, I2CTransaction_Write, buffer, count, callback, continue_transaction);
}
