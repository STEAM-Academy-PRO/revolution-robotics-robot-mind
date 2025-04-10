
/**
 * \file
 *
 * \brief Non-Volatile Memory Controller
 *
 * Copyright (c) 2016-2018 Microchip Technology Inc. and its subsidiaries.
 *
 * \asf_license_start
 *
 * \page License
 *
 * Subject to your compliance with these terms, you may use Microchip
 * software and any derivatives exclusively with Microchip products.
 * It is your responsibility to comply with third party license terms applicable
 * to your use of third party software (including open source software) that
 * may accompany Microchip software.
 *
 * THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES,
 * WHETHER EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE,
 * INCLUDING ANY IMPLIED WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY,
 * AND FITNESS FOR A PARTICULAR PURPOSE. IN NO EVENT WILL MICROCHIP BE
 * LIABLE FOR ANY INDIRECT, SPECIAL, PUNITIVE, INCIDENTAL OR CONSEQUENTIAL
 * LOSS, DAMAGE, COST OR EXPENSE OF ANY KIND WHATSOEVER RELATED TO THE
 * SOFTWARE, HOWEVER CAUSED, EVEN IF MICROCHIP HAS BEEN ADVISED OF THE
 * POSSIBILITY OR THE DAMAGES ARE FORESEEABLE.  TO THE FULLEST EXTENT
 * ALLOWED BY LAW, MICROCHIP'S TOTAL LIABILITY ON ALL CLAIMS IN ANY WAY
 * RELATED TO THIS SOFTWARE WILL NOT EXCEED THE AMOUNT OF FEES, IF ANY,
 * THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR THIS SOFTWARE.
 *
 * \asf_license_stop
 *
 */

#include <hpl_flash.h>
#include <hpl_user_area.h>
#include <string.h>
#include <utils_assert.h>
#include <utils.h>
#include <hpl_nvmctrl_config.h>

#define NVM_MEMORY ((volatile uint32_t *)FLASH_ADDR)
#define NVMCTRL_BLOCK_PAGES (NVMCTRL_BLOCK_SIZE / NVMCTRL_PAGE_SIZE)
#define NVMCTRL_REGIONS_NUM 32
#define NVMCTRL_INTFLAG_ERR                                                                                            \
    (NVMCTRL_INTFLAG_ADDRE | NVMCTRL_INTFLAG_PROGE | NVMCTRL_INTFLAG_LOCKE | NVMCTRL_INTFLAG_ECCSE                     \
     | NVMCTRL_INTFLAG_NVME | NVMCTRL_INTFLAG_SEESOVF)
/**
 * \brief NVM configuration type
 */
struct nvm_configuration {
    hri_nvmctrl_ctrla_reg_t ctrla; /*!< Control A Register */
};

/**
 * \brief Array of NVM configurations
 */
static struct nvm_configuration _nvm = {
    .ctrla = (CONF_NVM_CACHE0 << NVMCTRL_CTRLA_CACHEDIS0_Pos)
            | (CONF_NVM_CACHE1 << NVMCTRL_CTRLA_CACHEDIS1_Pos)
            | (NVMCTRL_CTRLA_PRM(CONF_NVM_SLEEPPRM))
};

/*!< Pointer to hpl device */
static struct _flash_device *_nvm_dev = NULL;

static void _flash_erase_block(void *const hw, const uint32_t dst_addr);
static void _flash_program_page(void *const hw, const uint32_t dst_addr, const uint8_t *buffer, const uint16_t size);

static uint32_t _page_start_addr(uint32_t addr)
{
    return addr & ~(NVMCTRL_PAGE_SIZE - 1u);
}

static uint32_t _block_start_addr(uint32_t addr)
{
    return addr & ~(NVMCTRL_BLOCK_SIZE - 1u);
}

static void _wait_for_flash(const void* const hw)
{
    while (!hri_nvmctrl_get_STATUS_READY_bit(hw))
    {
        __NOP();
    }
}

static void _execute_command(const void* const hw, uint16_t command)
{
    _wait_for_flash(hw);

    hri_nvmctrl_write_CTRLB_reg(hw, command | NVMCTRL_CTRLB_CMDEX_KEY);
}

