disk_controller
===========

this tool help to unify different disk controller output to `storcli` format.

Usage
-----

this tool include three basic scripts: `sas.py`, `megacli.py`, `storcli.py`,
which turn disk controller tool(`sas3ircu`, `MegaCli64`, `storcli64`) output into storecli output like format.

`disk_utility.py` is an example tells you how to use the 3 basic scripts.

by running `disk_utility.py` you will get this if there's no error:

```
pd_not_ok []
vd_not_ok []
pd_errors {}  # SAS controller doest have this line in output.
```

if there's error output will like this (megacli).

```
pd_not_ok [
    {
        "DID": "13",
        "Drive Temperature": "53C (127.40 F)",
        "EnclosureID": "32",
        "Foreign State": "None",
        "Intf": "SAS",
        "Med": "Hard Disk Device",
        "Media Error Count": "0",
        "Model": "SEAGATE xxx xxx",  # I've replace model and SN with xxx.
        "Other Error Count": "3",
        "Predictive Failure Count": "0",
        "Size": "278",
        "SlotID": "13",
        "State": "Failed"
    }
]
vd_not_ok [
    {
        "Access": "Read/Write",
        "Cache": "WriteThrough, ReadAheadNone, Direct, No Write Cache if Bad BBU",
        "DG/VD": "0/0",
        "Name": "",
        "Number Of Drives": "2",
        "Size": "278.875 GB",
        "State": "Degraded",
        "TYPE": "Primary-1, Secondary-0, RAID Level Qualifier-0"
    }
]
pd_errors {
    "Drive /c0/e32/s9 State": {
        "Media Error Count": 53751
    }
}
```

if there's error output will like this (storecli).

```
pd_not_ok [
    {
        "DG": "-",
        "DID": 16,
        "EID:Slt": "252:2",
        "Intf": "SAS",
        "Med": "HDD",
        "Model": "HUC101860CSS200 ",
        "PI": "N",
        "SED": "N",
        "SeSz": "512B",
        "Size": "558.406 GB",
        "Sp": "D",
        "State": "UGood",
        "Type": "-"
    }
]
vd_not_ok [
    {
        "Access": "RW",
        "Cac": "-",
        "Cache": "RWBD",
        "Consist": "Yes",
        "DG/VD": "0/0",
        "Name": "",
        "Size": "558.406 GB",
        "State": "Xxx",  # havn't met an error vd, don't know what it will be.
        "TYPE": "RAID1",
        "sCC": "ON"
    }
]
pd_errors {
    "Drive /c0/e252/s5 State": {
        "Drive Temperature": " 33C (91.40 F)",
        "Media Error Count": 1888,
        "Other Error Count": 2999,
        "Predictive Failure Count": 1001,
        "S.M.A.R.T alert flagged by drive": "No",
        "Shield Counter": 0
    }
}
```

you could create your own definition of error in `config.py`.
