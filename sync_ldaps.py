#!/usr/bin/env python

import sys, os
import ldap
from ldif3 import LDIFWriter
import ldap.modlist as modlist
import hashlib
from configparser import ConfigParser
import itertools

from optparse import OptionParser
from datetime import datetime

#def is_config_file_exist(filename):
#def get_all_ldap_users(ldap_info) :
#def get_ldap_user(ldap_mnfo, user_login) :
#def compare_dicts_in_order(dict1,dict2,verbose=False) :
#def compare_dicts_in_order(dict1,dict2,verbose=False) :
#def show_accounts_to_add(dict_source,dict_dest, counter=0) :
#def show_accounts_to_modify(dict_source,dict_dest, verbose=False, counter=0) :
#def LDAP_do_operation(ldap_info, dn, ldif, operation) :
#def sync_account(ldap_source, ldap_dest, hash_string, verbose=True) :
#def fix_all(accounts_to_fix, ldap_source, ldap_dest,verbose=False) :
#def print_info(data_dict, output_level=3) :
#def save_account(login, basedn, dict_login_info, backup_path="backup_accounts"):
#def delete_account(ldap_info, login, verbose=False) :

def is_config_file_exist(filename) :
    """
    Check if config file exists. Could be used for any file, but in our case we use it for config file
    Input : filename (with path)
    Output True if file exists, False if not.

    Attention! : filename should be a file, if it's directory will return False
    """
    if os.path.isfile(filename) :
        return True
    return False

def get_all_ldap_users(ldap_info) :
    """
    Get all ldap users from LDAP server indicated by ldap_info
    Return dict with all users (with all info about user from LDAP)
    If there is problem to connect to LDAP : stops with exit code 1

    Attention! The values in the dict are the strings (and not bytes-string as returned by python-ldap)
    This is the difference with "get_ldap_user" function that returns bytes-string.

    """
    url = ldap_info['url']
    basedn = ldap_info['basedn']
    searchFilter = ldap_info['filter']
    searchAttribute = []

    ldap_connect = ldap.initialize(url)
    searchScope = ldap.SCOPE_SUBTREE

    #Bind to the server
    try:
        ldap_connect.protocol_version = ldap.VERSION3
        ldap_connect.set_option(ldap.OPT_REFERRALS, 0)
        if ('pwd' in ldap_info) and ('bind' in ldap_info) :
            binddn = ldap_info['bind']
            ldap_connect.simple_bind_s(binddn, ldap_info['pwd'])
        else :
            ldap_connect.simple_bind()
    except ldap.INVALID_CREDENTIALS:
      print("Your username or password is incorrect.")
      sys.exit(1)
    except ldap.LDAPError as e:
        print(f"LDAP info : {ldap_info}")
        if type(e.args) == dict and e.args.has_key('desc'):
            print(e.args['desc'])
        else:
            print(e)
        sys.exit(1)
    #End of Bind

    try:
        ldap_result_id = ldap_connect.search(basedn, searchScope, searchFilter, searchAttribute)
        result_set = []

        cur_dict={}
        while 1:
            result_type, result_data = ldap_connect.result(ldap_result_id, 0)
            if (result_data == []):
                break
            else :
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)

        for account in result_set :
            if ('uid' in account[0][1]) :
                login = account[0][1]['uid'][0].decode('utf-8')
                if login in cur_dict :
                    print(f"Strange things, we already have user with same login: {account}")
                else :
                    cur_dict[login]={}
                    for key, item in account[0][1].items() :
                        if len(item) > 1 :
                            cur_dict[login][key]=[ cur_item.decode('utf-8') for cur_item in item ]
                        else :
                            cur_dict[login][key]=item[0].decode('utf-8')
    except ldap.LDAPError as e:
        print("Search problem")
        print(e)
    ldap_connect.unbind_s()

    return cur_dict

