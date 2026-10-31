"""
Unit and Integration Tests for Computer Vision Document Intelligence
Validates PDF rendering, morphological layout segmentation, and photo redaction.
"""
import os
import shutil
import tempfile
import numpy as np
import cv2
import pytest

from app.services.document_vision import DocumentVisionEngine


@pytest.fixture
def vision_engine():
    """Instantiate DocumentVisionEngine."""
    return DocumentVisionEngine()


@pytest.fixture
def synthetic_resume_image():
    """Create a realistic synthetic resume image with header, sidebar, and body sections."""
    img = np.full((1000, 750, 3), 255, dtype=np.uint8)

    # Header block
    cv2.rectangle(img, (50, 40), (700, 110), (30, 30, 30), -1)

    # Section 1 (Education)
    cv2.rectangle(img, (50, 150), (700, 260), (50, 50, 50), -1)

    # Section 2 (Technical Skills)
    cv2.rectangle(img, (50, 300), (700, 420), (50, 50, 50), -1)

    # Section 3 (Projects)
    cv2.rectangle(img, (50, 460), (700, 680), (50, 50, 50), -1)

    # Section 4 (Achievements)
    cv2.rectangle(img, (50, 720), (700, 920), (50, 50, 50), -1)

    return img


def test_document_layout_detection(vision_engine, synthetic_resume_image):
    """Test morphological layout segmentation on synthetic resume image."""
    sections = vision_engine.detect_document_layout(synthetic_resume_image)

    assert len(sections) >= 3
    # Top section should be detected as Header / Identity
    top_section = min(sections, key=lambda s: s["bbox"][1])
    assert "Header" in top_section["label"]
    assert top_section["bbox"][1] < 150


def test_photo_detection_and_redaction(vision_engine):
    """Test detection and redaction of portrait photo box."""
    img = np.full((1000, 750, 3), 255, dtype=np.uint8)

    # Simulate a portrait photo frame in top-right corner
    photo_x, photo_y, photo_w, photo_h = 600, 50, 100, 110
    cv2.rectangle(img, (photo_x, photo_y), (photo_x + photo_w, photo_y + photo_h), (80, 80, 80), -1)

    redacted_img, photos = vision_engine.detect_and_redact_photo(img)

    assert len(photos) >= 1
    detected_box = photos[0]["bbox"]
    # Check bounding box proximity
    assert abs(detected_box[0] - photo_x) < 25
    assert abs(detected_box[1] - photo_y) < 25

    # Check that pixel values inside photo region were redacted/blurred
    roi_original = img[photo_y + 10:photo_y + 30, photo_x + 10:photo_x + 30]
    roi_redacted = redacted_img[photo_y + 10:photo_y + 30, photo_x + 10:photo_x + 30]
    assert not np.array_equal(roi_original, roi_redacted)


def test_annotated_layout_image(vision_engine, synthetic_resume_image):
    """Test generating annotated visual layout overlay."""
    sections = vision_engine.detect_document_layout(synthetic_resume_image)
    annotated = vision_engine.generate_annotated_layout_image(synthetic_resume_image, sections, [])

    assert annotated.shape == synthetic_resume_image.shape
    assert annotated.dtype == np.uint8
    # Annotated image should differ from original due to overlays
    assert not np.array_equal(annotated, synthetic_resume_image)


def test_real_pdf_vision_processing(vision_engine):
    """Test end-to-end vision processing on actual PDF resume."""
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Rahul_Resume_AIRA_Matrix.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip(f"Test PDF not found at {pdf_path}")

    temp_dir = tempfile.mkdtemp()
    try:
        result = vision_engine.process_document(pdf_path, output_dir=temp_dir)

        assert result["width"] > 500
        assert result["height"] > 700
        assert result["sections_detected"] >= 4
        assert result["annotated_image_path"] is not None
        assert os.path.exists(result["annotated_image_path"])
        assert result["redacted_image_path"] is not None
        assert os.path.exists(result["redacted_image_path"])
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

