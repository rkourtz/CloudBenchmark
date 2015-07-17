# -*- mode: python -*-
import cryptography, os
a = Analysis(['/vagrant/bin/benchmark.py'],
             pathex=['/vagrant/release'],
             hiddenimports=['pkg_resources'],
             hookspath=None,
             runtime_hooks=None)
a.datas += [('data/google-credentials.json', '/vagrant/data/google-credentials.json', 'DATA')]
for file in ['_Cryptography_cffi_a269d620xd5c405b7.so', '_Cryptography_cffi_590da19fxffc7b1ce.so', '_Cryptography_cffi_26cb75b8x62b488b1.so', 'hazmat/bindings/openssl/src/osrandom_engine.c', 'hazmat/bindings/openssl/src/osrandom_engine.h', 'hazmat/primitives/src/constant_time.c', 'hazmat/primitives/src/constant_time.h', 'hazmat/primitives/src/padding.c', 'hazmat/primitives/src/padding.h']:
  a.datas += [("cryptography/%s" % file, os.path.join(os.path.dirname(cryptography.__file__), file), 'BINARY')]

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