def get_ldap_user(ldap_info, user_login) :
    """
    Get info about user with uid = user_login from LDAP-server ldap_info
    Return dict with all info about user
    If there is problem to connect to LDAP : stops with exit code 1

    Attention! The values in the dict are the bytes-strings
    This is the difference with "get_all_ldap_users" function that returns normal string.
    """
    url = ldap_info['url']
    basedn = ldap_info['basedn']
    searchFilter = f"(uid={user_login})"
    searchAttribute = []

    ldap_connect = ldap.initialize(url)
    searchScope = ldap.SCOPE_SUBTREE

    #Bind to the server
    try:
        ldap_connect.protocol_version = ldap.VERSION3
        ldap_connect.set_option(ldap.OPT_REFERRALS, 0)
        if ('pwd' in ldap_info) and ('bind' in ldap_info) :
            binddn = ldap_info['bind']
            ldap_connect.simple_bind_s(binddn, ldap_info['pwd'])
        else :
            ldap_connect.simple_bind()
    except ldap.INVALID_CREDENTIALS:
      print("Your username or password is incorrect.")
      sys.exit(1)
    except ldap.LDAPError as e:
        if type(e.message) == dict and e.message.has_key('desc'):
            print(e.message['desc'])
        else:
            print(e)
        sys.exit(1)
    #End of Bind

    try:
        ldap_result_id = ldap_connect.search(basedn, searchScope, searchFilter, searchAttribute)
        result_set = []

        cur_dict={}
        while 1:
            result_type, result_data = ldap_connect.result(ldap_result_id, 0)
            if (result_data == []):
                break
            else :
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)

        for account in result_set :
            if ('uid' in account[0][1]) :
                login = account[0][1]['uid'][0].decode('utf-8')
                if login in cur_dict :
                    print(f"Strange things, we already have user with same login: {account}")
                else :
                    cur_dict[login]={}
                    for key, item in account[0][1].items() :
                        if len(item) > 1 :
                            cur_dict[login][key]=item
                        else :
                            cur_dict[login][key]=item[0]

        # print(result_set)

    except ldap.LDAPError as e:
        print("Search problem")
        print(e)
    ldap_connect.unbind_s()

    return cur_dict

def compare_dicts_in_order(dict1,dict2,verbose=False) :
    """
    Compare two dicts.
    Return tuple (diff, hash_string) :
        diff : human readable string about difference between two dicts
        hash_string : small hash that encode diff between two dicts.
        hash_string is not really encoded : it's just condesed form of changes.
        hash_string form is : <uid>_modify_attributes (that should be modified)
        This hash_string will be consumed by function that will do changes in LDAP.
        If two dicts are the same return (None, None)
    """
    diff=f"{dict1['uid']} is different in source and dest\n"
    hash_string=f"{dict1['uid']}_modify"
    flag_diff=False
    for key in dict1 :
        if key not in dict2 :
            diff+=f"\t {key} not exists in dest\n"
            hash_string+=f"_{key}"
            flag_diff=True
        elif dict1[key] != dict2[key] :
            if verbose :
                diff+=f"\t {key} : SOURCE={dict1[key]}, DEST={dict2[key]}\n"
            else :
                diff+=f"\t {key}"
            hash_string+=f"_{key}"
            flag_diff=True
    for key in dict2 :
        if key not in dict1 :
            diff+=f"\t {key} not exists in source\n"
            flag_diff=True

    if flag_diff :
        return (diff,hash_string)

    return (None, None)

def show_accounts_to_add(dict_source,dict_dest, counter=0) :
    # Accounts in Source but not in Dest
    """
    Take dict with all accounts in first LDAP (sou)
    Take dict with all accounts in second LDAP (dest)
    Return dict with all accounts in first LDAP that don't exist in the second LDAP
        key : hash in form <uid>_add
        value : dict with 3 keys (0, 1, 2) with increasing output information (0 - less verbose, 2 very verbose)
    """
    output_levels=list(range(3))
    res_accounts={}

    for login in set(dict_source.keys()).difference(set(dict_dest.keys())) :
        output_dict=dict.fromkeys(output_levels)
        counter+=1
        hash_string=f"{login}_add"
        hash_sum=hashlib.md5(hash_string.encode('utf-8')).hexdigest()
        output_dict[0] = f"{hash_sum}"
        output_dict[1] = f"User {login} does not exist in dest ldap"
        output_dict[2] = f"{dict_source[login]}"
        res_accounts[hash_string] = output_dict
    return (counter,res_accounts)

def show_accounts_to_modify(dict_source,dict_dest, verbose=False, counter=0) :
    output_levels=list(range(3))
    res_accounts={}

    for login in set(dict_source.keys()).intersection(set(dict_dest.keys())) :
        output_dict=dict.fromkeys(output_levels)
        diff_res, hash_string = compare_dicts_in_order(dict_source[login],dict_dest[login],verbose)
        if diff_res :
            counter+=1
            hash_sum=hashlib.md5(hash_string.encode('utf-8')).hexdigest()
            output_dict[0] = f"{hash_sum}"
            output_dict[1] = f"""{diff_res}"""
            output_dict[2] = f"""
                {dict_source[login]}
                {dict_dest[login]}
                """
            res_accounts[hash_string] = output_dict

    return (counter,res_accounts)

