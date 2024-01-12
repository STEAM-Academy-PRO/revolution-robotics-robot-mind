#ifndef LIBRARY_INTERPOLATE_LINEAR_H_
#define LIBRARY_INTERPOLATE_LINEAR_H_

#include "interpolate_common.h"

float linear_interpolate(LUT_t lut, float value);
float linear_interpolate_symmetrical(LUT_t lut, float value);

#endif /* LIBRARY_INTERPOLATE_LINEAR_H_ */
