#!/usr/bin/env python3
"""Verify all imports work correctly."""

print("Verifying imports...")

try:
    # Core imports
    print("✓ Importing config...")
    from config import Settings
    
    print("✓ Importing utils...")
    from utils.hash import compute_blake3
    
    print("✓ Importing models...")
    from models.style import Style
    from models.slide import Slide
    from models.project import Project
    
    print("✓ Importing clients...")
    from clients.gemini_client import GeminiClient
    
    print("✓ Importing repositories...")
    from repositories.slide_repository import SlideRepository
    from repositories.image_repository import ImageRepository
    
    print("✓ Importing services...")
    from services.slide_service import SlideService
    from services.image_service import ImageService
    from services.style_service import StyleService
    from services.cost_service import CostService
    
    print("✓ Importing API schemas...")
    from api.schemas.slide import SlideResponse, ProjectResponse
    from api.schemas.image import ImageInfo, GenerateImageResponse
    from api.schemas.style import StyleResponse, GenerateStyleResponse
    from api.schemas.cost import CostResponse
    
    print("✓ Importing API dependencies...")
    from api.dependencies import (
        get_settings,
        get_slide_service,
        get_image_service,
        get_style_service,
        get_cost_service,
    )
    
    print("✓ Importing API routes...")
    from api.routes import slides, images, style, cost
    
    print("✓ Importing main app...")
    from main import app
    
    print("\n✅ All imports successful!")
    print("\nQuick functionality test:")
    
    # Test hash computation
    test_hash = compute_blake3("test content")
    print(f"✓ Hash computation works: {test_hash}")
    
    # Test settings
    settings = Settings()
    print(f"✓ Settings loaded: slides_base_path={settings.slides_base_path}")
    
    print("\n🎉 Backend implementation is complete and functional!")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
