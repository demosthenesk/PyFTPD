import sqlite3
from FTPD import *
import thread
from PyFTPD_GUI import *

class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, icon, parent)

        #create the systray menu
        menu = QtGui.QMenu(parent)
        exitAction = menu.addAction(QtGui.QIcon(QtGui.QPixmap("exit.png")), "Exit")
        showAction = menu.addAction(QtGui.QIcon(QtGui.QPixmap("window.png")), "Show Window")
        hideAction = menu.addAction(QtGui.QIcon(QtGui.QPixmap("window.png")), "Hide Window")

        self.setContextMenu(menu)
        QtCore.QObject.connect(exitAction, QtCore.SIGNAL('triggered()'), self.exit)
        QtCore.QObject.connect(showAction, QtCore.SIGNAL('triggered()'), self.showWindow)
        QtCore.QObject.connect(hideAction, QtCore.SIGNAL('triggered()'), self.hideWindow)

    def exit(self):
        '''Quit the application'''
        QtCore.QCoreApplication.exit()

    def showWindow(self):
        '''show the application'''
        self.parent().show()

    def hideWindow(self):
        '''Hide the application'''
        self.parent().hide()


class MyForm(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #Instansiate Server default to empty
        #instanciate server
        self.ftpd = FTP_SERVER()


        #connect to db
        # self.db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        # self.db.setDatabaseName('PyFTPD-users.sqlite')
        self.db = sqlite3.connect("PyFTPD-users.sqlite")

        #Log Watcher
        self.LogTimer = QtCore.QTimer()
        self.LogTimer.timeout.connect(self.WatchLog)

        #Read Config
        self.ReadServerConfig()

        #Create events
        QtCore.QObject.connect(self.ui.btnCertificate, QtCore.SIGNAL('clicked()'), self.btnCertificate_Click)
        QtCore.QObject.connect(self.ui.btnKey, QtCore.SIGNAL('clicked()'), self.btnKey_Click)
        QtCore.QObject.connect(self.ui.rdbDummy, QtCore.SIGNAL('clicked()'), self.rdbDummy_Click)
        QtCore.QObject.connect(self.ui.rdbUnix, QtCore.SIGNAL('clicked()'), self.rdbUnix_Click)
        QtCore.QObject.connect(self.ui.btnAnonymousHomeDir, QtCore.SIGNAL('clicked()'), self.btnAnonymousHomeDir_Click)
        QtCore.QObject.connect(self.ui.btnUserHomeDir, QtCore.SIGNAL('clicked()'), self.btnUserHomeDir_Click)
        QtCore.QObject.connect(self.ui.btnClear, QtCore.SIGNAL('clicked()'), self.btnClear_Click)
        self.ui.lstUsers.itemClicked.connect(self.lstUsers_Click)
        QtCore.QObject.connect(self.ui.btnRemoveUser, QtCore.SIGNAL('clicked()'), self.btnRemoveUser_Click)
        QtCore.QObject.connect(self.ui.btnAdd, QtCore.SIGNAL('clicked()'), self.btnAdd_Click)
        QtCore.QObject.connect(self.ui.btnApply, QtCore.SIGNAL('clicked()'), self.btnApply_Click)
        QtCore.QObject.connect(self.ui.btnLogFile, QtCore.SIGNAL('clicked()'), self.btnLogFile_Click)
        QtCore.QObject.connect(self.ui.btnApplyConfig, QtCore.SIGNAL('clicked()'), self.ApplyConfig)
        QtCore.QObject.connect(self.ui.btnStartServer, QtCore.SIGNAL('clicked()'), self.StartServer)
        QtCore.QObject.connect(self.ui.btnCloseAll, QtCore.SIGNAL('clicked()'), self.CloseAll)
        # QtCore.QObject.connect(self.ui.btnSetServer, QtCore.SIGNAL('clicked()'), self.SetServer_Click)

    def SetServer_Click(self):
        try:
            sAddress = str(self.ui.sIp.text())
            sPort = str(self.ui.sPort.text())

            #validate port
            if  self.IsInt(sPort)==False:
                raise Exception("Port value must be an integer!")

            #default
            sType = "Threaded"
            if self.ui.rdbNormal.isChecked() == True:
                sType = "Normal"
            if self.ui.rdbThreaded.isChecked() == True:
                sType = "Threaded"
            if self.ui.rdbMultiprocess.isChecked() == True:
                sType = "Multiprocess"

            self.ftpd.CloseAll()
            self.ftpd = FTP_SERVER(sAddress, sPort, sType)

            if self.IsInt(self.ui.sMaximumConnections.text()) == False:
                raise Exception("Maximum Connections value must be an integer!")
            if self.IsInt(self.ui.sMaximumConnectionsPerIp.text()) == False:
                raise Exception("Maximum Connections per Ip value must be an integer!")

            self.ftpd.SetMaxConnections(int(self.ui.sMaximumConnections.text()))
            self.ftpd.SetMaxConnectionsPerIp(int(self.ui.sMaximumConnectionsPerIp.text()))

        except Exception as e:
            print e.message
            QtGui.QMessageBox.critical(None, QtGui.qApp.tr("Error"),
                                       QtGui.qApp.tr(str(e.message)),
                                       QtGui.QMessageBox.Ok)

    def btnLogFile_Click(self):
        #show QFileDialog and selects a folder
        dirname = QtGui.QFileDialog.getExistingDirectory(self.parent(),"Select Log File Directory")
        self.ui.sLogFileName.setText(str(dirname)+str("/pyftpd.log"))

    def btnApply_Click(self):
        self.btnRemoveUser_Click(False)
        self.btnAdd_Click()

    def btnAdd_Click(self):
        sUser = str(self.ui.sUsername.text())
        sHome = str(self.ui.sHome.text())
        sPass = str(self.ui.sPassword.text())
        sMsgLog = str(self.ui.sMsgLogin.text())
        sMsgQuit = str(self.ui.sMsgQuit.text())
        sPerms = str(self.CreatePermString())

        try:
            if len(sUser)>0:
                self.ftpd.AddUser(sUser, sPass, sHome, sPerms, sMsgLog, sMsgQuit)
                self.db = sqlite3.connect("PyFTPD-users.sqlite")
                c = self.db.cursor()
                sSQLquery = "INSERT INTO `users`(`username`,`password`,`homedir`,`LoginMsg`,`QuitMsg`,`Permissions`) VALUES ('"+sUser+"','"+sPass+"','"+sHome+"','"+sMsgLog+"','"+sMsgQuit+"','"+sPerms+"');"
                c.execute(str(sSQLquery))
                self.db.commit()
                self.db.close()
                self.RefreshUserTable()
        except Exception as e:
            QtGui.QMessageBox.critical(None, QtGui.qApp.tr("Error"),
                                       QtGui.qApp.tr(str(e.message)),
                                       QtGui.QMessageBox.Ok)


    def CreatePermString(self):
        sPerms =""
        #e
        if self.ui.chk_e.isChecked():
            sPerms +="e"
        #l
        if self.ui.chk_l.isChecked():
            sPerms+="l"
        #r
        if self.ui.chk_r.isChecked():
            sPerms+="r"
        #a
        if self.ui.chk_a.isChecked():
            sPerms+="a"
        #d
        if self.ui.chk_d.isChecked():
            sPerms+="d"
        #f
        if self.ui.chk_f.isChecked():
            sPerms+="f"
        #m
        if self.ui.chk_m.isChecked():
            sPerms+="m"
        #w
        if self.ui.chk_w.isChecked():
            sPerms+="w"
        #M
        if self.ui.chk_M.isChecked():
            sPerms+="M"

        return sPerms

    def btnRemoveUser_Click(self, DoClear=True):

        try:
            sUser = self.ui.lstUsers.currentItem().text()

            if len(sUser)>0:
                self.db = sqlite3.connect("PyFTPD-users.sqlite")
                c = self.db.cursor()
                sSQLquery = "DELETE FROM `users` WHERE `username`='"+str(sUser)+"';"
                # sSQLquery = "DELETE FROM `users` WHERE `username`=?", (sUser,)
                c.execute(str(sSQLquery))
                self.db.commit()
                self.db.close()

                self.ftpd.RemoveUser(str(sUser))
                self.RefreshUserTable()
                if DoClear==True:
                    self.btnClear_Click()

        except AttributeError:
            QtGui.QMessageBox.critical(None, QtGui.qApp.tr("Cannot remove user"),
                                       QtGui.qApp.tr("Please select a user from the list and then click the Remove User button!"),
                                       QtGui.QMessageBox.Ok)

    def RefreshUserTable(self):
        self.ui.lstUsers.clear()
        self.ReadUserTable()

    def lstUsers_Click(self, item):
        self.db = sqlite3.connect("PyFTPD-users.sqlite")
        c = self.db.cursor()
        sSQLquery="SELECT * FROM `users` WHERE `username` = '"+str(item.text())+"' ORDER BY `id` ASC;"
        c.execute(str(sSQLquery))
        row = c.fetchall()

        #username
        self.ui.sUsername.setText(str(row[0][1]))
        #password
        self.ui.sPassword.setText(str(row[0][2]))
        #homedir
        self.ui.sHome.setText(str(row[0][3]))
        #login message
        self.ui.sMsgLogin.setText(str(row[0][4]))
        #quit message
        self.ui.sMsgQuit.setText(str(row[0][5]))
        #permissions
        sPerm = row[0][6]
        #e
        if "e" in sPerm:
            self.ui.chk_e.setChecked(True)
        else:
            self.ui.chk_e.setChecked(False)
        #l
        if "l" in sPerm:
            self.ui.chk_l.setChecked(True)
        else:
            self.ui.chk_l.setChecked(False)
        #r
        if "r" in sPerm:
            self.ui.chk_r.setChecked(True)
        else:
            self.ui.chk_r.setChecked(False)
        #a
        if "a" in sPerm:
            self.ui.chk_a.setChecked(True)
        else:
            self.ui.chk_a.setChecked(False)
        #d
        if "d" in sPerm:
            self.ui.chk_d.setChecked(True)
        else:
            self.ui.chk_d.setChecked(False)
        #f
        if "f" in sPerm:
            self.ui.chk_f.setChecked(True)
        else:
            self.ui.chk_f.setChecked(False)
        #m
        if "m" in sPerm:
            self.ui.chk_m.setChecked(True)
        else:
            self.ui.chk_m.setChecked(False)
        #w
        if "w" in sPerm:
            self.ui.chk_w.setChecked(True)
        else:
            self.ui.chk_w.setChecked(False)
        #M
        if "M" in sPerm:
            self.ui.chk_M.setChecked(True)
        else:
            self.ui.chk_M.setChecked(False)

        self.db.close()

    def ReadUserTable(self):
        self.db = sqlite3.connect("PyFTPD-users.sqlite")
        c = self.db.cursor()
        sSQLquery="SELECT * FROM `users`  ORDER BY `id` ASC;"
        c.execute(str(sSQLquery))
        rows = c.fetchall()

        for row in rows:
            item = QtGui.QListWidgetItem(str(row[1]))
            self.ui.lstUsers.addItem(item)
            # print row

        self.db.close()

    def WriteUserTable(self):
        self.db = sqlite3.connect("PyFTPD-users.sqlite")
        c = self.db.cursor()
        sSQLquery="SELECT * FROM `users`  ORDER BY `id` ASC;"
        c.execute(str(sSQLquery))
        rows = c.fetchall()
        try:
            for row in rows:
                self.ftpd.AddUser(str(row[1]),str(row[2]), str(row[3]), str(row[6]), str(row[4]), str(row[5]))
        except Exception as e:
            pass

        self.db.close()


    def btnClear_Click(self):
        #Clear the user form
        self.ui.sUsername.clear()
        self.ui.sPassword.clear()
        self.ui.sHome.clear()
        self.ui.sMsgLogin.clear()
        self.ui.sMsgQuit.clear()

        self.ui.chk_M.setChecked(False)
        self.ui.chk_m.setChecked(False)
        self.ui.chk_e.setChecked(False)
        self.ui.chk_a.setChecked(False)
        self.ui.chk_d.setChecked(False)
        self.ui.chk_f.setChecked(False)
        self.ui.chk_l.setChecked(False)
        self.ui.chk_w.setChecked(False)
        self.ui.chk_r.setChecked(False)

    def btnUserHomeDir_Click(self):
        #show QFileDialog and selects a folder
        dirname = QtGui.QFileDialog.getExistingDirectory(self.parent(),"Select Home Directory")
        self.ui.sHome.setText(str(dirname))

    def btnAnonymousHomeDir_Click(self):
        #show QFileDialog and selects a folder
        dirname = QtGui.QFileDialog.getExistingDirectory(self.parent(),"Select Home Directory")
        self.ui.sAnonymousHomeDir.setText(str(dirname))

    def rdbUnix_Click(self):
        self.ftpd.SetAuthorizer("Unix")
        self.ui.groupBoxDummy.setEnabled(False)

    def rdbDummy_Click(self):
        self.ftpd.SetAuthorizer("Dummy")
        self.ui.groupBoxDummy.setEnabled(True)

    def btnCertificate_Click(self):
        #show QFileDialog and selects .pem file.
        fname = QtGui.QFileDialog.getOpenFileName(self.parent(), 'Select Certificate file', QtCore.QDir.homePath(), "Certificate files (*.pem)")
        self.ui.sCertificate.setText(str(fname))

    def btnKey_Click(self):
        #show QFileDialog and selects .pem file.
        fname = QtGui.QFileDialog.getOpenFileName(self.parent(), 'Select Key file', QtCore.QDir.homePath(), "Certificate files (*.pem)")
        self.ui.sKey.setText(str(fname))

    #############################################################################
    def ReadHandlerType(self):
        #Handler
        sHandlerType = self.ftpd.GetHandlerType()
        if sHandlerType == "FTP":
            self.ui.rdbFTP.setChecked(True)
        elif sHandlerType == "Throttled":
            self.ui.rdbThrottled.setChecked(True)
        elif sHandlerType == "DTP":
            self.ui.rdbDTP.setChecked(True)
        elif sHandlerType == "TLS":
            self.ui.rdbTLS.setChecked(True)

    def ReadFTPHandler(self):
        #### Get FTP Handler values
        #sFTPTimeout
        self.ui.sFTPTimeout.setText(str(self.ftpd.GetFTPTimeout()))

        #sMaxLoginAtempts
        self.ui.sMaxLoginAtempts.setText(str(self.ftpd.GetMaxLogginAtempts()))

        #sMasqueradeAddress
        if self.ftpd.GetMasqueradeAddress() != None:
            self.ui.sMasqueradeAddress.setText(str(self.ftpd.GetMasqueradeAddress()))

        #GetRangePassivePorts
        lstPPRange = self.ftpd.GetRangePassivePorts()
        if type(lstPPRange) is not type(None):
            self.ui.sStart.setText(str(lstPPRange[0]))
            self.ui.sStop.setText(str(lstPPRange[-1]))

        #sBanner
        self.ui.sBanner.setText(str(self.ftpd.GetBanner()))

        #sAuthFailedTimeout
        self.ui.sAuthFailedTimeout.setText(str(self.ftpd.GetAuthFailedTimeout()))

        #chkPermitForeignAddresses
        self.ui.chkPermitForeignAddresses.setChecked(self.ftpd.GetPermitForeignAddresses())

        #chkPermitPrivilegedPorts
        self.ui.chkPermitPrivilegedPorts.setChecked(self.ftpd.GetPermitPrivilegedPorts())

        #chkUseGMTTimes
        self.ui.chkUseGMTTimes.setChecked(self.ftpd.GetGMTTimes())

        #chkTCPNoDelay
        self.ui.chkTCPNoDelay.setChecked(self.ftpd.GetSetTCPNoDelay())

        #chkUseSendFile
        self.ui.chkUseSendFile.setChecked(self.ftpd.GetUseSendFile())

    def ReadThrottledHandler(self):
        #### Get Throttled Handler values
        #sReadLimit
        self.ui.sReadLimit.setText(str(self.ftpd.GetReadLimit()))

        #sWriteLimit
        self.ui.sWriteLimit.setText(str(self.ftpd.GetWriteLimit()))

    def ReadDTPHandler(self):
        #### Get DTP Handler values
        #sDTPTimeout
        self.ui.sDTPTimeout.setText(str(self.ftpd.GetDTPTimeout()))

        #sInBufferSize
        self.ui.sInBufferSize.setText(str(self.ftpd.GetInBufferSize()))

        #sOutBufferSize
        self.ui.sOutBufferSize.setText(str(self.ftpd.GetOutBufferSize()))

    def ReadTLSHandler(self):
        ### TLS Handler Values
        #chkIsTLSControlRequired
        self.ui.chkIsTLSControlRequired.setChecked(self.ftpd.GetIsTLSControlRequired())

        #chkIsTLSDataRequired
        self.ui.chkIsTLSDataRequired.setChecked(self.ftpd.GetIsTLSDataRequired())

        self.ui.sCertificate.setText(str(self.ftpd.GetCertificate()))
        self.ui.sKey.setText(str(self.ftpd.GetKeyFile()))

    def ReadAuthorizerType(self):
        ##### Authorizer
        sAuthorizer = self.ftpd.GetAuthorizer()
        if sAuthorizer == "Dummy":
            self.ui.rdbDummy.setChecked(True)
            self.ui.groupBoxDummy.setEnabled(True)
        elif sAuthorizer == "Unix":
            self.ui.rdbUnix.setChecked(True)
            self.ui.groupBoxDummy.setEnabled(False)

    def ReadServerType(self):
        sType = self.ftpd.sServerType

        if sType == "Normal":
            self.ui.rdbNormal.setChecked(True)
        elif sType == "Threaded":
            self.ui.rdbThreaded.setChecked(True)
        elif sType == "Multiprocess":
            self.ui.rdbMultiprocess.setChecked(True)

    def ReadLogFilePath(self):
        sLogFile = self.ftpd.GetLogFilePath()+"pyftpd.log"
        self.ui.sLogFileName.setText(sLogFile)

    def ReadServerAddress(self):
        self.ui.sIp.setText(str(self.ftpd.GetAddress()))

    def ReadServerPort(self):
        self.ui.sPort.setText(str(self.ftpd.GetPort()))

    def ReadServerMaxCons(self):
        self.ui.sMaximumConnections.setText(str(self.ftpd.GetMaxConnections()))
        self.ui.sMaximumConnectionsPerIp.setText(str(self.ftpd.GetMaxConnectionsPerIp()))

    def ReadServerConfig(self):
        #Read server config values
        self.ReadHandlerType()
        self.ReadFTPHandler()
        self.ReadThrottledHandler()
        self.ReadDTPHandler()
        self.ReadTLSHandler()
        self.ReadAuthorizerType()
        self.RefreshUserTable()
        self.WriteUserTable()
        self.ReadServerType()
        self.ReadLogFilePath()
        self.ReadServerAddress()
        self.ReadServerPort()
        self.ReadServerMaxCons()


    def ApplyConfig(self, bShowMessage=True):
        self.SetServer_Click()
        self.ApplyHandlerType()
        self.ApplyAuthorizer()
        self.btnClear_Click()
        self.ApplyLogFilePAth()

        self.ReadServerConfig()

        if bShowMessage == True:
            QtGui.QMessageBox.information(None, QtGui.qApp.tr("Message"),
                                   QtGui.qApp.tr(str("Configuration applied successfully!")),
                                   QtGui.QMessageBox.Ok)

    def IsInt(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def ApplyLogFilePAth(self):
        try:
            sDir = self.ui.sLogFileName.text()[:-11]
            if os.path.isdir(str(sDir)):
                self.ftpd.SetLogFile(str(self.ui.sLogFileName.text()), self.ui.cmbLevel.currentText())
            else:
                raise Exception("Log path is incorrect!")

        except Exception as e:
            QtGui.QMessageBox.critical(None, QtGui.qApp.tr("Error"),
                                   QtGui.qApp.tr(str(e.message)),
                                   QtGui.QMessageBox.Ok)



    def ApplyAuthorizer(self):

        if self.ui.rdbDummy.isChecked() == True:
            self.ftpd.SetAuthorizer("Dummy")

            if self.ui.chkAnonumous.isChecked() == True:
                try:
                    if len(self.ui.sAnonymousHomeDir.text())>0:
                        if os.path.isdir(str(self.ui.sAnonymousHomeDir.text())):
                            self.ftpd.IsAnonymousMode(self.ui.chkAnonumous.isChecked())
                            self.ftpd.AddAnonyous(str(self.ui.sAnonymousHomeDir.text()))
                        else:
                            self.ui.chkAnonumous.setChecked(False)
                            raise Exception("Anonymous Home Directory is non valid!")
                    else:
                        self.ui.chkAnonumous.setChecked(False)

                except Exception as e:
                    QtGui.QMessageBox.critical(None, QtGui.qApp.tr("Error"),
                                               QtGui.qApp.tr(str(e.message)),
                                               QtGui.QMessageBox.Ok)

            else:
                try:
                    self.ftpd.RemoveAnonymous()
                except Exception as e:
                    QtGui.QMessageBox.critical(None, QtGui.qApp.tr("Error"),
                                               QtGui.qApp.tr(str(e.message)),
                                               QtGui.QMessageBox.Ok)

        else:
            self.ftpd.SetAuthorizer("Unix")

    def ApplyHandlerType(self):

        try:
            #FTP Handler
            if self.ui.rdbFTP.isChecked() == True:
                self.ftpd.SetHandler("FTP")

                if self.IsInt(self.ui.sFTPTimeout.text()):
                    self.ftpd.SetFTPimeout(int(self.ui.sFTPTimeout.text()))
                else:
                    raise Exception("FTP Timeout value must be an integer!")

                if self.IsInt(self.ui.sMaxLoginAtempts.text()):
                   self.ftpd.SetMaxLogginAtempts(int(self.ui.sMaxLoginAtempts.text()))
                else:
                    raise Exception("Max Loggin Atempts value must be an integer!")

                if len(self.ui.sMasqueradeAddress.text())>0:
                    self.ftpd.SetMasqueradeAddress(self.ui.sMasqueradeAddress.text())

                if self.IsInt(self.ui.sStart.text()) and self.IsInt(self.ui.sStop.text()):
                    if int(self.ui.sStop.text()) > int(self.ui.sStart.text()):
                        self.ftpd.SetRangePassivePorts(int(self.ui.sStart.text()), int(self.ui.sStop.text()))
                    else:
                        raise Exception("Stop value must be greater than Start value!")

                self.ftpd.SetBanner(self.ui.sBanner.text())

                if self.IsInt(self.ui.sAuthFailedTimeout.text()):
                    self.ftpd.SetAuthFailedTimeout(int(self.ui.sAuthFailedTimeout.text()))
                else:
                    raise Exception("Authentication Failed Timeout value must be an integer!")

                self.ftpd.PermitForeignAddresses(self.ui.chkPermitForeignAddresses.isChecked())
                self.ftpd.PermitPrivilegedPorts(self.ui.chkPermitPrivilegedPorts.isChecked())
                self.ftpd.UseGMTTimes(self.ui.chkUseGMTTimes.isChecked())
                self.ftpd.SetTCPNoDelay(self.ui.chkTCPNoDelay.isChecked())
                self.ftpd.UseSendFile(self.ui.chkUseSendFile.isChecked())

            #Throttled Handler
            elif self.ui.rdbThrottled.isChecked() == True:
                self.ftpd.SetHandler("Throttled")

                if len(self.ui.sReadLimit.text())>0:
                    if self.IsInt(self.ui.sReadLimit.text()):
                        self.ftpd.SetReadLimit(int(self.ui.sReadLimit.text()))
                    else:
                        raise Exception("Throttled Read Limit value must be an integer!")

                if len(self.ui.sWriteLimit.text())>0:
                    if self.IsInt(self.ui.sWriteLimit.text()):
                        self.ftpd.SetWriteLimit(int(self.ui.sWriteLimit.text()))
                    else:
                        raise Exception("Throttled Write Limit value must me an integer!")

            #DTP Handler
            elif self.ui.rdbDTP.isChecked() == True:
                self.ftpd.SetHandler("DTP")

                if self.IsInt(self.ui.sDTPTimeout.text()):
                    self.ftpd.SetDTPTimeout(int(self.ui.sDTPTimeout.text()))
                else:
                    raise Exception("DTP Timeout value must be an integer!")

                if self.IsInt(self.ui.sInBufferSize.text()):
                    self.ftpd.SetInBufferSize(int(self.ui.sInBufferSize.text()))
                else:
                    raise Exception("DTP In Buffer Size value must be an integer!")

                if self.IsInt(self.ui.sOutBufferSize.text()):
                    self.ftpd.SetOutBufferSize(int(self.ui.sOutBufferSize.text()))
                else:
                    raise Exception("DTP Out Buffer Size value must be an integer!")

            #TLS Handler
            elif self.ui.rdbTLS.isChecked() == True:
                self.ftpd.SetHandler("TLS")

                if len(self.ui.sCertificate.text())>0 and self.ui.sCertificate.text() != "None":
                    if os.path.isfile(self.ui.sCertificate.text()):
                        self.ftpd.SetCertificate(str(self.ui.sCertificate.text()))
                    else:
                        raise Exception("Certification file path is incorrect!")
                else:
                    self.ftpd.SetCertificate(None)

                if len(self.ui.sKey.text())>0 and self.ui.sKey.text() != "None":
                    if os.path.isfile(self.ui.sKey.text()):
                        self.ftpd.SetKeyFile(str(self.ui.sKey.text()))
                    else:
                        raise Exception("Key file path is incorrect!")
                else:
                    self.ftpd.SetKeyFile(None)

                self.ftpd.IsTLSControlRequired(self.ui.chkIsTLSControlRequired.isChecked())
                self.ftpd.IsTLSDataRequired(self.ui.chkIsTLSDataRequired.isChecked())


        except Exception as e:
            QtGui.QMessageBox.critical(None, QtGui.qApp.tr("Error"),
                                       QtGui.qApp.tr(str(e.message)),
                                       QtGui.QMessageBox.Ok)

    def StartLogTimer(self):
        self.LogTimer.start(5000)

    def StopLogTimer(self):
        self.LogTimer.stop()

    def CloseAll(self):
        self.StopLogTimer()
        self.ftpd.CloseAll()
        self.ui.btnStartServer.setEnabled(True)
        self.ui.btnApplyConfig.setEnabled(True)
        self.ApplyConfig(False)

    def StartServer(self):

        # #Apply config before start
        # self.ApplyConfig(False)

        # Start server
        thread.start_new_thread(self.ftpd.StartServer, ())

        self.ui.btnStartServer.setEnabled(False)
        self.ui.btnApplyConfig.setEnabled(False)
        self.StartLogTimer()


    def WatchLog(self):
        file = open(str(self.ftpd.GetLogFilePath()+"pyftpd.log"))
        lines = file.readlines()

        sLog=""
        for line in lines:
            sLog+=line

        file.close()
        self.ui.sLogFileView.setPlainText(sLog)
        self.ui.sLogFileView.moveCursor(QtGui.QTextCursor.End)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    # app.setQuitOnLastWindowClosed(False)

    myapp = MyForm()
    myapp.show()

    trayIcon = SystemTrayIcon(QtGui.QIcon("file-server-300px.png"), myapp)
    trayIcon.show()

    sys.exit(app.exec_())