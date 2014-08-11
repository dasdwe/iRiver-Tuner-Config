#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import struct
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QHeaderView
from app.iriverui import Ui_Tuner


try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class TunerSettings(QtGui.QMainWindow):
    filename = None


    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Tuner()
        self.ui.setupUi(self)

#         sloty i sygnaly
#        QtCore.QObject.connect(self.ui.loadButton,QtCore.SIGNAL("clicked()"),self.file_dialog)
#        QtCore.QObject.connect(self.ui.saveButton,QtCore.SIGNAL("clicked()"),self.save_tuner)
#        QtCore.QObject.connect(self.ui.stationsList,QtCore.SIGNAL("itemChanged(QTableWidgetItem*)"),self.enable_save)
        self.ui.loadButton.clicked.connect(self.file_dialog)
        self.ui.saveButton.clicked.connect(self.save_tuner)
        self.ui.stationsList.itemChanged.connect(self.enable_save)
        self.ui.radioUSA.clicked.connect(self.enable_save)
        self.ui.radioJapan.clicked.connect(self.enable_save)
        self.ui.radioEurope.clicked.connect(self.enable_save)
#        self.ui.stationsList.setItemDelegateForColumn(1, frequency_delegate(self))
        self.ui.stationsList.setColumnWidth(0,170)
        self.ui.stationsList.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
        self.ui.stationsList.horizontalHeader().setResizeMode(1, QHeaderView.Fixed)
        
        QtGui.QMessageBox.information(self, 'TODO'.decode('UTF-8'), '- "name" column max. 10 chars\n- "MHz" column only deciaml xxx.xx'.decode('UTF-8'))


    def enable_save(self):
        self.ui.saveButton.setEnabled(True)

    def disable_save(self):
        self.ui.saveButton.setEnabled(False)

        
    def file_dialog(self):
        response = False
        
        SAVE = 'Zapisz'.decode('UTF-8')
        DISCARD = 'Porzuć'.decode('UTF-8')
        CANCEL = 'Anuluj'.decode('UTF-8')
        # jeżeli są zmiany to pokazujemy okno QMessageBox
        if self.ui.saveButton.isEnabled() and self.filename:
            message = QtGui.QMessageBox(self)
            message.setText('Czy chcesz zapisać wprowadzone zmiany?'.decode('UTF-8'))
            message.setWindowTitle('Nie zapisano zmian w pliku'.decode('UTF-8'))
            message.setIcon(QtGui.QMessageBox.Question)
            message.addButton(SAVE, QtGui.QMessageBox.AcceptRole)
            message.addButton(DISCARD, QtGui.QMessageBox.DestructiveRole)
            message.addButton(CANCEL, QtGui.QMessageBox.RejectRole)
            message.setDetailedText('Nie zapisano zmian w pliku: ' + str(self.filename))
            message.exec_()
            response = message.clickedButton().text()
            
#            Zapisz zmiany w pliku
            if response == SAVE:
                self.save_tuner()
                self.disable_save()
#            Odrzuć zmiany w pliku
            elif response == DISCARD:
                self.disable_save()
        
        if response != CANCEL:
            self.load_tuner()
            self.disable_save()


    def load_tuner(self):
        minFreq = 0
        maxFreq = 0
        stations = []

        self.filename = QtGui.QFileDialog.getOpenFileName(self, 'Wczytaj plik'.decode('UTF-8'), '.')

        from os.path import isfile
        if isfile(self.filename):
            file = open(self.filename, mode='rb')

            fileContent = file.read(5)
            header = struct.unpack("5b", fileContent)

        # Ustawiony w nagłówku region
            if header[2] == 0:
#                USA/Korea (87-108 MHz)
                self.ui.radioUSA.setChecked(True)
                minFreq = 87
                maxFreq = 108
            elif header[2] == 1:
#                Japan (76-90 MHz)
                self.ui.radioJapan.setChecked(True)
                minFreq = 76
                maxFreq = 90
            elif header[2] == 2:
