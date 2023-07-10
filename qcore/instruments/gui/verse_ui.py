# Form implementation generated from reading ui file 'c:\Users\athar\src\qcore\qcore\instruments\gui\verse.ui'
#
# Created by: PyQt6 UI code generator 6.5.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_verse(object):
    def setupUi(self, verse):
        verse.setObjectName("verse")
        verse.resize(900, 412)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(verse.sizePolicy().hasHeightForWidth())
        verse.setSizePolicy(sizePolicy)
        verse.setMinimumSize(QtCore.QSize(900, 300))
        self.verticalLayout = QtWidgets.QVBoxLayout(verse)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verse_tabs = QtWidgets.QTabWidget(parent=verse)
        self.verse_tabs.setTabShape(QtWidgets.QTabWidget.TabShape.Rounded)
        self.verse_tabs.setTabsClosable(True)
        self.verse_tabs.setMovable(True)
        self.verse_tabs.setObjectName("verse_tabs")
        self.server_tab = QtWidgets.QWidget()
        self.server_tab.setObjectName("server_tab")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.server_tab)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.server_tab_layout = QtWidgets.QHBoxLayout()
        self.server_tab_layout.setContentsMargins(5, 5, 5, 5)
        self.server_tab_layout.setSpacing(5)
        self.server_tab_layout.setObjectName("server_tab_layout")
        self.instrument_types_layout = QtWidgets.QVBoxLayout()
        self.instrument_types_layout.setContentsMargins(5, 5, 5, 5)
        self.instrument_types_layout.setSpacing(5)
        self.instrument_types_layout.setObjectName("instrument_types_layout")
        self.instrument_types_label = QtWidgets.QLabel(parent=self.server_tab)
        self.instrument_types_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.instrument_types_label.setObjectName("instrument_types_label")
        self.instrument_types_layout.addWidget(self.instrument_types_label)
        self.instrument_types_list = QtWidgets.QListWidget(parent=self.server_tab)
        self.instrument_types_list.setObjectName("instrument_types_list")
        self.instrument_types_layout.addWidget(self.instrument_types_list)
        self.server_tab_layout.addLayout(self.instrument_types_layout)
        self.instrument_ids_layout = QtWidgets.QVBoxLayout()
        self.instrument_ids_layout.setContentsMargins(5, 5, 5, 5)
        self.instrument_ids_layout.setSpacing(5)
        self.instrument_ids_layout.setObjectName("instrument_ids_layout")
        self.instrument_ids_label = QtWidgets.QLabel(parent=self.server_tab)
        self.instrument_ids_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.instrument_ids_label.setObjectName("instrument_ids_label")
        self.instrument_ids_layout.addWidget(self.instrument_ids_label)
        self.instrument_ids_list = QtWidgets.QListWidget(parent=self.server_tab)
        self.instrument_ids_list.setObjectName("instrument_ids_list")
        self.instrument_ids_layout.addWidget(self.instrument_ids_list)
        self.server_tab_layout.addLayout(self.instrument_ids_layout)
        self.stage_buttons_layout = QtWidgets.QVBoxLayout()
        self.stage_buttons_layout.setContentsMargins(5, 5, 5, 5)
        self.stage_buttons_layout.setSpacing(5)
        self.stage_buttons_layout.setObjectName("stage_buttons_layout")
        self.stage_button = QtWidgets.QPushButton(parent=self.server_tab)
        self.stage_button.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stage_button.sizePolicy().hasHeightForWidth())
        self.stage_button.setSizePolicy(sizePolicy)
        self.stage_button.setObjectName("stage_button")
        self.stage_buttons_layout.addWidget(self.stage_button)
        self.unstage_button = QtWidgets.QPushButton(parent=self.server_tab)
        self.unstage_button.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.unstage_button.sizePolicy().hasHeightForWidth())
        self.unstage_button.setSizePolicy(sizePolicy)
        self.unstage_button.setObjectName("unstage_button")
        self.stage_buttons_layout.addWidget(self.unstage_button)
        self.server_tab_layout.addLayout(self.stage_buttons_layout)
        self.staged_instruments_layout = QtWidgets.QVBoxLayout()
        self.staged_instruments_layout.setContentsMargins(5, 5, 5, 5)
        self.staged_instruments_layout.setSpacing(5)
        self.staged_instruments_layout.setObjectName("staged_instruments_layout")
        self.staged_instruments_label = QtWidgets.QLabel(parent=self.server_tab)
        self.staged_instruments_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.staged_instruments_label.setObjectName("staged_instruments_label")
        self.staged_instruments_layout.addWidget(self.staged_instruments_label)
        self.staged_instruments_list = QtWidgets.QListWidget(parent=self.server_tab)
        self.staged_instruments_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        self.staged_instruments_list.setObjectName("staged_instruments_list")
        self.staged_instruments_layout.addWidget(self.staged_instruments_list)
        self.server_tab_layout.addLayout(self.staged_instruments_layout)
        self.serve_button_layout = QtWidgets.QVBoxLayout()
        self.serve_button_layout.setContentsMargins(5, 5, 5, 5)
        self.serve_button_layout.setSpacing(20)
        self.serve_button_layout.setObjectName("serve_button_layout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.serve_button_layout.addItem(spacerItem)
        self.serve_button = QtWidgets.QPushButton(parent=self.server_tab)
        self.serve_button.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.serve_button.sizePolicy().hasHeightForWidth())
        self.serve_button.setSizePolicy(sizePolicy)
        self.serve_button.setObjectName("serve_button")
        self.serve_button_layout.addWidget(self.serve_button)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.serve_button_layout.addItem(spacerItem1)
        self.serve_button_layout.setStretch(0, 3)
        self.serve_button_layout.setStretch(1, 2)
        self.serve_button_layout.setStretch(2, 3)
        self.server_tab_layout.addLayout(self.serve_button_layout)
        self.server_tab_layout.setStretch(1, 4)
        self.server_tab_layout.setStretch(2, 1)
        self.server_tab_layout.setStretch(3, 4)
        self.server_tab_layout.setStretch(4, 3)
        self.verticalLayout_2.addLayout(self.server_tab_layout)
        self.verse_tabs.addTab(self.server_tab, "")
        self.verticalLayout.addWidget(self.verse_tabs)
        self.message_box = QtWidgets.QTextEdit(parent=verse)
        self.message_box.setReadOnly(True)
        self.message_box.setObjectName("message_box")
        self.verticalLayout.addWidget(self.message_box)
        self.verticalLayout.setStretch(0, 2)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(verse)
        self.verse_tabs.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(verse)

    def retranslateUi(self, verse):
        _translate = QtCore.QCoreApplication.translate
        verse.setWindowTitle(_translate("verse", "Verse"))
        self.instrument_types_label.setText(_translate("verse", "Select instrument type"))
        self.instrument_ids_label.setText(_translate("verse", "Select instrument ID"))
        self.stage_button.setText(_translate("verse", "Stage"))
        self.unstage_button.setText(_translate("verse", "Unstage"))
        self.staged_instruments_label.setText(_translate("verse", "Staged instrument(s)"))
        self.serve_button.setText(_translate("verse", "Serve instrument(s)"))
        self.verse_tabs.setTabText(self.verse_tabs.indexOf(self.server_tab), _translate("verse", "Server"))
        self.message_box.setPlaceholderText(_translate("verse", "Message log"))
