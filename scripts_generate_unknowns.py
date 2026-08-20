import shutil
from pathlib import Path


def main():
    source = Path("dataset_1000/unknown")
    target = Path("dataset_1000/unknown_pool")
    target.mkdir(parents=True, exist_ok=True)
    copied = 0
    for identity in source.glob("*"):
        if not identity.is_dir():
            continue
        dest = target / identity.name
        dest.mkdir(exist_ok=True)
        for image in identity.glob("*.jpg"):
            shutil.copy2(image, dest / image.name)
            copied += 1
    print(f"Prepared {copied} unknown images across {len(list(target.glob('*')))} identities.")


if __name__ == "__main__":
    main()