#                Europe (87-108 MHz)
                self.ui.radioEurope.setChecked(True)
                minFreq = 87
                maxFreq = 108
            else:
#                Nieprawidłowy nagłówek
                QtGui.QMessageBox.warning(self, 'Błąd w pliku'.decode('UTF-8'), 'Nieprawidłowy region.'.decode('UTF-8'))

            fileContent = file.read(26)

            i = 0
            while i < 20 and len(fileContent) == 26:
                i += 1
                station = { 'name' : '', 'freq' : ''}
                (id, name, freq) = struct.unpack("b20s5s", fileContent)

                name = name.replace('\x00', '')
                name = name.decode('iso-8859-1').encode('utf8')
                freq = "%3.2f" % (float(freq)/100)

                station['name'] = name
                station['freq'] = freq

                stations.append(station)
                fileContent = file.read(26)

            file.close()
            self.fillTable(stations)


    def save_tuner(self):
#        Europe (87-108 MHz)
        if self.ui.radioEurope.isChecked():
            tunerRegion = '\x02'
#        Japan (76-90 MHz)
        elif self.ui.radioJapan.isChecked():
            tunerRegion = '\x01'
#        USA/Korea (87-108 MHz)
        else:
            tunerRegion = '\x00'

        stations = self.readTable()
        tunerHeader = ['\x01', '\x00', tunerRegion, chr(len(stations)), '\x00']

        if len(stations) > 0:

#            from os.path import isfile
            """If no filename then choose one"""
            if not self.filename:
                self.filename = QtGui.QFileDialog.getSaveFileName(self, 'Zapisz plik'.decode('UTF-8'), '.')

            if self.filename:
                file = open(self.filename, mode='wb')

#                Zapisz nagłówek
                for item in tunerHeader:
                    file.write(item)

#                Zapisz stacje
                counter = 0
                for station in stations:
                    stationName = "%s" % ('\x00'.join(station['name']).ljust(20,'\x00'))
                    stationFreq = station['freq']

                    file.write(chr(counter))
                    file.write(stationName)
                    file.write(stationFreq)
                    counter += 1

                file.close()
                self.disable_save()
                QtGui.QMessageBox.information(self, 'Zapisano zmiany'.decode('UTF-8'), 'Zmiany zostały zapisane.'.decode('UTF-8'))
        else:
            QtGui.QMessageBox.information(self, 'Brak stacji'.decode('UTF-8'), 'Brak skonfigurowanych stacji.'.decode('UTF-8'))


    def readTable(self):
        stations = []

#        Liczba wierszy w tabeli
        rowCount = self.ui.stationsList.rowCount()

#        Odczyt wierszy z tabeli
        for row in xrange(0,rowCount):
            station = {'name' : '', 'freq' : ''}

            item = self.ui.stationsList.item(row,1)
            if not item.text() or float(item.text()) == 0:
                continue

            station['name'] = "%s" % self.ui.stationsList.item(row,0).text()[:20].toLatin1()
            station['freq'] = "%05d" % int(float(self.ui.stationsList.item(row,1).text()) * 100)
            stations.append(station)

        return stations


    def fillTable(self, stations):
        self.clearTable()
        row = 0
        for station in stations:
            if float(station['freq']) == 0:
                continue

            self.ui.stationsList.item(row, 0).setText(_translate("Tuner", station['name'], None))
            self.ui.stationsList.item(row, 1).setText(station['freq'])
            row += 1


    def clearTable(self):
        rowCount = self.ui.stationsList.rowCount()
        for row in xrange(0,rowCount):
            self.ui.stationsList.item(row,0).setText('')
            self.ui.stationsList.item(row,1).setText('')


#
#class frequency_delegate(QItemDelegate):
#    def __init__(self, parent=None):
#        super(frequency_delegate, self).__init__(parent)
#    
#    def createEditor(self, parent, option, index):
#        return QProgressBar(parent)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = TunerSettings()
    myapp.show()
    sys.exit(app.exec_())