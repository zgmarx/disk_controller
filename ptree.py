#!/usr/bin/python
# encoding=utf-8

'''
ptree tool utility
'''

import re
import json
import collections


class Node(object):
    def __init__(self, name, parent=None):
        self.name = name
        self.children = []
        self.propety = {}
        self.parent = parent

    def __str__(self):
        r = collections.defaultdict()
        r[self.name] = {}
        for k, v in self.propety.items():
            r[self.name][k] = v
        return json.dumps(r)

    def __repr__(self):
        pass


class rulesTree(object):
    def __init__(
            self, rules, rule_tree_root_name='rules',
            data_tree_root_name='data'):
        self.rule_tree_root = Node(rule_tree_root_name)
        self.rules = rules
        self.build_rules_tree(self.rule_tree_root, self.rules)
        self.data_tree_root = Node(data_tree_root_name)

    def class_dict_keys_by_value(self, dic):
        keys_str = [k for k in dic.keys() if isinstance(dic[k], str)]
        keys_dict = [k for k in dic.keys() if isinstance(dic[k], dict)]
        return keys_dict, keys_str

    def build_rules_tree(self, parent, rules):
        for k in rules.keys():
            if isinstance(rules[k], str):
                parent.propety[k] = rules[k]
            else:
                node = Node(k, parent)
                node.parent.children.append(node)
                self.build_rules_tree(node, rules[k])

    def scan_rule_node(self, line, node, data_node):
        cur_data_node = data_node
        for n in node.children:
            if re.match(n.name, line):
                return n, cur_data_node
        _node = node
        while _node.parent:
            cur_data_node = cur_data_node.parent
            if re.match(_node.name, line):
                return _node, cur_data_node
            _node = _node.parent
        return None, cur_data_node

    def build_data_tree(self, f):
        return self.__build_data_tree(
            f, self.rule_tree_root, self.data_tree_root)

    def __build_data_tree(self, f, rule_tree_root, parent_data_root):
        find = False
        cur_rule_node = rule_tree_root
        cur_parent_data_node = parent_data_root
        p_list = cur_rule_node.propety.keys()
        cur_data_node = parent_data_root
        for i in f:
            i = i.strip()
            i = ' '.join(i.split())
            if find is False:
                if len(rule_tree_root.children) == 0:
                    find = True
                else:
                    r, cur_parent_data_node = self.scan_rule_node(
                        i, cur_rule_node, cur_data_node)
                    if r:
                        find = True
                        cur_rule_node = r
                        p_list = cur_rule_node.propety.keys()
                        _match = re.match(r.name, i)
                        _data_node = Node(_match.group(1))
                        _data_node.parent = cur_parent_data_node
                        cur_parent_data_node.children.append(_data_node)
                        cur_data_node = _data_node

            if find is True:
                for pr, pk in cur_rule_node.propety.items():
                    if re.match(pr, i):
                        p_list.remove(pr)
                        cur_data_node.propety[pk] = re.match(pr, i).group(1)
            if not p_list:
                if len(cur_rule_node.children) > 0:
                    self.__build_data_tree(f, cur_rule_node, cur_data_node)
                    find = False
                else:
                    find = False
                    return

    def __convert_tree_dict(self, root):
        r = collections.defaultdict()
        r[root.name] = {}
        r[root.name].update(root.propety)
        for n in root.children:
            r[root.name].update(self.__convert_tree_dict(n))
        return r

    def convert_data_dict(self):
        return dict(self.__convert_tree_dict(self.data_tree_root))

    def convert_rule_dict(self):
        return dict(self.__convert_tree_dict(self.rule_tree_root))

    def __str__(self):
        return json.dumps(self.__convert_tree_dict(self.data_tree_root))
