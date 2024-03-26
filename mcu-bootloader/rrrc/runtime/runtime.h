#ifndef RUNTIME_H_
#define RUNTIME_H_

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#include "rrrc/generated_runtime.h"

#include "comm_handlers.h"

void Runtime_RequestJumpToApplication(void);

#endif /* RUNTIME_H_ */