static void _execute_addressed_command(const void* const hw, uint32_t addr, uint16_t command)
{
    _wait_for_flash(hw);

    hri_nvmctrl_write_ADDR_reg(hw, addr);
    hri_nvmctrl_write_CTRLB_reg(hw, command | NVMCTRL_CTRLB_CMDEX_KEY);
}

/**
 * \brief Initialize NVM
 */
int32_t _flash_init(struct _flash_device *const device, void *const hw)
{
    ASSERT(device);
    ASSERT(hw == NVMCTRL);

    device->hw = hw;

    hri_nvmctrl_ctrla_reg_t ctrla = hri_nvmctrl_read_CTRLA_reg(hw);
    ctrla &= ~(NVMCTRL_CTRLA_CACHEDIS0 | NVMCTRL_CTRLA_CACHEDIS1 | NVMCTRL_CTRLA_PRM_Msk);
    ctrla |= _nvm.ctrla;
    hri_nvmctrl_write_CTRLA_reg(hw, ctrla);

    _nvm_dev = device;
    NVIC_DisableIRQ(NVMCTRL_0_IRQn);
    NVIC_DisableIRQ(NVMCTRL_1_IRQn);
    NVIC_ClearPendingIRQ(NVMCTRL_0_IRQn);
    NVIC_ClearPendingIRQ(NVMCTRL_1_IRQn);
    NVIC_EnableIRQ(NVMCTRL_0_IRQn);
    NVIC_EnableIRQ(NVMCTRL_1_IRQn);

    return ERR_NONE;
}

/**
 * \brief De-initialize NVM
 */
void _flash_deinit(struct _flash_device *const device)
{
    device->hw = NULL;
    NVIC_DisableIRQ(NVMCTRL_0_IRQn);
    NVIC_DisableIRQ(NVMCTRL_1_IRQn);
}

/**
 * \brief Get the flash page size.
 */
uint32_t _flash_get_page_size(struct _flash_device *const device)
{
    (void)device;
    return (uint32_t)NVMCTRL_PAGE_SIZE;
}

/**
 * \brief Get the numbers of flash page.
 */
uint32_t _flash_get_total_pages(struct _flash_device *const device)
{
    (void)device;
    return (uint32_t)hri_nvmctrl_read_PARAM_NVMP_bf(device->hw);
}

/**
 * \brief Get the number of wait states for read and write operations.
 */
uint8_t _flash_get_wait_state(struct _flash_device *const device)
{
    return hri_nvmctrl_get_CTRLA_reg(device->hw, NVMCTRL_CTRLA_RWS_Msk);
}

/**
 * \brief Set the number of wait states for read and write operations.
 */
void _flash_set_wait_state(struct _flash_device *const device, uint8_t state)
{
    hri_nvmctrl_write_CTRLA_RWS_bf(device->hw, state);
}

/**
 * \brief Reads a number of bytes to a page in the internal Flash.
 */
void _flash_read(struct _flash_device *const device, const uint32_t src_addr, uint8_t *buffer, uint32_t length)
{
    uint8_t *nvm_addr = (uint8_t *)NVM_MEMORY;

    /* Check if the module is busy */
    _wait_for_flash(device->hw);

    for (uint32_t i = 0u; i < length; i++)
    {
        buffer[i] = nvm_addr[src_addr + i];
    }
}

/**
 * Erase part of a block.
 */
static void _flash_erase_partial(struct _flash_device *const device, const uint32_t block_start_addr, uint16_t start_offset, uint16_t length)
{
    ASSERT(start_offset + length <= NVMCTRL_BLOCK_SIZE);

    uint8_t backup[NVMCTRL_BLOCK_PAGES * NVMCTRL_PAGE_SIZE];
    _flash_read(device, block_start_addr, backup, sizeof(backup));

    _flash_erase_block(device->hw, block_start_addr);

    /* clearing the buffer can happen while the erase is in progress */
    memset(&backup[start_offset], 0xFFu, length);

    for (uint32_t i = 0u; i < NVMCTRL_BLOCK_PAGES; i++)
    {
        uint32_t page_start = i * NVMCTRL_PAGE_SIZE;
        uint32_t page_end = page_start + NVMCTRL_PAGE_SIZE;

        bool page_is_dirty = page_end >= start_offset && page_start < start_offset + length;
        if (page_is_dirty)
        {
            _flash_program_page(device->hw, block_start_addr + page_start, &backup[i * NVMCTRL_PAGE_SIZE], NVMCTRL_PAGE_SIZE);
        }
    }
}

