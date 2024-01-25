C_SRCS += \
../mcu-common/Atmel/hal/src/hal_atomic.c \
../mcu-common/Atmel/hal/src/hal_cache.c \
../mcu-common/Atmel/hal/src/hal_delay.c \
../mcu-common/Atmel/hal/src/hal_flash.c \
../mcu-common/Atmel/hal/src/hal_gpio.c \
../mcu-common/Atmel/hal/src/hal_i2c_s_async.c \
../mcu-common/Atmel/hal/src/hal_init.c \
../mcu-common/Atmel/hal/src/hal_io.c \
../mcu-common/Atmel/hal/src/hal_sleep.c \
../mcu-common/Atmel/hal/utils/src/utils_syscalls.c \
../mcu-common/Atmel/hpl/cmcc/hpl_cmcc.c \
../mcu-common/Atmel/hpl/core/hpl_core_m4.c \
../mcu-common/Atmel/hpl/core/hpl_init.c \
../mcu-common/Atmel/hpl/dmac/hpl_dmac.c \
../mcu-common/Atmel/hpl/gclk/hpl_gclk.c \
../mcu-common/Atmel/hpl/mclk/hpl_mclk.c \
../mcu-common/Atmel/hpl/nvmctrl/hpl_nvmctrl.c \
../mcu-common/Atmel/hpl/osc32kctrl/hpl_osc32kctrl.c \
../mcu-common/Atmel/hpl/oscctrl/hpl_oscctrl.c \
../mcu-common/Atmel/hpl/pm/hpl_pm.c \
../mcu-common/Atmel/hpl/ramecc/hpl_ramecc.c \
../mcu-common/Atmel/hpl/sercom/hpl_sercom.c \
../mcu-common/Atmel/Device_Startup/startup_samd51.c \
../mcu-common/Atmel/Device_Startup/system_samd51.c \
../mcu-common/Atmel/hal/src/hal_spi_m_dma.c \
../mcu-common/Atmel/hal/src/hal_spi_m_sync.c \
../mcu-common/SEGGER/RTT/SEGGER_RTT.c \
../mcu-common/SEGGER/RTT/SEGGER_RTT_printf.c \
../mcu-common/SEGGER/RTT/Syscalls/SEGGER_RTT_Syscalls_GCC.c \
main.c \
driver_init.c \
atmel_start.c \
rrrc/components/LEDController/LEDController.c \
rrrc/components/MasterCommunicationInterface/i2cHal.c \
rrrc/components/MasterCommunicationInterface/MasterCommunicationInterface.c \
rrrc/components/MasterCommunication/CommunicationManager.c \
rrrc/components/MasterCommunication/MasterCommunication.c \
rrrc/components/UpdateManager/UpdateManager.c \
rrrc/components/VersionProvider/VersionProvider.c \
rrrc/flash_mapping.c \
rrrc/runtime/comm_handlers.c \
rrrc/utils/color.c \
rrrc/utils/converter.c \
rrrc/utils/crc.c \
rrrc/utils/functions.c \
rrrc/watchdog.c

INCLUDE_PATHS += \
rrrc/include \
Config \
. \
../mcu-common/Atmel/hpl/nvmctrl \
../mcu-common/Atmel/hpl/ramecc \
../mcu-common/Atmel/hal/include \
../mcu-common/Atmel/hal/utils/include \
../mcu-common/Atmel/hpl/adc \
../mcu-common/Atmel/hpl/cmcc \
../mcu-common/Atmel/hpl/core \
../mcu-common/Atmel/hpl/dmac \
../mcu-common/Atmel/hpl/eic \
../mcu-common/Atmel/hpl/gclk \
../mcu-common/Atmel/hpl/mclk \
../mcu-common/Atmel/hpl/osc32kctrl \
../mcu-common/Atmel/hpl/oscctrl \
../mcu-common/Atmel/hpl/pm \
../mcu-common/Atmel/hpl/port \
../mcu-common/Atmel/hpl/rtc \
../mcu-common/Atmel/hpl/sercom \
../mcu-common/Atmel/hpl/systick \
../mcu-common/Atmel/hpl/tc \
../mcu-common/Atmel/hri \
../mcu-common/Atmel/samd51a/include \
../mcu-common/CMSIS/Include \
../mcu-common/SEGGER/RTT \
rrrc \
rrrc/components/MasterCommunication \
rrrc/components/MasterCommunicationInterface \
rrrc/components/LEDController \
rrrc/components/VersionProvider \
rrrc/components/UpdateManager \
rrrc/include \
rrrc/components \
rrrc/runtime \
rrrc/utils \
third_party

