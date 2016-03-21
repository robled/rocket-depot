Name: rocket-depot
Version: 1.0.0
Release: 1%{?dist}
Summary: GTK+ 3 rdesktop/xfreerdp frontend
License: GPLv3
URL: https://github.com/robled/rocket-depot
Source0: https://github.com/robled/rocket-depot/archive/%{version}.tar.gz
BuildArch: noarch
BuildRequires: python2-devel
Requires: pygobject3 hicolor-icon-theme xterm freerdp rdesktop


%description
Rocket Depot is a simple graphical frontend for rdesktop and FreeRDP with
support for connection profiles. It runs on Linux desktops using GTK+ 3 and
takes advantage of modern desktop environment features such as Unity
Quicklists.


%prep
%autosetup -n rocket-depot-%{version}


%build
%py2_build


%install
%py2_install


%files -n rocket-depot
%license LICENSE.md
%doc README.txt
%{python2_sitelib}/rocket_depot-%{version}-py2.7.egg-info
%{_bindir}/rocket-depot
%{_prefix}/share/applications/rocket-depot.desktop
%{_prefix}/share/icons/hicolor/*/apps/rocket-depot.png
%{_prefix}/share/icons/hicolor/scalable/apps/rocket-depot.svg


%changelog
* Sun Mar 20 2016 David Roble <robled@electronsweatshop.com> 1.0.0-1
- Initial release