static void _flash_erase_range(struct _flash_device *const device, uint32_t dst_addr, uint32_t length)
{
    uint32_t block_start_addr = _block_start_addr(dst_addr);

    /* when address is not aligned with block start address */
    if (dst_addr != block_start_addr)
    {
        uint32_t offset = dst_addr - block_start_addr;
        uint32_t amount = min(length, NVMCTRL_BLOCK_SIZE - offset);
        _flash_erase_partial(device, block_start_addr, offset, amount);

        block_start_addr += NVMCTRL_BLOCK_SIZE;
        length -= amount;
    }

    while (length >= NVMCTRL_BLOCK_SIZE)
    {
        _flash_erase_block(device, block_start_addr);
        block_start_addr += NVMCTRL_BLOCK_SIZE;
        length -= NVMCTRL_BLOCK_SIZE;
    }

    if (length != 0u)
    {
        _flash_erase_partial(device, block_start_addr, 0u, length);
    }
}

static void _flash_program_range(struct _flash_device *const device, uint32_t dst_addr, uint8_t* buffer, uint32_t length)
{
    uint32_t page_start_addr = _page_start_addr(dst_addr);

    uint32_t wr_offset = 0u;
    if (dst_addr != page_start_addr)
    {
        uint32_t offset = dst_addr - page_start_addr;
        uint32_t amount = min(length, NVMCTRL_PAGE_SIZE - offset);
        _flash_program_page(device->hw, dst_addr, buffer, amount);

        page_start_addr += NVMCTRL_PAGE_SIZE;
        length -= amount;
        wr_offset += amount;
    }

    while (length >= NVMCTRL_PAGE_SIZE)
    {
        _flash_program_page(device->hw, page_start_addr, &buffer[wr_offset], NVMCTRL_PAGE_SIZE);

        page_start_addr += NVMCTRL_PAGE_SIZE;
        length -= NVMCTRL_PAGE_SIZE;
        wr_offset += NVMCTRL_PAGE_SIZE;
    }

    if (length != 0u)
    {
        _flash_program_page(device->hw, page_start_addr, &buffer[wr_offset], length);
    }
}

/**
 * \brief Writes a number of bytes to a page in the internal Flash.
 */
void _flash_write(struct _flash_device *const device, const uint32_t dst_addr, uint8_t *buffer, uint32_t length)
{
    _flash_erase_range(device, dst_addr, length);
    _flash_program_range(device, dst_addr, buffer, length);
}

/**
 * \brief Appends a number of bytes in the internal Flash.
 */
void _flash_append(struct _flash_device *const device, const uint32_t dst_addr, uint8_t *buffer, uint32_t length)
{
    _flash_program_range(device, dst_addr, buffer, length);
}

/**
 * \brief Execute erase in the internal flash
 */
void _flash_erase(struct _flash_device *const device, uint32_t dst_addr, uint32_t page_nums)
{
    uint32_t bytes = page_nums * NVMCTRL_PAGE_SIZE;
    _flash_erase_range(device->hw, dst_addr, bytes);
}

/**
 * \brief Execute lock in the internal flash
 */
int32_t _flash_lock(struct _flash_device *const device, const uint32_t dst_addr, uint32_t page_nums)
{
    uint32_t region_pages     = (uint32_t)FLASH_SIZE / (NVMCTRL_REGIONS_NUM * NVMCTRL_PAGE_SIZE);
    uint32_t block_start_addr = _block_start_addr(dst_addr);

    ASSERT(dst_addr == block_start_addr);
    ASSERT(page_nums == region_pages);

    _execute_addressed_command(device->hw, dst_addr, NVMCTRL_CTRLB_CMD_LR);

    return (int32_t)FLASH_SIZE / (NVMCTRL_REGIONS_NUM * NVMCTRL_PAGE_SIZE);
}

/**
 * \brief Execute unlock in the internal flash
 */
