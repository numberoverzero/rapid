import os
from setuptools import setup, find_packages
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "requirements.txt")) as f:
    requirements = f.readlines()


if __name__ == "__main__":
    setup(
        name="rapid",
        version="0",
        author="Joe Cross",
        author_email="joe.mcross@gmail.com",
        url="https://github.com/numberoverzero/rapid",
        license="MIT",
        include_package_data=True,
        packages=find_packages(exclude=("examples",)),
        install_requires=requirements,
    )
