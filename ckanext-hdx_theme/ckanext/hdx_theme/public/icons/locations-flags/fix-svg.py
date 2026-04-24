import os
import re
import argparse


def process_svg(content, filename, fix_colors=False):
    # Warn if viewBox is missing
    if 'viewBox' not in content:
        print(f"⚠️  WARNING: {filename} has no viewBox")

    # Remove width and height from <svg ...>
    content = re.sub(
        r'(<svg[^>]*?)\s(width|height)="[^"]+"',
        r'\1',
        content,
        flags=re.IGNORECASE
    )

    if fix_colors:
        # Replace fill (except none)
        content = re.sub(
            r'fill="(?!none)([^"]+)"',
            'fill="currentColor"',
            content,
            flags=re.IGNORECASE
        )

        # Replace stroke (except none)
        content = re.sub(
            r'stroke="(?!none)([^"]+)"',
            'stroke="currentColor"',
            content,
            flags=re.IGNORECASE
        )

    return content


def process_file(filepath, fix_colors):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = process_svg(content, filepath, fix_colors)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)


def main():
    parser = argparse.ArgumentParser(description="Clean SVG files")
    parser.add_argument(
        "--colors",
        action="store_true",
        help="Replace fill/stroke with currentColor"
    )

    args = parser.parse_args()

    for filename in os.listdir('.'):
        if filename.lower().endswith('.svg'):
            print(f"Processing: {filename}")
            process_file(filename, args.colors)

    print("Done!")


if __name__ == "__main__":
    main()
