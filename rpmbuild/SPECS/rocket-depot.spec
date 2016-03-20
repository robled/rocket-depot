%global srcname rocket-depot
%global sum GTK+ 3 rdesktop/xfreerdp frontend


Name: %{srcname}
Version: 1.0.0
Release: 1%{?dist}
Summary: %{sum}
License: GPLv3+
URL: https://github.com/robled/%{srcname}
Source0: https://github.com/robled/%{srcname}/archive/master.tar.gz
BuildArch: noarch
BuildRequires: python2-devel


%description
Rocket Depot is a simple graphical frontend for rdesktop and FreeRDP with
support for connection profiles. It runs on Linux desktops using GTK and takes
advantage of modern desktop environment features such as Unity Quicklists.


%package -n %{srcname}
Summary: %{sum}


%prep
%autosetup -n %{srcname}-%{version}


%build
%py2_build


%install
%py2_install


%files -n %{srcname}
%license ../LICENSE.md
%doc ../README.txt
%{python2_sitelib}/%{srcname}
%{python2_sitelib}/*.egg-info


%changelog
* Sat Mar 20 2016 David Roble <robled@electronsweatshop.com> 1.0.0-1
- Initial release
