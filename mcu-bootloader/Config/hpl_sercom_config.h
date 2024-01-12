/* Auto-generated config file hpl_sercom_config.h */
#ifndef HPL_SERCOM_CONFIG_H
#define HPL_SERCOM_CONFIG_H

// <<< Use Configuration Wizard in Context Menu >>>

#include <peripheral_clk_config.h>

#ifndef SERCOM_I2CM_CTRLA_MODE_I2C_SLAVE
#define SERCOM_I2CM_CTRLA_MODE_I2C_SLAVE (4 << 2)
#endif

#ifndef CONF_SERCOM_2_I2CS_ENABLE
#define CONF_SERCOM_2_I2CS_ENABLE 1
#endif

// <h> Basic Configuration

// <o> Address <0x0-0x3FF>
// <i> In 7-bit addressing mode the range is 0x00 to 0x7F, in 10-bit addressing mode the range is 0x000 to 0x3FF
// <id> i2c_slave_address
#ifndef CONF_SERCOM_2_I2CS_ADDRESS
#define CONF_SERCOM_2_I2CS_ADDRESS 0x2b
#endif

// </h>

// <e> Advanced Configuration
// <id> i2c_slave_advanced
#ifndef CONF_SERCOM_2_I2CS_ADVANCED_CONFIG
#define CONF_SERCOM_2_I2CS_ADVANCED_CONFIG 0
#endif

// <q> Run in stand-by
// <i> Determine if the module shall run in standby sleep mode
// <id> i2c_slave_runstdby
#ifndef CONF_SERCOM_2_I2CS_RUNSTDBY
#define CONF_SERCOM_2_I2CS_RUNSTDBY 0
#endif

// <o> SDA Hold Time (SDAHOLD)
// <0=>Disabled
// <1=>50-100ns hold time
// <2=>300-600ns hold time
// <3=>400-800ns hold time
// <i> Defines the SDA hold time with respect to the negative edge of SCL
// <id> i2c_slave_sdahold
#ifndef CONF_SERCOM_2_I2CS_SDAHOLD
#define CONF_SERCOM_2_I2CS_SDAHOLD 0x2
#endif

// <q> Slave SCL Low Extend Time-Out (SEXTTOEN)
// <i> Enables the slave SCL low extend time-out. If SCL is cumulatively held low for greater than 25ms from the initial START to a STOP, the slave will release its clock hold if enabled and reset the internal state machine
// <id> i2c_slave_sexttoen
#ifndef CONF_SERCOM_2_I2CS_SEXTTOEN
#define CONF_SERCOM_2_I2CS_SEXTTOEN 0
#endif

// <q> SCL Low Time-Out (LOWTOUT)
// <i> Enables SCL low time-out. If SCL is held low for 25ms-35ms, the master will release it's clock hold
// <id> i2c_slave_lowtout
#ifndef CONF_SERCOM_2_I2CS_LOWTOUT
#define CONF_SERCOM_2_I2CS_LOWTOUT 0
#endif

// <q> SCL Clock Stretch Mode (SCLSM)
// <i> Enables SCL stretching.
// <id> i2c_slave_sclsm
#ifndef CONF_SERCOM_2_I2CS_SCLSM
#define CONF_SERCOM_2_I2CS_SCLSM 0
#endif

// <q> General call addressing (GENCEN)
// <i> Enables general call addressing
// <id> i2c_slave_gencen
#ifndef CONF_SERCOM_2_I2CS_GENCEN
#define CONF_SERCOM_2_I2CS_GENCEN 0
#endif

// <o> Address mode (AMODE)
// <0=>Mask
// <1=>Two addresses
// <2=>Range
// <i> Defines the address mode of a slave device
// <id> i2c_slave_amode
#ifndef CONF_SERCOM_2_I2CS_AMODE
#define CONF_SERCOM_2_I2CS_AMODE 0x0
#endif

// <q> Ten bit addressing (TENBITEN)
// <i> Enables 10 bit addressing addressing
// <id> i2c_slave_tenbiten
#ifndef CONF_SERCOM_2_I2CS_TENBITEN
#define CONF_SERCOM_2_I2CS_TENBITEN 0
#endif

// <o> Address mask<0x0-0x3FF>
// <i> This mask acts as second address match register, an address mask register or the lower limit of an address range
// <i> When acts as mask, bit value 1 means that the corresponding address bit is ignored
// <id> i2c_slave_address_mask
#ifndef CONF_SERCOM_2_I2CS_ADDRESS_MASK
#define CONF_SERCOM_2_I2CS_ADDRESS_MASK 0x0
#endif
// </e>

#ifndef CONF_SERCOM_2_I2CS_SPEED
#define CONF_SERCOM_2_I2CS_SPEED 0x00 // Speed: Standard/Fast mode
#endif



// Enable configuration of module
#ifndef CONF_SERCOM_4_SPI_ENABLE
#define CONF_SERCOM_4_SPI_ENABLE 1
#endif

// Set module in SPI Master mode
#ifndef CONF_SERCOM_4_SPI_MODE
#define CONF_SERCOM_4_SPI_MODE 0x03
#endif

// <h> Basic Configuration

// <q> Receive buffer enable
// <i> Enable receive buffer to receive data from slave (RXEN)
// <id> spi_master_rx_enable
#ifndef CONF_SERCOM_4_SPI_RXEN
#define CONF_SERCOM_4_SPI_RXEN 0x0
#endif

