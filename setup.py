from setuptools import setup
from upstream.__init__ import VERSION

setup(
    name="upstream",
    version=VERSION,
    description="UpDog-like client with a design and features for the 21th century.",
    author="PaddeCraft",
    packages=["upstream"],
    install_requires=["rich", "flask", "typer", "log4py @ https://api.github.com/repos/PaddeCraft/Log4py/zipball"],
    include_package_data=True,
)
