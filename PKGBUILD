# Maintainer: Farosh Ryujinden <https://github.com/FaroshRyujinden>
pkgname=parshine
pkgver=1.0
pkgrel=1
pkgdesc="A professional GTK4/Libadwaita dashboard for Sunshine Host Manager"
arch=('any')
url="https://github.com/FaroshRyujinden/parshine"
license=('GPL')
depends=('python' 'python-gobject' 'libadwaita' 'python-requests' 'gtk4' 'sunshine')
source=("main.py" "backend_api.py" "style.css" "logo.png")
sha256sums=('SKIP' 'SKIP' 'SKIP' 'SKIP')

package() {
  # 1. Cria o diretório de biblioteca e instala os arquivos base
  install -d "${pkgdir}/usr/lib/parshine"
  install -m755 main.py "${pkgdir}/usr/lib/parshine/main.py"
  install -m644 backend_api.py "${pkgdir}/usr/lib/parshine/backend_api.py"
  install -m644 style.css "${pkgdir}/usr/lib/parshine/style.css"
  install -m644 logo.png "${pkgdir}/usr/lib/parshine/logo.png"

  # 2. Cria o Launcher em /usr/bin
  install -d "${pkgdir}/usr/bin"
  echo -e "#!/bin/bash\n/usr/bin/python /usr/lib/parshine/main.py \"\$@\"" > "${pkgdir}/usr/bin/parshine"
  chmod +x "${pkgdir}/usr/bin/parshine"

  # 3. Cria a entrada no Menu de Aplicativos (.desktop)
  install -d "${pkgdir}/usr/share/applications"
  echo -e "[Desktop Entry]\nName=ParShine\nComment=Sunshine Host Manager Dashboard\nExec=parshine\nIcon=parshine\nTerminal=false\nType=Application\nCategories=Settings;System;Network;" > "${pkgdir}/usr/share/applications/parshine.desktop"

  # 4. Instala o ícone no sistema
  install -d "${pkgdir}/usr/share/icons/hicolor/160x160/apps"
  install -m644 logo.png "${pkgdir}/usr/share/icons/hicolor/160x160/apps/parshine.png"
}
