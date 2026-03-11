from setuptools import setup
from glob import glob

package_name = 'pick_n_place_perception'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', [f'resource/{package_name}']),
        (f'share/{package_name}', ['package.xml']),
        (f'share/{package_name}/launch', glob('launch/*.py')),
        (f'share/{package_name}/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@email.com',
    description='Block detection using OpenCV HSV filtering for pick and place',
    license='MIT',
    entry_points={
        'console_scripts': [
            'block_detector = pick_n_place_perception.block_detector:main',
        ],
    },
)
