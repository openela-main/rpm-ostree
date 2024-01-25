# The canonical copy of this spec file is upstream at:
# https://github.com/coreos/rpm-ostree/blob/main/packaging/rpm-ostree.spec.in

Summary:              Hybrid image/package system
Name:                 rpm-ostree
Version:              2022.10.117.g52714b51
Release:              2%{?dist}
License:              LGPLv2+
URL:                  https://github.com/coreos/rpm-ostree
# This tarball is generated via "cd packaging && make -f Makefile.dist-packaging dist-snapshot"
# in the upstream git.  It also contains vendored Rust sources.  This is generated from the "rhel8" branch.
Source0:              https://github.com/coreos/rpm-ostree/releases/download/v%{version}/rpm-ostree-%{version}.tar.xz

Patch0:               0001-override-Honor-install-in-container-case-too.patch
Patch1:               0002-scripts-also-ignore-kernel-debug-modules.posttrans.patch

ExclusiveArch:        %{rust_arches}

BuildRequires:        make
%if 0%{?rhel} && !0%{?eln}
BuildRequires:        rust-toolset
%else
BuildRequires:        rust-packaging
BuildRequires:        cargo
BuildRequires:        rust
%endif

# Enable ASAN + UBSAN
%bcond_with sanitizers
# Embedded unit tests
%bcond_with bin_unit_tests

# This is copied from the libdnf spec
%if 0%{?rhel} && ! 0%{?centos}
%bcond_without rhsm
%else
%bcond_with rhsm
%endif

# RHEL8 doesn't ship zchunk today.  See also the comments
# in configure.ac around this as libdnf/librepo need to be in
# sync, and today we bundle libdnf but not librepo.
%if 0%{?rhel} && 0%{?rhel} <= 8
%bcond_with zchunk
%else
%bcond_without zchunk
%endif

%if 0%{?fedora} >= 34
%define sqlite_rpmdb_default "--enable-sqlite-rpmdb-default"
%endif

# For the autofiles bits below
BuildRequires:        /usr/bin/python3
# We always run autogen.sh
BuildRequires:        autoconf automake libtool git
# For docs
BuildRequires:        chrpath
BuildRequires:        gtk-doc
BuildRequires:        gnome-common
BuildRequires:        /usr/bin/g-ir-scanner
# Core requirements
# One way to check this: `objdump -p /path/to/rpm-ostree | grep LIBOSTREE` and pick the highest (though that might miss e.g. new struct members)
BuildRequires:        pkgconfig(ostree-1) >= 2020.7
BuildRequires:        pkgconfig(polkit-gobject-1)
BuildRequires:        pkgconfig(json-glib-1.0)
BuildRequires:        pkgconfig(rpm) >= 4.14.0
BuildRequires:        pkgconfig(libarchive)
BuildRequires:        pkgconfig(libsystemd)
BuildRequires:        libcap-devel
BuildRequires:        libattr-devel
BuildRequires: libassuan

# We currently interact directly with librepo (libdnf below also pulls it in,
# but duplicating to be clear)
BuildRequires:        pkgconfig(librepo)

# Needed by curl-rust
BuildRequires:        pkgconfig(libcurl)

BuildRequires:        cmake
BuildRequires:        pkgconfig(expat)
BuildRequires:        pkgconfig(check)

# We use some libsolv types directly too (libdnf below also pulls it in,
# but duplicating to be clear)
BuildRequires:        pkgconfig(libsolv)

# We need g++ for libdnf
BuildRequires:        gcc-c++


