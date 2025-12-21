import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="py-jsonic",
    version="1.0.1",
    author="Orr Benyamini",
    author_email="orrbenyamini@gmail.com",
    description="lightweight utility for JSON serialization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OrrBin/Jsonic",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)