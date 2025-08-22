from setuptools import setup

with open("README.md", "r", encoding="utf-8") as readme_file:
    long_description = readme_file.read()

setup(
    name="soursop",
    version="0.1.0",
    description="A simple tool to count intervals and show current time",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Lahiru Sampath",
    author_email="lsampath210@gmail.com",
    license="MIT",
    packages=["soursop"],
    package_dir={"soursop": "soursop/"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
    ],
    entry_points={
        "console_scripts": [
            "soursop=soursop.cli:main"
        ]
    },
    data_files=[
        ("lib/systemd/system", ["soursop.service"]),        # this might not be required
    ],
    keywords="soursop, counting, time, cli, tool",
    python_requires=">=3.6",
    install_requires=[
        "psutil",
        "scapy",
    ]
)
