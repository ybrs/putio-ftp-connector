from setuptools import setup

setup(
    name='putioftpserver',
    version='0.2',
    long_description=__doc__,
    packages=['putioftpserver'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    entry_points = {
        'console_scripts': [
            'putio_ftp_server = putioftpserver.connector:run_ftp_server',
        ],
    }
)
