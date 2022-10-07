import setuptools
from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="event-backtesting",
    version="0.0.1",
    author="Raul Ikeda",
    description="Simple Event Backtesting Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/raulikeda/EventBacktesting",
    project_urls={
        "Bug Tracker": "https://github.com/raulikeda/EventBacktesting/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    license='MIT',
    install_requires=[],
    setup_requires=['pytest-runner','event-processing'],
    tests_require=['pytest'],
    test_suite='tests',
)
