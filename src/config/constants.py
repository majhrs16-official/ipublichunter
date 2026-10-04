IFA_ADDRESS   = 1
NLMSG_DONE    = 3
RTA_OIF       = 4
RTA_GATEWAY   = 5
RTM_NEWADDR   = 20
RTM_GETADDR   = 22
RTM_NEWROUTE  = 24
RTM_GETROUTE  = 26
NLM_F_REQUEST = 0x1
NLM_F_ROOT    = 0x100
NLM_F_MATCH   = 0x200

CONFIG = b"""\
\r[%s]\
\r\t %s\
\r\t\t%i.%i.%i.%i\
\n"""

FARM   = b"""\
\r[%s]\
\r\t %s\
\r\t\t%i.%i.%i.%i\
\r\t\t\t\t%i\
\r\t\t\t\t\t%i\
\n"""
