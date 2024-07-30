# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 14:54:41 2024

@author: Jonathan
"""

import sys
import re

import numpy as np
import pandas as pd
from qtpy import QtCore, QtWidgets, QtGui

from .monitoring.main import Monitor
from .slider import Slider
from .GUI_utilities import setLineEditBackground
from .icons import icons
from ..devices import DEVICES
from ..utilities import data_to_str, str_to_data, clean_string
from ..variables import (VARIABLES, get_variable, set_variable,
                         rename_variable, remove_variable, is_Variable,
                         has_variable, has_eval, eval_variable, EVAL)
from ..devices import get_element_by_address

class VariablesDialog(QtWidgets.QDialog):

    def __init__(self, parent: QtWidgets.QMainWindow, name: str, defaultValue: str):

        super().__init__(parent)
        self.setWindowTitle(name)
        self.setWindowModality(QtCore.Qt.ApplicationModal)  # block GUI interaction

        self.variablesMenu = None
        # ORDER of creation mater to have button OK selected instead of Variables
        variablesButton = QtWidgets.QPushButton('Variables', self)
        variablesButton.clicked.connect(self.variablesButtonClicked)

        hbox = QtWidgets.QHBoxLayout(self)
        hbox.addStretch()
        hbox.addWidget(variablesButton)
        hbox.setContentsMargins(10,0,10,10)

        widget = QtWidgets.QWidget(self)
        widget.setLayout(hbox)

        dialog = QtWidgets.QInputDialog(self)
        dialog.setLabelText(f"Set {name} value")
        dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
        dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.Dialog)

        lineEdit = dialog.findChild(QtWidgets.QLineEdit)
        lineEdit.setMaxLength(10000000)
        dialog.setTextValue(defaultValue)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(dialog)
        layout.addWidget(widget)
        layout.addStretch()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)

        self.exec_ = dialog.exec_
        self.textValue = dialog.textValue
        self.setTextValue = dialog.setTextValue

    def variablesButtonClicked(self):
        if self.variablesMenu is None:
            self.variablesMenu = VariablesMenu(self)
            self.variablesMenu.setWindowTitle(
                self.windowTitle()+": "+self.variablesMenu.windowTitle())

            self.variablesMenu.variableSignal.connect(self.toggleVariableName)
            self.variablesMenu.deviceSignal.connect(self.toggleDeviceName)
            self.variablesMenu.show()
        else:
            self.variablesMenu.refresh()

    def clearVariablesMenu(self):
        """ This clear the variables menu instance reference when quitted """
        self.variablesMenu = None

    def toggleVariableName(self, name):
        value = self.textValue()
        if name in VARIABLES: name += '()'

        if value in ('0', "''"): value = ''
        if not has_eval(value): value = EVAL + value

        if value.endswith(name): value = value[:-len(name)]
        else: value += name

        if value == EVAL: value = ''

        self.setTextValue(value)

    def toggleDeviceName(self, name):
        name += '()'
        self.toggleVariableName(name)

    def closeEvent(self, event):
        for children in self.findChildren(QtWidgets.QWidget):
            children.deleteLater()
        super().closeEvent(event)


class VariablesMenu(QtWidgets.QMainWindow):

    variableSignal = QtCore.Signal(object)
    deviceSignal = QtCore.Signal(object)

    def __init__(self, parent: QtWidgets.QMainWindow = None):

        super().__init__(parent)
        self.gui = parent
        self.setWindowTitle('Variables manager')
        if self.gui is None: self.setWindowIcon(QtGui.QIcon(icons['autolab']))

        self.statusBar = self.statusBar()

        # Main widgets creation
        self.variablesWidget = QtWidgets.QTreeWidget(self)
        self.variablesWidget.setHeaderLabels(
            ['', 'Name', 'Value', 'Evaluated value', 'Type', 'Action'])
        self.variablesWidget.setAlternatingRowColors(True)
        self.variablesWidget.setIndentation(0)
        self.variablesWidget.setStyleSheet(
            "QHeaderView::section { background-color: lightgray; }")
        header = self.variablesWidget.header()
        header.setMinimumSectionSize(20)
        header.resizeSection(0, 20)
        header.resizeSection(1, 90)
        header.resizeSection(2, 120)
        header.resizeSection(3, 120)
        header.resizeSection(4, 50)
        header.resizeSection(5, 100)
        self.variablesWidget.itemDoubleClicked.connect(self.variableActivated)
        self.variablesWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.variablesWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.variablesWidget.customContextMenuRequested.connect(self.rightClick)

        addButton = QtWidgets.QPushButton('Add')
        addButton.clicked.connect(self.addVariableAction)

        removeButton = QtWidgets.QPushButton('Remove')
        removeButton.clicked.connect(self.removeVariableAction)

        self.devicesWidget = QtWidgets.QTreeWidget(self)
        self.devicesWidget.setHeaderLabels(['Name'])
        self.devicesWidget.setAlternatingRowColors(True)
        self.devicesWidget.setIndentation(10)
        self.devicesWidget.setStyleSheet("QHeaderView::section { background-color: lightgray; }")
        self.devicesWidget.itemDoubleClicked.connect(self.deviceActivated)
        self.devicesWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.devicesWidget.customContextMenuRequested.connect(self.rightClickDevice)

        # Main layout creation
        layoutWindow = QtWidgets.QVBoxLayout()
        layoutTab = QtWidgets.QVBoxLayout()
        layoutWindow.addLayout(layoutTab)

        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(layoutWindow)
        self.setCentralWidget(centralWidget)

        refreshButtonWidget = QtWidgets.QPushButton()
        refreshButtonWidget.setText('Refresh Manager')
        refreshButtonWidget.clicked.connect(self.refresh)

        # Main layout definition
        layoutButton = QtWidgets.QHBoxLayout()
        layoutButton.addWidget(addButton)
        layoutButton.addWidget(removeButton)
        layoutButton.addStretch()

        frameVariables = QtWidgets.QFrame()
        layoutVariables = QtWidgets.QVBoxLayout(frameVariables)
        layoutVariables.addWidget(self.variablesWidget)
        layoutVariables.addLayout(layoutButton)

        frameDevices = QtWidgets.QFrame()
        layoutDevices = QtWidgets.QVBoxLayout(frameDevices)
        layoutDevices.addWidget(self.devicesWidget)

        tab = QtWidgets.QTabWidget(self)
        tab.addTab(frameVariables, 'Variables')
        tab.addTab(frameDevices, 'Devices')

        layoutTab.addWidget(tab)
        layoutTab.addWidget(refreshButtonWidget)

        self.resize(550, 300)
        self.refresh()

        self.monitors = {}
        self.sliders = {}
        # self.timer = QtCore.QTimer(self)
        # self.timer.setInterval(400) # ms
        # self.timer.timeout.connect(self.refresh_new)
        # self.timer.start()
        # VARIABLES.removeVarSignal.remove.connect(self.removeVarSignalChanged)
        # VARIABLES.addVarSignal.add.connect(self.addVarSignalChanged)

    def variableActivated(self, item: QtWidgets.QTreeWidgetItem):
        self.variableSignal.emit(item.name)

    def rightClick(self, position: QtCore.QPoint):
        """ Provides a menu where the user right clicked to manage a variable """
        item = self.variablesWidget.itemAt(position)
        if hasattr(item, 'menu'): item.menu(position)

    def rightClickDevice(self, position: QtCore.QPoint):
        """ Provides a menu where the user right clicked to manage a variable """
        item = self.devicesWidget.itemAt(position)
        if hasattr(item, 'menu'): item.menu(position)

    def deviceActivated(self, item: QtWidgets.QTreeWidgetItem):
        if hasattr(item, 'name'): self.deviceSignal.emit(item.name)

    def removeVariableAction(self):
        for variableItem in self.variablesWidget.selectedItems():
            remove_variable(variableItem.name)
            self.removeVariableItem(variableItem)

    # def addVariableItem(self, name):
    #     MyQTreeWidgetItem(self.variablesWidget, name, self)

    def removeVariableItem(self, item: QtWidgets.QTreeWidgetItem):
        index = self.variablesWidget.indexFromItem(item)
        self.variablesWidget.takeTopLevelItem(index.row())

    def addVariableAction(self):
        basename = 'var'
        name = basename
        names = list(VARIABLES)

        compt = 0
        while True:
            if name in names:
                compt += 1
                name = basename + str(compt)
            else:
                break

        variable = set_variable(name, 0)

        MyQTreeWidgetItem(self.variablesWidget, name, variable, self)  # not catched by VARIABLES signal

    # def addVarSignalChanged(self, key, value):
    #     print('got add signal', key, value)
    #     all_items = [self.variablesWidget.topLevelItem(i) for i in range(
    #         self.variablesWidget.topLevelItemCount())]

    #     for variableItem in all_items:
    #         if variableItem.name == key:
    #             variableItem.raw_value = get_variable(variableItem.name)
    #             variableItem.refresh_rawValue()
    #             variableItem.refresh_value()
    #             break
    #     else:
    #         self.addVariableItem(key)
    #     # self.refresh()  # TODO: check if item exists, create if not, update if yes

    # def removeVarSignalChanged(self, key):
    #     print('got remove signal', key)
    #     all_items = [self.variablesWidget.topLevelItem(i) for i in range(
    #         self.variablesWidget.topLevelItemCount())]

    #     for variableItem in all_items:
    #         if variableItem.name == key:
    #             self.removeVariableItem(variableItem)

    #     # self.refresh()  # TODO: check if exists, remove if yes

    def refresh(self):
        self.variablesWidget.clear()
        for var_name in VARIABLES:
            variable = get_variable(var_name)
            MyQTreeWidgetItem(self.variablesWidget, var_name, variable, self)

        self.devicesWidget.clear()
        for device_name in DEVICES:
            device = DEVICES[device_name]
            deviceItem = QtWidgets.QTreeWidgetItem(
                self.devicesWidget, [device_name])
            deviceItem.setBackground(0, QtGui.QColor('#9EB7F5'))  # blue
            deviceItem.setExpanded(True)
            for elements in device.get_structure():
                var = get_element_by_address(elements[0])
                MyQTreeWidgetItem(deviceItem, var.address(), var, self)

    def setStatus(self, message: str, timeout: int = 0, stdout: bool = True):
        """ Modify the message displayed in the status bar and add error message to logger """
        self.statusBar.showMessage(message, timeout)
        if not stdout: print(message, file=sys.stderr)

    def closeEvent(self, event):
        # self.timer.stop()
        if hasattr(self.gui, 'clearVariablesMenu'):
            self.gui.clearVariablesMenu()

        for monitor in list(self.monitors.values()):
            monitor.close()

        for slider in list(self.sliders.values()):
            slider.close()

        for children in self.findChildren(QtWidgets.QWidget):
            children.deleteLater()

        super().closeEvent(event)

        if self.gui is None:
            QtWidgets.QApplication.quit()  # close the variable app

class MyQTreeWidgetItem(QtWidgets.QTreeWidgetItem):

    def __init__(self, itemParent, name, variable, gui):

        self.itemParent = itemParent
        self.gui = gui
        self.name = name
        self.variable = variable

        if is_Variable(self.variable):
            super().__init__(itemParent, ['', name])
        else:
            super().__init__(itemParent, [name])
            return None

        nameWidget = QtWidgets.QLineEdit()
        nameWidget.setText(name)
        nameWidget.setAlignment(QtCore.Qt.AlignCenter)
        nameWidget.returnPressed.connect(self.renameVariable)
        nameWidget.textEdited.connect(lambda: setLineEditBackground(
            nameWidget, 'edited'))
        setLineEditBackground(nameWidget, 'synced')
        self.gui.variablesWidget.setItemWidget(self, 1, nameWidget)
        self.nameWidget = nameWidget

        rawValueWidget = QtWidgets.QLineEdit()
        rawValueWidget.setMaxLength(10000000)
        rawValueWidget.setAlignment(QtCore.Qt.AlignCenter)
        rawValueWidget.returnPressed.connect(self.changeRawValue)
        rawValueWidget.textEdited.connect(lambda: setLineEditBackground(
            rawValueWidget, 'edited'))
        self.gui.variablesWidget.setItemWidget(self, 2, rawValueWidget)
        self.rawValueWidget = rawValueWidget

        valueWidget = QtWidgets.QLineEdit()
        valueWidget.setMaxLength(10000000)
        valueWidget.setReadOnly(True)
        valueWidget.setStyleSheet(
            "QLineEdit {border: 1px solid #a4a4a4; background-color: #f4f4f4}")
        valueWidget.setAlignment(QtCore.Qt.AlignCenter)
        self.gui.variablesWidget.setItemWidget(self, 3, valueWidget)
        self.valueWidget = valueWidget

        typeWidget = QtWidgets.QLabel()
        typeWidget.setAlignment(QtCore.Qt.AlignCenter)
        self.gui.variablesWidget.setItemWidget(self, 4, typeWidget)
        self.typeWidget = typeWidget

        self.actionButtonWidget = None

        self.refresh_rawValue()
        self.refresh_value()

    def menu(self, position: QtCore.QPoint):
        """ This function provides the menu when the user right click on an item """
        menu = QtWidgets.QMenu()
        monitoringAction = menu.addAction("Start monitoring")
        monitoringAction.setIcon(QtGui.QIcon(icons['monitor']))
        monitoringAction.setEnabled(
            (hasattr(self.variable, 'readable')  # Action don't have readable
             and self.variable.readable
             and self.variable.type in (int, float, np.ndarray, pd.DataFrame)
             ) or (
                 is_Variable(self.variable)
                 and (has_eval(self.variable.raw) or isinstance(
                     self.variable.value, (int, float, np.ndarray, pd.DataFrame)))
                 ))

        menu.addSeparator()
        sliderAction = menu.addAction("Create a slider")
        sliderAction.setIcon(QtGui.QIcon(icons['slider']))
        sliderAction.setEnabled(
            (hasattr(self.variable, 'writable')
             and self.variable.writable
             and self.variable.type in (int, float)))

        choice = menu.exec_(self.gui.variablesWidget.viewport().mapToGlobal(position))
        if choice == monitoringAction: self.openMonitor()
        elif choice == sliderAction: self.openSlider()

    def openMonitor(self):
        """ This function open the monitor associated to this variable. """
        # If the monitor is not already running, create one
        if id(self) not in self.gui.monitors:
            self.gui.monitors[id(self)] = Monitor(self)
            self.gui.monitors[id(self)].show()
        # If the monitor is already running, just make as the front window
        else:
            monitor = self.gui.monitors[id(self)]
            monitor.setWindowState(
                monitor.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
            monitor.activateWindow()

    def openSlider(self):
        """ This function open the slider associated to this variable. """
        # If the slider is not already running, create one
        if id(self) not in self.gui.sliders:
            self.gui.sliders[id(self)] = Slider(self.variable, self)
            self.gui.sliders[id(self)].show()
        # If the slider is already running, just make as the front window
        else:
            slider = self.gui.sliders[id(self)]
            slider.setWindowState(
                slider.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
            slider.activateWindow()

    def clearMonitor(self):
        """ This clear monitor instances reference when quitted """
        if id(self) in self.gui.monitors:
            self.gui.monitors.pop(id(self))

    def clearSlider(self):
        """ This clear the slider instances reference when quitted """
        if id(self) in self.gui.sliders:
            self.gui.sliders.pop(id(self))

    def renameVariable(self) -> None:
        new_name = self.nameWidget.text()
        if new_name == self.name:
            setLineEditBackground(self.nameWidget, 'synced')
            return None

        if new_name in VARIABLES:
            self.gui.setStatus(
                f"Error: {new_name} already exist!", 10000, False)
            return None

        new_name = clean_string(new_name)

        try:
            rename_variable(self.name, new_name)
        except Exception as e:
            self.gui.setStatus(f'Error: {e}', 10000, False)
        else:
            self.name = new_name
            new_name = self.nameWidget.setText(self.name)
            setLineEditBackground(self.nameWidget, 'synced')
            self.gui.setStatus('')
        return None

    def refresh_rawValue(self):
        raw_value_str = data_to_str(self.variable.raw)

        self.rawValueWidget.setText(raw_value_str)
        setLineEditBackground(self.rawValueWidget, 'synced')

        if has_variable(self.variable.raw):  # OPTIMIZE: use hide and show instead but doesn't hide on instantiation
            if self.actionButtonWidget is None:
                actionButtonWidget = QtWidgets.QPushButton()
                actionButtonWidget.setText('Update value')
                actionButtonWidget.setMinimumSize(0, 23)
                actionButtonWidget.setMaximumSize(85, 23)
                actionButtonWidget.clicked.connect(self.convertVariableClicked)
                self.gui.variablesWidget.setItemWidget(self, 5, actionButtonWidget)
                self.actionButtonWidget = actionButtonWidget
        else:
            self.gui.variablesWidget.removeItemWidget(self, 5)
            self.actionButtonWidget = None

    def refresh_value(self):
        value = self.variable.value
        value_str = data_to_str(value)

        self.valueWidget.setText(value_str)
        self.typeWidget.setText(str(type(value).__name__))

    def changeRawValue(self):
        name = self.name
        raw_value = self.rawValueWidget.text()
        try:
            if not has_eval(raw_value):
                raw_value = str_to_data(raw_value)
            else:
                # get all variables
                raw_value_check = raw_value[len(EVAL): ]  # Allows variable with name 'eval'
                pattern1 = r'[a-zA-Z][a-zA-Z0-9._]*'
                matches1 = re.findall(pattern1, raw_value_check)
                # get variables not unclosed by ' or " (gives bad name so needs to check with all variables)
                pattern2 = r'(?<!["\'])([a-zA-Z][a-zA-Z0-9._]*)(?!["\'])'
                matches2 = re.findall(pattern2, raw_value_check)
                matches = list(set(matches1) & set(matches2))
                # Add device/variable name to matches
                for match in list(matches):
                    matches.append(match.split('.')[0])
                matches = list(set(matches))
                assert name not in matches, f"Variable '{name}' name can't be used in eval to avoid circular definition"
        except Exception as e:
            self.gui.setStatus(f'Error: {e}', 10000, False)
        else:
            try: set_variable(name, raw_value)
            except Exception as e:
                self.gui.setStatus(f'Error: {e}', 10000)
            else:
                self.refresh_rawValue()
                self.refresh_value()

    def convertVariableClicked(self):
        try: value = eval_variable(self.variable)
        except Exception as e:
            self.gui.setStatus(f'Error: {e}', 10000, False)
        else:
            value_str = data_to_str(value)

            self.valueWidget.setText(value_str)
            self.typeWidget.setText(str(type(value).__name__))
            # self.gui.refresh()  # OPTIMIZE replace by each variable send update signal