def LDAP_do_operation(ldap_info, dn, ldif, operation) :
    url = ldap_info['url']
    basedn = ldap_info['basedn']

    ldap_connect = ldap.initialize(url)

    #Bind to the server and modify
    try:
        ldap_connect.protocol_version = ldap.VERSION3
        ldap_connect.set_option(ldap.OPT_REFERRALS, 0)
        if ('pwd' in ldap_info) and ('bind' in ldap_info) :
            binddn = ldap_info['bind']
            ldap_connect.simple_bind_s(binddn, ldap_info['pwd'])
        else :
            ldap_connect.simple_bind()

        if operation == 'add' :
            ldap_connect.add_s(dn,ldif)
        elif operation == 'modify' :
            ldap_connect.modify_s(dn,ldif)
        else :
            print(f"Unknown operation in LDAP_do_operation : {operation}")
            return 1
    except ldap.INVALID_CREDENTIALS:
      print("Your username or password is incorrect.")
      sys.exit(1)
    except ldap.LDAPError as e:
        print("LDAP Exception. Here some info")
        print(dn)
        print(ldif)
        print("Error info:")
        print(e)
        ldap_connect.unbind_s()
        sys.exit(1)
    #End of Bind & modify

    # Its nice to the server to disconnect and free resources when done
    ldap_connect.unbind_s()

    return 0

def sync_account(ldap_source, ldap_dest, hash_string, verbose=True) :
    """
    Modify account. Get account name and needed changes from hash
    Return 0 if account was seccessfully modifed
    Return 1 (>0) if could not modify
    """

    changes_info = hash_string.split("_")
    user = changes_info[0]
    operation = changes_info[1]

    user_in_source = get_ldap_user(ldap_source,user)
    if not user_in_source :
        if verbose :
            print(f"No such user in source-ldap : {user} (hash = {hash_string})")
        return 1
    user_in_dest = get_ldap_user(ldap_dest,user)

    if operation == 'add' :
        if user_in_dest :
            if verbose :
                print(f"Operation is add for user {user} (hash = {hash_string}), but he is already exist in dest-ldap")
            return 1
        attrs={}
        for key, value in user_in_source[user].items() :
            attrs[key] = value
        cur_ldif = modlist.addModlist(attrs)
        dn = f"uid={user},{ldap_dest['basedn']}"
        status = LDAP_do_operation(ldap_dest,dn,cur_ldif,operation)

    elif operation == 'modify' :
        user_in_dest = get_ldap_user(ldap_dest,user)
        if not user_in_dest :
            if verbose :
                print(f"No such user in dest-ldap: {user} (hash = {hash_string})")
                print(f'If you want to add user, use "add" operation')
            return 1

        old={}
        new={}
        for field_to_change in changes_info[2:] :
            if user_in_source[user][field_to_change] != user_in_dest[user][field_to_change] :
                old[field_to_change]=[user_in_dest[user][field_to_change]]
                new[field_to_change]=[user_in_source[user][field_to_change]]
            elif verbose :
                print(f"This field {field_to_change} is already identic in dest and source")

        if new :
            cur_ldif = modlist.modifyModlist(old,new)
            dn = f"uid={user},{ldap_dest['basedn']}"
            status = LDAP_do_operation(ldap_dest,dn,cur_ldif,operation)
        else :
            status = 1
    else :
        print(f"Unknown operation in sync_account function : {operation} (hash_string={hash_string})")
        return 1

    return status

def fix_all(accounts_to_fix, ldap_source, ldap_dest,verbose=False) :
    counter=0
    for cur_hash in accounts_to_fix :
        if verbose :
            print(f"Doing {cur_hash}")
        res = sync_account(ldap_source,ldap_dest,cur_hash)
        if res > 0 :
            print(f"For some reason operation {cur_hash} was not succesful.")
        else :
            counter+=1

    return counter

def print_info(data_dict, output_level=3) :
    if (output_level == 0) or ( not data_dict ) :
        return 0

    # In fact, level 3 and 4 are the same. It changed not here but with verbose flag in compare functions
    limit_level=output_level - 2
    if output_level == 4 :
        limit_level = 1
    elif output_level == 5 :
        limit_level = 2

    for key, value in data_dict.items() :
        print(key)
        cur_level=0
        while cur_level <= limit_level :
            print(f"{value[cur_level]}")
            cur_level+=1
        if output_level > 1:
            print("_______________________________")

    return 0

