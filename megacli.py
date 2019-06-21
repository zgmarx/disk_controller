#!/usr/bin/python
# encoding=utf-8

'''
1. install MegaCli or megacli
2. install glibc.i686
3. run as root
'''

import os
import json
import commands
import collections
import ptree


PWD = os.path.dirname(os.path.abspath(__file__))

MEGACLICMD = "/opt/MegaRAID/MegaCli/MegaCli64"
TMP_FILE = os.path.join(PWD, 'mega_info.tmp')

CMDS = {
    "adapter": " -AdpAllInfo -aAll -NoLog",
    "lds": " -LdPdInfo -aAll -NoLog",
}

INFO_STRUCTURE = {
    "adapter": {
        r"^(Adapter\s*#\d+)$": {
            r"^Product Name\s*:\s*(.*)$": "product"
            }
        },
    "lds": {
        r"^(Adapter\s*#\d+)$": {
            r"(^Virtual Drive:\s*\d+)": {
                r'Number Of Drives\s*(?:per span)?:\s*(\d+)$': 'disks_span',
                r'Span Depth *:\s*(\d+)$': 'span_num',
                r'^RAID Level\s*:\s*(.*)$': 'raid_level',
                r'^Size\s*:\s*(.*)$': 'size',
                r'(Span: \d+)': {
                    r'(PD:\s*\d+) Information.*$': {
                        r'Firmware state:\s*(.*)\s*$': 'state',
                        r'Inquiry Data:\s*(.*)\s*$': 'model',
                        r'Coerced Size:\s*(\d+).*$': 'size'
                    }
                }
            }
        }
    }
}


def store_out_to_file(cmd, filename):

    _response, _out = commands.getstatusoutput(cmd)
    if _response != 0:
        return False

    try:
        with open(filename, 'w') as _f:
            _f.write(_out)
    except Exception as ex:
        raise ex

    return True


def get_common_dict(rule_name):

    cmd = MEGACLICMD + CMDS[rule_name]
    _return = store_out_to_file(cmd, TMP_FILE)
    if not _return:
        print "call cmd fail: %s" % cmd
        return None

    rule_def = INFO_STRUCTURE[rule_name]
    _t = ptree.rulesTree(
        rule_def,
        data_tree_root_name=rule_name
    )
    with open(TMP_FILE) as tmpfd:
        _t.build_data_tree(tmpfd)
    os.remove(TMP_FILE)

    return _t.convert_data_dict()


def _mega_info(adp, ld_pd):

    rst = collections.defaultdict(dict)

    for adpt in adp['adapter'].keys():
        for key, value in adp['adapter'][adpt].items():
            rst[adpt][key] = value
        for key, value in ld_pd['lds'][adpt].items():
            rst[adpt][key] = value

    return dict(rst)


def mega_info():

    try:
        adp = get_common_dict('adapter')
        lds = get_common_dict('lds')
        _info = _mega_info(adp, lds)
        return _info
    except Exception as ex:
        raise ex


if __name__ == '__main__':
    try:
        print json.dumps(mega_info(), default=repr, indent=4, sort_keys=True)
    except Exception as ex:
        print ex
        import sys
        sys.exit(1)