# more libdnf build deps (see libdnf's spec for versions; maintain ordering)
%global libsolv_version 0.7.17
%global libmodulemd_version 2.11.2-2
%global librepo_version 1.13.0
%global swig_version 3.0.12
BuildRequires:        swig >= %{swig_version}
BuildRequires:        pkgconfig(modulemd-2.0) >= %{libmodulemd_version}
BuildRequires:        pkgconfig(librepo) >= %{librepo_version}
BuildRequires:        libsolv-devel >= %{libsolv_version}
BuildRequires:        pkgconfig(json-c)
BuildRequires:        pkgconfig(cppunit)
BuildRequires:        pkgconfig(sqlite3)
BuildRequires:        pkgconfig(smartcols)
%if %{with zchunk}
BuildRequires:        pkgconfig(zck) >= 0.9.11
%endif
BuildRequires:        gpgme-devel
%if 0%{?rhel} <= 8
# In current Fedora, this is a dependency of gpgme-devel, but
# not in RHEL8.  Missing this package breaks -znow.
BuildRequires:        libassuan-devel
%endif
%if %{with rhsm}
BuildRequires:        pkgconfig(librhsm) >= 0.0.3
%endif

# Runtime libdnf deps
Requires:             libmodulemd%{?_isa} >= %{libmodulemd_version}
Requires:             libsolv%{?_isa} >= %{libsolv_version}
Requires:             librepo%{?_isa} >= %{librepo_version}

# For now...see https://github.com/projectatomic/rpm-ostree/pull/637
# and https://github.com/fedora-infra/fedmsg-atomic-composer/pull/17
# etc.  We'll drop this dependency at some point in the future when
# rpm-ostree wraps more of ostree (such as `ostree admin unlock` etc.)
Requires:             ostree
Requires:             bubblewrap
Requires:             fuse

Requires:             %{name}-libs%{?_isa} = %{version}-%{release}

%description
rpm-ostree is a hybrid image/package system.  It supports
"composing" packages on a build server into an OSTree repository,
which can then be replicated by client systems with atomic upgrades.
Additionally, unlike many "pure" image systems, with rpm-ostree
each client system can layer on additional packages, providing
a "best of both worlds" approach.

%package libs
Summary:              Shared library for rpm-ostree

%description libs
The %{name}-libs package includes the shared library for %{name}.

%package devel
Summary:              Development headers for %{name}
Requires:             %{name}-libs%{?_isa} = %{version}-%{release}

%description devel
The %{name}-devel package includes the header files for %{name}-libs.

%prep
%autosetup -Sgit -n %{name}-%{version}

%build
env NOCONFIGURE=1 ./autogen.sh
# Since we're hybrid C++/Rust we need to propagate this manually;
# the %%configure macro today assumes (reasonably) that one is building
# C/C++ and sets C{,XX}FLAGS
%if 0%{?build_rustflags:1}
export RUSTFLAGS="%{build_rustflags}"
%endif
%configure --disable-silent-rules --enable-gtk-doc %{?rpmdb_default} %{?with_sanitizers:--enable-sanitizers}  %{?with_bin_unit_tests:--enable-bin-unit-tests} \
  %{?with_rhsm:--enable-featuresrs=rhsm}

%make_build

%install
%make_install INSTALL="install -p -c"
find $RPM_BUILD_ROOT -name '*.la' -delete

# I try to do continuous delivery via rpmdistro-gitoverlay while
# reusing the existing spec files.  Currently RPM only supports
# mandatory file entries.  What this is doing is making each file
# entry optional - if it exists it will be picked up.  That
# way the same spec file works more easily across multiple versions where e.g. an
# older version might not have a systemd unit file.
cat > autofiles.py <<EOF
import os,sys,glob
os.chdir(os.environ['RPM_BUILD_ROOT'])
for line in sys.argv[1:]:
    if line == '':
        break
    if line[0] != '/':
        sys.stdout.write(line + '\n')
    else:
        files = glob.glob(line[1:])
        if len(files) > 0:
            sys.stderr.write('{0} matched {1} files\n'.format(line, len(files)))
            sys.stdout.write(line + '\n')
        else:
            sys.stderr.write('{0} did not match any files\n'.format(line))
EOF
PYTHON=python3
if ! test -x /usr/bin/python3; then
    PYTHON=python2
