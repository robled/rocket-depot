Name: rocket-depot
Version: 849654dd321f070c92a569e26aa0d8a5e114eeb1
Release: 1%{?dist}
Summary: GTK+ 3 rdesktop/xfreerdp frontend
License: GPLv3
URL: https://github.com/robled/rocket-depot
Source0: https://github.com/robled/rocket-depot/archive/%{version}.tar.gz
BuildArch: noarch
BuildRequires: python3-devel
Requires: python3-gobject hicolor-icon-theme xterm freerdp rdesktop


%description
Rocket Depot is a simple graphical frontend for rdesktop and FreeRDP with
support for connection profiles. It runs on Linux desktops using GTK+ 3 and
takes advantage of modern desktop environment features such as Unity
Quicklists.


%prep
%autosetup -n rocket-depot-%{version}


%build
%py3_build


%install
%py3_install


%files -n rocket-depot
%license LICENSE.md
%doc README.txt
%{python3_sitelib}/rocket_depot-1.0.0-py%{python3_version}.egg-info
%{_bindir}/rocket-depot
%{_prefix}/share/applications/rocket-depot.desktop
%{_prefix}/share/icons/hicolor/*/apps/rocket-depot.png
%{_prefix}/share/icons/hicolor/scalable/apps/rocket-depot.svg


%changelog
* Tue Jun 22 2021 Manuel Bachmann <tarnyko@tarnyko.net> 849654dd321f070c92a569e26aa0d8a5e114eeb1-1
- First Python 3.x release
* Sun Mar 20 2016 David Roble <robled@electronsweatshop.com> 1.0.0-1
- Initial release
