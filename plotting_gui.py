import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QScrollArea, QPushButton,
                             QHBoxLayout, QCheckBox, QFileDialog, QSizePolicy, QDialog, QDialogButtonBox, QLabel,
                             QLineEdit, QMessageBox, QListWidget, QListWidgetItem, QShortcut)
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QScreen, QKeySequence
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
import pandas as pd

from matplotlib import rcParams

# Set the font family
rcParams['font.family'] = 'Tahoma'


class ImportDialog(QDialog):
    """Dialog to select columns for importing graphs."""
    def __init__(self, column_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Select Window')
        self.selected_columns = []

        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Add Select All and Unselect All buttons at the top
        button_layout = QHBoxLayout()
        self.select_all_button = QPushButton('Select All')
        self.select_all_button.clicked.connect(self.select_all)

        self.unselect_all_button = QPushButton('Unselect All')
        self.unselect_all_button.clicked.connect(self.unselect_all)

        self.separate = QCheckBox('Separate', self)
        
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.unselect_all_button)
        button_layout.addWidget(self.separate)
        self.layout.addLayout(button_layout)

        # Label for checkboxes
        self.label = QLabel('Select Columns to Plot:')
        self.layout.addWidget(self.label)

        # Scroll area for checkboxes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)

        self.checkboxes = []
        for col_name in column_names:
            checkbox = QCheckBox(col_name, self)
            self.checkboxes.append(checkbox)
            self.scroll_layout.addWidget(checkbox)

        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

        # Add OK/Cancel buttons at the bottom
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def select_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def unselect_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def get_selected_columns(self):
        """Return a list of selected columns."""
        self.selected_columns = [cb.text() for cb in self.checkboxes if cb.isChecked()]
        return self.separate.isChecked(), self.selected_columns


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=2, dpi=100, index=1, title=None):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_title(title)
        super(PlotCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.index = index
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def plot(self, title=None):
        # Set the number of data points
        num_points = 100

        # Generate random x values between 0 and 100
        x = np.random.uniform(0, 100, num_points)

        # Generate random y values between 0 and 50
        y = np.random.uniform(0, 50, num_points)
        self.axes.plot(x, y, label=f"Graph {self.index}")
        self.axes.legend()
        # self.axes.set_title(title if title else f"Plot {self.index} with Random Data")
        self.axes.grid(True)
        self.draw()

    def add_plot_data(self, x, y, label=None):
        self.axes.plot(x, y, label=label)
        self.axes.legend()
        self.axes.grid(True)
        self.draw()

    def show_in_new_window(self):
        """Display the current plot in a new window."""
        new_window = QMainWindow()
        new_window.setWindowTitle(f"Plot {self.index}")

        # Create a widget and layout for the new window
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Create a new canvas for the plot
        new_canvas = FigureCanvas(self.fig)
        layout.addWidget(new_canvas)
        new_canvas.draw()

        # Set the widget as the central widget of the new window
        new_window.setCentralWidget(widget)
        new_window.resize(800, 600)  # Adjust the size if needed
        new_window.show()


class MainWindow(QMainWindow):
    """Main window to hold the dynamic graphing UI with combine and import functionality."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic Graph Plotter")

        # Set the window size to half the display resolution
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        self.resize(3 * screen.width() // 4, 3 * screen.height() // 4)

        # Main widget container
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Main layout (horizontal) to hold the left-side controls and right-side scroll area
        self.main_layout = QHBoxLayout(self.main_widget)

        # Left-side layout for buttons and checkboxes
        self.left_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout)

        # Scroll area for graphs
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)

        # Add the scroll area to the right side of the main layout
        self.main_layout.addWidget(self.scroll_area)

        # Buttons and checkboxes
        self.btn_add = QPushButton('Add Graph', self)
        self.btn_delete = QPushButton('Delete Selected Graphs', self)
        self.btn_combine = QPushButton('Combine Selected Graphs', self)
        self.btn_import = QPushButton('Import from File', self)
        self.select_all = QCheckBox('Select All', self)

        self.btn_add.clicked.connect(self.add_graph)
        self.btn_delete.clicked.connect(self.delete_selected_graphs)
        self.btn_combine.clicked.connect(self.combine_selected_graphs)
        self.btn_import.clicked.connect(self.import_from_file)
        self.select_all.stateChanged.connect(self.select_all_fcn)

        # Add buttons and checkbox to the left-side layout
        self.left_layout.addWidget(self.btn_add)
        self.left_layout.addWidget(self.btn_delete)
        self.left_layout.addWidget(self.btn_combine)
        self.left_layout.addWidget(self.btn_import)
        self.left_layout.addWidget(self.select_all)
        self.left_layout.addStretch()  # Push buttons to the top

        # Keep track of the number of graphs added and checkboxes
        self.graph_count = 0
        self.graphs = []
        self.checkboxes = []
        self.layouts = []

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Keyboard shortcuts
        QShortcut(QKeySequence('Ctrl+A'), self, self.select_all_fcn_shortcut)
        QShortcut(QKeySequence('Ctrl+N'), self, self.add_graph)
        QShortcut(QKeySequence('Ctrl+D'), self, self.delete_selected_graphs)
        QShortcut(QKeySequence('Ctrl+I'), self, self.import_from_file)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith('.csv'):
                self.handle_file(file_path)
            else:
                self.warning_popup("Only CSV files are supported.")
                
    def handle_file(self, file_path):
        try:
            data = pd.read_csv(file_path)
            y_columns = data.columns[1:]
        except Exception as e:
            self.warning_popup(f"Failed to read file: {str(e)}")
            return
        
        # Create and show the import dialog to select columns
        dialog = ImportDialog(y_columns, self)
        if dialog.exec_() == QDialog.Accepted:
            separate, selected_columns = dialog.get_selected_columns()
            if not selected_columns:
                print("No columns selected.")
                self.warning_popup("No columns selected")
                return
            if separate:
                for column in selected_columns:
                    self.add_graph(data=data, selected=[column])
            else:
                # Create a new plot with the selected columns
                self.add_graph(data=data, selected=selected_columns)

    def select_all_fcn_shortcut(self):
        self.select_all.setChecked(True)
        self.select_all_fcn()

    def select_all_fcn(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(self.select_all.isChecked())

    def add_graph(self, data=None, selected=None, selected_graphs=None):
        """Add a new plot, optionally combining multiple selected plots."""
        self.graph_count += 1  # Increment the graph counter
        canvas = PlotCanvas(self, width=5, height=2, index=self.graph_count)  # Create a new graph canvas
        toolbar = NavigationToolbar(canvas, self)  # Create a toolbar for the graph
        toolbar.setFixedHeight(30)  # Fix the height of the toolbar

        self.change_flag = False
        # Create a checkbox to select this graph
        checkbox = QCheckBox(f"Plot number {self.graph_count}", self)
        
        # Create input fields for width and height
        width_input = QLineEdit(self)
        width_input.setPlaceholderText("Width")
        width_input.setFixedWidth(60)
        
        height_input = QLineEdit(self)
        height_input.setPlaceholderText("Height")
        height_input.setFixedWidth(60)
        
        # Create "Apply" and "Reset" buttons
        apply_button = QPushButton('Apply', self)
        reset_button = QPushButton('Reset', self)

        # Function to apply the new dimensions to the canvas
        def apply_size():
            try:
                new_width = float(width_input.text())
                new_height = float(height_input.text())
                dpi = canvas.figure.get_dpi()
                canvas.setFixedSize(int(new_width * dpi), int(new_height * dpi))  # Assuming width and height are in inches
                self.change_flag = True
            except ValueError:
                self.change_flag = False
                self.warning_popup("Invalid input for width or height.")


        # Function to reset the input fields
        def reset_size():
            if self.change_flag:
                nonlocal canvas, toolbar  # Use the current canvas and toolbar in this function's scope
                
                # Create a new canvas with the original size
                new_canvas = PlotCanvas(self, width=5, height=2, index=self.graph_count)
                
                # Copy all existing lines (plot data) from the old canvas to the new one
                for line in canvas.axes.get_lines():
                    x = line.get_xdata()
                    y = line.get_ydata()
                    label = line.get_label()
                    new_canvas.add_plot_data(x, y, label=label)
                
                # Create a new toolbar for the new canvas
                new_toolbar = NavigationToolbar(new_canvas, self)
                new_toolbar.setFixedHeight(30)
                
                # Remove old canvas and toolbar from the layout
                graph_layout.removeWidget(canvas)
                canvas.setParent(None)
                graph_layout.removeWidget(toolbar)
                toolbar.setParent(None)

                # Add the new toolbar and canvas to the layout
                graph_layout.insertWidget(1, new_toolbar)  # Insert toolbar at index 1
                graph_layout.insertWidget(2, new_canvas)   # Insert canvas at index 2

                # Update the self.graphs list with the new canvas and toolbar
                for i, (existing_canvas, _) in enumerate(self.graphs):
                    if existing_canvas == canvas:
                        self.graphs[i] = (new_canvas, new_toolbar)
                        break
                
                # Replace the old canvas and toolbar references with the new ones
                canvas = new_canvas
                toolbar = new_toolbar

                # Clear the input fields
                width_input.clear()
                height_input.clear()
                self.change_flag = False


        # Connect the buttons to their respective functions
        apply_button.clicked.connect(apply_size)
        reset_button.clicked.connect(reset_size)


        if selected_graphs is not None:
            # Combine multiple selected plots
            for graph in selected_graphs:
                for line in graph.axes.get_lines():
                    x = line.get_xdata()
                    y = line.get_ydata()
                    label = line.get_label()
                    # Add each line's data to the new combined plot
                    canvas.add_plot_data(x, y, label=f"{label} from plot {graph.index}")  # Assuming graph has an index attribute

        elif data is not None and selected is not None:
            # Original functionality: Add a new plot based on provided data and selected columns
            x = data.iloc[:, 0]
            for y_col in selected:
                y = data[y_col]
                canvas.add_plot_data(x, y, label=y_col)

        else:
            canvas.plot()
        
        # Combine the checkbox, width/height inputs, and buttons into a single layout
        control_layout = QHBoxLayout()
        control_layout.addWidget(checkbox)
        control_layout.addWidget(QLabel(" w:"))
        control_layout.addWidget(width_input)
        control_layout.addWidget(QLabel("h:"))
        control_layout.addWidget(height_input)
        control_layout.addWidget(apply_button)
        control_layout.addWidget(reset_button)
        control_layout.setSpacing(5) 
        control_layout.addStretch()

        # Combine toolbar and canvas into a vertical layout
        graph_layout = QVBoxLayout()
        graph_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around the layout
        graph_layout.setSpacing(5)  # Set consistent spacing between elements
        graph_layout.addLayout(control_layout)  # Add the control layout to the top of the graph's layout
        graph_layout.addWidget(toolbar)
        graph_layout.addWidget(canvas)
        graph_layout.addStretch()

        # Create a widget to contain this layout
        graph_widget = QWidget()
        graph_widget.setLayout(graph_layout)

        # Add this widget to the scroll layout
        self.scroll_layout.addWidget(graph_widget)

        # Keep track of the graph canvas, toolbar, checkbox, and layout
        self.graphs.append((canvas, toolbar))
        self.checkboxes.append(checkbox)
        self.layouts.append(graph_layout)


    def apply_size(self, canvas, width_input, height_input):
        """Apply the new width and height to the canvas."""
        try:
            new_width = float(width_input.text())
            new_height = float(height_input.text())
            canvas.figure.set_size_inches(new_width, new_height)
            self.update_canvas_size(canvas)
            canvas.draw()
        except ValueError:
            print("Invalid input for width or height.")
        
    def reset_size(self, canvas):
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def update_canvas_size(self, canvas):
        """Update the canvas size based on the figure's DPI."""
        width, height = 20, 20 #canvas.figure.get_size_inches()
        dpi = canvas.figure.get_dpi()
        canvas.setFixedSize(int(width * dpi), int(height * dpi))

    def warning_popup(self, message):
        """Show a warning popup with OK and Cancel options."""
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Warning")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        return msg_box.exec_()

    def combine_selected_graphs(self):
        """Combine selected graphs by overlaying their lines onto one graph."""
        selected_graphs = [self.graphs[i][0] for i, checkbox in enumerate(self.checkboxes) if checkbox.isChecked()]

        if len(selected_graphs) < 2:
            print("Need to select at least 2 plots.")
            self.warning_popup("You need to select at least 2 plots!")
            return  # Need at least two graphs to combine

        self.add_graph(None, None, selected_graphs)
        self.select_all.setChecked(False)
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def delete_selected_graphs(self):
        """Delete selected graphs with a warning popup."""
        selected_to_delete = [
            self.checkboxes[i].text()
            for i in range(len(self.checkboxes))
            if self.checkboxes[i].isChecked()
        ]
        
        if not selected_to_delete:
            return
        
        warning_message = (
            "You are about to delete the following plots:\n\n"
            + "\n".join(selected_to_delete) + 
            "\n\nDo you want to proceed?"
        )
        
        response = self.warning_popup(warning_message)
        
        if response == QMessageBox.Cancel:
            return

        for i in reversed(range(len(self.checkboxes))):
            if self.checkboxes[i].isChecked():
                widget_to_remove = self.scroll_layout.itemAt(i).widget()
                self.scroll_layout.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()

                del self.graphs[i]
                del self.checkboxes[i]

        self.select_all.setChecked(False)

    def import_from_file(self):
        """Import data from a file and allow the user to select columns for plotting."""
        # Open a file dialog to select a CSV file
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if not file_name:
            return

        try:
            data = pd.read_csv(file_name)
            y_columns = data.columns[1:]
        except Exception as e:
            self.warning_popup(f"Failed to read file: {str(e)}")
            return
        # Create and show the import dialog to select columns
        dialog = ImportDialog(y_columns, self)
        if dialog.exec_() == QDialog.Accepted:
            separate, selected_columns = dialog.get_selected_columns()
            if not selected_columns:
                print("No columns selected.")
                self.warning_popup("No columns selected")
                return
            if separate:
                for column in selected_columns:
                    self.add_graph(data=data, selected=[column])
            else:
                # Create a new plot with the selected columns
                self.add_graph(data=data, selected=selected_columns)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
