from setuptools import setup

package_name = 'direct_pose'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    package_dir={'': 'src'},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your@email.com',
    description='Move robot to a target pose',
    license='MIT',
    entry_points={
        'console_scripts': [
            'move_to_pose = direct_pose.move_to_pose:main',
        ],
    },
)
