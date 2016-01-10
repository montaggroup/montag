# coding=utf-8
import reisa_window
from PySide import QtCore, QtGui
import os
import re
import sys

import Pyro4

DEFAULT_FIDELITY = 60

from pydb import FileType
from pydb import TomeType


# REISA: RegExImportScannerAssistantToolThingy
class Reisa(QtGui.QMainWindow):
    def __init__(self, db, file_server):
        super(Reisa, self).__init__()
        self.db = db
        self.file_server = file_server
        self.ui = None
        self.dir_name = None
        self.file_list = None
        self.scanned_items = []
        self.author_list_is_comma_separated = True

    def set_initial_path(self, dir_name):
        self.dir_name = dir_name

    def setup_ui(self):
        self.ui = reisa_window.Ui_main_window()
        self.ui.setupUi(self)
        self.ui.regex_input.setText("(?P<author>[^_]+?) - \s*((?P<tag>[^_0-9]+[0-9]+ )-)*-?\s*(?P<title>[^_].+) ?")
        self.connect(self.ui.regex_input, QtCore.SIGNAL("textEdited(QString)"), self.update_table_widget)
        self.connect(self.ui.manual_tags_input, QtCore.SIGNAL("textEdited(QString)"), self.update_table_widget)
        self.connect(self.ui.author_list_comma_checkbox, QtCore.SIGNAL("clicked()"), self.update_table_widget)
        self.connect(self.ui.go_button, QtCore.SIGNAL("clicked()"), self.go_button_clicked)
        self.connect(self.ui.directory_button, QtCore.SIGNAL("clicked()"), self.directory_button_clicked)
        self.ui.go_button.setEnabled(False)
        if self.dir_name is not None:
            self.parse_folder()

    def insert_item(self, item):
        authors = item['author']

        if not authors:
            raise Exception("No authors for item %s" % repr(item))

        title = item['title']
        if not title:
            raise Exception("No title for item %s" % repr(item))

        language = self.ui.language_box.currentText()
        tome_type = TomeType.Fiction

        if self.ui.nonfic_radio_button.isChecked():
            tome_type = TomeType.NonFiction

        file_path = os.path.join(self.dir_name, item['filename'])

        print "Inserting: %s" % file_path

        author_ids = self.db.find_or_create_authors(list(authors), fidelity=DEFAULT_FIDELITY)

        tome_id = self.db.find_or_create_tome(title, language, author_ids, None, tome_type=tome_type,
                                              fidelity=DEFAULT_FIDELITY)

        # \todo the file might already be linked to another tome,
        # that ain't generic or completely different - we should handle that
        base, extension = os.path.splitext(file_path)
        extension = extension[1:]  # remove period

        (file_id, file_hash, size) = self.file_server.add_file_from_local_disk(file_path, extension, move_file=True)
        if file_id:
            self.db.link_tome_to_file(tome_id, file_hash, size, file_extension=extension, file_type=FileType.Content,
                                      fidelity=DEFAULT_FIDELITY)
        if item['tags']:
            self.db.add_tags_to_tome(tome_id, item['tags'], fidelity=DEFAULT_FIDELITY)

    def go_button_clicked(self):
        self.ui.table_widget.sortByColumn(3, QtCore.Qt.AscendingOrder)
        # noinspection PyArgumentList
        QtGui.QApplication.processEvents()
        for f in self.scanned_items:
            self.insert_item(f)
            self.parse_folder(do_resize=False)
            # noinspection PyArgumentList
            QtGui.QApplication.processEvents()

    def directory_button_clicked(self):
        # noinspection PyCallByClass
        self.dir_name = QtGui.QFileDialog.getExistingDirectory(self, 'Open file', r'.')
        self.parse_folder()

    def parse_folder(self, do_resize=True):
        # noinspection PyCallByClass,PyTypeChecker
        self.setWindowTitle(QtGui.QApplication.translate("main_window", "RegExImportScannerAssistant: %s", None,
                                                         QtGui.QApplication.UnicodeUTF8) % self.dir_name)
        self.file_list = os.listdir(self.dir_name)
        self.update_table_widget(do_resize=do_resize)

    def update_table_widget(self, do_resize=True):
        if self.ui.author_list_comma_checkbox.isChecked():
            self.author_list_is_comma_separated = True
        else:
            self.author_list_is_comma_separated = False

        manual_tag_string = self.ui.manual_tags_input.text().strip()
        manual_tags = []
        if manual_tag_string:
            manual_tags = manual_tag_string.split(',')
        self.scanned_items = apply_regex(self.file_list, self.ui.regex_input.text(),
                                         self.author_list_is_comma_separated, manual_tags)
        self.ui.table_widget.clearContents()
        self.ui.table_widget.setSortingEnabled(False)
        for row in range(self.ui.table_widget.rowCount()):
            self.ui.table_widget.removeRow(0)
        for item in self.scanned_items:
            self.ui.table_widget.insertRow(0)
            author_info = ', '.join(item['author']) + " ({})".format(len(item['author']))

            self.ui.table_widget.setItem(0, 0, QtGui.QTableWidgetItem(author_info))
            self.ui.table_widget.setItem(0, 1, QtGui.QTableWidgetItem(item['title']))
            self.ui.table_widget.setItem(0, 2, QtGui.QTableWidgetItem(",".join(item['tags'])))
            self.ui.table_widget.setItem(0, 3, QtGui.QTableWidgetItem(item['filename']))
        self.ui.table_widget.setSortingEnabled(True)
        if do_resize:
            self.ui.table_widget.resizeColumnsToContents()
        self.ui.lcd_number.display(self.ui.table_widget.rowCount())
        self.ui.go_button.setEnabled(True)


