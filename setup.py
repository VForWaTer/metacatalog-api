from setuptools import setup, find_packages

def version():
    loc = dict()
    with open('metacatalog_api/__version__.py') as f:
        exec(f.read(), loc, loc)
    return loc['__version__']

setup(
    name='metacatalog-api',
    version=version(),
    license='MIT',
    packages=find_packages(),
    install_requires=open('requirements.txt').read().splitlines(),
    author='Mirko Mälicke',
    author_email='mirko.maelicke@kit.edu',
    description='FastAPI backend for managing a Metacatalog instance',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/vforwater/metacatalog-api',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
    include_package_data=True,
)