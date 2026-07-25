from setuptools import setup

package_name = 'trajectory_player'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='inu',
    maintainer_email='inu@example.com',
    description='Trajectory player for UR robot',
    license='MIT',
    entry_points={
        'console_scripts': [
            'play_trajectory = trajectory_player.play_trajectory:main',
        ],
    },
)
