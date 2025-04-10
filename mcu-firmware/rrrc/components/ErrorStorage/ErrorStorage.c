#include "ErrorStorage.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "utils_assert.h"
#include <string.h>

#include <peripheral_clk_config.h>
#include <hal_flash.h>

/**
 * ErrorStorage implements EEPROM emulation in a few blocks of the MCU's internal flash memory.
 * We refer to these blocks as non-volatile memory (NVM) storage. The flash memory is NOR flash,
 * which we can erase in 8K blocks, and write in 4-byte words[*]. Erasing a block sets all bits
 * to 1, and writing a byte sets the corresponding bits to 0. We can only change bits from 1 to 0,
 * and we can only change bits to 1 by erasing the block.
 *
 * [*]: The SDK abstract away the 4-byte writes and exposes a function to program individual bytes.
 */

 /**
 * The expected block layout version number.
 *
 * If we encounter a block with a different version byte, we erase the
 * block and start over. This is to ensure that we don't try to read data with a different
 * layout version, which could lead to undefined behavior. Also, erasing the block is the simplest
 * migration strategy, as we don't have to worry about data migration.
 */
#define NVM_LAYOUT_VERSION   ((uint8_t) 0x02u)

/**
 * ErrorStorage works on a list of blocks. Each block is divided into 64 byte objects. The first
 * object in each block is a header, and the rest are data objects. The header contains a version
 * number, and the data objects contain the actual data. The data objects are further divided into
 * a status byte and a data payload. The status byte contains flags that indicate if the object is
 * allocated, valid, or deleted. The data payload contains the actual data.
 */
#define BLOCK_SIZE          (NVMCTRL_BLOCK_SIZE)
#define HEADER_OBJECT_SIZE  (64u)
#define DATA_OBJECT_SIZE    (64u)
#define OBJECTS_PER_BLOCK   ((BLOCK_SIZE - HEADER_OBJECT_SIZE) / DATA_OBJECT_SIZE)

/** Information about a flash block used by ErrorStorage. */
typedef struct {
    /** The starting address of the memory block */
    uint32_t base_address;

    /**
     * The number of objects that are currently in use, used to indicate where new data can be written to.
     * This is populated by scanning the block.
     */
    uint16_t allocated;

    /**
     * The number of deleted objects in the block, used to indicate where valid data can be read from.
     * This is populated by scanning the block.
     */
    uint16_t deleted;
} BlockInfo_t;

/** The  */
static BlockInfo_t errorStorageBlocks[] = {
    { .base_address = 0x3C000u },
    { .base_address = 0x3E000u },
};

typedef struct {
    /** Block layout version. */
    uint8_t layout_version;

    /** Pad header to 64 bytes, and reserve some memory for future use. */
    uint8_t reserved[63];
} FlashHeader_t;

typedef uint8_t FlashObjectStatus_t;

/**
 * Helper macros for bit manipulation in the data object status byte.
 * An unset bit has the value of `1`, as dictated by the flash memory's properties.
 */
#define NVM_SET_BIT(storage, bit)  ((storage) & !(bit))
#define NVM_IS_BIT_SET(storage, bit)  (((storage) & (bit)) == 0u)

/**
 * We use the data object status bits to indicate the state of the object. The status byte is
 * structured as follows:
 * - Bit 7: Allocated: the object is in use and should not be written to again.
 * - Bit 6: Valid: the object contains finalized data and can be considered complete.
 * - Bit 5: Deleted: the object is no longer in use and should be ignored or cleaned up.
 * - Bits 4-0: Reserved
 *
 * The reserved bits are not used and are set to 1. This is to ensure that the status byte is
 * never 0xFF, which would indicate an erased flash byte. The reserved bits are checked when
 * reading the status byte to ensure that the object is not in an invalid state.
 */
#define ALLOCATED_BIT ((uint8_t) 0x80u)
#define VALID_BIT ((uint8_t) 0x40u)
#define DELETED_BIT ((uint8_t) 0x20u)

static bool _is_object_valid(const FlashObjectStatus_t status)
{
    return NVM_IS_BIT_SET(status, VALID_BIT);
}

static bool _is_object_deleted(const FlashObjectStatus_t status)
{
    return NVM_IS_BIT_SET(status, DELETED_BIT);
}

static bool _is_object_allocated(const FlashObjectStatus_t status)
{
    return NVM_IS_BIT_SET(status, ALLOCATED_BIT);
}

static bool _is_object_reserved_bits_set(const FlashObjectStatus_t status)
{
    uint8_t mask = !(ALLOCATED_BIT | VALID_BIT | DELETED_BIT);
    return (status & mask) != mask;
}