def apply_regex(file_list, regex, author_list_is_comma_separated, manual_tags=list()):
    def strip_if_exists(a):
        if a:
            return a.strip()
        return a

    # print file_list
    result = []
    for filename in file_list:
        fn, ext = os.path.splitext(filename)
        m = re.match(regex, fn)
        if m:
            tags = []
            tag = strip_if_exists(m.group('tag'))
            if tag:
                tags.append(tag)
            tags = tags + manual_tags

            item = {
                "author": set(author_list_generator(m.group('author'), author_list_is_comma_separated)),
                "title": m.group('title').strip(),
                "tags": tags,
                "filename": filename
            }
            print "a_r: item=%s" % repr(item)
            result.append(item)
    return result


def author_list_generator(author_string, author_list_is_comma_separated):
    author_string = author_string.replace(' u ', '&')

    if author_list_is_comma_separated:
        for name in author_string.split(','):
            yield name.strip()
    else:
        for name in author_string.split('&'):
            name = swap_name_parts(name)
            yield name.strip()


def swap_name_parts(name):
    if ',' in name:
        a, b = name.split(',', 1)
        name = b.strip() + ' ' + a.strip()
    return name.strip()


def launch_reisa():
    # noinspection PyUnresolvedReferences
    sys.excepthook = Pyro4.util.excepthook
    from .. import pyrosetup

    db = pyrosetup.pydbserver()

    if db.ping() != "pong":
        print >> sys.stderr, "Unable to talk to server, is it running?`"
        sys.exit(-1)

    file_server = pyrosetup.fileserver()

    app = QtGui.QApplication(sys.argv)

    # noinspection PyArgumentList
    cmdline_args = QtCore.QCoreApplication.arguments()
    ui = Reisa(db, file_server)
    print "args:", cmdline_args
    cmdline_args = cmdline_args[1:]
    if cmdline_args:
        if "reisa.py" in cmdline_args[0]:  # quick fix for windows, here we have command line starting with the python file
            cmdline_args = cmdline_args[1:]
        ui.set_initial_path(os.path.abspath(cmdline_args[0]))

    ui.setup_ui()
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    launch_reisa()
