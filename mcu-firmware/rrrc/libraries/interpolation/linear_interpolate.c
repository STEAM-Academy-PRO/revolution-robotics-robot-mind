#include "interpolate_common.h"
#include "libraries/functions.h"
#include <math.h>

float linear_interpolate(LUT_t lut, float value)
{
    int32_t left_idx = interpolate_lookup_left(lut, value);
    if (left_idx < 0)
    {
        left_idx = 0;
    }
    else if ((size_t) left_idx >= lut.size - 1u)
    {
        left_idx = lut.size - 2;
    }
    else if (lut.xs[left_idx] == value)
    {
        return lut.ys[left_idx];
    }

    return map(value,
               lut.xs[left_idx], lut.xs[left_idx + 1],
               lut.ys[left_idx], lut.ys[left_idx + 1]);
}

float linear_interpolate_symmetrical(LUT_t lut, float value)
{
    const float abs_value = fabsf(value);
    return linear_interpolate(lut, abs_value) * sgn_float(value);
}
