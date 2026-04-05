from src.utils import get_compatible_fonts


def list_fonts():
    try:
        compatible = get_compatible_fonts()

        print("Available Fonts (with Bold and Italic variants):")
        print("-" * 60)

        if not compatible:
            print("No fonts found that satisfy both Bold and Italic requirements.")
            print("\nTroubleshooting:")
            print(
                "1. Ensure ImageMagick is installed ('convert' or 'magick' command should work)."
            )
            print(
                "2. On Linux, check /etc/ImageMagick-7/policy.xml (or similar) to ensure 'read/write' is allowed for 'path' or 'label'."
            )
            return

        for base in compatible:
            print(base)

    except Exception as e:
        print(f"Error listing fonts: {e}")


if __name__ == "__main__":
    list_fonts()
