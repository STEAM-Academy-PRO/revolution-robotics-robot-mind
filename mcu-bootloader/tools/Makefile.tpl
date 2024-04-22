# This Makefile was generated using "python -m tools.generate_makefile"

C_SRCS += \
{{# sources }}
	{{ source }}{{^ last }} \{{/ last }}
{{/ sources }}

INCLUDE_PATHS += \
{{# includes }}
	{{ path }}{{^ last }} \{{/ last }}
{{/ includes }}

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
	NULL := nul
	DEL := rmdir /s /q
	TRUE := VER>nul
else
	SHELL := /bin/bash
	MKDIR := mkdir -p
	NULL := /dev/null
	DEL := rm -rf
	TRUE := true
endif

DEBUG_COMPILE_FLAGS := \
	-DDEBUG \
	-DDEBUG_LOG \
	-DBOOTLOADER_VERSION=0 \
	-DHARDWARE_VERSION=2 \
	-O0 \
	-g3

RELEASE_COMPILE_FLAGS := \
	-DDEBUG_LOG \
	-DBOOTLOADER_VERSION=0 \
	-DHARDWARE_VERSION=2 \
	-DI2CS_DATA_DELAY=9 \
	-O3 \
	-g3

ifeq ($(config), debug)
	OUTPUT_DIR :=Build/Debug/mcu-bootloader
	COMPILE_FLAGS += $(DEBUG_COMPILE_FLAGS)
else
	OUTPUT_DIR :=Build/Release/mcu-bootloader
	COMPILE_FLAGS += $(RELEASE_COMPILE_FLAGS)
endif

ifeq ($(ci), true)
	COMPILE_FLAGS += -fanalyzer
endif

OUTPUT_FILE :=$(OUTPUT_DIR)/rrrc_samd51

.PHONY: all clean

all: $(OUTPUT_FILE).elf

clean:
	-@$(DEL) Build
	@echo Removed Build directory

OBJS := $(C_SRCS:%.c=$(OUTPUT_DIR)/%.o)
C_DEPS := $(OBJS:%.o=%.d)

ifneq ($(MAKECMDGOALS),clean)
-include $(C_DEPS)
endif

$(OUTPUT_DIR)/%.d: %.c
	@echo Collecting dependencies: $<
	@$(MKDIR) "$(@D)" 2>$(NULL) || $(TRUE)
	@{{{ gcc }}} $(addprefix -I,$(INCLUDE_PATHS)) $(COMPILE_FLAGS) -MF $@ -MT$@ -M $<

$(OUTPUT_DIR)/%.o: %.c
	@echo Building file: $<
	@{{{ gcc }}} $(addprefix -I,$(INCLUDE_PATHS)) $(COMPILE_FLAGS) -o $@ $<
	@echo Finished building: $<

$(OUTPUT_FILE).elf: $(OBJS)
	@echo Building target: $@
	@{{{ gcc }}} -o$(OUTPUT_FILE).elf $(OBJS) $(LINKER_FLAGS) -Wl,-Map=$(OUTPUT_FILE).map -Wl,--start-group -lm  -Wl,--end-group -Wl,--gc-sections
	@echo Finished building target: $@
	@{{{ objcopy }}} -O binary $(OUTPUT_FILE).elf $(OUTPUT_FILE).bin
	@{{{ size }}} $(OUTPUT_FILE).elf
