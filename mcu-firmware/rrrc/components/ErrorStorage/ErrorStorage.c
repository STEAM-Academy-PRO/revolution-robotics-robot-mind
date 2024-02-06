#include "ErrorStorage.h"
#include "utils.h"

/* Begin User Code Section: Declarations */
#include "utils_assert.h"
#include <string.h>

#include <peripheral_clk_config.h>
#include <hal_flash.h>

#define NVM_LAYOUT_VERSION   ((uint8_t) 0x02u)

#define BLOCK_SIZE          (8192u)
#define HEADER_OBJECT_SIZE  (64u)
#define DATA_OBJECT_SIZE    (64u)
#define OBJECTS_PER_BLOCK   ((BLOCK_SIZE - HEADER_OBJECT_SIZE) / DATA_OBJECT_SIZE)

typedef struct {
    uint32_t base_address;
    uint16_t allocated;
    uint16_t deleted;
} BlockInfo_t;

static BlockInfo_t errorStorageBlocks[] = {
    { .base_address = 0x3C000u },
    { .base_address = 0x3E000u },
};

typedef struct {
    uint8_t layout_version;
} FlashHeader_t;

typedef union {
    FlashHeader_t header;
    uint8_t raw[64];
} FlashHeaderObject_t;

typedef struct {
    uint8_t reserved:5;
    uint8_t deleted:1;
    uint8_t valid:1;
    uint8_t allocated:1;
} FlashObjectStatus_t;

typedef struct __attribute__((packed)) {
    FlashObjectStatus_t status;
    uint8_t data[63];
} FlashData_t;

_Static_assert(NVM_LAYOUT_VERSION != 0xFFu, "NVM version can't be same as empty byte");

/* this 32 bytes size is set in stone */
_Static_assert(sizeof(FlashHeaderObject_t) == HEADER_OBJECT_SIZE, "Incorrect flash header size");

/* this is not set in stone, depends on layout version */
_Static_assert(sizeof(FlashData_t) == DATA_OBJECT_SIZE, "Incorrect flash data object size");
_Static_assert(sizeof(ErrorInfo_t) <= DATA_OBJECT_SIZE - 1, "Incorrect error object size");

static struct flash_descriptor FLASH_0;
static uint32_t esActiveBlock;
static bool esInitialized = false;

#define NVM_IS_BIT_SET(bit)  ((bit) == 0u)

static void _count_objects_in_block(BlockInfo_t* block);

static const FlashHeader_t* _block_header(BlockInfo_t* block)
{
    return &((const FlashHeaderObject_t*) block->base_address)->header;
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

static FlashObjectStatus_t _read_data_obj_status(const BlockInfo_t* block, uint8_t idx)
{
    ASSERT (idx < OBJECTS_PER_BLOCK);

    const FlashData_t* ptr = _get_object(block, idx);
    return ptr->status;
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

    if (!NVM_IS_BIT_SET(status.deleted) && (NVM_IS_BIT_SET(status.allocated) || NVM_IS_BIT_SET(status.valid)))
    {
        /* set the deleted bit on a copy */
        status.deleted = 0u;

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
    object.status.allocated = 0u;
    memcpy(&object.data[0], data, size);
    _write_flash(addr, (uint8_t*) &object, sizeof(object));

    /* finalize flash */
    object.status.valid = 0u;
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

static void _count_objects_in_block(BlockInfo_t* block)
{
    block->allocated = 0u;
    block->deleted = 0u;

    /* walk through objects in valid used blocks */
    for (size_t obj_idx = 0u; obj_idx < OBJECTS_PER_BLOCK; obj_idx++)
    {
        FlashObjectStatus_t obj_status = _read_data_obj_status(block, obj_idx);

        /* track available (actually, allocated) space in each block */
        if (NVM_IS_BIT_SET(obj_status.valid))
        {
            block->allocated++;
            if (NVM_IS_BIT_SET(obj_status.deleted))
            {
                block->deleted++;
            }
        }
        else
        {
            /* object is not supposed to have any 0 bits */
            if (NVM_IS_BIT_SET(obj_status.deleted) || NVM_IS_BIT_SET(obj_status.allocated))
            {
                /* this is an invalid block, treat it as deleted */
                block->allocated++;
                block->deleted++;
            }
        }
    }
}

static void _init_block(BlockInfo_t* block)
{
    const FlashHeader_t* header = _block_header(block);

    if (_block_header_empty(header))
    {
        block->allocated = 0u;
        block->deleted = 0u;
        return;
    }
    else if (!_block_header_valid(header))
    {
        /* if a block is not empty and has an invalid layout version, it shall be erased */
        _erase_block(block);
    }
    else
    {
        _count_objects_in_block(block);

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
        /* TODO: store error on init */
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
    /* NOTE: the errors are not returned in allocation order */
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
