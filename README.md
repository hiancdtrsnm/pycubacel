# PyCubacel

You should include your own configuration file. `username` must have your cell phone number without any country code or plus sign. `password` must be the one you use on cubacel dashboard

**config.json or micubacel_config.json**

```json
{
    "login": {
        "language": "en_US",
        "username": "123456789",
        "password": "qwerty",
        "uword": "-",
        "": "on"
    },
    "data_path": "~/.internethistory.json",
    "cookies_path": "~/.cookie.json"
}
```

By default the files `config.json` or `micubacel_config.json` are search in the current working directory and are searh in the home too, but a full path can be sepecified.
