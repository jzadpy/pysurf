import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QLineEdit, QShortcut, QFrame, QMenu, QAction)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QKeySequence, QFont

class Tab:
    def __init__(self, webview, title="Nueva pestaña", url=""):
        self.webview = webview
        self.title = title
        self.url = url
        self.button = None

class PySurfBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tabs = []
        self.current_tab_index = 0
        self.visible_tabs = 0  # Solo mostrar 2 pestañas máximo
        self.max_visible_tabs = 2
        self.init_ui()
        self.setup_shortcuts()
        self.new_tab()
    
    def init_ui(self):
        self.setWindowTitle("PySurf Browser")
        self.setGeometry(100, 100, 1000, 600)
        # Fondo gris y barra de título negra
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QMainWindow::title {
                background-color: #000000;
                color: white;
            }
        """)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(8, 8, 8, 0)
        layout.setSpacing(8)
        
        # Barra superior - TODO alineado a la izquierda
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.setAlignment(Qt.AlignLeft)  # Alinear todo a la izquierda
        
        # Botón recargar (circular como en la imagen)
        self.reload_btn = QPushButton("↻")
        self.reload_btn.setFixedSize(32, 32)
        self.reload_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #777; }
            QPushButton:pressed { background-color: #555; }
        """)
        self.reload_btn.clicked.connect(self.reload_page)
        toolbar.addWidget(self.reload_btn)
        
        # Barra URL - más pequeña
        self.url_bar = QLineEdit()
        self.url_bar.setFixedSize(300, 32)  # Tamaño fijo más pequeño
        self.url_bar.setStyleSheet("""
            QLineEdit {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 16px;
                padding: 0 15px;
                font-size: 13px;
            }
            QLineEdit:focus {
                background-color: #777;
                outline: none;
            }
        """)
        self.url_bar.setPlaceholderText("URL")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        toolbar.addWidget(self.url_bar)
        
        # Contenedor para pestañas visibles (solo 2) - AL LADO de la URL
        self.tab_container = QHBoxLayout()
        self.tab_container.setSpacing(4)
        
        # Botón ">" para más pestañas
        self.more_tabs_btn = QPushButton(">")
        self.more_tabs_btn.setFixedSize(32, 32)
        self.more_tabs_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #777; }
        """)
        self.more_tabs_btn.clicked.connect(self.show_tabs_menu)
        self.more_tabs_btn.hide()  # Oculto inicialmente
        
        # Agregar pestañas y botón ">" a la barra principal
        toolbar.addLayout(self.tab_container)
        toolbar.addWidget(self.more_tabs_btn)
        
        # Agregar stretch para mantener todo a la izquierda
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Área del navegador (quitamos la fila extra de pestañas)
        self.browser_area = QWidget()
        self.browser_area.setStyleSheet("background-color: white; border-radius: 8px;")
        layout.addWidget(self.browser_area)
        
        # Layout para el webview actual
        self.browser_layout = QVBoxLayout(self.browser_area)
        self.browser_layout.setContentsMargins(0, 0, 0, 0)
    
    def create_tab_button(self, title, tab_index):
        """Crear botón de pestaña con el estilo de la imagen"""
        btn = QPushButton(title[:15] + "..." if len(title) > 15 else title)
        btn.setFixedSize(120, 32)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 12px;
                text-align: center;
            }
            QPushButton:hover { background-color: #777; }
        """)
        
        # CONECTAR el botón correctamente
        btn.clicked.connect(lambda: self.switch_to_tab(tab_index))
        return btn
    
    def new_tab(self, url="https://www.google.com"):
        # Crear webview
        webview = QWebEngineView()
        webview.titleChanged.connect(lambda title: self.update_tab_title(title))
        webview.urlChanged.connect(lambda url: self.update_url_bar(url))
        
        # Crear pestaña
        tab = Tab(webview, "Cargando...", url)
        self.tabs.append(tab)
        
        # Solo mostrar botón si hay menos de 2 pestañas visibles
        if self.visible_tabs < self.max_visible_tabs:
            tab_index = len(self.tabs) - 1  # Índice de la pestaña recién creada
            tab.button = self.create_tab_button("Cargando...", tab_index)
            self.tab_container.addWidget(tab.button)
            self.visible_tabs += 1
        
        # Mostrar/ocultar botón ">" - ARREGLADO
        if len(self.tabs) > self.max_visible_tabs:
            self.more_tabs_btn.show()
        else:
            self.more_tabs_btn.hide()
        
        # Cambiar a la nueva pestaña
        self.switch_to_tab(len(self.tabs) - 1)
        webview.load(QUrl(url))
        
        return tab
    
    def switch_to_tab(self, index):
        if 0 <= index < len(self.tabs):
            # Remover webview actual
            for i in reversed(range(self.browser_layout.count())): 
                self.browser_layout.itemAt(i).widget().setParent(None)
            
            # Agregar nuevo webview
            current_tab = self.tabs[index]
            self.browser_layout.addWidget(current_tab.webview)
            self.current_tab_index = index
            
            # Actualizar barra URL
            current_url = current_tab.webview.url().toString()
            if current_url:
                self.url_bar.setText(current_url)
            
            # Actualizar estilo de botones
            self.update_tab_buttons()
    
    def update_tab_buttons(self):
        """Actualizar estilo visual de botones de pestañas"""
        for i, tab in enumerate(self.tabs[:self.max_visible_tabs]):
            if tab.button:
                if i == self.current_tab_index:
                    # Pestaña activa - más clara
                    tab.button.setStyleSheet("""
                        QPushButton {
                            background-color: #888;
                            color: white;
                            border: none;
                            border-radius: 16px;
                            font-size: 12px;
                            text-align: center;
                        }
                    """)
                else:
                    # Pestañas inactivas
                    tab.button.setStyleSheet("""
                        QPushButton {
                            background-color: #666;
                            color: white;
                            border: none;
                            border-radius: 16px;
                            font-size: 12px;
                            text-align: center;
                        }
                        QPushButton:hover { background-color: #777; }
                    """)
    
    def update_tab_title(self, title):
        """Actualizar título de pestaña cuando la página carga"""
        if self.current_tab_index < len(self.tabs):
            tab = self.tabs[self.current_tab_index]
            tab.title = title
            if tab.button:
                short_title = title[:15] + "..." if len(title) > 15 else title
                tab.button.setText(short_title)
                
                # Reconectar el botón por si acaso
                tab.button.clicked.disconnect()
                tab.button.clicked.connect(lambda: self.switch_to_tab(self.current_tab_index))
    
    def update_url_bar(self, url):
        """Actualizar barra URL cuando cambia la página"""
        if self.current_tab_index < len(self.tabs):
            current_tab = self.tabs[self.current_tab_index]
            if current_tab.webview.url() == url:
                self.url_bar.setText(url.toString())
    
    def navigate_to_url(self):
        url = self.url_bar.text().strip()
        
        if url == 'cfg.pysurf':
            self.load_config_page()
            return
        
        if not url.startswith(('http://', 'https://')):
            if '.' in url and ' ' not in url:
                url = 'https://' + url
            else:
                url = 'https://www.google.com/search?q=' + url
        
        if self.current_tab_index < len(self.tabs):
            self.tabs[self.current_tab_index].webview.load(QUrl(url))
    
    def load_config_page(self):
        config_html = """
        <html>
        <head><title>cfg.pysurf</title></head>
        <body style="font-family: Arial; padding: 40px; background: #f5f5f5; margin: 0;">
            <div style="max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h1 style="color: #333; margin-bottom: 30px;">🏄 PySurf Browser</h1>
                
                <h3 style="color: #666;">Atajos de teclado:</h3>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 15px 0;">
                    <p><strong>Ctrl+T</strong> - Nueva pestaña</p>
                    <p><strong>Ctrl+W</strong> - Cerrar pestaña actual</p>
                    <p><strong>Ctrl+R</strong> - Recargar página</p>
                    <p><strong>F5</strong> - Recargar página</p>
                    <p><strong>Ctrl+L</strong> - Enfocar barra URL</p>
                </div>
                
                <h3 style="color: #666;">Funciones especiales:</h3>
                <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 15px 0;">
                    <p>• Escribe <strong>cfg.pysurf</strong> en la URL para abrir esta página</p>
                    <p>• Las pestañas muestran el título real de la página</p>
                    <p>• Solo 2 pestañas visibles + botón ">" para más</p>
                    <p>• Búsqueda automática en Google</p>
                </div>
                
                <p style="color: #999; text-align: center; margin-top: 40px;">PySurf Browser - Ultra minimalista</p>
            </div>
        </body>
        </html>
        """
        if self.current_tab_index < len(self.tabs):
            self.tabs[self.current_tab_index].webview.setHtml(config_html)
    
    def show_tabs_menu(self):
        """Mostrar menú con todas las pestañas ocultas"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #444;
                color: white;
                border: 1px solid #666;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 8px 20px;
                border-radius: 3px;
                margin: 1px;
            }
            QMenu::item:selected {
                background-color: #555;
            }
            QMenu::item:pressed {
                background-color: #666;
            }
        """)
        
        # Agregar todas las pestañas ocultas (las que no tienen botón visible)
        hidden_tabs_added = False
        
        for i, tab in enumerate(self.tabs):
            # Si la pestaña no tiene botón visible o está fuera del rango visible
            if i >= self.max_visible_tabs or tab.button is None:
                # Obtener título de la pestaña
                tab_title = tab.title if tab.title and tab.title != "Nueva pestaña" else f"Pestaña {i+1}"
                if len(tab_title) > 30:
                    tab_title = tab_title[:30] + "..."
                
                # Crear acción del menú
                action = QAction(tab_title, self)
                action.setData(i)  # Guardar índice de la pestaña
                action.triggered.connect(lambda checked, idx=i: self.switch_to_tab(idx))
                
                # Marcar la pestaña actual
                if i == self.current_tab_index:
                    action.setText(f"● {tab_title}")  # Punto para indicar pestaña actual
                
                menu.addAction(action)
                hidden_tabs_added = True
        
        # Si no hay pestañas ocultas, mostrar mensaje
        if not hidden_tabs_added:
            no_tabs_action = QAction("No hay más pestañas", self)
            no_tabs_action.setEnabled(False)
            menu.addAction(no_tabs_action)
        else:
            # Agregar separador y opción para nueva pestaña
            menu.addSeparator()
            new_tab_action = QAction("+ Nueva pestaña", self)
            new_tab_action.triggered.connect(self.new_tab)
            menu.addAction(new_tab_action)
        
        # Mostrar el menú debajo del botón
        button_pos = self.more_tabs_btn.mapToGlobal(self.more_tabs_btn.rect().bottomLeft())
        menu.exec_(button_pos)
    
    def close_current_tab(self):
        if len(self.tabs) > 1:
            tab_to_remove = self.tabs.pop(self.current_tab_index)
            if tab_to_remove.button:
                tab_to_remove.button.deleteLater()
                self.visible_tabs -= 1
            
            # Cambiar a pestaña anterior
            if self.current_tab_index >= len(self.tabs):
                self.current_tab_index = len(self.tabs) - 1
            self.switch_to_tab(self.current_tab_index)
            
            # Ocultar botón ">" si no hay suficientes pestañas - ARREGLADO
            if len(self.tabs) <= self.max_visible_tabs:
                self.more_tabs_btn.hide()
        else:
            # Si es la última pestaña, crear una nueva antes de cerrar
            self.new_tab()
            if len(self.tabs) > 1:
                self.tabs.pop(0)
    
    def reload_page(self):
        if self.current_tab_index < len(self.tabs):
            self.tabs[self.current_tab_index].webview.reload()
    
    def focus_url_bar(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()
    
    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+T"), self, self.new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+R"), self, self.reload_page)
        QShortcut(QKeySequence("F5"), self, self.reload_page)
        QShortcut(QKeySequence("Ctrl+L"), self, self.focus_url_bar)

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("PySurf Browser")
    
    browser = PySurfBrowser()
    browser.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()