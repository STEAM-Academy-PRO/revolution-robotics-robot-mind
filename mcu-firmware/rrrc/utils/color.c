/*
* color.c
*
* Created: 2019. 04. 18. 14:41:49
*  Author: D�niel Buga
*/

#include "color.h"

#include "functions.h"
#include <math.h>

rgb_t hsv_to_rgb(hsv_t hsv_col)
{
    uint16_t h = hsv_col.h % 360;
    float s = hsv_col.s / 100.0f;
    float v = hsv_col.v / 100.0f;

    float hh = h / 60.0f;
    uint8_t hue = (uint8_t) hh;

    float ff = hh - hue;
    float p = v * (1.0f - s);
    float q = v * (1.0f - (s * ff));
    float t = v * (1.0f - (s * (1.0f - ff)));

    uint8_t qq = (uint8_t)(q * 255u);
    uint8_t vv = (uint8_t)(v * 255u);
    uint8_t tt = (uint8_t)(t * 255u);
    uint8_t pp = (uint8_t)(p * 255u);

    switch (hue)
    {
        case 0:
            return (rgb_t) {
                .R = vv,
                .G = tt,
                .B = pp };
        case 1:
            return (rgb_t) {
                .R = qq,
                .G = vv,
                .B = pp };
        case 2:
            return (rgb_t) {
                .R = pp,
                .G = vv,
                .B = tt };
        case 3:
            return (rgb_t) {
                .R = pp,
                .G = qq,
                .B = vv };
        case 4:
            return (rgb_t) {
                .R = tt,
                .G = pp,
                .B = vv };
        case 5:
        default:
            return (rgb_t) {
                .R = vv,
                .G = pp,
                .B = qq };
    }
}

static inline float max(float x, float y)
{
    if (x > y)
    {
        return x;
    }
    else
    {
        return y;
    }
}

static inline float min(float x, float y)
{
    if (x < y)
    {
        return x;
    }
    else
    {
        return y;
    }
}

#define max3(x, y, z) max(max((x), (y)), (z))
#define min3(x, y, z) min(min((x), (y)), (z))

hsv_t rgb_to_hsv(rgb_t rgb)
{
    int32_t cmin_u = min3(rgb.R, rgb.G, rgb.B);
    int32_t cmax_u = max3(rgb.R, rgb.G, rgb.B);

    int32_t delta_u = (cmax_u - cmin_u);

    hsv_t hsv;
    if (cmin_u == cmax_u)
    {
        hsv.s = 0;
        hsv.h = 0;
    }
    else
    {
        hsv.s = 100 - ((100 * cmin_u) / cmax_u);
        if (cmax_u == rgb.R)
        {
            hsv.h = ((60 * (rgb.G - rgb.B) / delta_u) + 360) % 360;
        }
        else if (cmax_u == rgb.G)
        {
            hsv.h = 60 * (rgb.B - rgb.R) / delta_u + 120;
        }
        else
        {
            hsv.h = 60 * (rgb.R - rgb.G) / delta_u + 240;
        }
    }

    hsv.v = (100 * cmax_u) / 255;
    return hsv;
}

rgb_t rgb565_to_rgb(rgb565_t rgb565)
{
    return (rgb_t) { rgb565.R << 3, rgb565.G << 2, rgb565.B << 3 };
}

rgb565_t rgb_to_rgb565(rgb_t rgb)
{
    return (rgb565_t) { rgb.R >> 3, rgb.G >> 2, rgb.B >> 3 };
}

rgb_t rgb_change_brightness(rgb_t color, float brightness)
{
    return (rgb_t) {
        .R = lroundf(constrain_f32(color.R * brightness, 0.0f, 255.0f)),
        .G = lroundf(constrain_f32(color.G * brightness, 0.0f, 255.0f)),
        .B = lroundf(constrain_f32(color.B * brightness, 0.0f, 255.0f)),
    };
}

rgb565_t rgb565_change_brightness(rgb565_t color, float brightness)
{
    return (rgb565_t) {
        .R = lroundf(constrain_f32(color.R * brightness, 0.0f, 31.0f)),
        .G = lroundf(constrain_f32(color.G * brightness, 0.0f, 63.0f)),
        .B = lroundf(constrain_f32(color.B * brightness, 0.0f, 31.0f)),
    };
}
