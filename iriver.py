#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import struct
from PyQt4 import QtCore, QtGui
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

        # sloty i sygnaly
        # wczytaj plik
#        QtCore.QObject.connect(self.ui.loadButton,QtCore.SIGNAL("clicked()"),self.file_dialog)
        self.ui.loadButton.clicked.connect(self.file_dialog)
        # zapisz plik
#        QtCore.QObject.connect(self.ui.saveButton,QtCore.SIGNAL("clicked()"),self.save_tuner)
        self.ui.saveButton.clicked.connect(self.save_tuner)
#        zmieniono komórkę w tabeli
#        QtCore.QObject.connect(self.ui.stationsList,QtCore.SIGNAL("itemChanged(QTableWidgetItem*)"),self.enable_save)
        self.ui.stationsList.itemChanged.connect(self.enable_save)
        self.ui.radioUSA.clicked.connect(self.enable_save)
        self.ui.radioJapan.clicked.connect(self.enable_save)
        self.ui.radioEurope.clicked.connect(self.enable_save)


    def enable_save(self):
        self.ui.saveButton.setEnabled(True)

    def disable_save(self):
        self.ui.saveButton.setEnabled(False)

        
    def file_dialog(self):
        response = False
        
        SAVE = 'Zapisz'
        DISCARD = 'Porzuć'.decode('UTF-8')
        CANCEL = 'Anuluj'
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

        self.filename = QtGui.QFileDialog.getOpenFileName(self, 'Wczytaj plik', '.')

        from os.path import isfile
        if isfile(self.filename):
            file = open(self.filename, mode='rb')

            fileContent = file.read(5)
            header = struct.unpack("5b", fileContent)

        # Ustawiony w nagłówku region
            if header[2] == 0:
#                    print "USA/Korea (87-108 MHz)"
                self.ui.radioUSA.setChecked(True)
                minFreq = 87
                maxFreq = 108
            elif header[2] == 1:
#                    print "Japan (76-90 MHz)"
                self.ui.radioJapan.setChecked(True)
                minFreq = 76
                maxFreq = 90
            elif header[2] == 2:
#                    print "Europe (87-108 MHz)"
                self.ui.radioEurope.setChecked(True)
                minFreq = 87
                maxFreq = 108
            else:
#                    print "Nieznany (%d)" % (header[2])
                QtGui.QMessageBox.warning(self, "Region", "Nieprawidłowy region.".decode('UTF-8'))

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
        if self.ui.radioEurope.isChecked():
            tunerRegion = '\x02'
        elif self.ui.radioJapan.isChecked():
            tunerRegion = '\x01'
        else:
            tunerRegion = '\x00'

        stations = self.readTable()
        tunerHeader = ['\x01', '\x00', tunerRegion, chr(len(stations)), '\x00']

        if len(stations) > 0:
            from os.path import isfile

#            print "Zapisz do: %s" + self.filename

            if not self.filename:
                self.filename = QtGui.QFileDialog.getSaveFileName(self, 'Zapisz plik', '.')

            file = open(self.filename, mode='wb')

#            Zapisz nagłówek
            for item in tunerHeader:
                file.write(item)

#            Zapisz stacje
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
        else:
            QtGui.QMessageBox.information(self, "Brak stacji", "Brak skonfigurowanych stacji.")
        
        
#        print "Nagłówek:"
#        print tunerHeader
#        print "Dane:"
#        print stations
#        print '*' * 80


    def fillTable(self, stations):
        row = 0
        for station in stations:
            if float(station['freq']) == 0:
                continue

            self.ui.stationsList.item(row, 0).setText(_translate("Tuner", station['name'], None))
#            self.ui.stationsList.item(row, 0).setText(station['name'])
            self.ui.stationsList.item(row, 1).setText(station['freq'])
            row += 1


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

            #print "%d - %05d" % (row, int(float(self.ui.stationsList.item(row,1).text()) *100))
            station['name'] = "%s" % self.ui.stationsList.item(row,0).text()[:20].toLatin1()
            station['freq'] = "%05d" % int(float(self.ui.stationsList.item(row,1).text()) * 100)
            stations.append(station)

        return stations


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = TunerSettings()
    myapp.show()
    sys.exit(app.exec_())