static void _mark_object_allocated(FlashObjectStatus_t* status)
{
    *status = NVM_SET_BIT(*status, ALLOCATED_BIT);
}

static void _mark_object_deleted(FlashObjectStatus_t* status)
{
    *status = NVM_SET_BIT(*status, DELETED_BIT);
}

static void _mark_object_valid(FlashObjectStatus_t* status)
{
    *status = NVM_SET_BIT(*status, VALID_BIT);
}

typedef struct __attribute__((packed)) {
    FlashObjectStatus_t status;
    uint8_t data[63];
} FlashData_t;

_Static_assert(NVM_LAYOUT_VERSION != 0xFFu, "NVM version can't be same as empty byte");

/* this 64 byte size is set in stone */
_Static_assert(sizeof(FlashHeader_t) == HEADER_OBJECT_SIZE, "Incorrect flash header size");

/* this is not set in stone, depends on layout version */
_Static_assert(sizeof(FlashData_t) == DATA_OBJECT_SIZE, "Incorrect flash data object size");
_Static_assert(sizeof(ErrorInfo_t) <= DATA_OBJECT_SIZE - 1, "Incorrect error object size");

static struct flash_descriptor FLASH_0;
static uint32_t esActiveBlock;
static bool esInitialized = false;

static void _scan_block(BlockInfo_t* block);

static const FlashHeader_t* _block_header(BlockInfo_t* block)
{
    return (const FlashHeader_t*) block->base_address;
}

static bool _block_header_valid(const FlashHeader_t* header)
{
    return header->layout_version == NVM_LAYOUT_VERSION;
}

static bool _block_header_empty(const FlashHeader_t* header)
{
    return header->layout_version == 0xFFu;
}

static const FlashData_t* _get_object(const BlockInfo_t* block, uint8_t idx)
{
    uint32_t start_addr = block->base_address + HEADER_OBJECT_SIZE;
    const FlashData_t* ptrs = (const FlashData_t*) start_addr;
    return &ptrs[idx];
}

static FlashData_t _read_data_obj(const BlockInfo_t* block, uint8_t idx)
{
    ASSERT (idx < OBJECTS_PER_BLOCK);

    const FlashData_t* ptr = _get_object(block, idx);
    return *ptr;
}

static void _write_flash(uint32_t address, uint8_t* src, size_t size)
{
    int32_t status = flash_append(&FLASH_0, address, src, size);
    ASSERT(status == ERR_NONE);
}

static void _delete_object(BlockInfo_t* block, uint8_t idx)
{
    ASSERT (idx < OBJECTS_PER_BLOCK);

    const FlashData_t* ptr = _get_object(block, idx);
    FlashObjectStatus_t status = ptr->status;

    if (!_is_object_deleted(status) && (_is_object_allocated(status) || _is_object_valid(status)))
    {
        /* set the deleted bit on a copy */
        _mark_object_deleted(&status);

        /* write the first byte back */
        _write_flash((uint32_t) ptr, (uint8_t*) &status, 1u);
    }
}

static void _write_block_header(BlockInfo_t* block, FlashHeader_t* header)
{
    _write_flash(block->base_address, (uint8_t*) header, sizeof(*header));
}

static void _store_object(BlockInfo_t* block, const void* data, size_t size)
{
    /* The caller shall select a non-full block as the storage destination. */
    ASSERT (block->allocated != OBJECTS_PER_BLOCK);

    /* it is possible handling the above assert changes the number of errors in the current block */
    if (block->allocated == OBJECTS_PER_BLOCK)
    {
        /* we can't store more errors */
        return;
    }

    if (block->allocated == 0u)
    {
        const FlashHeader_t* header = _block_header(block);
        if (_block_header_empty(header))
        {
            FlashHeader_t new_header = {
                .layout_version = NVM_LAYOUT_VERSION
            };
            memset(&new_header.reserved[0], 0xFFu, sizeof(new_header.reserved));
            _write_block_header(block, &new_header);
        }
    }

    uint32_t idx = block->allocated;

    const FlashData_t* ptr = _get_object(block, idx);
    uint32_t addr = (uint32_t) ptr;

    /* create object with default data */
    FlashData_t object;
    memset(&object, 0xFFu, sizeof(object));

    /* allocate flash and write data */
    _mark_object_allocated(&object.status);
    memcpy(&object.data[0], data, size);
    _write_flash(addr, (uint8_t*) &object, sizeof(object));

    /* finalize flash */
    _mark_object_valid(&object.status);
    _write_flash(addr, (uint8_t*) &object, 1u);

    block->allocated += 1u;
}

