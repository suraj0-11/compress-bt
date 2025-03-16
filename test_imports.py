print("Starting import tests...")

try:
    import sys
    print("Python version:", sys.version)
except Exception as e:
    print("❌ Failed to get Python version:", str(e))

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
print(sys.path)

print("\nInstalled packages:")
try:
    from pip._internal.operations.freeze import freeze
    packages = list(freeze())
    print("\n".join(packages))
except Exception as e:
    print("❌ Failed to list packages:", str(e)) 