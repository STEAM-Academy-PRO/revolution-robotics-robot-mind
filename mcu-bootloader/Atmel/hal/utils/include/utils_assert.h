#ifndef _ASSERT_H_INCLUDED
#define _ASSERT_H_INCLUDED

#ifdef __cplusplus
extern "C" {
#endif

#include <compiler.h>

#ifdef DEBUG

extern void assert_failed(const char *file, uint32_t line);
#define ASSERT(condition)                               \
    if (!(condition))                                   \
        assert_failed(__FILE__, __LINE__)

#else

#define ASSERT(condition) (void) (condition)

#endif

#ifdef __cplusplus
}
#endif
#endif /* _ASSERT_H_INCLUDED */
