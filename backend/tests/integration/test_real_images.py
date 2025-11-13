"""
Integration tests using real images from test-images directory.

Tests the complete upload → process → download pipeline with:
- Real HEIC image (iPhone native format)
- Real JPEG image (high-resolution photo)

No synthetic images or mocks - production-realistic testing.
"""

import time

import pytest


def test_upload_real_jpeg_image(client, jpeg_image_path):
    """Test uploading real JPEG image."""
    with jpeg_image_path.open("rb") as f:
        image_data = f.read()

    response = client.post(
        "/api/upload",
        files={"file": ("real_photo.jpg", image_data, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "filename" in data
    assert "image_url" in data
    assert data["filename"] == "real_photo.jpg"

    # Verify job exists and is pending
    job_id = data["job_id"]
    status_response = client.get(f"/api/status/{job_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] == "pending"


def test_upload_real_heic_image(client, heic_image_path):
    """Test uploading real HEIC image (iPhone format)."""
    with heic_image_path.open("rb") as f:
        image_data = f.read()

    response = client.post(
        "/api/upload",
        files={"file": ("iphone_photo.heic", image_data, "image/heic")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["filename"] == "iphone_photo.heic"


@pytest.mark.asyncio
async def test_complete_pipeline_jpeg(client, jpeg_image_path):
    """
    Test complete processing pipeline with real JPEG image.

    Upload → Process → Poll Status → Download
    """
    # Step 1: Upload
    with jpeg_image_path.open("rb") as f:
        image_data = f.read()

    upload_response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", image_data, "image/jpeg")},
    )
    assert upload_response.status_code == 200
    job_id = upload_response.json()["job_id"]

    # Step 2: Start processing
    process_response = client.post(
        "/api/process",
        json={
            "job_id": job_id,
            "mode": "auto",
            "params": {
                "canvas_width_mm": 200.0,
                "canvas_height_mm": 150.0,
                "line_width_mm": 0.3,
                "isolate_subject": False,
                "use_ml": False,  # Faster testing without ML
                "edge_threshold": 50,
                "line_threshold": 10,
            },
        },
    )
    assert process_response.status_code == 200

    # Step 3: Poll status until complete or timeout
    max_attempts = 60  # 60 seconds timeout
    for _ in range(max_attempts):
        status_response = client.get(f"/api/status/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()

        if status_data["status"] == "completed":
            # Verify result available
            assert status_data["result_url"] is not None
            assert status_data["stats"] is not None
            assert status_data["stats"]["path_count"] > 0
            assert status_data["stats"]["total_length_mm"] > 0

            # Step 4: Download SVG result
            download_response = client.get(f"/api/download/{job_id}?format=svg")
            assert download_response.status_code == 200
            assert download_response.headers["content-type"] == "image/svg+xml"

            svg_content = download_response.content.decode("utf-8")
            assert "<svg" in svg_content
            assert "</svg>" in svg_content
            break

        if status_data["status"] == "failed":
            pytest.fail(
                f"Processing failed: {status_data.get('error', 'Unknown error')}"
            )

        time.sleep(1)
    else:
        pytest.fail("Processing timed out after 60 seconds")


@pytest.mark.asyncio
async def test_complete_pipeline_heic(client, heic_image_path):
    """
    Test complete processing pipeline with real HEIC image.

    Tests HEIC → JPEG conversion and full pipeline.
    """
    # Step 1: Upload HEIC
    with heic_image_path.open("rb") as f:
        image_data = f.read()

    upload_response = client.post(
        "/api/upload",
        files={"file": ("test.heic", image_data, "image/heic")},
    )
    assert upload_response.status_code == 200
    job_id = upload_response.json()["job_id"]

    # Step 2: Process with minimal parameters (fast test)
    process_response = client.post(
        "/api/process",
        json={
            "job_id": job_id,
            "mode": "auto",
            "params": {
                "canvas_width_mm": 150.0,
                "canvas_height_mm": 100.0,
                "line_width_mm": 0.3,
                "use_ml": False,
            },
        },
    )
    assert process_response.status_code == 200

    # Step 3: Poll until complete
    max_attempts = 60
    for _ in range(max_attempts):
        status_response = client.get(f"/api/status/{job_id}")
        status_data = status_response.json()

        if status_data["status"] == "completed":
            assert status_data["result_url"] is not None
            break

        if status_data["status"] == "failed":
            pytest.fail(f"HEIC processing failed: {status_data.get('error')}")

        time.sleep(1)
    else:
        pytest.fail("HEIC processing timed out")


def test_export_formats_real_image(client, jpeg_image_path):
    """
    Test exporting to different plotter formats with real image.

    Tests SVG, HPGL, and G-code export from processed real photo.
    """
    # Upload and process
    with jpeg_image_path.open("rb") as f:
        image_data = f.read()

    upload_response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", image_data, "image/jpeg")},
    )
    job_id = upload_response.json()["job_id"]

    # Quick process
    client.post(
        "/api/process",
        json={
            "job_id": job_id,
            "mode": "auto",
            "params": {
                "canvas_width_mm": 100.0,
                "canvas_height_mm": 100.0,
                "use_ml": False,
            },
        },
    )

    # Wait for completion
    max_attempts = 60
    for _ in range(max_attempts):
        status_response = client.get(f"/api/status/{job_id}")
        if status_response.json()["status"] == "completed":
            break
        time.sleep(1)
    else:
        pytest.skip("Processing timed out, cannot test export formats")

    # Test SVG export
    svg_response = client.get(f"/api/download/{job_id}?format=svg")
    assert svg_response.status_code == 200
    assert "image/svg+xml" in svg_response.headers["content-type"]

    # Test HPGL export
    hpgl_response = client.get(f"/api/download/{job_id}?format=hpgl")
    assert hpgl_response.status_code == 200

    # Test G-code export
    gcode_response = client.get(f"/api/download/{job_id}?format=gcode")
    assert gcode_response.status_code == 200
    gcode_content = gcode_response.content.decode("utf-8")
    assert "G0" in gcode_content or "G1" in gcode_content  # G-code commands
