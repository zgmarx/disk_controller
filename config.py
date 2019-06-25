#!/usr/bin/python
# encoding=utf-8

"""
put all user config here
"""

GOOD_PD = [
    'Online, Spun Up',  # for megacli
    'Onln',             # for storcli
    'Ready (RDY)',      # for SAS
    'Optimal (OPT)',    # for SAS
]

GOOD_VD = [
    "Optimal",     # for megacli
    "Optl",        # for storcli
    "Okay (OKY)",  # for SAS
]

CHECK_LIST = [
    ("Media Error Count", 1000),
    ("Other Error Count", 1000),
    ("Predictive Failure Count", 1000),
]