int32_t _flash_unlock(struct _flash_device *const device, const uint32_t dst_addr, uint32_t page_nums)
{
    uint32_t region_pages     = (uint32_t)FLASH_SIZE / (NVMCTRL_REGIONS_NUM * NVMCTRL_PAGE_SIZE);
    uint32_t block_start_addr = _block_start_addr(dst_addr);

    ASSERT(dst_addr == block_start_addr);
    ASSERT(page_nums == region_pages);

    _execute_addressed_command(device->hw, dst_addr, NVMCTRL_CTRLB_CMD_UR);

    return (int32_t)FLASH_SIZE / (NVMCTRL_REGIONS_NUM * NVMCTRL_PAGE_SIZE);
}

/**
 * \brief check whether the region which is pointed by address
 */
bool _flash_is_locked(struct _flash_device *const device, const uint32_t dst_addr)
{
    /* Get region for given page */
    uint16_t region_id = dst_addr / (FLASH_SIZE / NVMCTRL_REGIONS_NUM);

    return !(hri_nvmctrl_get_RUNLOCK_reg(device->hw, 1 << region_id));
}

/**
 * \brief Enable/disable Flash interrupt
 */
void _flash_set_irq_state(struct _flash_device *const device, const enum _flash_cb_type type, const bool state)
{
    ASSERT(device);

    if (FLASH_DEVICE_CB_READY == type)
    {
        hri_nvmctrl_write_INTEN_DONE_bit(device->hw, state);
    }
    else if (FLASH_DEVICE_CB_ERROR == type)
    {
        /* these are multiple interrupts */
        if (state)
        {
            hri_nvmctrl_write_INTEN_reg(device->hw, NVMCTRL_INTFLAG_ERR);
        }
        else
        {
            hri_nvmctrl_clear_INTEN_reg(device->hw, NVMCTRL_INTFLAG_ERR);
        }
    }
    else
    {
        ASSERT(0);
    }
}

/**
 * \internal   erase a row in flash
 * \param[in]  hw            The pointer to hardware instance
 * \param[in]  dst_addr      Destination page address to erase
 */
static void _flash_erase_block(void *const hw, const uint32_t dst_addr)
{
    _execute_addressed_command(hw, dst_addr, NVMCTRL_CTRLB_CMD_EB);
}

/**
 * \internal   write a page in flash
 * \param[in]  hw            The pointer to hardware instance
 * \param[in]  dst_addr      Destination page address to write
 * \param[in]  buffer        Pointer to buffer where the data to
 *                           write is stored
 * \param[in] size           The size of data to write to a page
 */
static void _flash_program_page(void *const hw, const uint32_t dst_addr, const uint8_t *buffer, const uint16_t size)
{
    /* ensure writes are not crossing page boundaries */
    uint32_t offset_in_page = dst_addr - _page_start_addr(dst_addr);
    ASSERT(offset_in_page + size <= NVMCTRL_PAGE_SIZE);

    /* TODO: lift word-aligned restriction */
    ASSERT((dst_addr & 0x03u) == 0u);

    uint32_t *ptr_read    = (uint32_t *)buffer;
    uint32_t  nvm_address = dst_addr / 4;

    _execute_command(hw, NVMCTRL_CTRLB_CMD_PBC);
    _wait_for_flash(hw);

    /* Writes to the page buffer must be 32 bits, perform manual copy
     * to ensure alignment */
    uint16_t remaining = size;
    while (remaining >= 4u)
    {
        NVM_MEMORY[nvm_address++] = *ptr_read;
        ptr_read++;
        remaining -= 4u;
    }

    if (remaining > 0u)
    {
        uint32_t nvm = ~((1u << (remaining * 8u)) - 1u);
        for (uint32_t i = 0u; i < remaining; i++)
        {
            nvm |= buffer[size - remaining + i] << (i * 8u);
        }
        NVM_MEMORY[nvm_address] = nvm;
    }

    if (size > 16u)
    {
        _execute_addressed_command(hw, dst_addr, NVMCTRL_CTRLB_CMD_WP);
    }
    else
    {
        _execute_addressed_command(hw, dst_addr, NVMCTRL_CTRLB_CMD_WQW);
    }

    _wait_for_flash(hw);
}