fi
$PYTHON autofiles.py > files \
  '%{_bindir}/*' \
  '%{_libdir}/%{name}' \
  '%{_mandir}/man*/*' \
  '%{_datadir}/dbus-1/system.d/*' \
  '%{_sysconfdir}/rpm-ostreed.conf' \
  '%{_prefix}/lib/systemd/system/*' \
  '%{_libexecdir}/rpm-ostree*' \
  '%{_libexecdir}/libostree/ext/*' \
  '%{_datadir}/polkit-1/actions/*.policy' \
  '%{_datadir}/dbus-1/system-services' \
  '%{_datadir}/bash-completion/completions/*'

$PYTHON autofiles.py > files.lib \
  '%{_libdir}/*.so.*' \
  '%{_libdir}/girepository-1.0/*.typelib'

$PYTHON autofiles.py > files.devel \
  '%{_libdir}/lib*.so' \
  '%{_includedir}/*' \
  '%{_datadir}/dbus-1/interfaces/org.projectatomic.rpmostree1.xml' \
  '%{_libdir}/pkgconfig/*' \
  '%{_datadir}/gtk-doc/html/*' \
  '%{_datadir}/gir-1.0/*-1.0.gir'

%files -f files
%doc COPYING.GPL COPYING.LGPL LICENSE README.md

%files libs -f files.lib

%files devel -f files.devel

%changelog
* Mon Aug 07 2023 Joseph Marrero <jmarrero@fedoraproject.org> - 2022.10.117.g52714b51-2
- Backport fb97c48f3 & eae7e1d8
  https://github.com/coreos/rpm-ostree/commit/fb97c48f3cd070c1ad559f3f43f86ad6548f6b02
  https://github.com/coreos/rpm-ostree/commit/eae7e1d8d692b5ce6d3d6eef29abbd7512ae4682
  Resolves: rhbz#2229804

* Sun Apr 30 2023 Joseph Marrero <jmarrero@fedoraproject.org> - 2022.10.117.g52714b51-1
- Sync to latest rhel8 branch
  Resolves: rhbz#2192235

* Thu Feb 16 2023 Colin Walters <walters@verbum.org> - 2022.10.112.g3d0ac35b-3
- Cherry pick
  https://github.com/coreos/rpm-ostree/pull/4311/commits/a0f1275dfbd835b704355d095e610ac1f1254f25
  Resolves: rhbz#2170579

* Tue Feb 14 2023 Colin Walters <walters@verbum.org> - 2022.10.112.g3d0ac35b-2
- Sync to latest rhel8 branch
  Resolves: rhbz#2169429

* Fri Oct 14 2022 Colin Walters <walters@verbum.org> - 2022.10.99.g0049dbdd-3
- Resolves: rhbz#2134630

* Wed Sep 28 2022 Colin Walters <walters@verbum.org> - 2022.10.97.gade6df33-2
- Update to latest https://github.com/coreos/rpm-ostree/tree/rhel8 at commit
  https://github.com/coreos/rpm-ostree/commit/ac182cb920f84946bb155e9cf061db7f5f26e917
- Resolves: rhbz#2122289

* Wed Aug 31 2022 Colin Walters <walters@verbum.org> - 2022.10.94.g89f58028-2
- Update to latest https://github.com/coreos/rpm-ostree/tree/rhel8 at commit
  https://github.com/coreos/rpm-ostree/commit/89f58028f0bea5b6fa59bdb3506078e09957ec00
- Resolves: rhbz#2122289
- Resolves: rhbz#2122299

* Tue Aug 16 2022 Colin Walters <walters@verbum.org> - 2022.10.90.g4abaf4b4-4
- Update to latest https://github.com/coreos/rpm-ostree/tree/rhel8 at commit
  https://github.com/coreos/rpm-ostree/commit/4abaf4b4
  Resolves: rhbz#2118774

* Tue Jul 19 2022 Colin Walters <walters@verbum.org> - 2022.10.86.gd8f0c67a-3
- Update to latest https://github.com/coreos/rpm-ostree/tree/rhel8 at commit
  https://github.com/coreos/rpm-ostree/commit/d8f0c67a0eba32281c9f2782a286e06486a4b909
  Resolves: rhbz#2105414