static void _update_number_of_stored_errors(void)
{
    uint32_t errors = 0u;
    for (size_t i = 0u; i < ARRAY_SIZE(errorStorageBlocks); i++)
    {
        const BlockInfo_t* block = &errorStorageBlocks[i];
        ASSERT(block->allocated >= block->deleted);

        errors += block->allocated - block->deleted;
    }
    ErrorStorage_Write_NumberOfStoredErrors(errors);
}

static void _erase_block(BlockInfo_t* block)
{
    int32_t status = flash_erase(&FLASH_0, block->base_address, NVMCTRL_BLOCK_SIZE / NVMCTRL_PAGE_SIZE);
    block->allocated = 0u;
    block->deleted = 0u;

    ASSERT(status == ERR_NONE);
}

/**
 * Collect usage information (number of allocated/deleted objects) about the block to initialize the
 * in-memory representation.
 */
static void _scan_block(BlockInfo_t* block)
{
    block->allocated = 0u;
    block->deleted = 0u;

    /* Walk through objects in the block */
    for (size_t obj_idx = 0u; obj_idx < OBJECTS_PER_BLOCK; obj_idx++)
    {
        FlashData_t flashdata = _read_data_obj(block, obj_idx);

        if (_is_object_valid(flashdata.status))
        {
            block->allocated++;
            /* If the object is not allocated but "valid", it is in fact invalid. */
            if (_is_object_deleted(flashdata.status) || !_is_object_allocated(flashdata.status))
            {
                block->deleted++;
            }
        }
        else
        {
            /* Empty or invalid object */

            /*
               Object header is not supposed to have any 0 bits if it's not valid.
               We can have an interrupted write (which can set the allocated bit),
               or an otherwise dirty/invalid object.
            */
            bool is_dirty = _is_object_deleted(flashdata.status)
                || _is_object_allocated(flashdata.status)
                || _is_object_reserved_bits_set(flashdata.status);

            if (!is_dirty) {
                /* Header is fine, make sure the contents are empty, too! */
                for (size_t i = 0u; i < sizeof(flashdata.data); i++)
                {
                    if (flashdata.data[i] != 0xFFu)
                    {
                        is_dirty = true;
                        break;
                    }
                }
            }

            if (is_dirty)
            {
                /* This is an invalid object, treat it as deleted. */
                block->allocated++;
                block->deleted++;
            }
            else
            {
                /* This is an empty object. */
            }
        }
    }

    ASSERT(block->allocated >= block->deleted);
}

static void _init_block(BlockInfo_t* block)
{
    const FlashHeader_t* header = _block_header(block);

    if (_block_header_empty(header))
    {
        block->allocated = 0u;
        block->deleted = 0u;
    }
    else if (!_block_header_valid(header))
    {
        /* if a block is not empty and has an invalid layout version, it shall be erased */
        _erase_block(block);
    }
    else
    {
        _scan_block(block);

        /* if all objects in the old block are marked as deleted, the block shall be erased */
        if (block->deleted == OBJECTS_PER_BLOCK)
        {
            _erase_block(block);
        }
    }
}

static void _cleanup_invalid_and_full_blocks(void)
{
    for (size_t i = 0u; i < ARRAY_SIZE(errorStorageBlocks); i++)
    {
        _init_block(&errorStorageBlocks[i]);
    }
}

static bool _select_active_block(void)
{
    /* pick the block that has the most data but is not full */
    int32_t max_allocated = -1;
    uint32_t block_idx = 0u;

    for (size_t i = 0u; i < ARRAY_SIZE(errorStorageBlocks); i++)
    {
        const BlockInfo_t* block = &errorStorageBlocks[i];
        if (block->allocated > max_allocated)
        {
            if (block->allocated != OBJECTS_PER_BLOCK)
            {
                block_idx = i;
                max_allocated = (int32_t) block->allocated;
            }
        }
    }

    esActiveBlock = block_idx;
    return max_allocated != OBJECTS_PER_BLOCK;
}

static void _force_select_active_block(void)
{
    uint32_t last_active = esActiveBlock;
    _cleanup_invalid_and_full_blocks();
    if (!_select_active_block())
    {
        /* no more empty space to store errors */
        /* delete a block that is not the same as the last active */
        uint32_t new_active = (last_active + 1u) % ARRAY_SIZE(errorStorageBlocks);
        _erase_block(&errorStorageBlocks[new_active]);
        esActiveBlock = new_active;
    }
}
/* End User Code Section: Declarations */

