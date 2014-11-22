# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'reisa_window.ui'
#
# Created: Wed Dec 25 18:18:48 2013
# by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui


# noinspection PyAttributeOutsideInit,PyShadowingNames
class Ui_main_window(object):
    def setupUi(self, main_window_):
        main_window_.setObjectName("main_window")
        main_window_.resize(800, 622)
        self.centralwidget = QtGui.QWidget(main_window_)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.regex_input = QtGui.QLineEdit(self.centralwidget)
        self.regex_input.setObjectName("regex_input")
        self.horizontalLayout_2.addWidget(self.regex_input)
        self.directory_button = QtGui.QPushButton(self.centralwidget)
        self.directory_button.setObjectName("directory_button")
        self.horizontalLayout_2.addWidget(self.directory_button)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.table_widget = QtGui.QTableWidget(self.centralwidget)
        self.table_widget.setObjectName("table_widget")
        self.table_widget.setColumnCount(4)
        self.table_widget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(3, item)
        self.verticalLayout_3.addWidget(self.table_widget)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.fiction_radio_button = QtGui.QRadioButton(self.centralwidget)
        self.fiction_radio_button.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.fiction_radio_button.setChecked(True)
        self.fiction_radio_button.setObjectName("fiction_radio_button")
        self.verticalLayout_2.addWidget(self.fiction_radio_button)
        self.nonfic_radio_button = QtGui.QRadioButton(self.centralwidget)
        self.nonfic_radio_button.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.nonfic_radio_button.setObjectName("nonfic_radio_button")
        self.verticalLayout_2.addWidget(self.nonfic_radio_button)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_3 = QtGui.QLabel(self.centralwidget)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3)
        spacerItem = QtGui.QSpacerItem(20, 30, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        self.verticalLayout.addItem(spacerItem)
        self.language_box = QtGui.QComboBox(self.centralwidget)
        self.language_box.setObjectName("language_box")
        self.language_box.addItem("")
        self.language_box.addItem("")
        self.verticalLayout.addWidget(self.language_box)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.label_4 = QtGui.QLabel(self.centralwidget)
        self.label_4.setObjectName("label_4")

        self.horizontalLayout.addWidget(self.label_4)
        self.manual_tags_input = QtGui.QLineEdit(self.centralwidget)
        self.manual_tags_input.setObjectName("manual_tags_input")
        self.horizontalLayout.addWidget(self.manual_tags_input)

        self.label_5 = QtGui.QLabel(self.centralwidget)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout.addWidget(self.label_5)
        self.author_list_comma_checkbox = QtGui.QCheckBox(self.centralwidget)
        self.author_list_comma_checkbox.setObjectName("author_list_comma_checkbox")
        self.horizontalLayout.addWidget(self.author_list_comma_checkbox)

        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.lcd_number = QtGui.QLCDNumber(self.centralwidget)
        self.lcd_number.setObjectName("lcd_number")
        self.horizontalLayout.addWidget(self.lcd_number)
        self.go_button = QtGui.QPushButton(self.centralwidget)
        self.go_button.setMinimumSize(QtCore.QSize(0, 40))
        self.go_button.setObjectName("go_button")
        self.horizontalLayout.addWidget(self.go_button)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        main_window_.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(main_window_)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        main_window_.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(main_window_)
        self.statusbar.setObjectName("statusbar")
        main_window_.setStatusBar(self.statusbar)

        self.retranslateUi(main_window_)
        QtCore.QMetaObject.connectSlotsByName(main_window_)

    # noinspection PyCallByClass
    def retranslateUi(self, main_window):
        main_window.setWindowTitle(
            QtGui.QApplication.translate("main_window", "RegExImportScannerAssistantToolThingy: no path set yet", None,
                                         QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("main_window", "Regex:", None, QtGui.QApplication.UnicodeUTF8))
        self.regex_input.setText(
            QtGui.QApplication.translate("main_window", "fdf", None, QtGui.QApplication.UnicodeUTF8))
        self.directory_button.setText(
            QtGui.QApplication.translate("main_window", "Directory", None, QtGui.QApplication.UnicodeUTF8))
        self.table_widget.horizontalHeaderItem(0).setText(
            QtGui.QApplication.translate("main_window", "Author(s)", None, QtGui.QApplication.UnicodeUTF8))
        self.table_widget.horizontalHeaderItem(1).setText(
            QtGui.QApplication.translate("main_window", "Title", None, QtGui.QApplication.UnicodeUTF8))
        self.table_widget.horizontalHeaderItem(2).setText(
            QtGui.QApplication.translate("main_window", "Tag", None, QtGui.QApplication.UnicodeUTF8))
        self.table_widget.horizontalHeaderItem(3).setText(
            QtGui.QApplication.translate("main_window", "Filename", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(
            QtGui.QApplication.translate("main_window", "Tome type:", None, QtGui.QApplication.UnicodeUTF8))
        self.fiction_radio_button.setText(
            QtGui.QApplication.translate("main_window", "fiction", None, QtGui.QApplication.UnicodeUTF8))
        self.nonfic_radio_button.setText(
            QtGui.QApplication.translate("main_window", "non-fiction", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(
            QtGui.QApplication.translate("main_window", "Language:", None, QtGui.QApplication.UnicodeUTF8))
        self.language_box.setItemText(0, QtGui.QApplication.translate("main_window", "de", None,
                                                                      QtGui.QApplication.UnicodeUTF8))
        self.language_box.setItemText(1, QtGui.QApplication.translate("main_window", "en", None,
                                                                      QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("main_window", "Add tags manually (comma separated):", None,
                                                          QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("main_window", "Assume comma separated author names", None,
                                                          QtGui.QApplication.UnicodeUTF8))
        self.go_button.setText(QtGui.QApplication.translate("main_window", "Go!", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    main_window = QtGui.QMainWindow()
    ui = Ui_main_window()
    ui.setupUi(main_window)
    main_window.show()
    sys.exit(app.exec_())

