from setuptools import setup

setup(name='programaker-telegram-service',
      version='0.1',
      description='Programaker bridge to use Telegram bots.',
      author='kenkeiras',
      author_email='kenkeiras@codigoparallevar.com',
      license='Apache License 2.0',
      packages=['programaker_telegram_service'],
      scripts=['bin/programaker-telegram-service'],
      include_package_data=True,
      install_requires=[
          'python-telegram-bot',
          'programaker-bridge',
          'xdg',
          'sqlalchemy',
      ],
      zip_safe=False)
