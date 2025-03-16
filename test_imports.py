print("Starting import tests...")

try:
    import pyrogram
    print("✅ Pyrogram imported successfully:", pyrogram.__version__)
except ImportError as e:
    print("❌ Failed to import pyrogram:", str(e))

try:
    import tgcrypto
    print("✅ TgCrypto imported successfully:", tgcrypto.__version__)
except ImportError as e:
    print("❌ Failed to import tgcrypto:", str(e))

try:
    import dotenv
    print("✅ python-dotenv imported successfully:", dotenv.__version__)
except ImportError as e:
    print("❌ Failed to import python-dotenv:", str(e))

try:
    import aiofiles
    print("✅ aiofiles imported successfully:", aiofiles.__version__)
except ImportError as e:
    print("❌ Failed to import aiofiles:", str(e))

try:
    import hachoir
    print("✅ hachoir imported successfully:", hachoir.__version__)
except ImportError as e:
    print("❌ Failed to import hachoir:", str(e))

print("\nPython path:")
import sys
print(sys.path)

print("\nInstalled packages:")
import pkg_resources
print([p.key for p in pkg_resources.working_set]) 