# -*- mode: python -*-

a = Analysis(['/vagrant/bin/benchmark.py'],
             pathex=['/vagrant/release'],
             hiddenimports=['pkg_resources'],
             hookspath=None,
             runtime_hooks=None)
a.datas += [('data/google-credentials.json', '/vagrant/data/google-credentials.json', 'DATA')]

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='benchmark',
          debug=False,
          strip=None,
          upx=True,
          console=True )
