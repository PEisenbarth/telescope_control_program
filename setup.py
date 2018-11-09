from setuptools import setup

setup(
    name='telescope_control',
    version='1.0.dev0',
    packages=['telescopecontrol'],
    url='',
    license='',
    author='Experimental Radio Cosmology group, Oxford Physics',
    author_email='',
    description='',
    package_data={'telescopecontrol': ['Catalogues/CBASS_Catalogue.csv',
                                       'Catalogues/MESSIER.edb']},
    include_package_data=True,
    install_requires=[
        'katcp',
        'katpoint',
        'numpy',
        'pymodbus',
        'h5py'
    ],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Topic :: Scientific/Engineering :: Physics",
        "Intended Audience :: Science/Research",
    ]
)

