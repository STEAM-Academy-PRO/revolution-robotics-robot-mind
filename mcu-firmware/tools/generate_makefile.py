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
-I{{ path }}{{^ last }} \\{{/ last }}
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
-TAtmel/Device_Startup/samd51p19a_flash.ld

ifeq ($(OS),Windows_NT)
\tSHELL := cmd.exe
\tMKDIR := md
\tGCC_BINARY_PREFIX := "C:/gcc/gcc-arm-none-eabi-9-2019-q4-major/bin/arm-none-eabi-
\tGCC_BINARY_SUFFIX := .exe"
else
\tSHELL := /bin/bash
\tMKDIR := mkdir -p
\tGCC_BINARY_PREFIX := /usr/share/gcc-arm/gcc-arm-none-eabi-9-2019-q4-major/bin/arm-none-eabi-
\tGCC_BINARY_SUFFIX :=
endif

ifeq ($(config), debug)
OUTPUT_DIR :=Build/Debug
COMPILE_FLAGS += -DDEBUG -O0 -g3
else
OUTPUT_DIR :=Build/Release
COMPILE_FLAGS += -O3 -g3 -flto
LINKER_FLAGS += -flto
endif

OUTPUT_FILE :=$(OUTPUT_DIR)/rrrc_samd51

all: $(OUTPUT_FILE).elf

OBJS := $(C_SRCS:%.c=$(OUTPUT_DIR)/%.o)
DIRS := $(sort $(dir $(OBJS)))
C_DEPS := $(OBJS:%.o=%.d)

$(DIRS):
\t-$(MKDIR) "$@"

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
endif

$(OUTPUT_DIR)/%.o: %.c | $(DIRS)
\t@echo Building file: $<
\t$(GCC_BINARY_PREFIX)gcc$(GCC_BINARY_SUFFIX) $(INCLUDE_PATHS) $(COMPILE_FLAGS) -MF $(@:%.o=%.d) -MT$(@:%.o=%.d) -MT$(@:%.o=%.o) -o $@ $<
\t@echo Finished building: $<

$(OUTPUT_FILE).elf: $(OBJS)
\t@echo Building target: $@
\t$(GCC_BINARY_PREFIX)gcc$(GCC_BINARY_SUFFIX) -o$(OUTPUT_FILE).elf $(OBJS) $(LINKER_FLAGS) -Wl,-Map=$(OUTPUT_FILE).map -Wl,--start-group -lm  -Wl,--end-group $(LINK_DIRS) -Wl,--gc-sections
\t@echo Finished building target: $@
\t$(GCC_BINARY_PREFIX)objcopy$(GCC_BINARY_SUFFIX) -O binary $(OUTPUT_FILE).elf $(OUTPUT_FILE).bin
\t$(GCC_BINARY_PREFIX)objcopy$(GCC_BINARY_SUFFIX) -O ihex -R .eeprom -R .fuse -R .lock -R .signature  $(OUTPUT_FILE).elf $(OUTPUT_FILE).hex
\t$(GCC_BINARY_PREFIX)objcopy$(GCC_BINARY_SUFFIX) -j .eeprom --set-section-flags=.eeprom=alloc,load --change-section-lma .eeprom=0 --no-change-warnings -O binary $(OUTPUT_FILE).elf $(OUTPUT_FILE).eep || exit 0
\t$(GCC_BINARY_PREFIX)objdump$(GCC_BINARY_SUFFIX) -h -S $(OUTPUT_FILE).elf > $(OUTPUT_FILE).lss
\t$(GCC_BINARY_PREFIX)objcopy$(GCC_BINARY_SUFFIX) -O srec -R .eeprom -R .fuse -R .lock -R .signature  $(OUTPUT_FILE).elf $(OUTPUT_FILE).srec
\t$(GCC_BINARY_PREFIX)size$(GCC_BINARY_SUFFIX) $(OUTPUT_FILE).elf

clean:
\t-rm -rf Build
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Name of project config json file', default="./project.json")
    parser.add_argument('--cleanup', help='Clean up newly created backup', action="store_true")

    args = parser.parse_args()

    rt = CGlue(args.config)
    rt.add_plugin(project_config_compactor())
    rt.add_plugin(builtin_data_types())
    rt.add_plugin(runtime_events())
    rt.add_plugin(locks())
    rt.add_plugin(async_server_calls())

    rt.load()
    config = rt._project_config

    source_files = config['sources']

    for component in config['components']:
        component_file = 'rrrc/components/{}/{{}}'.format(component)
        component_config_path = component_file.format('config.json')
        with open(component_config_path, "r") as f:
            component_config = json.load(f)

        source_files += [component_file.format(source) for source in component_config['source_files']]

    template_context = {
        'sources':  list_to_chevron_list(source_files, 'source', 'last'),
        'includes': list_to_chevron_list(config['includes'], 'path', 'last')
    }
    makefile_contents = chevron.render(makefile_template, template_context)

    if change_file('Makefile', makefile_contents, args.cleanup):
        print('New makefile generated')
    else:
        print('Makefile up to date')
