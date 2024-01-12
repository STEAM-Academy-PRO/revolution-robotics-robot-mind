/*
* color.c
*
* Created: 2019. 04. 18. 14:41:49
*  Author: Dániel Buga
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

static inline float max3(float x, float y, float z)
{
    float m = max(x, y);
    return max(m, z);
}

static inline float min3(float x, float y, float z)
{
    float m = min(x, y);
    return min(m, z);
}

hsv_t rgb_to_hsv(rgb_t rgb)
{
    float rp = rgb.R / 255.0f;
    float gp = rgb.G / 255.0f;
    float bp = rgb.B / 255.0f;

    float cmax = max3(rp, gp, bp);
    float cmin = min3(rp, gp, bp);

    float delta = cmax - cmin;

    hsv_t hsv;
    if (delta == 0.0f)
    {
        hsv.s = 0;
        hsv.h = 0;
    }
    else if (cmax == rp)
    {
        hsv.h = 60 * (lroundf(((gp - bp) / delta)) % 6);
    }
    else if (cmax == gp)
    {
        hsv.s = lroundf(100 * delta / cmax);
        hsv.h = 60 * ((bp - rp) / delta + 2);
    }
    else
    {
        hsv.s = lroundf(100 * delta / cmax);
        hsv.h = 60 * ((rp - gp) / delta + 4);
    }

    hsv.v = lroundf(100 * cmax);
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
