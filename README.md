# Sync LDAPS

This is small script that sync two LDAP servers.

## Preface

At some moment I had two LDAP servers : the old and the new one. \
As I had a lot of scripts, procedures and services that were based on old LDAP server 
I decided to maintain the old and the new server for some time.

And, as all of procedures were based on old ldap server, I decided to create a small script 
that sync old LDAP with new one.

This script was developed without planing or even specifications. 
The features and how to proceed etc were developed during script creation. 
So script is a little bit fuzzy. 
Still I found that it could be useful for some peoples, 
so I made it a little bit general and publish it here.

Please use it on your **OWN RISK**!

Normally, this script will **NEVER** change Source-ldap. But be careful (backup often).

## Install

I put requirement file. It should do the work (not sure for 100% as I use system-wide python install for this project).

The script need a config file.

a) it could be set using **-c** (**--config**) command-line option (ex.: `./sync_ldaps.py -c /home/user/script/my_conf.conf`)  
b) if **-c** option is not set, script try to use default config file : _<current script directory>/sync_ldaps.conf_

If no config file found script exit with error and return code 2.

## Config file

Config file follow configparser python syntax (https://docs.python.org/3/library/configparser.html)

Two sections are mandatory : **LDAP Source** and **LDAP Dest** (be careful, for configparser section names are case-sensitives, but the values are not).

En each section value **url** should be defined.

Script also need following parameters : **bind**, **pwd**, **basedn**, **filter**  
These attributes could be defined in **LDAP Source** and **LDAP Dest** sections or in global section **DEFAULT**.  
**DEFAUL** section could be useful if you have similar LDAP structure, so **basedn** or other attributes could be the same.  
If parameter is defined in **LDAP Source** or **LDAP Dest** we take the values there (respectively), if not we try to get value from **DEFAULT**.  
If any of these values is not defined script exits with code 7.

## Options and how it works

The script has two directions : 
* <ins>default</ins> : it shows/sync Source ldap to Dest ldap
* <ins>reverse</ins> : it shows/sync accounts that are present in Dest, but not in Source

If script is launched without any option, it will just show current date and accounts that are different between Source and Dest. 
```shell
$ ./sync_ldaps.py 
Current date and time = 21/06/2021 17:34:21
user1_modify_userPassword
7aa4fe23c80a7aafb2c2fc49ce1188a9
user1 is different in source and dest
         userPassword
_______________________________
user2_modify_mail
83cf2701ff1f5a316202d49c05255485
user2 is different in source and dest
         mail
s_______________________________`
```

For each difference it shows : 
- \<human-readable hash of difference\>
- \<md5 hash sum of difference\>
- \<long description of difference with list of attributes that are different\>

md5-sum is not really useful. There was a small idea to use such hash to identify the differences.   
Finally I abandon this idea, but  md5-sum for is still here the moment.   
May be somebody find how to use it. Or may be I will remove it in the future.

\<human-readable hash of difference\> is the real way how we identify the differences.  
The format is very simple :  
\<account\>\_\<modify|add\>\_\<list of attrs separated by \_\>

**add** : signify that this account exists in Source, but not in Dest  
**modify** : signify that for this account attrs, presented in the list, are different in Source and Dest

### Here the options for default sync (from Source to Dest)

| Short | Long | Description |
| --- | --- | --- |
-f | -fix | flag indicate that we want really *fix/sync*, not just show
 &nbsp; | --hash-string <human readable hash> | indicate that account should be fixed
 &nbsp; | --fix-all | fix all accounts different between Source and Dest

### Options for reverse direction (accounts from Dest not existing in Source)

| Short | Long | Description |
| --- | --- | --- |
-r | --removed-accounts | activate "reverse" mode, show removed accounts in Source 
 &nbsp; | --prepare-ldif-for-removed | work only together with "-r", prepare ldif file with remove accounts. This ldif could be used with ldapdelete command
 &nbsp; | --backup_all_before_remove | work only together with "-r", backup account before delete it
 &nbsp; | --confirm_remove_all | work only together with "-r", remove all acounts that not exists in Source

### Options for groups sync

**NB** _groups_basedn_ should be set in config file to use in order to Sync Group could work. 

| Short | Long | Description |
| --- | --- | --- |
-g | --groups | activate "groups" mode, show difference between the groups in Source and Dest 
 &nbsp; | --not_remove_new_members | work only together with "-g", disable searching for the groups where are more members in Dest than in Source
 &nbsp; | --fix-groups | activate fixing groups differences, if not activated we just simple show differences and exit

#### Some words about "not_remove_new_members".  
By default we will check (and try to fix if --fix-groups is set) all the differences.  
But sometimes there are some situations where in new ldap (Dest) there are more members than in the old one (Source). 
If we don't want that such difference will be fixed we should set --not_remove_new_members. So these differences will 
not be detected and so will not be fixed. 
 
### General options
 
 | Short | Long | Description |
| --- | --- | --- |
-c | --config | which config-file to use (default <cur_dir>/sync_ldaps.conf) 
-v <level number> | --verbose-level <level number> | verbose level
-q | --quiet | quiet mode, the same as _-v 0_
 
 Verbose levels :
 - 0 : none (same as -q) : print almost nothing
 - 1 : hash_string : for each diffenet account print only human readable hash string
 - 2 : hash_sum : print hash_string and hash_sum
 - 3 : small (_default_) : same output as showed before in this doc
 - 4 : detailed : almost as 3, but show some technical information
 - 5 : full : print all information provided by script
 
## Some usage examples

Launch script via crontabs all week days at 09:00 to sync Source and Dest  
And  each monday at 10:00 to remove accounts that were removed from Source.
```shell script
00 09 * * 1-5 /usr/bin/python /root/scripts/sync_ldaps.py -v 4 --fix-all >> ~/scripts/logs/sync_ldaps.log
00 10 * * 1   /usr/bin/python /root/scripts/sync_ldaps.py -r --backup_all_before_remove --confirm_remove_all -v4 >> ~/scripts/logs/removed.log
```
 
## Future and developement

For the moment I plan to maintain (and may be even develop) this script for some moment, 
but not sure about long-term future.  
So if you want some features the best way is to fork and change it to suite your needs.  
Nevertheless bugs and requests are welcome.
 