void ErrorStorage_Run_OnInit(void)
{
    /* Begin User Code Section: OnInit:run Start */
    hri_mclk_set_AHBMASK_NVMCTRL_bit(MCLK);
    flash_init(&FLASH_0, NVMCTRL);

    _force_select_active_block();

    _update_number_of_stored_errors();
    esInitialized = true;
    /* End User Code Section: OnInit:run Start */
    /* Begin User Code Section: OnInit:run End */

    /* End User Code Section: OnInit:run End */
}

void ErrorStorage_Run_Store(const ErrorInfo_t* data)
{
    /* Begin User Code Section: Store:run Start */
    if (esInitialized)
    {
        uint32_t primask = __get_PRIMASK();
        __disable_irq();
        if (errorStorageBlocks[esActiveBlock].allocated == OBJECTS_PER_BLOCK)
        {
            _force_select_active_block();
        }

        /* We copy the data to add the version info. */
        ErrorInfo_t copy = *data;

        copy.hardware_version = ErrorStorage_Read_HardwareVersion();
        copy.firmware_version = ErrorStorage_Read_FirmwareVersion();

        _store_object(&errorStorageBlocks[esActiveBlock], &copy, sizeof(ErrorInfo_t));
        _update_number_of_stored_errors();
        __set_PRIMASK(primask);
    }
    else
    {
        /* TODO: We can defer storing the error in OnInit */
    }
    /* End User Code Section: Store:run Start */
    /* Begin User Code Section: Store:run End */

    /* End User Code Section: Store:run End */
}

bool ErrorStorage_Run_Read(uint32_t index, ErrorInfo_t* data)
{
    /* Begin User Code Section: Read:run Start */
    ASSERT (esInitialized);

    uint32_t distance = index;
    /* NOTE: because we use multiple blocks, the errors are not returned in allocation order. */
    for (size_t i = 0u; i < ARRAY_SIZE(errorStorageBlocks); i++)
    {
        const BlockInfo_t* block = &errorStorageBlocks[i];
        uint32_t errors_in_block = block->allocated - block->deleted;

        if (errors_in_block <= distance)
        {
            distance -= errors_in_block;
            /* check next block */
        }
        else
        {
            /* Assume linear deletion, and assume correct entry. Reader will sort out the errors */
            FlashData_t flashdata = _read_data_obj(block, block->deleted + distance);
            memcpy(data, &flashdata.data[0], sizeof(ErrorInfo_t));
            return true;
        }
    }
    /* End User Code Section: Read:run Start */
    /* Begin User Code Section: Read:run End */
    return false;
    /* End User Code Section: Read:run End */
}

void ErrorStorage_Run_Clear(void)
{
    /* Begin User Code Section: Clear:run Start */
    ASSERT (esInitialized);

    /* delete every allocated object */
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    for (size_t i = 0u; i < ARRAY_SIZE(errorStorageBlocks); i++)
    {
        BlockInfo_t* block = &errorStorageBlocks[i];

        for (uint32_t j = 0u; j < block->allocated; j++)
        {
            _delete_object(block, j);
        }

        block->deleted = block->allocated;
    }
    _update_number_of_stored_errors();
    __set_PRIMASK(primask);
    /* End User Code Section: Clear:run Start */
    /* Begin User Code Section: Clear:run End */

    /* End User Code Section: Clear:run End */
}

__attribute__((weak))
void ErrorStorage_Write_NumberOfStoredErrors(uint32_t value)
{
    (void) value;
    /* Begin User Code Section: NumberOfStoredErrors:write Start */

    /* End User Code Section: NumberOfStoredErrors:write Start */
    /* Begin User Code Section: NumberOfStoredErrors:write End */

    /* End User Code Section: NumberOfStoredErrors:write End */
}

__attribute__((weak))
uint32_t ErrorStorage_Read_FirmwareVersion(void)
{
    /* Begin User Code Section: FirmwareVersion:read Start */

    /* End User Code Section: FirmwareVersion:read Start */
    /* Begin User Code Section: FirmwareVersion:read End */

    /* End User Code Section: FirmwareVersion:read End */
    return 0;
}

__attribute__((weak))
uint32_t ErrorStorage_Read_HardwareVersion(void)
{
    /* Begin User Code Section: HardwareVersion:read Start */

    /* End User Code Section: HardwareVersion:read Start */
    /* Begin User Code Section: HardwareVersion:read End */

    /* End User Code Section: HardwareVersion:read End */
    return 0;
}
