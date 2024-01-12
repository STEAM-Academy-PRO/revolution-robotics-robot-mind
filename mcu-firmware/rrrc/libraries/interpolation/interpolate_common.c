#include "interpolate_common.h"

/**
 * Return the index of the rightmost point in the LUT that is less than or equal to the input x.
 */
int32_t interpolate_lookup_left(LUT_t lut, float x)
{
    int32_t right = 0;

    while (x >= lut.xs[right] && ++right < (int32_t) lut.size);

    return right - 1;
}
