import argparse
import json

import chevron

from cglue.utils.filesystem import change_file
from cglue.utils.common import list_to_chevron_list
from cglue.plugins.AsyncServerCalls import async_server_calls
from cglue.plugins.BuiltinDataTypes import builtin_data_types
from cglue.plugins.Locks import locks
from cglue.plugins.ProjectConfigCompactor import project_config_compactor
from cglue.plugins.RuntimeEvents import runtime_events
from cglue.cglue import CGlue

makefile_template = """# This Makefile was generated using "python -m tools.generate_makefile"
C_SRCS += \\
{{# sources }}
{{ source }}{{^ last }} \\{{/ last }}
{{/ sources }}

INCLUDE_PATHS += \\
{{# includes }}
{{ path }}{{^ last }} \\{{/ last }}
{{/ includes }}

COMPILE_FLAGS += \\
-x c \\
-mthumb \\
-D__SAMD51P19A__ \\
-DCOMPATIBLE_HW_VERSIONS=2 \\
-ffunction-sections \\
-fdata-sections \\
-mlong-calls \\
-Wall \\
-Wextra \\
-Wundef \\
-Wdouble-promotion \\
-mcpu=cortex-m4 \\
-c \\
-std=gnu99 \\
-mfloat-abi=hard \\
-mfpu=fpv4-sp-d16 \\
-MD \\
-MP

LINKER_FLAGS := \\
-mthumb \\
-mfloat-abi=hard \\
-mfpu=fpv4-sp-d16 \\
-mcpu=cortex-m4 \\
--specs=nano.specs \\
-TConfig/samd51p19a_flash.ld

ifeq ($(OS),Windows_NT)
\tSHELL := cmd.exe
\tMKDIR := md
\tGCC_BINARY_PREFIX := "C:/gcc/gcc-arm-none-eabi-10.3-2021.10/bin/arm-none-eabi-
\tGCC_BINARY_SUFFIX := .exe"
\tNULL := nul
\tDEL := rmdir /s /q
\tTRUE := VER>nul
else
\tSHELL := /bin/bash
\tMKDIR := mkdir -p
\tGCC_BINARY_PREFIX := /usr/share/gcc-arm/gcc-arm-none-eabi-10.3-2021.10/bin/arm-none-eabi-
\tGCC_BINARY_SUFFIX :=
\tNULL := /dev/null
\tDEL := rm -rf
\tTRUE := true
endif

DEBUG_COMPILE_FLAGS := \\
\t-DDEBUG \\
\t-DDEBUG_LOG \\
\t-DBOOTLOADER_VERSION=0 \\
\t-DHARDWARE_VERSION=2 \\
\t-O0 \\
\t-g3

RELEASE_COMPILE_FLAGS := \\
\t-DBOOTLOADER_VERSION=0 \\
\t-DHARDWARE_VERSION=2 \\
\t-O3 \\
\t-g3 \\
\t-flto

ifeq ($(config), debug)
OUTPUT_DIR :=Build/Debug/mcu-firmware
COMPILE_FLAGS += $(DEBUG_COMPILE_FLAGS)
else ifeq ($(config), ci)
OUTPUT_DIR :=Build/Debug/mcu-firmware
COMPILE_FLAGS += \\
\t$(DEBUG_COMPILE_FLAGS) \\
\t-fanalyzer
else
OUTPUT_DIR :=Build/Release/mcu-firmware
COMPILE_FLAGS += $(RELEASE_COMPILE_FLAGS)
LINKER_FLAGS += \\
\t-flto
endif

OUTPUT_FILE :=$(OUTPUT_DIR)/rrrc_samd51

all: $(OUTPUT_FILE).elf

OBJS := $(C_SRCS:%.c=$(OUTPUT_DIR)/%.o)
C_DEPS := $(OBJS:%.o=%.d)

ifneq ($(MAKECMDGOALS),clean)
-include $(C_DEPS)
endif

$(OUTPUT_DIR)/%.d: %.c
\t@echo Collecting dependencies: $<
\t@$(MKDIR) "$(@D)" 2>$(NULL) || $(TRUE)
\t@$(GCC_BINARY_PREFIX)gcc$(GCC_BINARY_SUFFIX) $(addprefix -I,$(INCLUDE_PATHS)) $(COMPILE_FLAGS) -MF $@ -MT$@ -M $<

$(OUTPUT_DIR)/%.o: %.c
\t@echo Building file: $<
\t@$(GCC_BINARY_PREFIX)gcc$(GCC_BINARY_SUFFIX) $(addprefix -I,$(INCLUDE_PATHS)) $(COMPILE_FLAGS) -o $@ $<
\t@echo Finished building: $<

$(OUTPUT_FILE).elf: $(OBJS)
\t@echo Building target: $@
\t@$(GCC_BINARY_PREFIX)gcc$(GCC_BINARY_SUFFIX) -o$(OUTPUT_FILE).elf $(OBJS) $(LINKER_FLAGS) -Wl,-Map=$(OUTPUT_FILE).map -Wl,--start-group -lm  -Wl,--end-group -Wl,--gc-sections
\t@echo Finished building target: $@
\t@$(GCC_BINARY_PREFIX)objcopy$(GCC_BINARY_SUFFIX) -O binary $(OUTPUT_FILE).elf $(OUTPUT_FILE).bin
\t$(GCC_BINARY_PREFIX)size$(GCC_BINARY_SUFFIX) $(OUTPUT_FILE).elf

clean:
\t-@$(DEL) Build
\t@echo Removed Build directory
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", help="Name of project config json file", default="./project.json"
    )
    parser.add_argument(
        "--cleanup", help="Clean up newly created backup", action="store_true"
    )

    args = parser.parse_args()

    rt = CGlue(args.config)
    rt.add_plugin(project_config_compactor())
    rt.add_plugin(builtin_data_types())
    rt.add_plugin(runtime_events())
    rt.add_plugin(locks())
    rt.add_plugin(async_server_calls())

    rt.load()
    config = rt._project_config

    source_files = config["sources"]

    for component in config["components"]:
        component_file = rt.component_dir(component) + "/{}"
        component_config_path = component_file.format("config.json")
        with open(component_config_path, "r") as f:
            component_config = json.load(f)

        source_files += [
            component_file.format(source) for source in component_config["source_files"]
        ]

    template_context = {
        "sources": list_to_chevron_list(source_files, "source", "last"),
        "includes": list_to_chevron_list(config["includes"], "path", "last"),
    }
    makefile_contents = chevron.render(makefile_template, template_context)

    if change_file("Makefile", makefile_contents, args.cleanup):
        print("New makefile generated")
    else:
        print("Makefile up to date")