def save_account(login, basedn, dict_login_info, backup_path="backup_accounts"):
    prepared_dict = {}
    for k, v in dict_login_info.items() :
        if type(v) is list :
            prepared_dict[k]=v
        else :
            prepared_dict[k]=[v]

    with open(f"{backup_path}/{login}.ldif", "wb") as file_backup :
        w = LDIFWriter(file_backup)
        w.unparse(f"uid={login},{basedn}",prepared_dict)

    return 0

def delete_account(ldap_info, login, verbose=False) :
    url = ldap_info['url']
    basedn = ldap_info['basedn']

    ldap_connect = ldap.initialize(url)
    #Bind to the server and modify
    try:
        ldap_connect.protocol_version = ldap.VERSION3
        ldap_connect.set_option(ldap.OPT_REFERRALS, 0)
        if ('pwd' in ldap_info) and ('bind' in ldap_info) :
            binddn = ldap_info['bind']
            ldap_connect.simple_bind_s(binddn, ldap_info['pwd'])
        else :
            ldap_connect.simple_bind()

        ldap_connect.delete(f"uid={login},{basedn}")
        if verbose and ldap_connect.result :
            print(f"Account {login} was successfully deleted from {url}")
        return ldap_connect.result

    except ldap.INVALID_CREDENTIALS:
      print("Your username or password is incorrect.")
      sys.exit(1)
    except ldap.LDAPError as e:
        print("LDAP Exception. Here some info")
        print(ldap_info)
        print("Error info:")
        print(e)
        ldap_connect.unbind_s()
        sys.exit(1)
    #End of Bind & modify


#_______________________________________________________________________________
#_______________________________________________________________________________
#_______________________________________________________________________________
#_______________________________________________________________________________

# BLOCK : Get date-time
# datetime object containing current date and time
now = datetime.now()
# dd/mm/YY H:M:S
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
# END BLOCK : Get date-time

# BLOCK: Parsing command line options
parser = OptionParser(usage="usage: %prog [options] ",
                          version="%prog 0.2")
parser.add_option("-v", "--verbose-level",
                  type='int',
                  action="store",
                  dest="show_type",
                  default=3,
                  help=("""\
                  Level of output details. 5 levels :
                  All options : full (5), detailed (4), small (3,default), hash_sum (2), hash_string (1), none (0)
                  Levels are comulative : level N show itselfs and all smallers
                  """),
                 )
parser.add_option("-q", "--quiet",
                  action="store_true", # optional because action defaults to "store"
                  dest="quiet",
                  help="Quiet (no output) (the same as -v 0). This option overwrite --show (set it to none)",)

parser.add_option("-r", "--removed-accounts",
                  action="store_true", # optional because action defaults to "store"
                  dest="removed",
                  help="Search only for accounts that existent in dest but not in source",)
parser.add_option("--prepare-ldif-for-removed",
                  action="store_true", # optional because action defaults to "store"
                  dest="removed_ldif",
                  help="Prepare ldif for accounts to remove, works only together with '-r' option",)
parser.add_option("--backup_all_before_remove",
                  action="store_true", # optional because action defaults to "store"
                  dest="backup_removed",
                  help="Backup all accounts info before remove '-r' option",)
parser.add_option("--confirm_remove_all",
                  action="store_true", # optional because action defaults to "store"
                  dest="confirm_remove_all",
                  help="Remove all account that exist in dest but not in source, works only with '-r' option",)

parser.add_option("-f", "--fix",
                  action="store_true", # optional because action defaults to "store"
                  dest="fix",
                  help="Fix account (copy from source to dest). --hash-string=hash should be provided",)

parser.add_option("--hash-string",
                  action="store", # optional because action defaults to "store"
                  dest="hash",
                  help="Search only for accounts that existent in dest but not in source",)

parser.add_option("--fix-all",
                  action="store_true", # optional because action defaults to "store"
                  dest="fix_all",
                  default=False,
                  help="Will fix all changes (add and modify)",)
parser.add_option("-c", "--config",
                  action="store", # optional because action defaults to "store"
                  dest="config_file",
                  help="Config file, if not set use sync_ldaps.conf in current directory",)

(options, args) = parser.parse_args()
# END BLOCK: Parsing command line options

# BLOCK: Read config
curConf = ConfigParser()
if options.config_file:
    config_filename = options.config_file
    if not is_config_file_exist(config_filename) :
        print(f"You provide filename for config file ({config_filename}), but it does not exist")
        sys.exit(2)