/**
 * \internal NVM interrupt handler
 *
 * \param[in] p The pointer to interrupt parameter
 */
static void _nvm_interrupt_handler(struct _flash_device *device)
{
    void *const hw = device->hw;

    if (hri_nvmctrl_get_INTFLAG_DONE_bit(hw))
    {
        hri_nvmctrl_clear_INTFLAG_DONE_bit(hw);

        if (device->flash_cb.ready_cb) {
            device->flash_cb.ready_cb(device);
        }
    }
    else if (hri_nvmctrl_read_INTFLAG_reg(hw) & NVMCTRL_INTFLAG_ERR)
    {
        hri_nvmctrl_clear_INTFLAG_reg(hw, NVMCTRL_INTFLAG_ERR);

        if (device->flash_cb.error_cb) {
            device->flash_cb.error_cb(device);
        }
    }
}

/**
 * \internal NVM 0 interrupt handler
 */
void NVMCTRL_0_Handler(void)
{
    _nvm_interrupt_handler(_nvm_dev);
}

/**
 * \internal NVM 1 interrupt handler
 */
void NVMCTRL_1_Handler(void)
{
    _nvm_interrupt_handler(_nvm_dev);
}

/*
   The NVM User Row contains calibration data that are automatically read at device
   power on.
   The NVM User Row can be read at address 0x804000.

   The first eight 32-bit words (32 Bytes) of the Non Volatile Memory (NVM) User
   Page contain calibration data that are automatically read at device power-on.
   The remaining 480 Bytes can be used for storing custom parameters.
 */
#ifndef _NVM_USER_ROW_BASE
#define _NVM_USER_ROW_BASE 0x804000
#endif
#define _NVM_USER_ROW_N_BITS 4096
#define _NVM_USER_ROW_N_BYTES (_NVM_USER_ROW_N_BITS / 8)
#define _NVM_USER_ROW_END (((uint8_t *)_NVM_USER_ROW_BASE) + _NVM_USER_ROW_N_BYTES - 1)
#define _IS_NVM_USER_ROW(b)                                                                                            \
    (((uint8_t *)(b) >= (uint8_t *)(_NVM_USER_ROW_BASE)) && ((uint8_t *)(b) <= (uint8_t *)(_NVM_USER_ROW_END)))
#define _IN_NVM_USER_ROW(b, o) (((uint8_t *)(b) + (o)) <= (uint8_t *)(_NVM_USER_ROW_END))

/*
   The NVM Software Calibration Area can be read at address 0x00800080.
   The NVM Software Calibration Area can not be written.
 */
#ifndef _NVM_SW_CALIB_AREA_BASE
#define _NVM_SW_CALIB_AREA_BASE 0x00800080
#endif
#define _NVM_SW_CALIB_AREA_N_BITS 45
#define _NVM_SW_CALIB_AREA_N_BYTES (_NVM_SW_CALIB_AREA_N_BITS / 8)
#define _NVM_SW_CALIB_AREA_END (((uint8_t *)_NVM_SW_CALIB_AREA_BASE) + _NVM_SW_CALIB_AREA_N_BYTES - 1)
#define _IS_NVM_SW_CALIB_AREA(b)                                                                                       \
    (((uint8_t *)(b) >= (uint8_t *)_NVM_SW_CALIB_AREA_BASE) && ((uint8_t *)(b) <= (uint8_t *)_NVM_SW_CALIB_AREA_END))
#define _IN_NVM_SW_CALIB_AREA(b, o) (((uint8_t *)(b) + (o)) <= (uint8_t *)(_NVM_SW_CALIB_AREA_END))

/**
 * \internal Read left aligned data bits
 * \param[in] base       Base address for the data
 * \param[in] bit_offset Offset for the bitfield start
 * \param[in] n_bits     Number of bits in the bitfield
 */
static inline uint32_t _user_area_read_l32_bits(const volatile uint32_t *base, const uint32_t bit_offset,
                                                const uint8_t n_bits)
{
    return base[bit_offset >> 5] & ((1 << n_bits) - 1);
}

/**
 * \internal Read right aligned data bits
 * \param[in] base       Base address for the data
 * \param[in] bit_offset Offset for the bitfield start
 * \param[in] n_bits     Number of bits in the bitfield
 */
