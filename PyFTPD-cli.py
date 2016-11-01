from FTPD import *
import thread

def main():

    ftpd = FTP_SERVER()

    ### (A) Set a Handler
    #1) FTP Handler
    # ftpd.SetHandler("FTP")

    #2) Throttled Hadler
    # ftpd.SetHandler("Throttled")
    # ftpd.SetReadLimit(30720)
    # ftpd.SetWriteLimit(30720)

    #3) DTP Hadler
    # ftpd.SetHandler("DTP")
    # ftpd.SetDTPTimeout(300)
    # ftpd.SetInBufferSize(30720)
    # ftpd.SetOutBufferSize(30720)

    #4) TLS FTP Handler
    # ftpd.SetHandler("TLS")
    # ftpd.SetCertificate("/home/user/Documents/PycharmProjects/PyFTPD/cert.pem")
    # ftpd.SetKeyFile("/home/user/Documents/PycharmProjects/PyFTPD/key.pem")
    # ftpd.IsTLSControlRequired(True)
    # ftpd.IsTLSDataRequired(True)
    # #Unix Auth must be enabled
    # ftpd.SetAuthorizer("Unix")
    # ftpd.port=21

    ### (B) Set Auth Unix or Dummy
    #1) UNIX Auth
    # ftpd.SetAuthorizer("Unix")
    # or
    #2) User Auth
    # ftpd.SetAuthorizer("Dummy")
    # ftpd.AddUser("user1", "12345", "/home/user", "elradfmwM", "Hello!!!", "Goodbye!!!")
    # ftpd.AddUser("user2", "345", "/home/user/Downloads", "elradfmwM", "Hello!!!", "Goodbye!!!")
    # ftpd.AddAnonyous("/home/user/Downloads")

    ### (C) Custom setup
    #Custom setup
    # ftpd.SetBanner("ftpd service ready.")
    # ftpd.port = 2121
    # ftpd.address = "0.0.0.0"
    # ftpd.SetLogFile('/home/user/Documents/PycharmProjects/PyFTPD/pyftpd.log', "INFO")

    ### (D) Apply configuration
    #Set server config
    # ftpd.SetServer("Threaded")
    #or
    # ftpd.SetServer("Normal")
    #or
    # ftpd.SetServer("Multiprocess")

    ### (E) set server specific settings
    # ftpd.SetMaxConnections(256)
    # ftpd.SetMaxConnectionsPerIp(5)

    ### (F) Start server
    #Start server
    thread.start_new_thread(ftpd.StartServer, ())
    # ftpd.StartServer()

    x = raw_input("Hit Enter to finish...")

    ### (F) Stop server
    # ftpd.CloseAll()


if __name__ == '__main__':
    main()