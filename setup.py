import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="neval",
    author="AutoActuary",
    description="Execute raw Python code in an isolated namespace",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AutoActuary/neval",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.4",
    use_scm_version={
        "write_to": "neval/version.py",
    },
    setup_requires=[
        "setuptools_scm",
    ],
    install_requires=[],
)
