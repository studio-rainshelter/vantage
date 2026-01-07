"""
VANTAGE Main Window

Primary application window with Industrial Brutalism design.
Full-featured implementation with async processing.
"""

from typing import Optional, List
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QPushButton, QFileDialog,
    QStatusBar, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from config.constants import (
    APP_NAME, APP_FULL_NAME,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    MosaicMode
)
from config import Settings
from i18n import tr, Translator
from ui.styles import Styles
from ui.components import (
    ThumbnailGrid, InspectorPane, MainToolbar
)
from ui.dialogs import SettingsDialog, ImageViewerDialog
from core import (
    ImageProcessor, ThumbnailCache, ImageDataManager,
    ImageLoaderWorker, FaceDetectionWorker, ProcessingWorker, ExportWorker,
    EffectType
)


class MainWindow(QMainWindow):
    """
    VANTAGE main application window.
    
    Features:
    - Industrial Brutalism design
    - Drag & drop image loading
    - Async image loading and processing
    - Face detection with MediaPipe
    - Mosaic/Blur application
    - Batch export
    - Multi-language support (EN/KR)
    """
    
    def __init__(self):
        super().__init__()
        
        # Core services
        self._settings = Settings()
        self._translator = Translator()
        self._image_processor = ImageProcessor()
        self._thumbnail_cache = ThumbnailCache()
        self._data_manager = ImageDataManager()
        
        # Workers
        self._loader_worker: Optional[ImageLoaderWorker] = None
        self._detection_worker: Optional[FaceDetectionWorker] = None
        self._processing_worker: Optional[ProcessingWorker] = None
        self._export_worker: Optional[ExportWorker] = None
        
        # Processed images cache (in-memory)
        self._processed_images: dict = {}
        
        # Setup
        self._setup_window()
        self._setup_ui()
        self._setup_status_bar()
        self._connect_signals()
        
        # Apply styles
        self.setStyleSheet(Styles.get_main_stylesheet())
        
        # Language observer
        self._translator.add_observer(self._on_language_changed)
    
    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle(f"{APP_NAME} - {APP_FULL_NAME}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        
        # Enable drag & drop
        self.setAcceptDrops(True)
    
    def _setup_ui(self):
        """Create the main UI layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar (always visible at top)
        self.toolbar = MainToolbar()
        main_layout.addWidget(self.toolbar)
        
        # Content container (for thumbnail grid + empty state overlay)
        self.content_container = QWidget()
        content_container_layout = QVBoxLayout(self.content_container)
        content_container_layout.setContentsMargins(0, 0, 0, 0)
        content_container_layout.setSpacing(0)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Thumbnail grid (main area)
        self.thumbnail_grid = ThumbnailGrid()
        content_layout.addWidget(self.thumbnail_grid, 1)
        
        # Inspector pane
        self.inspector = InspectorPane()
        self.inspector.show_panel()  # Open by default
        content_layout.addWidget(self.inspector)
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        content_container_layout.addWidget(content_widget, 1)
        
        main_layout.addWidget(self.content_container, 1)
        
        # Empty state overlay (child of content_container, NOT central widget)
        self._setup_empty_state()
    
    def _setup_empty_state(self):
        """Create the empty state / drop zone."""
        # Parent is content_container so toolbar stays visible
        self.empty_state = QFrame(self.content_container)
        self.empty_state.setStyleSheet(Styles.get_empty_state_style())
        
        layout = QVBoxLayout(self.empty_state)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel(tr("empty.title"))
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel(tr("empty.subtitle"))
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(16)
        
        browse_btn = QPushButton(tr("empty.browse"))
        browse_btn.clicked.connect(self._open_files)
        browse_btn.setFixedWidth(150)
        layout.addWidget(browse_btn, 0, Qt.AlignCenter)
        
        self.empty_state.raise_()
    
    def _setup_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel(tr("status.ready"))
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addWidget(self.progress_bar)
        
        self.count_label = QLabel()
        self.status_bar.addPermanentWidget(self.count_label)
        
        self.faces_label = QLabel()
        self.status_bar.addPermanentWidget(self.faces_label)
    
    def _connect_signals(self):
        """Connect UI signals."""
        # Toolbar
        self.toolbar.open_files.connect(self._open_files)
        self.toolbar.open_folder.connect(self._open_folder)
        self.toolbar.auto_detect.connect(self._run_face_detection)
        self.toolbar.apply_mosaic.connect(self._apply_mosaic)
        self.toolbar.apply_blur.connect(self._apply_blur)
        self.toolbar.revert_mosaic.connect(self._revert_mosaic)
        self.toolbar.select_all.connect(self.thumbnail_grid.toggle_select_all)
        self.toolbar.remove_selected.connect(self._remove_selected_images)
        self.toolbar.save_triggered.connect(self._save_current)
        self.toolbar.save_all_triggered.connect(self._save_all)
        
        # Thumbnail grid
        self.thumbnail_grid.item_double_clicked.connect(self._open_image_viewer)
        self.thumbnail_grid.item_clicked.connect(self._on_image_selected)
        
        # Inspector
        self.inspector.close_requested.connect(self._close_inspector)
        self.inspector.apply_requested.connect(self._apply_from_inspector)
        self.inspector.edit_requested.connect(self._on_inspector_edit_requested)
        self.inspector.mode_changed.connect(self._on_mode_changed)
        
        # Language (now from toolbar)
        self.toolbar.lang_switcher.language_changed.connect(self._on_language_changed)
        
        # Theme
        self.toolbar.theme_toggled.connect(self._toggle_theme)
    
    # =========================================================================
    # FILE OPERATIONS
    # =========================================================================
    
    def _open_files(self):
        """Open file dialog for image selection."""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr("toolbar.open"),
            self._settings.get('last_open_directory', ''),
            "Images (*.jpg *.jpeg *.png *.bmp *.webp *.tiff)"
        )
        
        if paths:
            self._settings.set('last_open_directory', str(Path(paths[0]).parent))
            self._load_images([Path(p) for p in paths])
    
    def _open_folder(self):
        """Open folder dialog for batch loading."""
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("menu.file.open_folder"),
            self._settings.get('last_open_directory', '')
        )
        
        if folder:
            self._settings.set('last_open_directory', folder)
            # Scan directory (recursive=False by default now)
            images = self._image_processor.scan_directory(folder)
            self._load_images(images)

    def _remove_selected_images(self):
        """Remove selected images from the list."""
        # Use checked paths for batch removal
        selected_paths = self.thumbnail_grid.checked_paths
        
        if not selected_paths:
            return

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            APP_NAME,
            tr("dialog.confirm_remove", count=len(selected_paths)),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return

        for path in selected_paths:
            # Remove from data manager
            self._data_manager.remove(path)
            
            # Remove from processed cache
            if path in self._processed_images:
                del self._processed_images[path]
                
            # Remove from thumbnail grid
            self.thumbnail_grid.remove_thumbnail(path)
            
        self._update_status()
    
    def _load_images(self, paths: List[Path]):
        """Load images asynchronously."""
        if not paths:
            return
        
        # Hide empty state
        self.empty_state.hide()
        
        # Add to data manager
        for path in paths:
            self._data_manager.add(str(path))
        
        # Start async loader
        self._loader_worker = ImageLoaderWorker(paths)
        self._loader_worker.thumbnail_ready.connect(self._on_thumbnail_ready)
        self._loader_worker.progress.connect(self._on_load_progress)
        self._loader_worker.finished.connect(self._on_load_finished)
        self._loader_worker.error.connect(self._on_load_error)
        
        # Show progress
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(paths))
        self.progress_bar.setVisible(True)
        self.status_label.setText(tr("status.loading"))
        
        self._loader_worker.start()
    
    def _on_thumbnail_ready(self, path: str, thumbnail):
        """Handle thumbnail loaded."""
        self._thumbnail_cache.put(path, thumbnail)
        
        # Check for manual edits
        img_data = self._data_manager.get(path)
        has_edit = img_data.has_manual_edit if img_data else False
        
        self.thumbnail_grid.add_thumbnail(path, thumbnail, has_edit)
    
    def _on_load_progress(self, current: int, total: int):
        """Update loading progress."""
        self.progress_bar.setValue(current)
    
    def _on_load_finished(self):
        """Handle loading complete."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(tr("status.ready"))
        self._update_status()
        self._loader_worker = None
    
    def _on_load_error(self, path: str, error: str):
        """Handle load error."""
        print(f"[MainWindow] Failed to load {path}: {error}")
    
    # =========================================================================
    # FACE DETECTION
    # =========================================================================
    
    def _run_face_detection(self):
        """Run face detection on selected images."""
        # Use checked paths for batch detection
        selected_paths = self.thumbnail_grid.checked_paths
        
        if not selected_paths:
            QMessageBox.information(
                self,
                APP_NAME,
                "No images selected. Please check thumbnails to detect faces."
            )
            return
            
        paths = selected_paths
        
        # Start worker
        self._detection_worker = FaceDetectionWorker(paths)
        self._detection_worker.detection_complete.connect(self._on_detection_complete)
        self._detection_worker.progress.connect(self._on_detection_progress)
        self._detection_worker.finished.connect(self._on_detection_finished)
        self._detection_worker.error.connect(self._on_detection_error)
        
        # Show progress
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(paths))
        self.progress_bar.setVisible(True)
        self.status_label.setText(tr("status.processing"))
        
        self._detection_worker.start()
    
    def _on_detection_complete(self, path: str, faces: list, size: tuple):
        """Handle detection result for one image."""
        self._data_manager.set_faces(path, faces)
        
        # Update size in data manager
        w, h = size
        img_data = self._data_manager.get(path)
        manual_regions = []
        if img_data:
            img_data.width = w
            img_data.height = h
            manual_regions = img_data.manual_regions
            
        # Update thumbnail overlay - Preserve manual regions!
        self.thumbnail_grid.set_overlays(path, faces, manual_regions, w, h)
        
        # If this is the current inspector image, update inspector too
        if self.inspector.current_path == path:
            self._open_inspector(path)
    
    def _on_detection_progress(self, current: int, total: int):
        """Update detection progress."""
        self.progress_bar.setValue(current)
    
    def _on_detection_finished(self):
        """Handle detection complete."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(tr("status.complete"))
        self._update_status()
        self._detection_worker = None
    
    def _on_detection_error(self, path: str, error: str):
        """Handle detection error."""
        print(f"[MainWindow] Detection failed for {path}: {error}")
    
    # =========================================================================
    # MOSAIC / BLUR APPLICATION
    # =========================================================================
    
    def _apply_mosaic(self):
        """Apply mosaic to all images with detected faces."""
        self._apply_effect(EffectType.MOSAIC)
    
    def _apply_blur(self):
        """Apply blur to all images with detected faces."""
        self._apply_effect(EffectType.BLUR)
    
    
    def _apply_effect(self, effect: EffectType):
        """Apply effect to selected images, or warn if none selected."""
        # Get selected paths (Checked)
        selected_paths = self.thumbnail_grid.checked_paths
        
        if not selected_paths:
            QMessageBox.information(
                self,
                APP_NAME,
                "No images selected. Please check thumbnails to process."
            )
            return
            
        # Get images with faces or manual regions within selection
        processing_data = []
        for path in selected_paths:
            img_data = self._data_manager.get(path)
            if img_data and (img_data.faces or img_data.manual_regions):
                # Prepare data dictionary manually or via helper
                # Since get_processing_data() returns all, we build list manually or filter
                processing_data.append({
                    'path': path,
                    'faces': img_data.faces,
                    'manual_regions': img_data.manual_regions,
                    'mode': img_data.mode
                })
        
        if not processing_data:
            QMessageBox.information(
                self,
                APP_NAME,
                "Selected images have no detected faces or manual regions."
            )
            return
        
        # Start worker
        self._processing_worker = ProcessingWorker(processing_data, effect)
        self._processing_worker.image_processed.connect(self._on_image_processed)
        self._processing_worker.progress.connect(self._on_processing_progress)
        self._processing_worker.finished.connect(self._on_processing_finished)
        self._processing_worker.error.connect(self._on_processing_error)
        
        # Show progress
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(processing_data))
        self.progress_bar.setVisible(True)
        self.status_label.setText(tr("status.processing"))
        
        self._processing_worker.start()

    def _revert_mosaic(self):
        """Revert selected images to original."""
        # Use checked paths
        selected_paths = self.thumbnail_grid.checked_paths
        
        # If no selection, ask to revert all
        if not selected_paths:
            reply = QMessageBox.question(
                self,
                APP_NAME,
                "Revert all processed images to original?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                selected_paths = list(self._processed_images.keys())
            else:
                return
        
        for path in selected_paths:
            if path in self._processed_images:
                # Remove from processed cache
                del self._processed_images[path]
                
                # Reset data status
                img_data = self._data_manager.get(path)
                if img_data:
                    img_data.is_processed = False
                
                # Regenerate original thumbnail
                original = self._image_processor.load_image(path)
                if original is not None:
                    thumb = self._image_processor.generate_thumbnail(original)
                    self.thumbnail_grid.update_thumbnail(path, thumb)
                    
        self.status_label.setText("Reverted to original.")
    
    def _on_image_processed(self, path: str, processed_image):
        """Handle processed image."""
        # Store in memory
        self._processed_images[path] = processed_image
        
        # Update thumbnail with processed preview
        thumbnail = self._image_processor.generate_thumbnail(processed_image)
        self.thumbnail_grid.update_thumbnail(path, thumbnail)
        
        # Mark as processed
        img_data = self._data_manager.get(path)
        if img_data:
            img_data.is_processed = True
    
    def _on_processing_progress(self, current: int, total: int):
        """Update processing progress."""
        self.progress_bar.setValue(current)
    
    def _on_processing_finished(self):
        """Handle processing complete."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(tr("status.complete"))
        self._processing_worker = None
    
    def _on_processing_error(self, path: str, error: str):
        """Handle processing error."""
        print(f"[MainWindow] Processing failed for {path}: {error}")
    
    def _apply_from_inspector(self):
        """Apply effect from inspector to current image."""
        if not self.inspector._current_path:
            return
        
        path = self.inspector._current_path
        img_data = self._data_manager.get(path)
        
        if not img_data:
            return
        
        # Get effect based on current mode
        effect = img_data.effect
        
        # Single image processing
        processing_data = [{
            'path': path,
            'faces': img_data.faces,
            'manual_regions': img_data.manual_regions,
            'mode': img_data.mode
        }]
        
        self._processing_worker = ProcessingWorker(processing_data, effect)
        self._processing_worker.image_processed.connect(self._on_image_processed)
        self._processing_worker.finished.connect(self._on_processing_finished)
        self._processing_worker.start()
    
    def _clear_regions(self):
        """Clear all manual regions."""
        for path in self._data_manager.get_all_paths():
            img_data = self._data_manager.get(path)
            if img_data:
                img_data.clear_manual_regions()
                self.thumbnail_grid.set_manual_edit(path, False)
    
    # =========================================================================
    # EXPORT -> SAVE ALL
    # =========================================================================
    
    def _save_current(self):
        """Save currently selected processed image."""
        # Use active path (Inspector target)
        path = self.thumbnail_grid.active_path
        if not path:
            QMessageBox.information(self, APP_NAME, "No image selected.")
            return
        
        if path not in self._processed_images:
            QMessageBox.information(
                self, APP_NAME,
                "No processed image. Apply mosaic/blur first."
            )
            return
        
        # Get output path
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            tr("menu.file.save"),
            str(Path(path).with_stem(Path(path).stem + "_processed")),
            "Images (*.jpg *.png *.webp)"
        )
        
        if output_path:
            success = self._image_processor.save_image(
                self._processed_images[path],
                output_path
            )
            
            if success:
                self.status_label.setText(tr("status.complete"))
            else:
                QMessageBox.warning(self, APP_NAME, "Failed to save image.")
    
    def _save_all(self):
        """Save processed images (Checked only, or all if none checked)."""
        if not self._processed_images:
            QMessageBox.information(
                self, APP_NAME,
                "No processed images. Apply mosaic/blur first."
            )
            return
        
        # Determine targets: Checked paths that have been processed
        checked_paths = self.thumbnail_grid.checked_paths
        target_paths = []
        
        if checked_paths:
            target_paths = [p for p in checked_paths if p in self._processed_images]
        else:
            # If nothing checked, save ALL processed
            target_paths = list(self._processed_images.keys())
            
        if not target_paths:
            msg = "No processed images selected." if checked_paths else "No processed images found."
            QMessageBox.information(self, APP_NAME, msg)
            return
        
        # Get output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            tr("toolbar.save_all"),
            self._settings.get('last_save_directory', '')
        )
        
        if not output_dir:
            return
        
        self._settings.set('last_save_directory', output_dir)
        
        # Prepare export data
        export_data = []
        for path in target_paths:
            image = self._processed_images[path]
            original_name = Path(path).stem
            ext = Path(path).suffix
            output_path = Path(output_dir) / f"{original_name}_processed{ext}"
            
            export_data.append({
                'path': path,
                'image': image,
                'output_path': output_path
            })
        
        # Start export worker (using same worker as it just saves images)
        self._export_worker = ExportWorker(export_data)
        self._export_worker.export_complete.connect(self._on_save_all_complete)
        self._export_worker.progress.connect(self._on_save_all_progress)
        self._export_worker.finished.connect(self._on_save_all_finished)
        self._export_worker.error.connect(self._on_save_all_error)
        
        # Show progress
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(export_data))
        self.progress_bar.setVisible(True)
        self.status_label.setText(tr("status.processing"))
        
        self._export_worker.start()
    
    def _on_save_all_complete(self, original_path: str, export_path: str):
        """Handle single image save complete."""
        pass 
    
    def _on_save_all_progress(self, current: int, total: int):
        """Update save all progress."""
        self.progress_bar.setValue(current)
    
    def _on_save_all_finished(self):
        """Handle save all complete."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(tr("status.complete"))
        self._export_worker = None
        
        QMessageBox.information(
            self, APP_NAME,
            f"Saved {len(self._processed_images)} images successfully."
        )
    
    def _on_save_all_error(self, path: str, error: str):
        """Handle save all error."""
        print(f"[MainWindow] Save All failed for {path}: {error}")
    
    # =========================================================================
    # IMAGE VIEWER
    # =========================================================================
    
    def _open_image_viewer(self, path: str):
        """Open image viewer dialog for the selected image."""
        # Use processed image if available, otherwise load original
        if path in self._processed_images:
            image = self._processed_images[path]
        else:
            image = self._image_processor.load_image(path)
            
        if image is None:
            return
        
        # Get existing regions and faces
        img_data = self._data_manager.get(path)
        existing_regions = img_data.manual_regions if img_data else []
        detected_faces = img_data.faces if img_data else []
        
        viewer = ImageViewerDialog(path, image, existing_regions, detected_faces, self)
        viewer.regions_changed.connect(self._on_regions_changed)
        viewer.show()
    
    def _on_regions_changed(self, path: str, regions: list):
        """Handle regions changed from image viewer."""
        img_data = self._data_manager.get(path)
        if img_data:
            img_data.manual_regions = regions
            # Update thumbnail marker AND overlay
            has_manual = len(regions) > 0
            self.thumbnail_grid.set_manual_edit(path, has_manual)
            
            # Fetch dimensions and faces to update overlay
            image = self._image_processor.load_image(path)
            if image is not None:
                h, w = image.shape[:2]
                detected_faces = img_data.faces if img_data else []
                self.thumbnail_grid.set_overlays(path, detected_faces, regions, w, h)
                
            # If this is the current inspector image, update inspector too
            if self.inspector.current_path == path:
                self._open_inspector(path)
                
    def _on_inspector_edit_requested(self):
        """Handle edit request from inspector."""
        path = self.inspector.current_path
        if path:
            self._open_image_viewer(path)
    
    # =========================================================================
    # INSPECTOR
    # =========================================================================
    
    def _open_inspector(self, path: str):
        """Open inspector for an image."""
        image = self._image_processor.load_image(path)
        if image is None:
            return
        
        h, w = image.shape[:2]
        img_data = self._data_manager.get(path)
        face_count = img_data.face_count if img_data else 0
        mode = img_data.mode if img_data else None
        faces = img_data.faces if img_data else []
        manual_regions = img_data.manual_regions if img_data else []
        
        self.inspector.set_image(path, image, (w, h), face_count, mode, faces, manual_regions)
        self.inspector.show_panel()
        
    def _close_inspector(self):
        """Handle inspector closing."""
        # Persistent inspector doesn't close via this method anymore
        pass
            
    def _on_image_selected(self, path: str):
        """Handle image selection in grid."""
        # Always update inspector
        self._open_inspector(path)
        
    def _on_mode_changed(self, mode: str):
        """Handle mode change from inspector."""
        path = self.inspector.current_path
        if path:
            img_data = self._data_manager.get(path)
            if img_data:
                img_data.mode = mode
    
    # =========================================================================
    # DIALOGS
    # =========================================================================
    
    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            tr("menu.help.about"),
            f"<h2>{APP_NAME}</h2>"
            f"<p>{APP_FULL_NAME}</p>"
            "<p>Version 0.1.0</p>"
            "<p>© 2026 Studio RainShelter</p>"
            "<p>Industrial Brutalism Design</p>"
        )
    
    # =========================================================================
    # STATUS & UI UPDATES
    # =========================================================================
    
    def _update_status(self):
        """Update status bar."""
        count = self._data_manager.count
        if count > 0:
            self.count_label.setText(tr("status.images_count", count=count))
        else:
            self.count_label.clear()
        
        # Update face count
        total_faces = self._data_manager.total_faces
        if total_faces > 0:
            self.faces_label.setText(
                tr("status.faces_detected", count=total_faces)
            )
        else:
            self.faces_label.setText("")

    def _toggle_theme(self):
        """Toggle between light and dark theme."""
        current = self._settings.theme
        new_theme = 'light' if current == 'dark' else 'dark'
        self._settings.theme = new_theme
        
        # Apply styles
        self.setStyleSheet(Styles.get_main_stylesheet())
        self.toolbar.update_style()
        self.thumbnail_grid.update_style()
        self.inspector.update_style()
        self.empty_state.setStyleSheet(Styles.get_empty_state_style())
    
    def _on_language_changed(self, lang: str = None):
        """Handle language change."""
        # Update status
        self.status_label.setText(tr("status.ready"))
        self._update_status()
        
        # Update inspector
        self.inspector.update_translations()
    
    # =========================================================================
    # DRAG & DROP
    # =========================================================================
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop."""
        paths = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file() and self._image_processor.is_supported(path):
                paths.append(path)
            elif path.is_dir():
                paths.extend(self._image_processor.scan_directory(path))
        
        if paths:
            self._load_images(paths)
    
    # =========================================================================
    # WINDOW EVENTS
    # =========================================================================
    
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)
        self._update_empty_state_geometry()
    
    def showEvent(self, event):
        """Handle window first shown."""
        super().showEvent(event)
        # Update empty state geometry after window is shown
        self._update_empty_state_geometry()
    
    def _update_empty_state_geometry(self):
        """Update empty state overlay size to match content container."""
        if hasattr(self, 'empty_state') and hasattr(self, 'content_container'):
            self.empty_state.setGeometry(self.content_container.rect())
    
    def closeEvent(self, event):
        """Handle window close."""
        # Cancel any running workers
        for worker in [self._loader_worker, self._detection_worker,
                       self._processing_worker, self._export_worker]:
            if worker and worker.isRunning():
                worker.cancel()
                worker.wait()
        
        # Save window geometry
        self._settings.set('window_geometry', {
            'width': self.width(),
            'height': self.height(),
            'x': self.x(),
            'y': self.y()
        })
        
        # Cleanup
        self._image_processor.shutdown()
        self._thumbnail_cache.clear()
        
        event.accept()
