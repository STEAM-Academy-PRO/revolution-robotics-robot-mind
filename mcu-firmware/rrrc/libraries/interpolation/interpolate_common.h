#ifndef LIBRARY_INTERPOLATE_COMMON_H_
#define LIBRARY_INTERPOLATE_COMMON_H_

#include <float.h>
#include <stdio.h>

typedef struct {
    float* xs;
    float* ys;
    size_t size;
} LUT_t;

int32_t interpolate_lookup_left(LUT_t lut, float x);

#endif /* LIBRARY_INTERPOLATE_COMMON_H_ */
