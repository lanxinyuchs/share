#!/usr/bin/env drgn

from os import stat
import argparse
import sys

from drgn import container_of
from drgn.helpers.linux.list import list_for_each_entry, list_empty
from drgn.helpers.linux.mm import decode_page_flags
from drgn.helpers.linux.cgroup import cgroup_path, cgroup_name

memcg_array = {}
lru_value = {}
lru_name = {}
lru_name[0] = "inactive_anon"
lru_name[1] = "active_anon"
lru_name[2] = "inactive_file"
lru_name[3] = "active_file"
lru_name[4] = "unevictable"


def err(s):
    sys.exit(1)


def find_memcg_ids(css):
    if not list_empty(css.children.address_of_()):
        for css in list_for_each_entry('struct cgroup_subsys_state',
                                       css.children.address_of_(),
                                       'sibling'):
            memcg = container_of(css, 'struct mem_cgroup', 'css')
            memcg_array[css.cgroup.kn.id.value_()] = memcg
            find_memcg_ids(css)


def get_memory_stat_value(memcg):
    cgroup_full_path = "/sys/fs/cgroup" + cgroup_path(memcg.css.cgroup).decode('utf-8')
    cgroup_mem_stat_file = cgroup_full_path + '/' + "memory.stat"

    with open(cgroup_mem_stat_file, 'r') as file:
        for line in file:
            for i in range(5):
                if line.startswith(lru_name[i]):
                    lru_value[i] = line.split(" ")[1]


def calc_memory_usage(memcg):
    print("\nfor cgroup %s:\n" %(cgroup_name(memcg.css.cgroup).decode("utf-8")))

    memcg_total_lru_pages = 0
    for i in range(5):
        list_count = 0
        for page in list_for_each_entry("struct page", 
                                        memcg.nodeinfo[0].lruvec.lists[i].address_of_(), 
                                        "lru"):
            #print(decode_page_flags(page))
            list_count += 1
        print("%s has %u pages, %u bytes memory" %(lru_name[i], list_count, list_count * prog["PAGE_SIZE"]))
        print("memory.stat show %u bytes\n" %(int(lru_value[i])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cgroup_path')
    args = parser.parse_args()

    try:
        cgroup_id = stat(args.cgroup_path).st_ino
        find_memcg_ids(prog['root_mem_cgroup'].css)
        memcg = memcg_array[cgroup_id]
    except KeyError:
        err('Can\'t find the memory cgroup')

    get_memory_stat_value(memcg)
    calc_memory_usage(memcg)
    

main()
