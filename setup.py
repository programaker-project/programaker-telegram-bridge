from setuptools import setup

setup(name='plaza-telegram-service',
      version='0.1',
      description='Plaza bridge to use Telegram bots.',
      author='kenkeiras',
      author_email='kenkeiras@codigoparallevar.com',
      license='Apache License 2.0',
      packages=['plaza_telegram_service'],
      scripts=['bin/plaza-telegram-service'],
      include_package_data=True,
      install_requires=[
          'python-telegram-bot',
          'plaza-bridge',
          'xdg',
      ],
      zip_safe=False)
