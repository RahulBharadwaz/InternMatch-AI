"""
Computer Vision Document Layout Intelligence & Privacy Redaction Service
Provides OpenCV-based document segmentation, section bounding box detection,
and automated photo/avatar detection and redaction for unbiased recruitment screening.
Tailored for deep learning and image processing engineering standards.
"""
import os
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import cv2

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocumentVisionEngine:
    """
    Computer Vision engine for document image processing and layout parsing.
    Uses morphological filtering, contour analysis, and Haar Cascades.
    """

    def __init__(self, face_cascade_path: Optional[str] = None):
        """
        Initialize the vision engine with OpenCV Haar cascades.
        """
        if face_cascade_path and os.path.exists(face_cascade_path):
            self.cascade_path = face_cascade_path
        else:
            self.cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')

        if os.path.exists(self.cascade_path):
            self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
        else:
            logger.warning("Face cascade file not found at %s. Photo detection will use contour heuristics.", self.cascade_path)
            self.face_cascade = None

    def render_pdf_to_image(self, pdf_path: str, page_num: int = 0, dpi: int = 150) -> np.ndarray:
        """
        Render a PDF page to an OpenCV BGR image array.

        Args:
            pdf_path: Absolute or relative path to PDF file.
            page_num: Page index (0-indexed).
            dpi: Rendering resolution (default 150 DPI).

        Returns:
            np.ndarray: BGR image array (H, W, 3).
        """
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is required to render PDF pages.")

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            page_num = 0

        page = doc[page_num]
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        # Convert pixmap buffer to numpy array
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, 3))
        doc.close()

        # RGB to BGR for OpenCV
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    def load_image(self, file_path: str) -> np.ndarray:
        """Load image from disk or render first page if PDF."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return self.render_pdf_to_image(file_path)
        elif ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff']:
            img = cv2.imread(file_path)
            if img is None:
                raise ValueError(f"Failed to decode image from {file_path}")
            return img
        else:
            raise ValueError(f"Unsupported document format for vision analysis: {ext}")

    def detect_document_layout(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extract structural layout bounding boxes (Header, Body Sections, Columns)
        using grayscale thresholding and morphological kernel filtering.

        Args:
            image: BGR document image.

        Returns:
            List of detected section bounding boxes with classification labels.
        """
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Invert and apply Otsu thresholding: text becomes white, background black
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Morphological operation 1: Connect horizontal text characters into text lines
        h_kernel_size = max(15, int(width * 0.025))
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (h_kernel_size, 2))
        lines = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_h)

        # Morphological operation 2: Connect vertically adjacent lines into visual section blocks
        v_kernel_size = max(4, int(height * 0.004))
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (2, v_kernel_size))
        blocks = cv2.dilate(lines, kernel_v, iterations=1)

        # Find external contours of structural blocks
        contours, _ = cv2.findContours(blocks, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        layout_sections = []
        min_block_area = (width * height) * 0.002  # ignore micro-artifacts

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            if area < min_block_area:
                continue

            # Classify segment based on spatial coordinates and geometric aspect ratio
            y_ratio = y / float(height)
            w_ratio = w / float(width)
            h_ratio = h / float(height)

            if y_ratio < 0.18 and w_ratio > 0.45:
                label = "Header / Identity"
                color = (34, 197, 94)  # Green
            elif w_ratio < 0.40 and h_ratio > 0.25:
                label = "Sidebar / Skills Column"
                color = (249, 115, 22)  # Orange
            elif h_ratio < 0.08 and w_ratio > 0.50:
                label = "Section Divider / Heading"
                color = (168, 85, 247)  # Purple
            else:
                label = "Content Body Section"
                color = (37, 99, 235)  # Blue

            layout_sections.append({
                "label": label,
                "bbox": [int(x), int(y), int(w), int(h)],
                "area": int(area),
                "width_ratio": round(w_ratio, 3),
                "height_ratio": round(h_ratio, 3),
                "color_bgr": color
            })

        # Sort blocks in reading order: top-to-bottom, then left-to-right
        layout_sections.sort(key=lambda s: (s["bbox"][1] // 50, s["bbox"][0]))
        return layout_sections

    def detect_and_redact_photo(self, image: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Detect candidate face / avatar photo in document and redact it visually
        to eliminate demographic bias during candidate screening.

        Args:
            image: BGR document image.

        Returns:
            Tuple of (redacted_image, list_of_detected_photo_regions).
        """
        redacted = image.copy()
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        detected_photos = []

        # Strategy A: Haar Cascade Face Detector
        if self.face_cascade is not None:
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(int(width * 0.04), int(width * 0.04)),
                maxSize=(int(width * 0.35), int(height * 0.35))
            )
            for (x, y, w, h) in faces:
                detected_photos.append({
                    "method": "haar_cascade",
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "confidence": 0.95
                })

        # Strategy B: Contour-based photo bounding box in header / upper third
        if not detected_photos:
            # Check for bordered portrait frames in top 25% of document
            top_roi = gray[:int(height * 0.28), :]
            edges = cv2.Canny(top_roi, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w) / float(h) if h > 0 else 0
                # Square-ish portrait photo box (0.7 to 1.3 aspect ratio)
                if 0.7 <= aspect_ratio <= 1.3:
                    if int(width * 0.06) <= w <= int(width * 0.25):
                        # Verify position is at left or right margin (typical photo placement)
                        if x < width * 0.25 or (x + w) > width * 0.75:
                            detected_photos.append({
                                "method": "geometric_portrait_detector",
                                "bbox": [int(x), int(y), int(w), int(h)],
                                "confidence": 0.82
                            })
                            break

        # Apply Privacy Redaction to detected photos
        for photo in detected_photos:
            x, y, w, h = photo["bbox"]
            pad = 6
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(width, x + w + pad)
            y2 = min(height, y + h + pad)

            # Heavy Gaussian blur + dark overlay
            roi = redacted[y1:y2, x1:x2]
            if roi.size > 0:
                blurred = cv2.GaussianBlur(roi, (51, 51), 30)
                dark_tint = np.full_like(blurred, (24, 24, 27))
                blended = cv2.addWeighted(blurred, 0.3, dark_tint, 0.7, 0)
                redacted[y1:y2, x1:x2] = blended

                # Draw border and privacy label
                cv2.rectangle(redacted, (x1, y1), (x2, y2), (239, 68, 68), 2)
                label_text = "PHOTO REDACTED"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = max(0.4, (x2 - x1) / 280.0)
                thickness = 1
                (tw, th), _ = cv2.getTextSize(label_text, font, font_scale, thickness)
                text_x = x1 + max(2, ((x2 - x1) - tw) // 2)
                text_y = y1 + ((y2 - y1) + th) // 2
                cv2.putText(redacted, label_text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

        return redacted, detected_photos

    def generate_annotated_layout_image(self, image: np.ndarray,
                                        layout_sections: List[Dict[str, Any]],
                                        photos: List[Dict[str, Any]]) -> np.ndarray:
        """
        Draw visual bounding boxes and labels for layout sections and detected photos.
        """
        annotated = image.copy()
        height, width = image.shape[:2]

        for s in layout_sections:
            x, y, w, h = s["bbox"]
            color = s.get("color_bgr", (37, 99, 235))
            label = s["label"]

            # Draw translucent bounding overlay
            overlay = annotated.copy()
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
            cv2.addWeighted(overlay, 0.12, annotated, 0.88, 0, annotated)
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

            # Label banner
            tag_text = f"{label} ({w}x{h})"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = max(0.35, min(0.55, width / 1800.0))
            (tw, th), _ = cv2.getTextSize(tag_text, font, font_scale, 1)

            cv2.rectangle(annotated, (x, max(0, y - th - 6)), (x + tw + 8, y), color, -1)
            cv2.putText(annotated, tag_text, (x + 4, max(th + 2, y - 4)), font, font_scale, (255, 255, 255), 1, cv2.LINE_AA)

        for p in photos:
            x, y, w, h = p["bbox"]
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (239, 68, 68), 3)
            tag = "PHOTO DETECTED"
            cv2.putText(annotated, tag, (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (239, 68, 68), 2, cv2.LINE_AA)

        return annotated

    def process_document(self, file_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        End-to-end computer vision processing of a document.
        Detects layout, segments sections, redacts candidate photos, and saves previews.
        """
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        img = self.load_image(file_path)
        h, w = img.shape[:2]

        # 1. Detect layout sections
        sections = self.detect_document_layout(img)

        # 2. Detect and redact candidate photo / avatar
        redacted_img, photos = self.detect_and_redact_photo(img)

        # 3. Create annotated visualization
        annotated_img = self.generate_annotated_layout_image(img, sections, photos)

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        annotated_path = None
        redacted_path = None

        if output_dir:
            annotated_path = os.path.join(output_dir, f"{base_name}_vision_layout.png")
            redacted_path = os.path.join(output_dir, f"{base_name}_photo_redacted.png")
            cv2.imwrite(annotated_path, annotated_img)
            cv2.imwrite(redacted_path, redacted_img)
            logger.info("Saved vision assets to %s and %s", annotated_path, redacted_path)

        return {
            "document_name": os.path.basename(file_path),
            "width": int(w),
            "height": int(h),
            "sections_detected": len(sections),
            "sections": sections,
            "photo_detected": len(photos) > 0,
            "photos": photos,
            "annotated_image_path": annotated_path,
            "redacted_image_path": redacted_path
        }
