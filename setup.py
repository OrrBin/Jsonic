import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jsonical",
    version="0.0.2",
    author="Orr Benyamini",
    author_email="orrbenyamini@gmail.com",
    description="lightweight utility for serializing/deserializing python objects to/from JSON",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OrrBin/Jsonic",
    packages=['jsonic'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)