// <o> Character Size
// <i> Bit size for all characters sent over the SPI bus (CHSIZE)
// <0x0=>8 bits
// <0x1=>9 bits
// <id> spi_master_character_size
#ifndef CONF_SERCOM_4_SPI_CHSIZE
#define CONF_SERCOM_4_SPI_CHSIZE 0x0
#endif
// <o> Baud rate <1-18000000>
// <i> The SPI data transfer rate
// <id> spi_master_baud_rate
#ifndef CONF_SERCOM_4_SPI_BAUD
#define CONF_SERCOM_4_SPI_BAUD 4500000
#endif

// </h>

// <e> Advanced Configuration
// <id> spi_master_advanced
#ifndef CONF_SERCOM_4_SPI_ADVANCED
#define CONF_SERCOM_4_SPI_ADVANCED 0
#endif

// <o> Dummy byte <0x00-0x1ff>
// <id> spi_master_dummybyte
// <i> Dummy byte used when reading data from the slave without sending any data
#ifndef CONF_SERCOM_4_SPI_DUMMYBYTE
#define CONF_SERCOM_4_SPI_DUMMYBYTE 0x1ff
#endif

// <o> Data Order
// <0=>MSB first
// <1=>LSB first
// <i> I least significant or most significant bit is shifted out first (DORD)
// <id> spi_master_arch_dord
#ifndef CONF_SERCOM_4_SPI_DORD
#define CONF_SERCOM_4_SPI_DORD 0x0
#endif

// <o> Clock Polarity
// <0=>SCK is low when idle
// <1=>SCK is high when idle
// <i> Determines if the leading edge is rising or falling with a corresponding opposite edge at the trailing edge. (CPOL)
// <id> spi_master_arch_cpol
#ifndef CONF_SERCOM_4_SPI_CPOL
#define CONF_SERCOM_4_SPI_CPOL 0x0
#endif

// <o> Clock Phase
// <0x0=>Sample input on leading edge
// <0x1=>Sample input on trailing edge
// <i> Determines if input data is sampled on leading or trailing SCK edge. (CPHA)
// <id> spi_master_arch_cpha
#ifndef CONF_SERCOM_4_SPI_CPHA
#define CONF_SERCOM_4_SPI_CPHA 0x0
#endif

// <o> Immediate Buffer Overflow Notification
// <i> Controls when OVF is asserted (IBON)
// <0x0=>In data stream
// <0x1=>On buffer overflow
// <id> spi_master_arch_ibon
#ifndef CONF_SERCOM_4_SPI_IBON
#define CONF_SERCOM_4_SPI_IBON 0x0
#endif

// <q> Run in stand-by
// <i> Module stays active in stand-by sleep mode. (RUNSTDBY)
// <id> spi_master_arch_runstdby
#ifndef CONF_SERCOM_4_SPI_RUNSTDBY
#define CONF_SERCOM_4_SPI_RUNSTDBY 0x0
#endif

// <o> Debug Stop Mode
// <i> Behavior of the baud-rate generator when CPU is halted by external debugger. (DBGSTOP)
// <0=>Keep running
// <1=>Halt
// <id> spi_master_arch_dbgstop
#ifndef CONF_SERCOM_4_SPI_DBGSTOP
#define CONF_SERCOM_4_SPI_DBGSTOP 0
#endif

// </e>

// Address mode disabled in master mode
#ifndef CONF_SERCOM_4_SPI_AMODE_EN
#define CONF_SERCOM_4_SPI_AMODE_EN 0
#endif

#ifndef CONF_SERCOM_4_SPI_AMODE
#define CONF_SERCOM_4_SPI_AMODE 0
#endif

#ifndef CONF_SERCOM_4_SPI_ADDR
#define CONF_SERCOM_4_SPI_ADDR 0
#endif

#ifndef CONF_SERCOM_4_SPI_ADDRMASK
#define CONF_SERCOM_4_SPI_ADDRMASK 0
#endif

#ifndef CONF_SERCOM_4_SPI_SSDE
#define CONF_SERCOM_4_SPI_SSDE 0
#endif

#ifndef CONF_SERCOM_4_SPI_MSSEN
#define CONF_SERCOM_4_SPI_MSSEN 0x0
#endif

#ifndef CONF_SERCOM_4_SPI_PLOADEN
#define CONF_SERCOM_4_SPI_PLOADEN 0
#endif

// <o> Receive Data Pinout
// <0x0=>PAD[0]
// <0x1=>PAD[1]
// <0x2=>PAD[2]
// <0x3=>PAD[3]
// <id> spi_master_rxpo
#ifndef CONF_SERCOM_4_SPI_RXPO
#define CONF_SERCOM_4_SPI_RXPO 2
#endif

// <o> Transmit Data Pinout
// <0x0=>PAD[0,1]_DO_SCK
// <0x1=>PAD[2,3]_DO_SCK
// <0x2=>PAD[3,1]_DO_SCK
// <0x3=>PAD[0,3]_DO_SCK
// <id> spi_master_txpo
#ifndef CONF_SERCOM_4_SPI_TXPO
#define CONF_SERCOM_4_SPI_TXPO 2
#endif

// Calculate baud register value from requested baudrate value
#ifndef CONF_SERCOM_4_SPI_BAUD_RATE
#define CONF_SERCOM_4_SPI_BAUD_RATE ((float)CONF_GCLK_SERCOM4_CORE_FREQUENCY / (float)(2 * CONF_SERCOM_4_SPI_BAUD)) - 1
#endif

// <<< end of configuration section >>>

#endif // HPL_SERCOM_CONFIG_H