static inline uint32_t _user_area_read_r32_bits(const volatile uint32_t *base, const uint32_t bit_offset,
                                                const uint8_t n_bits)
{
    return (base[bit_offset >> 5] >> (bit_offset & 0x1F)) & ((1 << n_bits) - 1);
}

int32_t _user_area_read(const void *base, const uint32_t offset, uint8_t *buf, uint32_t size)
{
    ASSERT(buf);

    /** Parameter check. */
    if (_IS_NVM_USER_ROW(base)) {
        if (!_IN_NVM_USER_ROW(base, offset)) {
            return ERR_BAD_ADDRESS;
        }

        /* Cut off if request too many bytes */
        if (!_IN_NVM_USER_ROW(base, offset + size - 1)) {
            return ERR_INVALID_ARG;
        }
    } else if (_IS_NVM_SW_CALIB_AREA(base)) {
        if (!_IN_NVM_SW_CALIB_AREA(base, offset)) {
            return ERR_BAD_ADDRESS;
        }

        /* Cut off if request too many bytes */
        if (!_IN_NVM_SW_CALIB_AREA(base, offset + size - 1)) {
            return ERR_INVALID_ARG;
        }
    } else {
        return ERR_UNSUPPORTED_OP;
    }

    /* Copy data */
    memcpy(buf, ((uint8_t *)base) + offset, size);
    return ERR_NONE;
}

uint32_t _user_area_read_bits(const void *base, const uint32_t bit_offset, const uint8_t n_bits)
{
    volatile uint32_t *mem_base = (volatile uint32_t *)base;
    uint32_t           l_off, l_bits;
    uint32_t           r_off, r_bits;

    /** Parameter check. */
    if (_IS_NVM_USER_ROW(base)) {
        ASSERT(_IN_NVM_USER_ROW(base, bit_offset >> 3) && _IN_NVM_USER_ROW(base, (bit_offset + n_bits - 1) >> 3));
    } else if (_IS_NVM_SW_CALIB_AREA(base)) {
        ASSERT(_IN_NVM_SW_CALIB_AREA(base, bit_offset >> 3)
               && _IN_NVM_SW_CALIB_AREA(base, (bit_offset + n_bits - 1) >> 3));
    } else {
        ASSERT(false);
    }

    /* Since the bitfield can cross 32-bits boundaries,
     * left and right bits are read from 32-bit aligned address
     * and then combined together. */
    l_off  = bit_offset & (~(32 - 1));
    r_off  = l_off + 32;
    l_bits = 32 - (bit_offset & (32 - 1));

    if (n_bits > l_bits) {
        r_bits = n_bits - l_bits;
    } else {
        l_bits = n_bits;
        r_bits = 0;
    }

    return _user_area_read_r32_bits(mem_base, bit_offset, l_bits)
           + (_user_area_read_l32_bits(mem_base, r_off, r_bits) << l_bits);
}

/** \internal Write 4096-bit user row
 *  \param[in] _row Pointer to 4096-bit user row data.
 */
