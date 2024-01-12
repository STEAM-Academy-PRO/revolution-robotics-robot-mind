/*
 * color.h
 *
 * Created: 2019. 04. 18. 14:42:15
 *  Author: Dániel Buga
 */ 


#ifndef COLOR_H_
#define COLOR_H_

#include <stdint.h>

typedef struct
{
    uint16_t R:5;
    uint16_t G:6;
    uint16_t B:5;
} __attribute__((packed)) rgb565_t;
_Static_assert(sizeof(rgb565_t) == 2, "Size of rgb565_t should be 2 bytes");

#define rgb565_equals(a, b) (\
    a.R == b.R && \
    a.G == b.G && \
    a.B == b.B    \
)

typedef struct
{
    uint8_t R;
    uint8_t G;
    uint8_t B;
} rgb_t;

#define rgb_equals(a, b) (\
    a.R == b.R && \
    a.G == b.G && \
    a.B == b.B    \
)

typedef struct
{
    uint16_t h;
    uint8_t s;
    uint8_t v;
} hsv_t;

#define hsv_equals(a, b) (\
    a.h == b.h && \
    a.s == b.s && \
    a.v == b.v    \
)

rgb_t rgb565_to_rgb(rgb565_t rgb565);
rgb565_t rgb_to_rgb565(rgb_t rgb);
rgb_t hsv_to_rgb(hsv_t hsv_col);
hsv_t rgb_to_hsv(rgb_t rgb);

rgb_t rgb_change_brightness(rgb_t color, float brightness);
rgb565_t rgb565_change_brightness(rgb565_t color, float brightness);

#endif /* COLOR_H_ */