from pyftpdlib.authorizers import *
from pyftpdlib.handlers import *
from pyftpdlib.filesystems import *
from pyftpdlib.ioloop import *
from pyftpdlib.servers import *
import os

class FTP_SERVER(DummyAuthorizer, UnixAuthorizer, FTPServer, FTPHandler, DTPHandler):

    __dummy_authorizer = DummyAuthorizer()
    __unix_authorizer = UnixAuthorizer(rejected_users=["root"])

    __ftp_handler = FTPHandler
    __DTP_handler = DTPHandler
    __throttledDTP_handler = ThrottledDTPHandler
    __TLS_FTP_handler = TLS_FTPHandler
    # __TLS_DTP_handler = TLS_DTPHandler

    address = "0.0.0.0"
    port=2121
    bIsAnonymus = False
    shandlerType = "FTP"
    sAuthorizer = "Unix"
    sServerType = "Threaded"

    def __init__(self, sAddress="0.0.0.0", sPort="21", sType="Threaded"):
        #Default start up
        self.SetHandler(self.shandlerType)
        self.SetAuthorizer(self.sAuthorizer)
        self.IsAnonymousMode(False)
        self.SetBanner("ftpd service ready!")
        self.port=sPort
        self.address=sAddress
        self.SetServer(sType)
        self.SetMaxConnections(256)
        self.SetMaxConnectionsPerIp(5)
        self.LogLevel = "INFO"
        self.LogFilePath = os.getcwd()+"/"
        self.SetLogFile(self.LogFilePath+"pyftpd.log", self.LogLevel)

    def GetLogFilePath(self):
        return self.LogFilePath

    def SetHandler(self, sHandler):
        if sHandler == "FTP":
            self.__handler = self.__ftp_handler
            self.shandlerType="FTP"
        elif sHandler == "Throttled":
            self.__handler = self.__ftp_handler
            self.__handler.dtp_handler = self.__throttledDTP_handler
            self.shandlerType="Throttled"
        elif sHandler == "DTP":
            self.__handler = self.__ftp_handler
            self.__handler.dtp_handler = self.__DTP_handler
            self.shandlerType="DTP"
        elif sHandler == "TLS":
            self.__handler = self.__TLS_FTP_handler
            self.shandlerType = "TLS"

    def GetHandlerType(self):
        return self.shandlerType

    def SetAuthorizer(self, sAuthorizer):
        if sAuthorizer == "Dummy":
            self.__handler.authorizer=""
            self.__handler.authorizer = self.__dummy_authorizer
            self.sAuthorizer="Dummy"
        elif sAuthorizer == "Unix":
            self.__handler.authorizer=""
            self.__handler.authorizer = self.__unix_authorizer
            # self.__handler.abstracted_fs = UnixFilesystem
            self.sAuthorizer="Unix"

    def GetAuthorizer(self):
        return self.sAuthorizer

    ##### DummyAuthorizer Users
    def AddUser(self, sUser, sPassword, sHomedir, sPerm, sMsgLogin=None, sMsgQuit=None):
        self.__dummy_authorizer.add_user(sUser, sPassword, sHomedir, perm=sPerm, msg_login=sMsgLogin, msg_quit=sMsgQuit)

    def IsAnonymousMode(self, b):
        self.bIsAnonymus = b
    def GetIsAnonymousMode(self):
        return self.bIsAnonymus

    def RemoveAnonymous(self):
        if self.__dummy_authorizer.has_user("anonymous"):
            self.__dummy_authorizer.remove_user("anonymous")

    def AddAnonyous(self, sHomedir):
        self.__dummy_authorizer.add_anonymous(sHomedir)

    def RemoveUser(self, sUsername):
        self.__dummy_authorizer.remove_user(sUsername)
    #####

    ### TLS_FTP Handler
    def SetCertificate(self, sFile):
        self.__TLS_FTP_handler.certfile = sFile
    def GetCertificate(self):
        return self.__TLS_FTP_handler.certfile

    def SetKeyFile(self, sFile):
        self.__TLS_FTP_handler.keyfile=sFile
    def GetKeyFile(self):
        return self.__TLS_FTP_handler.keyfile

    def IsTLSControlRequired(self, b):
        self.__TLS_FTP_handler.tls_control_required=b
    def GetIsTLSControlRequired(self):
        return self.__TLS_FTP_handler.tls_control_required

    def IsTLSDataRequired(self,b):
        self.__TLS_FTP_handler.tls_data_required=b
    def GetIsTLSDataRequired(self):
        return self.__TLS_FTP_handler.tls_data_required
    ###

    ### DTP handler
    def SetDTPTimeout(self, iSeconds):
        self.__DTP_handler.timeout=iSeconds
    def GetDTPTimeout(self):
        return self.__DTP_handler.timeout

    def SetInBufferSize(self, iSize):
        self.__DTP_handler.ac_in_buffer_size = iSize
    def GetInBufferSize(self):
        return self.__DTP_handler.ac_in_buffer_size

    def SetOutBufferSize(self, iSize):
        self.__DTP_handler.ac_out_buffer_size = iSize
    def GetOutBufferSize(self):
        return self.__DTP_handler.ac_out_buffer_size
    ###

    ### ThrottledDTP handler
    def SetReadLimit(self, iLimit):
        self.__throttledDTP_handler.read_limit = iLimit
    def GetReadLimit(self):
        return self.__throttledDTP_handler.read_limit

    def SetWriteLimit(self, iLimit):
        self.__throttledDTP_handler.write_limit = iLimit
    def GetWriteLimit(self):
        return self.__throttledDTP_handler.write_limit
    ###

    ##### FTPHandler Control connection
    def SetFTPimeout(self, iSeconds):
        self.__ftp_handler.timeout = iSeconds
    def GetFTPTimeout(self):
        return self.__ftp_handler.timeout

    def SetMaxLogginAtempts(self, iNum):
        self.__ftp_handler.max_login_attempts = iNum
    def GetMaxLogginAtempts(self):
        return self.__ftp_handler.max_login_attempts

    def PermitForeignAddresses(self, b):
        self.__ftp_handler.permit_foreign_addresses=b
    def GetPermitForeignAddresses(self):
        return self.__ftp_handler.permit_foreign_addresses

    def PermitPrivilegedPorts(self, b):
        self.__ftp_handler.permit_privileged_ports=b
    def GetPermitPrivilegedPorts(self):
        return self.__ftp_handler.permit_privileged_ports

    def SetMasqueradeAddress(self, sIp):
        self.__ftp_handler.masquerade_address=sIp
    def GetMasqueradeAddress(self):
        return self.__ftp_handler.masquerade_address

    #TODO Implement in PyQT and ui
    def SetMasqueradeAddressMap(self, MapDictionary):
        self.__ftp_handler.masquerade_address_map=MapDictionary
    def GetMasqueradeAddressMap(self):
        return self.__ftp_handler.masquerade_address_map

    def SetRangePassivePorts(self, iStart, iStop):
        self.__ftp_handler.passive_ports = range(iStart, iStop)
    def GetRangePassivePorts(self):
        return self.__ftp_handler.passive_ports

    def UseGMTTimes(self, b):
        self.__ftp_handler.use_gmt_times=b
    def GetGMTTimes(self):
        return self.__ftp_handler.use_gmt_times

    def SetTCPNoDelay(self, b):
        self.__ftp_handler.tcp_no_delay=b
    def GetSetTCPNoDelay(self):
        return self.__ftp_handler.tcp_no_delay

    def UseSendFile(self,b):
        self.__ftp_handler.use_sendfile=b
    def GetUseSendFile(self):
        return self.__ftp_handler.use_sendfile

    def SetAuthFailedTimeout(self, iSeconds):
        self.__ftp_handler.auth_failed_timeout=iSeconds
    def GetAuthFailedTimeout(self):
        return self.__ftp_handler.auth_failed_timeout

    def SetBanner(self, sMsg):
        self.__ftp_handler.banner = sMsg
    def GetBanner(self):
        return self.__ftp_handler.banner
    ###

    def SetAddress(self, sIp):
        self.address=sIp
    def GetAddress(self):
        return self.address

    def SetPort(self, iPort):
        self.port=iPort
    def GetPort(self):
        return self.port

    ### Server
    def SetServer(self, sServerType=None):
        if sServerType == "Normal":
            self.sServerType="Normal"
            self.server= FTPServer((self.address, self.port), self.__handler)
        elif sServerType == "Threaded":
            self.sServerType=="Threaded"
            self.server = ThreadedFTPServer((self.address, self.port), self.__handler)
        elif sServerType == "Multiprocess":
            self.sServerType="Multiprocess"
            self.server = MultiprocessFTPServer((self.address, self.port), self.__handler)
        else: #default Normal
            self.sServerType="Normal"
            self.server= FTPServer((self.address, self.port), self.__handler)

    def SetMaxConnections(self, iNum=512):
        self.server.max_cons=iNum
    def GetMaxConnections(self):
        return self.server.max_cons

    def SetMaxConnectionsPerIp(self, iNum=0):
        self.server.max_cons_per_ip=iNum
    def GetMaxConnectionsPerIp(self):
        return self.server.max_cons_per_ip

    def StartServer(self):
        self.server.serve_forever()

    def Close(self):
        self.server.close()

    def CloseAll(self):
        self.server.close_all()
    ###

    def SetLogFile(self, fname, lvl=None):
        import logging

        logger = logging.getLogger('pyftpdlib')
        hdlr = logging.FileHandler(fname)
        frm = logging.Formatter("[%(asctime)s];%(name)s;%(levelname)s;%(message)s", "%d-%m-%Y %H:%M:%S")
        hdlr.setFormatter(frm)
        logger.setLevel(logging.INFO)

        if lvl == "INFO":
           logger.setLevel(logging.INFO)
        elif lvl == "CRITICAL":
            logger.setLevel(logging.CRITICAL)
        elif lvl == "ERROR":
            logger.setLevel(logging.ERROR)
        elif lvl == "WARNING":
            logger.setLevel(logging.WARNING)
        elif lvl == "DEBUG":
            logger.setLevel(logging.DEBUG)
        else: #Default INFO
            logger.setLevel(logging.INFO)

        logger.addHandler(hdlr)
