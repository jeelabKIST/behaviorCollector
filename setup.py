from setuptools import setup, find_packages


def setup_package():
    setup(
        name="Behavior collector",
        version="0.1.0",
        author="jungyoung",
        description="A package for behavior collector",
        packages=find_packages(),
        python_requires=">=3.10" ,
        install_requires=[
            "pyqt5",
            "numpy",
            "scipy",
            "opencv-python",
            "matplotlib",
            "tqdm"
        ],
        entry_points={
            "console_scripts": [
                "collect_behavior = behaviorCollector.main:main",
            ],
        },
    )

    
if __name__ == "__main__":
    setup_package()