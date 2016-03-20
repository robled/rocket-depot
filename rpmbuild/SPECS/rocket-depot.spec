Name: rocket-depot
Version: 1.0.0
Release: 1%{?dist}
Summary: GTK+ 3 rdesktop/xfreerdp frontend
License: GPLv3+
URL: https://github.com/robled/rocket-depot
Source0: https://github.com/robled/rocket-depot/archive/%{version}.tar.gz
BuildArch: noarch
BuildRequires: python2-devel
Requires: pygobject3 xterm freerdp rdesktop


%description
Rocket Depot is a simple graphical frontend for rdesktop and FreeRDP with
support for connection profiles. It runs on Linux desktops using GTK and takes
advantage of modern desktop environment features such as Unity Quicklists.


%prep
%autosetup -n rocket-depot-%{version}


%build
%py2_build


%install
%py2_install


%files -n rocket-depot
%license LICENSE.md
%doc README.txt
%{_bindir}/rocket-depot
%{_prefix}/share/applications/rocket-depot.desktop
%{_prefix}/share/icons/hicolor/*/apps/rocket-depot.png
#%{_prefix}/share/icons/hicolor/128x128/apps/rocket-depot.png
#%{_prefix}/share/icons/hicolor/16x16/apps/rocket-depot.png
#%{_prefix}/share/icons/hicolor/22x22/apps/rocket-depot.png
#%{_prefix}/share/icons/hicolor/24x24/apps/rocket-depot.png
#%{_prefix}/share/icons/hicolor/256x256/apps/rocket-depot.png
#%{_prefix}/share/icons/hicolor/32x32/apps/rocket-depot.png
#%{_prefix}/share/icons/hicolor/48x48/apps/rocket-depot.png
#%{_prefix}/share/icons/hicolor/64x64/apps/rocket-depot.png
#%{_prefix}/share/icons/hicolor/scalable/apps/rocket-depot.svg


%changelog
* Sun Mar 20 2016 David Roble <robled@electronsweatshop.com> 1.0.0-1
- Initial release
