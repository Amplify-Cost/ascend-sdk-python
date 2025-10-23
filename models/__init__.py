"""
Models Package
Provides organized structure while maintaining backward compatibility with root models.py
"""
import sys
import os
import importlib.util  # ← Fixed: explicit import

# Add parent directory to path to access root models.py
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import ALL models from root models.py and re-export them
try:
    # Import the root-level models module
    root_models_path = os.path.join(parent_dir, 'models.py')
    
    spec = importlib.util.spec_from_file_location('root_models', root_models_path)
    root_models = importlib.util.module_from_spec(spec)
    sys.modules['root_models'] = root_models
    spec.loader.exec_module(root_models)
    
    # Get all public attributes from root models
    model_exports = [attr for attr in dir(root_models) if not attr.startswith('_')]
    
    # Re-export everything
    for attr_name in model_exports:
        globals()[attr_name] = getattr(root_models, attr_name)
    
    # Explicitly define __all__ for clarity
    __all__ = model_exports
    
except Exception as e:
    import traceback
    print(f"ERROR loading models: {e}")
    traceback.print_exc()
    raise ImportError(f"Failed to load models from root models.py: {e}")