else :
    cur_dir_path = os.path.dirname(os.path.realpath(__file__))
    config_filename = os.path.join(cur_dir_path,"sync_ldaps.conf")
    if not is_config_file_exist(config_filename) :
        print(f"You do not provide config file name and default config file <cur_dir>/sync_ldaps.conf does not exist.")
        print(f"Config file is mandatory. Either create a default config file <cur_dir>/sync_ldaps.conf or provide filename (with path) using -c/--config option.")
        sys.exit(2)

curConf.read(config_filename)
# END BLOCK: Read config

# BLOCK : Read LDAPs conf from config file
all_ldaps={'source_section_name':'LDAP Source', 'dest_section_name':'LDAP Dest'}
if not all_ldaps['source_section_name'] in curConf.sections() :
    print(f"No section '{all_ldaps['source_section_name']}' in config file {config_filename}")
    sys.exit(3)
if not all_ldaps['dest_section_name'] in curConf.sections() :
    print(f"No section '{all_ldaps['dest_section_name']}' in config file {config_filename}")
    sys.exit(4)

ldap_attrs = ['bind', 'pwd', 'basedn', 'filter']

if not 'url' in curConf[all_ldaps['source_section_name']] :
    print(f"url is not provided for LDAP Source")
    sys.exit(5)
if not 'url' in curConf[all_ldaps['dest_section_name']] :
    print(f"url is not provided for LDAP Dest")
    sys.exit(6)

for conf_item in itertools.product(all_ldaps.values(),ldap_attrs) :
    if not conf_item[1] in curConf[conf_item[0]] :
        if conf_item[1] in curConf["DEFAULT"] :
            curConf[conf_item[0]][conf_item[1]] = curConf["DEFAULT"][conf_item[1]]
        else :
            print(f"Option {conf_item[1]} is not set for {conf_item[0]} and no default value provided.")
            sys.exit(7)

ldap_source = {}
for key, value in curConf[all_ldaps['source_section_name']].items() :
    ldap_source[key] = value

ldap_dest = {}
for key, value in curConf[all_ldaps['dest_section_name']].items() :
    ldap_dest[key] = value
# END BLOCK : Read LDAPs conf from config file


if options.quiet :
    options.show_type=0
else :
    print("Current date and time =", dt_string)

dict_source = get_all_ldap_users(ldap_source)
dict_dest = get_all_ldap_users(ldap_dest)

counter=0
compare_verbose = False
if options.show_type > 3 :
    compare_verbose = True

# Search for accounts in Dest but not in Source
# and then exit returning the number of account of such type
if options.removed :
    if options.removed_ldif :
        file1 = open("uid_to_remove.ldif", "w")

    for login in set(dict_dest.keys()).difference(set(dict_source.keys())) :
        counter+=1
        if compare_verbose :
            print(f"{counter} : User {login} exists in Dest ldap but not in Source")
        if options.removed_ldif :
            new_line="\n"
            file1.write(f"uid={login},{ldap_dest['basedn']}{new_line}")
        if options.backup_removed :
            save_account(login, ldap_dest['basedn'], dict_dest[login])

        if options.confirm_remove_all :
            delete_account(ldap_dest, login, verbose=compare_verbose)

        if compare_verbose :
            print("_______________________________________")


    if options.removed_ldif :
        file1.close()

    quit(0)

if options.fix_all :
    print("Fixing all changes")
    counter, accounts_to_add = show_accounts_to_add(dict_source,dict_dest, counter)
    res = fix_all(accounts_to_add, ldap_source, ldap_dest,compare_verbose)
    print(f"Added {res} accounts")
    counter, accounts_to_modify = show_accounts_to_modify(dict_source,dict_dest, compare_verbose, counter)
    res = fix_all(accounts_to_modify, ldap_source, ldap_dest,compare_verbose)
    print(f"Changed {res} accounts")
elif options.fix and options.hash :
    res = sync_account(ldap_source,ldap_dest,options.hash)
    print(f"Changed : {options.hash}")
else :
    counter, accounts_to_add = show_accounts_to_add(dict_source,dict_dest)
    if compare_verbose :
        print(f"Number of accounts to add: {counter}")
    print_info(accounts_to_add,options.show_type)
    counter, accounts_to_modify = show_accounts_to_modify(dict_source,dict_dest, compare_verbose)
    if compare_verbose :
        print(f"Number of accounts to modify: {counter}")    
    print_info(accounts_to_modify,options.show_type)
quit(0)