static int32_t _user_row_write_exec(const uint32_t *_row)
{
    Nvmctrl *hw    = NVMCTRL;
    uint32_t ctrla = hri_nvmctrl_read_CTRLA_reg(NVMCTRL);

    /* Denied if Security Bit is set */
    if (DSU->STATUSB.bit.PROT) {
        return ERR_DENIED;
    }

    /* Do Save */

    /* - Prepare. */
    _wait_for_flash(hw);
    hri_nvmctrl_clear_CTRLA_WMODE_bf(NVMCTRL, NVMCTRL_CTRLA_WMODE_Msk);

    /* - Erase AUX row. */
    hri_nvmctrl_write_ADDR_reg(hw, (hri_nvmctrl_addr_reg_t)_NVM_USER_ROW_BASE);
    hri_nvmctrl_write_CTRLB_reg(hw, NVMCTRL_CTRLB_CMD_EP | NVMCTRL_CTRLB_CMDEX_KEY);
    _wait_for_flash(hw);

    volatile uint32_t* usr_ptr = (volatile uint32_t *) NVMCTRL_USER;

    for (uint32_t i = 0u; i < 128u; i += 4u) /* 32 Quad words [128 bits or 16 bytes] for User row: 32 * 4 * 4 bytes = 512 bytes */
    {
        /* - Page buffer clear & write. */
        hri_nvmctrl_write_CTRLB_reg(hw, NVMCTRL_CTRLB_CMD_PBC | NVMCTRL_CTRLB_CMDEX_KEY);
        _wait_for_flash(hw);

        usr_ptr[i]      = _row[i];
        usr_ptr[i + 1u] = _row[i + 1u];
        usr_ptr[i + 2u] = _row[i + 2u];
        usr_ptr[i + 3u] = _row[i + 3u];

        /* - Write AUX row. */
        hri_nvmctrl_write_ADDR_reg(hw, (hri_nvmctrl_addr_reg_t)(_NVM_USER_ROW_BASE + i * 16));
        hri_nvmctrl_write_CTRLB_reg(hw, NVMCTRL_CTRLB_CMD_WQW | NVMCTRL_CTRLB_CMDEX_KEY);
        _wait_for_flash(hw);
    }

    /* Restore CTRLA */
    hri_nvmctrl_write_CTRLA_reg(NVMCTRL, ctrla);

    return ERR_NONE;
}

int32_t _user_area_write(void *base, const uint32_t offset, const uint8_t *buf, const uint32_t size)
{
    uint32_t _row[NVMCTRL_PAGE_SIZE / 4]; /* Copy of user row. */

    /** Parameter check. */
    if (_IS_NVM_USER_ROW(base)) {
        if (!_IN_NVM_USER_ROW(base, offset)) {
            return ERR_BAD_ADDRESS;
        } else if (!_IN_NVM_USER_ROW(base, offset + size - 1)) {
            return ERR_INVALID_ARG;
        }
    } else if (_IS_NVM_SW_CALIB_AREA(base)) {
        return ERR_DENIED;
    } else {
        return ERR_UNSUPPORTED_OP;
    }

    memcpy(_row, base, NVMCTRL_PAGE_SIZE);       /* Store previous data. */
    memcpy((uint8_t *)_row + offset, buf, size); /* Modify with buf data. */

    return _user_row_write_exec(_row);
}

int32_t _user_area_write_bits(void *base, const uint32_t bit_offset, const uint32_t bits, const uint8_t n_bits)
{
    uint32_t _row[NVMCTRL_PAGE_SIZE / 4]; /* Copy of user row. */
    uint32_t l_off, l_bits;
    uint32_t r_off, r_bits;

    /** Parameter check. */
    if (_IS_NVM_USER_ROW(base)) {
        if (!_IN_NVM_USER_ROW(base, bit_offset >> 3)) {
            return ERR_BAD_ADDRESS;
        } else if (!_IN_NVM_USER_ROW(base, (bit_offset + n_bits - 1) >> 3)) {
            return ERR_INVALID_ARG;
        }
    } else if (_IS_NVM_SW_CALIB_AREA(base)) {
        return ERR_DENIED;
    } else {
        return ERR_UNSUPPORTED_OP;
    }

    /* Since the bitfield can cross 32-bits boundaries,
     * left and right bits are splitted for 32-bit aligned address
     * and then saved. */
    l_off  = bit_offset & (~(32 - 1));
    r_off  = l_off + 32;
    l_bits = 32 - (bit_offset & (32 - 1));

    if (n_bits > l_bits) {
        r_bits = n_bits - l_bits;
    } else {
        l_bits = n_bits;
        r_bits = 0;
    }

    memcpy(_row, base, NVMCTRL_PAGE_SIZE); /* Store previous data. */

    if (l_bits) {
        uint32_t l_mask = ((1 << l_bits) - 1) << (bit_offset & (32 - 1));
        _row[bit_offset >> 5] &= ~l_mask;
        _row[bit_offset >> 5] |= (bits << (bit_offset & (32 - 1))) & l_mask;
    }

    if (r_bits) {
        uint32_t r_mask = (1 << r_bits) - 1;
        _row[r_off >> 5] &= ~r_mask;
        _row[r_off >> 5] |= bits >> l_bits;
    }

    return _user_row_write_exec(_row);
}
