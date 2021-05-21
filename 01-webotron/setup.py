from setuptools import setup

setup(
    name='webotron-80',
    version='0.1',
    author='Robin Norwood',
    description='Webotron 80 is a tool to deploy static web to AWS.',
    license='GPLv3+',
    packages=['webotron'],
    install_requires=['click', 'boto3'],
    entry_points='''
        [console_scripts]
        webotron=webotron.webotron:cli
    '''
)