COMPILE_FLAGS += \
-x c \
-mthumb \
-D__SAMD51P19A__ \
-ffunction-sections \
-fdata-sections \
-mlong-calls \
-Wall \
-Wextra \
-Wundef \
-Wdouble-promotion \
-mcpu=cortex-m4 \
-c \
-std=gnu99 \
-mfloat-abi=hard \
-mfpu=fpv4-sp-d16 \
-MD \
-MP

LINKER_FLAGS := \
-mthumb \
-mfloat-abi=hard \
-mfpu=fpv4-sp-d16 \
-mcpu=cortex-m4 \
--specs=nano.specs \
-TConfig/samd51p19a_flash.ld

ifeq ($(OS),Windows_NT)
	SHELL := cmd.exe
	MKDIR := md
	GCC_BINARY_PREFIX := "C:/gcc/gcc-arm-none-eabi-9-2019-q4-major/bin/arm-none-eabi-
	GCC_BINARY_SUFFIX := .exe"
	NULL := nul
	DEL := rmdir /s /q
	TRUE := VER>nul
else
	SHELL := /bin/bash
	MKDIR := mkdir -p
	GCC_BINARY_PREFIX := /usr/share/gcc-arm/gcc-arm-none-eabi-9-2019-q4-major/bin/arm-none-eabi-
	GCC_BINARY_SUFFIX :=
	NULL := /dev/null
	DEL := rm -rf
	TRUE := true
endif

ifeq ($(config), debug)
OUTPUT_DIR :=Build/Debug/mcu-bootloader
COMPILE_FLAGS += \
-DDEBUG \
-DBOOTLOADER_VERSION=0 \
-DHARDWARE_VERSION=2 \
-O0 \
-g3
else
OUTPUT_DIR :=Build/Release/mcu-bootloader
COMPILE_FLAGS += \
-DBOOTLOADER_VERSION=0 \
-DHARDWARE_VERSION=2 \
-O3 \
-g3 \
-flto
LINKER_FLAGS += -flto
endif

OUTPUT_FILE :=$(OUTPUT_DIR)/rrrc_samd51

all: $(OUTPUT_FILE).elf

OBJS := $(C_SRCS:%.c=$(OUTPUT_DIR)/%.o)
C_DEPS := $(OBJS:%.o=%.d)

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
endif

# Make sure files from the outer mcu-common directory don't escape Build
$(OUTPUT_DIR)/%.o: %.c
	@echo Building file: $<
	@$(MKDIR) "$(@D)" 2>$(NULL) || $(TRUE)
	@$(GCC_BINARY_PREFIX)gcc$(GCC_BINARY_SUFFIX) $(addprefix -I,$(INCLUDE_PATHS)) $(COMPILE_FLAGS) -MF $(@:%.o=%.d) -MT$(@:%.o=%.d) -o $@ $<
	@echo Finished building: $<

$(OUTPUT_FILE).elf: $(OBJS)
	@echo Building target: $@
	@$(GCC_BINARY_PREFIX)gcc$(GCC_BINARY_SUFFIX) -o$(OUTPUT_FILE).elf $(OBJS) $(LINKER_FLAGS) -Wl,-Map=$(OUTPUT_FILE).map -Wl,--start-group -lm  -Wl,--end-group -Wl,--gc-sections
	@echo Finished building target: $@
	@$(GCC_BINARY_PREFIX)objcopy$(GCC_BINARY_SUFFIX) -O binary $(OUTPUT_FILE).elf $(OUTPUT_FILE).bin
	@$(GCC_BINARY_PREFIX)objcopy$(GCC_BINARY_SUFFIX) -O ihex -R .eeprom -R .fuse -R .lock -R .signature  $(OUTPUT_FILE).elf $(OUTPUT_FILE).hex
	@$(GCC_BINARY_PREFIX)objcopy$(GCC_BINARY_SUFFIX) -j .eeprom --set-section-flags=.eeprom=alloc,load --change-section-lma .eeprom=0 --no-change-warnings -O binary $(OUTPUT_FILE).elf $(OUTPUT_FILE).eep
	@$(GCC_BINARY_PREFIX)objdump$(GCC_BINARY_SUFFIX) -h -S $(OUTPUT_FILE).elf > $(OUTPUT_FILE).lss
	@$(GCC_BINARY_PREFIX)objcopy$(GCC_BINARY_SUFFIX) -O srec -R .eeprom -R .fuse -R .lock -R .signature  $(OUTPUT_FILE).elf $(OUTPUT_FILE).srec
	$(GCC_BINARY_PREFIX)size$(GCC_BINARY_SUFFIX) $(OUTPUT_FILE).elf

clean:
	-@$(DEL) Build
	@echo Removed Build directory
