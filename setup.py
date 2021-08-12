import setuptools

setuptools.setup(
    name="moneyforward",
    version="0.0.1",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': ['moneyforward = moneyforwardcli.main:cli']
    },
    install_requires=[
        'click',
    ],
    python_requires='>=3.9',
)
