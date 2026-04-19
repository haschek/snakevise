import argparse
from src.utils import get_compatible_fonts, check_font_renderable


def list_fonts():
    parser = argparse.ArgumentParser(description="List available fonts for SnakeVISE.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test each font for usability with ImageMagick.",
    )
    args = parser.parse_args()

    try:
        compatible = get_compatible_fonts()

        header = "Available Fonts (with Bold and Italic variants)"
        if args.test:
            header += " [Usability Tested]"

        print(header + ":")
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
            if args.test:
                if check_font_renderable(base):
                    print(f"[OK] {base}")
                else:
                    # Skip broken fonts when testing is enabled
                    pass
            else:
                print(base)

    except Exception as e:
        print(f"Error listing fonts: {e}")


if __name__ == "__main__":
    list_fonts()
