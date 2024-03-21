Robot configuration
===================

Logging
-------

You may not be interested to read all log messages. You can configure the logging framework in the
`user/data/config/log_config.json` file.

The default configuration is:

```json
{
    "modules": {}, // Specify a per-tag minimum log level. If a tag is missing, it defaults to `min_log_level`
    "min_log_level": 0, // Messages below this level will not be printed. Default: Level.DEBUG
    "default_log_level": 1, // Default message level if not specified. Default: Level.INFO
}
```

If you want to specify a tag-specific filter, you need to add an entry with the complete tag:

```json
{
    "modules": {
        "[Motor][Port]": 2,
        "[Motor][Port][1]": 5,
        "[McuUpdater]": 3,
    },
    "min_log_level": 0,
    "default_log_level": 1,
}
```

Numeric log levels:

- `0`: `DEBUG`
- `1`: `INFO`
- `2`: `WARNING`
- `3`: `ERROR`
- `4`: `OFF` - log message will not be displayed

Sound, volume
-------------

You can set the default volume in the `user/data/config/sound.json` file.

The default configuration is:

```json
{
    "default_volume": 90 // in %
}
```
