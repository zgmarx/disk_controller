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
                r'^Name\s*:\s*(.*)$': 'Name',
                r'^Number Of Drives\s*(?:per span)?:\s*(\d+)$': 'Number Of Drives',
                r'^[Current]*\s*Access Policy\s*:\s*(.*)$': 'Access',
                r'^Current Cache Policy\s*:\s*(.*)$': 'Cache',  # RWBD
                r'^State\s*:\s*(.*)$': 'State',  # Optimal
                r'^RAID Level\s*:\s*(.*)$': 'TYPE',  # RAID1 / RAID5
                r'^Size\s*:\s*(.*)$': 'Size',

                r'(Span: \d+)': {
                    r'(PD:\s*\d+) Information.*$': {
                        r'^Enclosure Device ID:\s*(.*)$': 'EnclosureID',
                        r'^Slot Number:\s*(.*)$': 'SlotID',
                        r'^Device Id:\s*(.*)$': 'DID',

                        r'^Media Error Count:\s*(.*)$': 'Media Error Count',
                        r'^Other Error Count:\s*(.*)$': 'Other Error Count',
                        r'^Predictive Failure Count:\s*(.*)$': 'Predictive Failure Count',

                        r'^Drive Temperature :\s*(.*)$': 'Drive Temperature',
                        r'^Firmware state:\s*(.*)\s*$': 'State',
                        r'^Foreign State:\s*(.*)$': 'Foreign State',
                        r'^Media Type:\s*(.*)$': 'Med',  # HDD / Hard Disk Device
                        r'^PD Type:\s*(.*)$': 'Intf',    # SAS
                        r'^Inquiry Data:\s*(.*)\s*$': 'Model',
                        r'^Coerced Size:\s*(\d+).*$': 'Size',
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

    for adapter in adp['adapter'].keys():
        for key, value in adp['adapter'][adapter].items():
            rst[adapter][key] = value
        for key, value in ld_pd['lds'][adapter].items():
            rst[adapter][key] = value

    return dict(rst)


def mega_info():

    try:
        adp = get_common_dict('adapter')
        lds = get_common_dict('lds')
        _info = _mega_info(adp, lds)
        return _info
    except Exception as ex:
        raise ex


def get_pd_detail_storcli_format():
    _data = mega_info()
    _data = _turn_megacli_output_storcli(_data)
    return _get_megacli_pds(_data)


def get_vdpd_storcli_format():
    data = mega_info()
    return _turn_megacli_output_storcli(data)


def _get_megacli_pds(data):

    key_list = [
        "Drive Temperature",
        "Media Error Count",
        "Other Error Count",
        "Predictive Failure Count",
    ]
    _return = {}
    adapter_count = 0
    for adapter in data:
        for _pd in adapter["PD LIST"]:
            key = "Drive /c{CID}/e{EID}/s{SID} State".format(
                CID=adapter_count,
                EID=_pd["EnclosureID"],
                SID=_pd["SlotID"],

            )
            for _k in key_list:
                if key not in _return:
                    _return[key] = {}
                _return[key][_k] = _pd[_k]
        adapter_count += 1

    return _return


def _turn_megacli_output_storcli(data):

    _return = []

    for _, vds in data.items():

        pd_list = []
        vd_list = []
        for k, vd in vds.items():
            if 'Virtual' not in k:
                continue
            tmp = {}

            for kk, pds in vd.items():
                if 'Span:' in kk:
                    for __, pd in pds.items():
                        pd_list.append(pd)

            for kk in vd:
                if 'Span' in kk:
                    continue
                tmp[kk] = vd[kk]
                _vd = k.split(':')[1].strip()
                tmp['DG/VD'] = "{0}/{1}".format(_vd, _vd)

            vd_list.append(tmp)

        _return.append(
            {
                'PD LIST': pd_list,
                'VD LIST': vd_list,
                'Physical Drives': len(pd_list),
                'Virtual Drives': len(vd_list),
            }
        )

    return _return


if __name__ == '__main__':
    try:
        print json.dumps(mega_info(), default=repr, indent=4, sort_keys=True)
    except Exception as ex:
        print ex
        import sys
        sys.exit(1)