* Wed Jun 15 2022 Colin Walters <walters@verbum.org> - 2022.2.8.gd50a74bd-2
- Update to latest rhel8 branch
  https://github.com/coreos/rpm-ostree/pull/3749
  https://github.com/coreos/rpm-ostree/pull/3751
  Resolves: rhbz#2095528

* Mon Feb 07 2022 Colin Walters <walters@verbum.org> - 2022.2-2
- Rebase to 2022.1

* Tue Jan 11 2022 Colin Walters <walters@verbum.org> - 2022.1-2
- Rebase to 2022.1
  Resolves: rhbz#2032594

* Wed Dec 15 2021 Colin Walters <walters@verbum.org> - 2021.14-3
- Rebase to 2021.14
  Resolves: rhbz#2032594

* Fri Jun 18 2021 Luca BRUNO <lucab@redhat.com> - 2021.5-2
- Backport _dbpath fixes, see
  https://github.com/coreos/rpm-ostree/issues/2904
  Resolves: rhbz#1973579

* Wed May 12 2021 Luca BRUNO <lucab@lucabruno.net> - 2021.5-1
- New upstream version
  https://github.com/coreos/rpm-ostree/releases/tag/v2021.5
  Resolves: rhbz#1959874

* Tue Mar 30 2021 Colin Walters <walters@verbum.org> - 2020.7-4
- Backport https://github.com/coreos/rpm-ostree/pull/2386/commits/aa8e49aaeddfc5d38651fa08f46e059655818fd1
  Resolves: #1944760

* Thu Nov 05 2020 Colin Walters <walters@verbum.org> - 2020.7-2
- Update to 2020.7
  Resolves: #1894061

* Wed Jul 29 2020 Jonathan Lebon <jonathan@jlebon.com> - 2020.4-1
- New upstream version
  https://github.com/coreos/rpm-ostree/releases/tag/v2020.4
  Resolves: #1861786

* Fri May 15 2020 Colin Walters <walters@verbum.org> - 2020.2-2
- https://github.com/coreos/rpm-ostree/releases/tag/v2020.2
  Resolves: #1827712

* Tue Mar 03 2020 Colin Walters <walters@verbum.org> - 2019.6-8
- Backport patches for initramfs /etc
  Resolves: #1808459

* Thu Feb 27 2020 Colin Walters <walters@verbum.org> - 2019.6-7
- Backport f295f543064f1a0b5833fefccd6bb203b3527623
  Resolves: #1807487

* Thu Dec 05 2019 Jonathan Lebon <jlebon@redhat.com> - 2019.6-6
- Backport dracut mknod patch for FIPS:
  https://github.com/coreos/rpm-ostree/pull/1946

* Thu Oct 31 2019 Jonathan Lebon <jlebon@redhat.com> - 2019.6-5
- Backport HMAC patch for FIPS:
  https://github.com/coreos/rpm-ostree/pull/1934

* Fri Oct 18 2019 Colin Walters <walters@verbum.org> - 2019.6-4
- Backport zchunk patch

* Tue Oct 15 2019 Colin Walters <walters@verbum.org> - 2019.6-3
- https://github.com/coreos/rpm-ostree/releases/tag/v20196
- Backport zstd patch

* Fri May 17 2019 Jonathan Lebon <jlebon@redhat.com> - 2019.3-3
- Rebuild for rhel-8.1.0 branch

* Fri Mar 29 2019 Colin Walters <walters@verbum.org> - 2019.3-2
- Backport patch for pivot rebases

* Wed Mar 27 2019 Jonathan Lebon <jonathan@jlebon.com> - 2019.3-1
- New upstream version

* Thu Feb 14 2019 Jonathan Lebon <jonathan@jlebon.com> - 2019.2-1
- New upstream version

* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 2019.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Tue Jan 22 2019 Jonathan Lebon <jonathan@jlebon.com> - 2019.1-1
- New upstream version

* Fri Dec 14 2018 Jonathan Lebon <jonathan@jlebon.com> - 2018.10-1
- New upstream version

* Tue Dec 04 2018 Jonathan Lebon <jonathan@jlebon.com>
- Simplify Rust conditionals

* Fri Nov 02 2018 Jonathan Lebon <jonathan@jlebon.com> - 2018.9-3
- Backport patch for https://pagure.io/dusty/failed-composes/issue/956

* Tue Oct 30 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 2018.9-2
- Rebuild for libsolv 0.7

* Sun Oct 28 2018 Jonathan Lebon <jonathan@jlebon.com> - 2018.9-1
- New upstream version

* Mon Oct 15 2018 Jonathan Lebon <jonathan@jlebon.com> - 2018.8-2
- Add new source and patch to drop cbindgen requirement

* Tue Sep 11 2018 Jonathan Lebon <jonathan@jlebon.com> - 2018.8-1
- New upstream version

* Thu Aug 09 2018 Jonathan Lebon <jonathan@jlebon.com> - 2018.7-1
- New upstream version

* Wed Aug 01 2018 Jonathan Lebon <jonathan@jlebon.com> - 2018.6.42.gda27b94b-1
- git master snapshot for https://bugzilla.redhat.com/show_bug.cgi?id=1565647

* Mon Jul 30 2018 Colin Walters <walters@verbum.org> - 2018.6-4
- Backport patch for https://bugzilla.redhat.com/show_bug.cgi?id=1607223
  from https://github.com/projectatomic/rpm-ostree/pull/1469
- Also https://github.com/projectatomic/rpm-ostree/pull/1461

* Mon Jul 16 2018 Colin Walters <walters@verbum.org> - 2018.6-3
- Make build python3-only compatible for distributions that want that

* Fri Jun 29 2018 Jonathan Lebon <jonathan@jlebon.com> - 2018.6-2
- Rebuild for yummy Rusty bitsy

* Fri Jun 29 2018 Jonathan Lebon <jonathan@jlebon.com> - 2018.6-1
- New upstream version

* Tue May 15 2018 Jonathan Lebon <jonathan@jlebon.com> - 2018.5-1
- New upstream version

* Mon Mar 26 2018 Jonathan Lebon <jonathan@jlebon.com> - 2018.4-1
- New upstream version

* Sun Mar 18 2018 Iryna Shcherbina <ishcherb@redhat.com> - 2018.3-4
- Update Python 2 dependency declarations to new packaging standards
  (See https://fedoraproject.org/wiki/FinalizingFedoraSwitchtoPython3)

* Wed Mar 07 2018 Jonathan Lebon <jlebon@redhat.com> - 2018.3-3
- Add BR on gcc-c++

* Thu Mar 01 2018 Dusty Mabe <dusty@dustymabe.com> - 2018.3-2
- backport treating FUSE as netfs
- See https://github.com/projectatomic/rpm-ostree/pull/1285

* Sun Feb 18 2018 Jonathan Lebon <jlebon@redhat.com> - 2018.3-1
- New upstream version (minor bugfix release)

* Fri Feb 16 2018 Jonathan Lebon <jlebon@redhat.com> - 2018.2-1
- New upstream version

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2018.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Jan 19 2018 Dusty Mabe <dusty@dustymabe.com> - 2018.1-2
- Revert the ostree:// formatting in the output.
- See https://github.com/projectatomic/rpm-ostree/pull/1136#issuecomment-358122137

* Mon Jan 15 2018 Colin Walters <walters@verbum.org> - 2018.1-1
- https://github.com/projectatomic/rpm-ostree/releases/tag/v2018.1

* Tue Dec 05 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.11-1
- New upstream version

* Wed Nov 22 2017 Colin Walters <walters@verbum.org> - 2017.10-3
- Backport patch for NFS issues
- https://pagure.io/atomic-wg/issue/387

* Sun Nov 12 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.10-2
- Backport fix for --repo handling
  https://github.com/projectatomic/rpm-ostree/pull/1101

* Thu Nov 02 2017 Colin Walters <walters@verbum.org> - 2017.10-1
- https://github.com/projectatomic/rpm-ostree/releases/tag/v2017.10

* Mon Sep 25 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.9-1
- New upstream version

* Mon Aug 21 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.8-2
- Patch to allow metadata_expire=0
  https://github.com/projectatomic/rpm-ostree/issues/930

* Fri Aug 18 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.8-1
- New upstream version

* Thu Aug 10 2017 Igor Gnatenko <ignatenko@redhat.com> - 2017.7-7
- Rebuilt for RPM soname bump

* Thu Aug 10 2017 Igor Gnatenko <ignatenko@redhat.com> - 2017.7-6
- Rebuilt for RPM soname bump

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2017.7-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2017.7-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jul 21 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.7-3
- Tweak new pkg name to rpm-ostree-libs to be more consistent with the main
  package name and ostree's ostree-libs.

* Fri Jul 21 2017 Colin Walters <walters@verbum.org> - 2017.7-2
- Enable introspection, rename shared lib to librpmostree
  Due to an oversight, we were not actually building with introspection.
  Fix that.  And while we are here, split out a shared library package,
  so that e.g. containers can do `from gi.repository import RpmOstree`
  without dragging in the systemd service, etc. (RHBZ#1473701)

* Mon Jul 10 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.7-1
- New upstream version

* Sat Jun 24 2017 Colin Walters <walters@verbum.org>
- Update to git snapshot to help debug compose failure

* Wed May 31 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.6-3
- Make sure we don't auto-provide libdnf (RHBZ#1457089)

* Fri May 26 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.6-2
- Bump libostree dep

* Fri May 26 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.6-1
- New upstream version

* Fri Apr 28 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.5-2
- Bump libostree dep and rebuild in override

* Fri Apr 28 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.5-1
- New upstream version

* Fri Apr 14 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.4-2
- Backport patch to allow unprivileged `rpm-ostree status`

* Thu Apr 13 2017 Jonathan Lebon <jlebon@redhat.com> - 2017.4-1
- New upstream version.

* Fri Apr 07 2017 Colin Walters <walters@verbum.org> - 2017.3-4
- Backport patch to add API devices for running on CentOS 7
  https://github.com/projectatomic/rpm-ostree/issues/727

* Thu Mar 16 2017 Colin Walters <walters@verbum.org> - 2017.3-3
- Add patch to fix f26 altfiles

* Fri Mar 10 2017 Colin Walters <walters@verbum.org> - 2017.3-2
- Backport patch for running in koji

* Mon Mar 06 2017 Colin Walters <walters@verbum.org> - 2017.3-1
- New upstream version
  Fixes: CVE-2017-2623
  Resolves: #1422157

* Fri Mar 03 2017 Colin Walters <walters@verbum.org> - 2017.2-5
- Add patch to bump requires for ostree

* Mon Feb 27 2017 Colin Walters <walters@verbum.org> - 2017.2-4
- Add requires on ostree

* Sat Feb 18 2017 Colin Walters <walters@verbum.org> - 2017.2-3
- Add patch for gperf 3.1 compatibility
  Resolves: #1424268

* Wed Feb 15 2017 Colin Walters <walters@verbum.org> - 2017.2-2
- New upstream version

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2017.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Jan 27 2017 Colin Walters <walters@verbum.org> - 2017.1-3
- Back out netns usage for now for https://pagure.io/releng/issue/6602

* Sun Jan 22 2017 Colin Walters <walters@verbum.org> - 2017.1-2
- New upstream version

* Mon Dec 12 2016 walters@redhat.com - 2016.13-1
- New upstream version

* Sat Nov 26 2016 walters@redhat.com - 2016.12-4
- Backport patch to fix install-langs

* Tue Nov 15 2016 walters@redhat.com - 2016.11-2
- New upstream version

* Mon Oct 24 2016 walters@verbum.org - 2016.11-1
- New upstream version

* Fri Oct 07 2016 walters@redhat.com - 2016.10-1
- New upstream version

* Thu Sep 08 2016 walters@redhat.com - 2016.9-1
- New upstream version

* Thu Sep 08 2016 walters@redhat.com - 2016.8-1
- New upstream version

* Thu Sep 01 2016 walters@redhat.com - 2016.7-4
- Add requires on fuse https://github.com/projectatomic/rpm-ostree/issues/443

* Wed Aug 31 2016 Colin Walters <walters@verbum.org> - 2016.7-3
- Backport patch for running inside mock

* Sat Aug 13 2016 walters@redhat.com - 2016.6-3
- New upstream version

* Sat Aug 13 2016 Colin Walters <walters@verbum.org> - 2016.6-2
- Backport patches from master to fix non-containerized composes

* Thu Aug 11 2016 walters@redhat.com - 2016.6-1
- New upstream version

* Mon Jul 25 2016 Colin Walters <walters@verbum.org> - 2016.5-1
- New upstream version

* Fri Jul 08 2016 walters@verbum.org - 2016.4-2
- Require bubblewrap

* Fri Jul 08 2016 walters@redhat.com - 2016.4-1
- New upstream version

* Thu Jul 07 2016 Colin Walters <walters@verbum.org> - 2016.3.5.g4219a96-1
- Backport fixes from https://github.com/projectatomic/rpm-ostree/commits/2016.3-fixes

* Wed Jun 15 2016 Colin Walters <walters@verbum.org> - 2016.3.3.g17fb980-2
- Backport fixes from https://github.com/projectatomic/rpm-ostree/commits/2016.3-fixes

* Fri May 20 2016 Colin Walters <walters@redhat.com> - 2016.3-2
- New upstream version

* Thu Mar 31 2016 Colin Walters <walters@redhat.com> - 2016.1-3
- Backport patch to fix Fedora composes writing data into source file:/// URIs

* Thu Mar 24 2016 Colin Walters <walters@redhat.com> - 2016.1-2
- New upstream version

* Tue Feb 23 2016 Colin Walters <walters@redhat.com> - 2015.11.43.ga2c052b-2
- New git snapshot, just getting some new code out there
- We are now bundling a copy of libhif, as otherwise coordinated releases with
  PackageKit/dnf would be required, and we are not ready for that yet.

* Wed Feb 10 2016 Matthew Barnes <mbarnes@redhat.com> - 2015.11-3
- Fix URL: https://github.com/projectatomic/rpm-ostree

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2015.11-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Dec 15 2015 Colin Walters <walters@redhat.com> - 2015.11-1
- New upstream version

* Sat Nov 21 2015 Colin Walters <walters@redhat.com> - 2015.10-1
- New upstream version

* Mon Nov 09 2015 Colin Walters <walters@redhat.com> - 2015.9-4
- Fix files list for -devel, which should in turn fix Anaconda
  builds which pull in rpm-ostree, but should not have devel bits.

* Sat Oct 31 2015 Colin Walters <walters@redhat.com> - 2015.9-3
- Add patch that should fix bodhis use of --workdir-tmpfs

* Sat Sep 05 2015 Kalev Lember <klember@redhat.com> - 2015.9-2
- Rebuilt for librpm soname bump

* Wed Aug 26 2015 Colin Walters <walters@redhat.com> - 2015.9-2
- New upstream version

* Tue Aug 04 2015 Colin Walters <walters@redhat.com> - 2015.8-1
- New upstream version

* Mon Jul 27 2015 Colin Walters <walters@redhat.com> - 2015.7-5
- rebuilt

* Mon Jul 20 2015 Colin Walters <walters@redhat.com> - 2015.7-4
- Rebuild for CentOS update to libhif

* Tue Jun 16 2015 Colin Walters <walters@redhat.com> - 2015.7-3
- Rebuild to pick up hif_source_set_required()

* Mon Jun 15 2015 Colin Walters <walters@redhat.com> - 2015.7-2
- New upstream version

* Tue Jun 09 2015 Colin Walters <walters@redhat.com> - 2015.6-2
- New upstream version

* Tue May 12 2015 Colin Walters <walters@redhat.com> - 2015.5-3
- Add patch to fix rawhide composes

* Mon May 11 2015 Colin Walters <walters@redhat.com> - 2015.5-2
- New upstream release
  Adds shared library and -devel subpackage

* Fri Apr 10 2015 Colin Walters <walters@redhat.com> - 2015.4-2
- New upstream release
  Port to libhif, drops dependency on yum.

* Thu Apr 09 2015 Colin Walters <walters@redhat.com> - 2015.3-8
- Cherry pick f21 patch to disable read only /etc with yum which
  breaks when run inside docker

* Wed Apr 08 2015 Colin Walters <walters@redhat.com> - 2015.3-7
- Add patch to use yum-deprecated
  Resolves: #1209695

* Fri Feb 27 2015 Colin Walters <walters@redhat.com> - 2015.3-5
- Drop /usr/bin/atomic, now provided by the "atomic" package

* Fri Feb 06 2015 Dennis Gilmore <dennis@ausil.us> - 2015.3-4
- add git to BuildRequires

* Thu Feb 05 2015 Colin Walters <walters@redhat.com> - 2015.3-3
- Adapt to Hawkey 0.5.3 API break

* Thu Feb 05 2015 Dennis Gilmore <dennis@ausil.us> - 2015.3-3
- rebuild for libhawkey soname bump

* Fri Jan 23 2015 Colin Walters <walters@redhat.com> - 2015.3-2
- New upstream release

* Thu Jan 08 2015 Colin Walters <walters@redhat.com> - 2015.2-1
- New upstream release

* Wed Dec 17 2014 Colin Walters <walters@redhat.com> - 2014.114-2
- New upstream release

* Tue Nov 25 2014 Colin Walters <walters@redhat.com> - 2014.113-1
- New upstream release

* Mon Nov 24 2014 Colin Walters <walters@redhat.com> - 2014.112-1
- New upstream release

* Mon Nov 17 2014 Colin Walters <walters@redhat.com> - 2014.111-1
- New upstream release

* Fri Nov 14 2014 Colin Walters <walters@redhat.com> - 2014.110-1
- New upstream release

* Fri Oct 24 2014 Colin Walters <walters@redhat.com> - 2014.109-1
- New upstream release

* Sat Oct 04 2014 Colin Walters <walters@redhat.com> - 2014.107-2
- New upstream release

* Mon Sep 08 2014 Colin Walters <walters@redhat.com> - 2014.106-3
- New upstream release
- Bump requirement on ostree

* Mon Aug 18 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2014.105-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Aug 08 2014 Colin Walters <walters@verbum.org> - 2014.105-2
- New upstream release

* Sun Jul 13 2014 Colin Walters <walters@verbum.org>
- New upstream release

* Sat Jun 21 2014 Colin Walters <walters@verbum.org>
- New upstream release
- Bump OSTree requirements
- Enable hawkey package diff, we have new enough versions
  of libsolv/hawkey
- Enable /usr/bin/atomic symbolic link

* Tue Jun 10 2014 Colin Walters <walters@verbum.org>
- New upstream git snapshot

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2014.101-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Fri May 30 2014 Colin Walters <walters@verbum.org>
- New upstream release

* Fri May 23 2014 Colin Walters <walters@verbum.org>
- Previous autobuilder code is split off into rpm-ostree-toolbox

* Sun Apr 13 2014 Colin Walters <walters@verbum.org>
- New upstream release

* Tue Apr 08 2014 Colin Walters <walters@verbum.org>
- Drop requires on yum to allow minimal images without it

* Mon Mar 31 2014 Colin Walters <walters@verbum.org>
- New upstream release

* Sat Mar 22 2014 Colin Walters <walters@verbum.org> - 2014.6.3.g5707fa7-2
- Bump ostree version requirement

* Sat Mar 22 2014 Colin Walters <walters@verbum.org> - 2014.6.3.g5707fa7-1
- New git snapshot, add rpm-ostree-sign to file list

* Sat Mar 22 2014 Colin Walters <walters@verbum.org> - 2014.6-1
- New upstream version

* Fri Mar 07 2014 Colin Walters <walters@verbum.org> - 2014.5-1
- Initial package

