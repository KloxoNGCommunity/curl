# Detect the distribution in use
%global __despace head -n 1 | tr -d '[:space:]' | sed -e 's/[(].*[)]//g'
%global __lower4 cut -c 1-4 | tr '[:upper:]' '[:lower:]'
%global __distfile %([ -f /etc/SuSE-release ] && echo /etc/SuSE-release || echo /etc/redhat-release)
%global __distinit %(sed -e 's/ release .*//' -e 's/\\([A-Za-z]\\)[^ ]*/\\1/g' %{__distfile} | %{__despace} | %{__lower4})
%global __distvers %(sed -e 's/.* release \\([^. ]*\\).*/\\1/' %{__distfile} | %{__despace})
# Identify Alma, CentOS, CentOS Stream and Rocky Linux as rhel
%if "%{__distinit}" == "a" || "%{__distinit}" == "c" || "%{__distinit}" == "cl" || "%{__distinit}" == "cs" || "%{__distinit}" == "rl"
%global __distinit rhel
%endif
# Dist tag for Fedora is still "fc"
%if "%{__distinit}" == "f"
%global __distinit fc
%endif

# Set to 0 for regular curl package, 1 for libcurl compatibility package
%global compat 0

# Use rpmbuild --without nss to build with OpenSSL rather than nss
%{!?_without_nss: %{!?_with_nss: %global _with_nss --with-nss}}
%{?_with_nss:		%global disable_nss 0}
%{?_without_nss:	%global disable_nss 1}

# Build with nss rather than OpenSSL for Fedora up to 26 and RHEL-7 unless OpenSSL is requested
# (older distributions don't have recent enough nss versions)
%global nss_ok %([ '(' -n '%{?fedora}' -a 0%{?fedora} -lt 27 ')' -o 0%{?rhel} -eq 7 ] && echo 1 || echo 0)
%if %{nss_ok} && !%{disable_nss}
%global ssl_provider nss
%global ssl_versionreq >= 3.14.0
%global use_nss 1
%else
%global ssl_provider openssl
%global ssl_versionreq %{nil}
%global use_nss 0
%endif

# Use libidn2 from Fedora 25 onwards
%global use_libidn2 %([ 0%{?fedora} -gt 24 -o 0%{?rhel} -gt 7 ] && echo 1 || echo 0)

# Also build (lib)curl-minimal from Fedora 27 onwards
%global build_minimal %([ 0%{?fedora} -gt 26 -o 0%{?rhel} -gt 7 ] && echo 1 || echo 0)

# Use libssh backend rather than libssh2 from Fedora 28 onwards
%if %([ 0%{?fedora} -gt 27 -o 0%{?rhel} -gt 7 ] && echo 1 || echo 0)
%global libssh libssh
%global libssh_minimum_version 0.7.5
%else
%global libssh libssh2
%global libssh_minimum_version 1.2
%endif

# The krb5-devel packages for Fedora 19 and 20 do not include pkgconfig files,
# which breaks GSSAPI detection in curl 7.78.0 onwards
# https://github.com/curl/curl/commit/6fe4e7d3
%if %([ 0%{?fedora} -ge 19 -a 0%{?fedora} -le 20 ] && echo 1 || echo 0)
%global no_gssapi_pkgconfig 1
%else
%global no_gssapi_pkgconfig 0
%endif

# Test suite wants python-impacket too (TODO get python3-impacket in EPEL-9 and use it)
%if %([ 0%{?fedora} -gt 28 -o 0%{?rhel} -gt 8 ] && echo 1 || echo 0)
%global python_impacket python3-impacket
%endif
%if %([ 0%{?fedora} -gt 0 -a 0%{?fedora} -le 28 ] && echo 1 || echo 0)
%global python_impacket %{nil}
%endif
%if %([ 0%{?rhel} -gt 0 -a 0%{?rhel} -le 9 ] && echo 1 || echo 0)
%global python_impacket %{nil}
%endif

# %%make_build only defined from EL-7, F-21 onwards
%{!?make_build:%global make_build make %{_smp_mflags} V=1}

Version:	7.84.0
Release:	2.1.kng.%{__distinit}%{__distvers}
%if %{compat}
Summary:	Curl library for compatibility with old applications
Name:		libcurl%(echo %{version} | tr -d .)
Obsoletes:	compat-libcurl < %{version}-%{release}
Provides:	compat-libcurl = %{version}-%{release}
%else
Summary:	Utility for getting files from remote servers (FTP, HTTP, and others)
Name:		curl
Provides:	webclient
%endif
License:	MIT
Source0:	https://curl.se/download/curl-%{version}.tar.xz
Source1:	curl-pkg-changelog.old

# easy_lock.h: include sched.h if available to fix build
Patch1:		0001-curl-7.84.0-sched-yield.patch

# Fixes for test3026
Patch2:		https://github.com/curl/curl/commit/945a81e.patch
Patch3:		https://github.com/curl/curl/commit/0484127.patch

# Patch making libcurl multilib ready
Patch101:	0101-curl-7.74.0-multilib.patch

# Use localhost6 instead of ip6-localhost in the curl test-suite
Patch104:	0104-curl-7.76.0-localhost6.patch

# Fix FTBFS when building curl dynamically with no libcurl.so.4 in system
Patch300:	curl-7.64.1-zsh-cpl.patch

# Remove redundant compiler/linker flags from libcurl.pc
# Assumes %%{_libdir} = /usr/lib or /usr/lib64 and %%{_includedir} = /usr/include
Patch302:	0302-curl-7.74.0-pkgconfig.patch

URL:		https://curl.se/
%if 0%{?fedora} > 28 || 0%{?rhel} > 7
BuildRequires:	brotli-devel
%endif
BuildRequires:	coreutils
BuildRequires:	gcc
BuildRequires:	krb5-devel
%if %{use_libidn2}
BuildRequires:	libidn2-devel
%endif
BuildRequires:	openldap-devel
BuildRequires:	pkgconfig
BuildRequires:	groff
%if 0%{?fedora} > 24 || 0%{?rhel}
BuildRequires:	libnghttp2-devel >= 1.12.0
# nghttpx (an HTTP/2 proxy) is used by the upstream test-suite
BuildRequires:	nghttp2
%endif
BuildRequires:	libpsl-devel
BuildRequires:	%{libssh}-devel >= %{libssh_minimum_version}
BuildRequires:	make
BuildRequires:	perl-interpreter
BuildRequires:	sed
BuildRequires:	%{ssl_provider}-devel %{ssl_versionreq}
BuildRequires:	zlib-devel
# Needed to compress content of tool_hugehelp.c after changing curl.1 man page
BuildRequires:	perl(IO::Compress::Gzip)
# Needed for generation of shell completions
BuildRequires:	perl(Getopt::Long)
BuildRequires:	perl(Pod::Usage)
BuildRequires:	perl(strict)
BuildRequires:	perl(warnings)
# Using an older version of libcurl could result in CURLE_UNKNOWN_OPTION
Requires:	libcurl%{?_isa} >= %{version}-%{release}
%if ! %{use_nss}
Requires:	%{_sysconfdir}/pki/tls/certs/ca-bundle.crt
%endif
# Test suite requirements
BuildRequires:	gnutls-utils
%if 0%{?fedora} > 20 || 0%{?rhel} > 7
BuildRequires:	hostname
%else
BuildRequires:	/bin/hostname
%endif
BuildRequires:	openssh-clients
BuildRequires:	openssh-server
BuildRequires:	perl(Cwd)
BuildRequires:	perl(Digest::MD5)
BuildRequires:	perl(Digest::SHA)
BuildRequires:	perl(Exporter)
BuildRequires:	perl(File::Basename)
BuildRequires:	perl(File::Copy)
BuildRequires:	perl(File::Spec)
BuildRequires:	perl(IPC::Open2)
BuildRequires:	perl(MIME::Base64)
BuildRequires:	perl(Time::Local)
BuildRequires:	perl(Time::HiRes)
BuildRequires:	perl(vars)
# python used for http-pipe tests (190x)
BuildRequires:	python3-devel %{python_impacket}

# stunnel is used by upstream tests but it does not seem to work reliably
# on s390x and occasionally breaks some tests (mainly 1561 and 1562)
%ifnarch s390x
BuildRequires:	stunnel
%endif

# require at least the version of libpsl that we were built against,
# to ensure that we have the necessary symbols available (#1631804)
%global libpsl_version %(pkg-config --modversion libpsl 2>/dev/null || echo 0)

# require at least the version of libssh/libssh2 that we were built against,
# to ensure that we have the necessary symbols available (#525002, #642796)
%global libssh_version %(pkg-config --modversion %{libssh} 2>/dev/null || echo 0)

# require at least the version of openssl-libs that we were built against,
# to ensure that we have the necessary symbols available (#1462184, #1462211)
# (we need to translate 3.0.0-alpha16 -> 3.0.0-0.alpha16 and 3.0.0-beta1 -> 3.0.0-0.beta1 though)
%if ! %{use_nss}
%global openssl_version %({ pkg-config --modversion openssl 2>/dev/null || echo 0;} | sed 's|-|-0.|')
%endif

%if ! %{compat}
%description
curl is a command line tool for transferring data with URL syntax, supporting
FTP, FTPS, HTTP, HTTPS, SCP, SFTP, TFTP, TELNET, DICT, LDAP, LDAPS, FILE, IMAP,
SMTP, POP3 and RTSP.  curl supports SSL certificates, HTTP POST, HTTP PUT, FTP
uploading, HTTP form based upload, proxies, cookies, user+password
authentication (Basic, Digest, NTLM, Negotiate, kerberos...), file transfer
resume, proxy tunneling and a busload of other useful tricks.

%package -n libcurl
Summary:	A library for getting files from web servers
# libpsl adds symbols that curl uses if available, so we need to enforce
# version dependency
Requires:	libpsl%{?_isa} >= %{libpsl_version}
# libssh/libssh2 adds symbols that curl uses if available, so we need to enforce
# version dependency
Requires:	%{libssh}%{?_isa} >= %{libssh_version}
# same issue with openssl
%if ! %{use_nss}
Requires:	openssl-libs%{?_isa} >= 1:%{openssl_version}
%endif
# libnsspem.so is no longer included in the nss package from F-23 onwards (#1347336)
%if 0%{?fedora} > 22 || 0%{?rhel} > 7
%if %{use_nss}
%if 0%{?fedora} > 24 || 0%{?rhel} > 7
BuildRequires:	nss-pem%{?_isa}
Requires:	nss-pem%{?_isa}
%else
BuildRequires:	nss-pem
Requires:	nss-pem
%endif
%endif
%endif

%description -n libcurl
libcurl is a free and easy-to-use client-side URL transfer library, supporting
FTP, FTPS, HTTP, HTTPS, SCP, SFTP, TFTP, TELNET, DICT, LDAP, LDAPS, FILE, IMAP,
SMTP, POP3 and RTSP. libcurl supports SSL certificates, HTTP POST, HTTP PUT,
FTP uploading, HTTP form based upload, proxies, cookies, user+password
authentication (Basic, Digest, NTLM, Negotiate, Kerberos4), file transfer
resume, HTTP proxy tunneling and more.

%package -n libcurl-devel
Requires:	libcurl%{?_isa} = %{version}-%{release}
Requires:	%{ssl_provider}-devel %{ssl_versionreq}
Requires:	%{libssh}-devel
Summary:	Files needed for building applications with libcurl
Provides:	curl-devel = %{version}-%{release}
Provides:	curl-devel%{?_isa} = %{version}-%{release}
Obsoletes:	curl-devel < %{version}-%{release}

%description -n libcurl-devel
The libcurl-devel package includes header files and libraries necessary for
developing programs that use the libcurl library. It contains the API
documentation of the library, too.

%if %{build_minimal}
%package -n curl-minimal
Summary:		Conservatively configured build of curl for minimal installations
Provides:		curl = %{version}-%{release}
Conflicts:		curl
Suggests:		libcurl-minimal
# Using an older version of libcurl could result in CURLE_UNKNOWN_OPTION
Requires:		libcurl%{?_isa} >= %{version}-%{release}
RemovePathPostfixes:	.minimal
# Needed for RemovePathPostfixes to work with shared libraries
%undefine __brp_ldconfig

%description -n curl-minimal
This is a replacement of the 'curl' package for minimal installations. It
comes with a limited set of features compared to the 'curl' package. On the
other hand, the package is smaller and requires fewer run-time dependencies to
be installed.

%package -n libcurl-minimal
Summary:		Conservatively configured build of libcurl for minimal installations
Provides:		libcurl = %{version}-%{release}
Provides:		libcurl%{?_isa} = %{version}-%{release}
Conflicts:		libcurl%{?_isa}
RemovePathPostfixes:	.minimal
%if ! %{use_nss}
Requires:		openssl-libs%{?_isa} >= 1:%{openssl_version}
%endif

%description -n libcurl-minimal
This is a replacement of the 'libcurl' package for minimal installations. It
comes with a limited set of features compared to the 'libcurl' package. On the
other hand, the package is smaller and requires fewer run-time dependencies to
be installed.
%endif
%else
%description
This package provides an old version of cURL's libcurl library, necessary
for some old applications that have not been rebuilt against an up to date
version of cURL.
%endif

%prep
%setup -q -n curl-%{version}

# Old package changelog
cp -p %{SOURCE1} .

# Upstream patches
%patch1 -p1
%patch2 -p1
%patch3 -p1

# Fedora Patches
%patch101 -p1
#%patch104 -p1

# Local Patches
%patch300
%patch302

# Temporarily disable tests 300{0,1} on x86_64 (stunnel clashes with itself)
%if %([ 0%{?fedora} -gt 32 ] && echo 1 || echo 0)
%ifarch x86_64
printf "3000\n3001\n" >> tests/data/DISABLED
%endif
%endif

# Some tests fail on 32-bit Fedora 35?
# Looks to be due to attempted re-use of ports 24718 and 25313 with port already in use on second test run
%if %([ 0%{?fedora} -eq 35 ] && echo 1 || echo 0)
%ifnarch x86_64
printf "1562\n1630\n1631\n1632\n1904\n2050\n2055\n" >> tests/data/DISABLED
%endif
%endif

# Adapt test 323 for updated OpenSSL
sed -i -e 's/^35$/35,52/' tests/data/test323

# Workaround for broken GSSAPI detection in Fedora 19 and Fedora 20
%if %{no_gssapi_pkgconfig}
mkdir pkgconfig
cat << 'MIT_KRB5_PKGCONFIG' > pkgconfig/mit-krb5-gssapi.pc
prefix=%{_prefix}
exec_prefix=%{_prefix}
libdir=%{_libdir}
includedir=%{_includedir}

Name: mit-krb5-gssapi
Description: Kerberos implementation of the GSSAPI
Version: 1.11.3
Cflags: -I${includedir}
Libs: -L${libdir} -lgssapi_krb5
MIT_KRB5_PKGCONFIG
%endif

%build
%if %{no_gssapi_pkgconfig}
export PKG_CONFIG_PATH=$(pwd)/pkgconfig
%endif
%if ! %{use_nss}
export CPPFLAGS="$(pkg-config --cflags openssl)"
%endif
mkdir build-{full,minimal}
%global _configure ../configure
export common_configure_opts=" \
	--cache-file=../config.cache \
	--disable-static \
	--enable-hsts \
	--enable-ipv6 \
	--enable-symbol-hiding \
	--enable-threaded-resolver \
	--without-zstd \
	--with-gssapi \
%if %{use_libidn2}
	--with-libidn2 \
%else
	--without-libidn2 \
%endif
%if 0%{?fedora} > 24 || 0%{?rhel}
	--with-nghttp2 \
%endif
%if %{use_nss}
	--with-nss \
	--with-nss-deprecated \
	--without-ssl \
	--without-ca-bundle \
%else
	--with-openssl \
	--with-ca-bundle=%{_sysconfdir}/pki/tls/certs/ca-bundle.crt \
%endif
	"

# configure minimal build
%if %{build_minimal}
(
	cd build-minimal
	%configure $common_configure_opts \
	--disable-dict \
	--disable-gopher \
	--disable-imap \
	--disable-ldap \
	--disable-ldaps \
	--disable-manual \
	--disable-mqtt \
	--disable-ntlm \
	--disable-ntlm-wb \
	--disable-pop3 \
	--disable-rtsp \
	--disable-smb \
	--disable-smtp \
	--disable-telnet \
	--disable-tftp \
	--disable-tls-srp \
	--without-brotli \
	--without-libpsl \
	--without-%{libssh}
)
%endif

# configure full build
(
	cd build-full
	%configure $common_configure_opts \
	--enable-dict \
	--enable-gopher \
	--enable-imap \
	--enable-ldap \
	--enable-ldaps \
	--enable-manual \
	--enable-mqtt \
	--enable-ntlm \
	--enable-ntlm-wb \
	--enable-pop3 \
	--enable-rtsp \
	--enable-smb \
	--enable-smtp \
	--enable-telnet \
	--enable-tftp \
	--enable-tls-srp \
%if 0%{?fedora} > 28 || 0%{?rhel} > 7
	--with-brotli \
%else
	--without-brotli \
%endif
	--with-libpsl \
	--with-%{libssh}
)

# Remove bogus rpath
sed -i \
	-e 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' \
	-e 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' \
%if %{build_minimal}
	build-{full,minimal}/libtool
%else
	build-full/libtool
%endif

%if %{build_minimal}
%{make_build} -C build-minimal
%endif
%{make_build} -C build-full

%install
%if %{build_minimal}
# Install and rename the library that will be packaged as libcurl-minimal
%{make_install} -C build-minimal/lib
rm -f %{buildroot}%{_libdir}/libcurl.{la,so}
for i in %{buildroot}%{_libdir}/*; do
	mv -v $i $i.minimal
done

# Install and rename the executable that will be packaged as curl-minimal
%{make_install} -C build-minimal/src
mv -v %{buildroot}%{_bindir}/curl{,.minimal}
%endif

# Install the executable and library that will be packaged as curl and libcurl
%{make_install} -C build-full

# Install zsh completion for curl
# (we have to override LD_LIBRARY_PATH because we eliminated rpath)
LD_LIBRARY_PATH="%{buildroot}%{_libdir}:$LD_LIBRARY_PATH" \
	%{make_install} -C build-full/scripts

# --disable-static not always honoured
rm -f %{buildroot}%{_libdir}/libcurl.a
install -d %{buildroot}%{_datadir}/aclocal
install -m 644 -p docs/libcurl/libcurl.m4 %{buildroot}%{_datadir}/aclocal

%check
# Skip the (lengthy) checks on EOL Fedora releases (over ~400 days old)
if [ -z "$(find /etc/fedora-release -mtime +400)" %{?rhel:-o rhel} ]; then
%if %{build_minimal}
	%{make_build} V=1 -C build-minimal/tests
%endif
	%{make_build} V=1 -C build-full/tests

	# Relax crypto policy for the test-suite to make it pass again (#1610888)
	export OPENSSL_SYSTEM_CIPHERS_OVERRIDE=XXX
	export OPENSSL_CONF=

	# Make runtests.pl work for out-of-tree builds
	export srcdir=../../tests

	# Run the upstream test-suite for both curl-minimal and curl-full
%if %{build_minimal}
	for size in minimal full; do (
%else
	for size in full; do (
%endif
		cd build-${size}

		# We have to override LD_LIBRARY_PATH because we eliminated rpath
		export LD_LIBRARY_PATH="${PWD}/lib/.libs"

		cd tests
		perl -I../../tests ../../tests/runtests.pl -a -p -v '!flaky'
	)
	done
fi

%if %([ 0%{?fedora} -lt 28 -a 0%{?rhel} -lt 8 ] && echo 1 || echo 0)
%if ! %{compat}
%post -n libcurl -p /sbin/ldconfig
%postun -n libcurl -p /sbin/ldconfig
%if %{build_minimal}
%post -n libcurl-minimal -p /sbin/ldconfig
%postun -n libcurl-minimal -p /sbin/ldconfig
%endif
%else
%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig
%endif
%endif

%files
%license COPYING
%doc CHANGES README*
%doc docs/BUGS.md docs/DEPRECATE.md docs/FAQ docs/FEATURES.md docs/SECURITY-PROCESS.md
%doc docs/TODO docs/TheArtOfHttpScripting.md
%doc curl-pkg-changelog.old
%if ! %{compat}
%{_bindir}/curl
%{_datadir}/fish/
%{_datadir}/zsh/
%{_mandir}/man1/curl.1*
%else
%exclude %{_bindir}/curl
%exclude %{_datadir}/zsh/site-functions/_curl
%exclude %{_mandir}/man1/curl.1*
%{_libdir}/libcurl.so.*
%endif

%if ! %{compat}
%files -n libcurl
%license COPYING
%{_libdir}/libcurl.so.4
%{_libdir}/libcurl.so.4.[0-9].[0-9]

%files -n libcurl-devel
%doc docs/examples/*.c docs/examples/Makefile.example docs/INTERNALS.md
%doc docs/CHECKSRC.md docs/CONTRIBUTE.md docs/libcurl/ABI.md docs/CODE_STYLE.md
%doc docs/GOVERNANCE.md
%{_bindir}/curl-config
%{_includedir}/curl/
%{_libdir}/*.so
%{_libdir}/pkgconfig/libcurl.pc
%{_mandir}/man1/curl-config.1*
%{_mandir}/man3/*
%{_datadir}/aclocal/libcurl.m4

%if %{build_minimal}
%files -n curl-minimal
%{_bindir}/curl.minimal
%{_mandir}/man1/curl.1*

%files -n libcurl-minimal
%license COPYING
%{_libdir}/libcurl.so.4.minimal
%{_libdir}/libcurl.so.4.[0-9].[0-9].minimal
%endif
%else
%exclude %{_bindir}/curl-config
%exclude %{_includedir}/curl/
%exclude %{_libdir}/*.so
%exclude %{_libdir}/pkgconfig/libcurl.pc
%exclude %{_mandir}/man1/curl-config.1*
%exclude %{_mandir}/man3/*
%exclude %{_datadir}/aclocal/libcurl.m4
%endif
%exclude %{_libdir}/libcurl.la

%changelog
* Mon Aug  8 2022 Paul Howarth <paul@city-fan.org> - 7.84.0-2.1.cf
- Add upstream fixes for test3026

* Thu Jul 21 2022 Paul Howarth <paul@city-fan.org> - 7.84.0-2.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Tue Jun 28 2022 Paul Howarth <paul@city-fan.org> - 7.84.0-1.1.cf
- Improve workaround for test3026 issues

* Mon Jun 27 2022 Paul Howarth <paul@city-fan.org> - 7.84.0-1.0.cf
- Update to 7.84.0
  - curl: Add --rate to set max request rate per time unit
  - curl: Deprecate --random-file and --egd-file
  - curl_version_info: Add CURL_VERSION_THREADSAFE
  - CURLINFO_CAPATH/CAINFO: Get the default CA paths from libcurl
  - lib: Make curl_global_init() thread-safe when possible
  - libssh2: Add CURLOPT_SSH_HOSTKEYFUNCTION
  - opts: Deprecate RANDOM_FILE and EGDSOCKET
  - socks: Support unix sockets for socks proxy
  - aws-sigv4: Fix potential NULL pointer arithmetic
  - bindlocal: Don't use a random port if port number would wrap
  - c-hyper: Mark status line as status for Curl_client_write()
  - ci: Avoid 'cmake -Hpath'
  - ci: Bump FreeBSD 13.0 to 13.1
  - ci: Update GitHub actions
  - cmake: Add libpsl support
  - cmake: Do not add libcurl.rc to the static libcurl library
  - cmake: Enable curl.rc for all Windows targets
  - cmake: Fix detecting libidn2
  - cmake: Support adding a suffix to the OS value
  - configure: Skip libidn2 detection when winidn is used
  - configure: Use the SED value to invoke sed
  - configure: Warn about rustls being experimental
  - content_encoding: Return error on too many compression steps
    (CVE-2022-32206)
  - cookie: Address secure domain overlay
  - cookie: Apply limits (CVE-2022-32205)
  - copyright.pl: Parse and use .reuse/dep5 for skips
  - copyright: Make repository REUSE compliant
  - curl.1: Add a few see also --tls-max
  - curl.1: Mention exit code zero too
  - curl: Re-enable --no-remote-name
  - curl_easy_pause.3: Remove explanation of progress function
  - curl_getdate.3: Document that some illegal dates pass through
  - Curl_parsenetrc: Don't access local pwbuf outside of scope
  - curl_url_set.3: Clarify by default using known schemes only
  - CURLOPT_ALTSVC.3: Document the file format
  - CURLOPT_FILETIME.3: Fix the protocols this works with
  - CURLOPT_HTTPHEADER.3: Improve comment in example
  - CURLOPT_NETRC.3: Document the .netrc file format
  - CURLOPT_PORT.3: We discourage using this option
  - CURLOPT_RANGE.3: Remove ranged upload advice
  - digest: Added detection of more syntax errors in server headers
  - digest: Tolerate missing "realm"
  - digest: Unquote realm and nonce before processing
  - DISABLED: Disable 1021 for hyper again
  - docs/cmdline-opts: Add copyright and license identifier to each file
  - docs/CONTRIBUTE.md: Document the 'needs-votes' concept
  - docs: Clarify data replacement policy for MIME API
  - doh: Remove UNITTEST macro definition
  - examples/crawler.c: Use the curl license
  - examples: Remove fopen.c and rtsp.c
  - FAQ: Clarify Windows double quote usage
  - fopen: Add Curl_fopen() for better overwriting of files (CVE-2022-32207)
  - ftp: Restore protocol state after http proxy CONNECT
  - ftp: When failing to do a secure GSSAPI login, fail hard
  - GHA/hyper: Enable debug in the build
  - gssapi: Improve handling of errors from gss_display_status
  - gssapi: Initialize gss_buffer_desc strings
  - headers API: Remove EXPERIMENTAL tag
  - http2: Always debug print stream id in decimal with %%u
  - http2: Reject overly many push-promise headers
  - http: Restore header folding behaviour
  - hyper: Use 'alt-used'
  - krb5: Return error properly on decode errors (CVE-2022-32208)
  - lib: Make more protocol specific struct fields #ifdefed
  - libcurl-security.3: Add "Secrets in memory"
  - libcurl-security.3: Document CRLF header injection
  - libssh: Skip the fake-close when libssh does the right thing
  - links: Update dead links to the curl-wiki
  - log2changes: Do not indent empty lines
  - macos9: Remove partial support
  - Makefile.am: Fix portability issues
  - Makefile.m32: Delete obsolete options, improve -On
  - Makefile.m32: Delete two obsolete OpenSSL options
  - Makefile.m32: Stop forcing XP target with ipv6 enabled
  - max-time.d: Clarify max-time sets max transfer time
  - mprintf: Ignore clang non-literal format string
  - netrc: Check %%USERPROFILE%% as well on Windows
  - netrc: Support quoted strings
  - ngtcp2: Allow curl to send larger UDP datagrams
  - ngtcp2: Correct use of ngtcp2 and nghttp3 signed integer types
  - ngtcp2: Enable Linux GSO
  - ngtcp2: Extend QUIC transport parameters buffer
  - ngtcp2: Fix alert_read_func return value
  - ngtcp2: Fix typo in preprocessor condition
  - ngtcp2: Handle error from ngtcp2_conn_submit_crypto_data
  - ngtcp2: Send appropriate connection close error code
  - ngtcp2: Support boringssl crypto backend
  - ngtcp2: Use helper funcs to simplify TLS handshake integration
  - ntlm: Provide a fixed fake host name
  - projects: Fix third-party SSL library build paths for Visual Studio
  - quic: Add Curl_quic_idle
  - quiche: Support ca-fallback
  - rand: Stop detecting /dev/urandom in cross-builds
  - remote-name.d: Mention --output-dir
  - runtests.pl: Add the --repeat parameter to the --help output
  - runtests: Fix skipping tests not done event-based
  - runtests: Skip starting the ssh server if user name is lacking
  - scripts/copyright.pl: fix the exclusion to not ignore man pages
  - sectransp: Check for a function defined when __BLOCKS__ is undefined
  - select: Return error from "lethal" poll/select errors
  - server/sws: Support spaces in the HTTP request path
  - speed-limit/time.d: Mention these affect transfers in either direction
  - strcase: Some optimizations
  - test 2081: Add a valid reply for the second request
  - test 675: Add missing CR so the test passes when run through Privoxy
  - test414: Add the '--resolve' keyword
  - test681: Verify --no-remote-name
  - tests 266, 116 and 1540: Add a small write delay
  - tests/data/test1501: Kill ftp server after slow LIST response
  - tests/getpart: Fix getpartattr to work with "data" and "data2"
  - tests/server/sws.c: Change the HTTP writedelay unit to milliseconds
  - test{440,441,493,977}: Add "HTTP proxy" keywords
  - tool_getparam: Fix --parallel-max maximum value constraint
  - tool_operate: Make sure --fail-with-body works with --retry
  - transfer: Fix potential NULL pointer dereference
  - transfer: Maintain --path-as-is after redirects
  - transfer: Upload performance; avoid tiny send
  - url: Free old conn better on reuse
  - url: Remove redundant #ifdefs in allocate_conn()
  - url: URL encode the path when extracted, if spaces were set
  - urlapi: Make curl_url_set(url, CURLUPART_URL, NULL, 0) clear all parts
  - urlapi: Support CURLU_URLENCODE for curl_url_get()
  - urldata: Reduce size of a few struct fields
  - urldata: Remove three unused booleans from struct UserDefined
  - urldata: Store tcp_keepidle and tcp_keepintvl as ints
  - version: Allow stricmp() for sorting the feature list
  - vtls: Make curl_global_sslset thread-safe
  - wolfssh.h: Removed
  - wolfSSL: Correct the failf() message when a handle can't be made
  - wolfSSL: Explicitly use compatibility layer
  - x509asn1: Mark msnprintf return as unchecked
- Disable flaky test 3026 for now

* Sat May 21 2022 Paul Howarth <paul@city-fan.org> - 7.83.1-1.1.cf
- Rebuild for updated EL-7 libpsl (GH#8834)

* Wed May 11 2022 Paul Howarth <paul@city-fan.org> - 7.83.1-1.0.cf
- Update to 7.83.1
  - altsvc: Fix host name matching for trailing dots
  - cirrus: Update to FreeBSD 12.3
  - cirrus: Use pip for Python packages on FreeBSD
  - conn: Fix typo 'connnection' → 'connection' in two function names
  - cookies: Make bad_domain() not consider a trailing dot fine (CVE-2022-27779)
  - curl: Free resource in error path
  - curl: Guard against size_t wraparound in no-clobber code
  - CURLOPT_DOH_URL.3: Mention the known bug
  - CURLOPT_HSTS*FUNCTION.3: Document the involved structs as well
  - CURLOPT_SSH_AUTH_TYPES.3: Fix the default
  - data/test376: Set a proper name
  - GHA/mbedtls: Enabled nghttp2 in the build
  - gha: Build msh3
  - gskit: Fixed bogus setsockopt calls
  - gskit: Remove unused function set_callback
  - hsts: Ignore trailing dots when comparing hosts' names (CVE-2022-30115)
  - HTTP-COOKIES: Add missing CURLOPT_COOKIESESSION
  - http: Move Curl_allow_auth_to_host()
  - http_proxy/hyper: Handle closed connections
  - hyper: Fix test 357
  - Makefile: Fix "make ca-firefox"
  - mbedtls: Bail out if rng init fails
  - mbedtls: Fix compile when h2-enabled
  - mbedtls: Fix some error messages
  - misc: Use "autoreconf -fi" instead of buildconf
  - msh3: Get msh3 version from MsH3Version
  - msh3: Print boolean value as text representation
  - msh3: Pass remote_port to MsH3ConnectionOpen
  - ngtcp2: Add ca-fallback support for OpenSSL backend
  - nss: Return error if seemingly stuck in a cert loop (CVE-2022-27781)
  - openssl: Define HAVE_SSL_CTX_SET_EC_CURVES for libressl
  - post_per_transfer: Remove the updated file name (CVE-2022-27778)
  - sectransp: Bail out if SSLSetPeerDomainName fails
  - tests/server: Declare variable 'reqlogfile' static
  - tests: Fix markdown formatting in README
  - test{898,974,976}: Add 'HTTP proxy' keywords
  - tls: Check more TLS details for connection reuse (CVE-2022-27782)
  - url: Check SSH config match on connection reuse (CVE-2022-27782)
  - urlapi: Address (harmless) UndefinedBehavior sanitizer warning
  - urlapi: Reject percent-decoding host name into separator bytes
    (CVE-2022-27780)
  - x509asn1: Make do_pubkey handle EC public keys

* Wed Apr 27 2022 Paul Howarth <paul@city-fan.org> - 7.83.0-1.0.cf
- Update to 7.83.0
  - curl: Add %%header{name} experimental support in -w handling
  - curl: Add %%{header_json} experimental support in -w handling
  - curl: Add --no-clobber
  - curl: Add --remove-on-error
  - header api: Add curl_easy_header and curl_easy_nextheader
  - msh3: Add support for QUIC and HTTP/3 using msh3
  - appveyor: Add Cygwin build
  - appveyor: Only add MSYS2 to PATH where required
  - BearSSL: Add CURLOPT_SSL_CIPHER_LIST support
  - BearSSL: Add CURLOPT_SSL_CTX_FUNCTION support
  - BINDINGS.md: Add Hollywood binding
  - CI: Do not use buildconf; instead, just use: autoreconf -fi
  - CI: Install Python package impacket to run SMB test 1451
  - configure.ac: Move -pthread CFLAGS setting back where it used to be
  - configure: Bump the copyright year range in the generated output
  - conncache: Include the zone id in the "bundle" hashkey (CVE-2022-27775)
  - connecache: Remove duplicate connc->closure_handle check
  - connect: Make Curl_getconnectinfo work with conn cache from share handle
  - connect: Use TCP_KEEPALIVE only if TCP_KEEPIDLE is not defined
  - cookie.d: Clarify when cookies are sent
  - cookies: Improve error handling for reading cookiefile
  - curl/system.h: Update ifdef condition for MCST-LCC compiler
  - curl: Error out if -T and -d are used for the same URL
  - curl: Error out when options need features not present in libcurl
  - curl: Escape '?' in generated --libcurl code
  - curl: Fix segmentation fault for empty output file names
  - curl_easy_header: Fix typos in documentation
  - CURLINFO_PRIMARY_PORT.3: Clarify which port this is
  - CURLOPT*TLSAUTH.3: They only work with OpenSSL or GnuTLS
  - CURLOPT_DISALLOW_USERNAME_IN_URL.3: Use uppercase URL
  - CURLOPT_PREQUOTE.3: Only works for FTP file transfers, not dirs
  - CURLOPT_PROGRESSFUNCTION.3: Fix typo in example
  - CURLOPT_UNRESTRICTED_AUTH.3: Extended explanation
  - CURLSHOPT_UNLOCKFUNC.3: Fix the callback prototype
  - docs/HYPER.md: Updated to reflect current hyper build needs
  - docs/opts: Mention Schannel client cert type is P12
  - docs: Fix missing semicolon in example code
  - docs: Lots of minor language polish
  - English: Use American spelling consistently
  - fail.d: Tweak the description
  - firefox-db2pem.sh: Make the shell script safer
  - ftp: Fix error message for partial file upload
  - gen.pl: Change wording for mutexed options
  - GHA: Add openssl3 jobs moved over from Zuul
  - GHA: Build hyper with nightly rustc
  - GHA: Move bearssl jobs over from Zuul
  - GHA: Move the event-based test over from Zuul
  - gtls: Fix build for disabled TLS-SRP
  - http2: Handle DONE called for the paused stream
  - http2: RST the stream if we stop it on our own will
  - http: Avoid auth/cookie on redirects same host diff port (CVE-2022-27776)
  - http: Close the stream (not connection) on time condition abort
  - http: Reject header contents with nul bytes
  - http: Return error on colon-less HTTP headers
  - http: streamclose "already downloaded"
  - hyper: Fix status_line() return code
  - hyper: Fix tests 580 and 581 for hyper
  - hyper: No h2c support
  - infof: Consistent capitalization of warning messages
  - ipv4/6.d: Clarify that they are about using IP addresses
  - json.d: Fix typo (overriden → overridden)
  - keepalive-time.d: It takes many probes to detect brokenness
  - lib/warnless.[ch]: Only check for WIN32 and ignore _WIN32
  - lib670: Avoid double check result
  - lib: #ifdef on USE_HTTP2 better
  - lib: Fix some misuse of curlx_convert_wchar_to_UTF8
  - lib: Remove exclamation marks
  - libssh2: Compare sha256 strings case sensitively
  - libssh2: Make the md5 comparison fail if wrong length
  - libssh: Fix build with old libssh versions
  - libssh: Fix double close
  - libssh: Improve fix for missing SSH_S_ stat macros
  - libssh: Unstick SFTP transfers when done event-based
  - macos: Set .plist version in autoconf
  - mbedtls: Remove 'protocols' array from backend when ALPN is not used
  - mbedtls: Remove server_fd from backend
  - mk-ca-bundle.pl: Use stricter logic to process the certificates
  - mk-ca-bundle.vbs: Delete this script in favor of mk-ca-bundle.pl
  - mlc_config.json: Add file to ignore known troublesome URLs
  - mqtt: Better handling of TCP disconnect mid-message
  - ngtcp2: Add client certificate authentication for OpenSSL
  - ngtcp2: Avoid busy loop in low CWND situation
  - ngtcp2: Deal with sub-millisecond timeout
  - ngtcp2: Disconnect the QUIC connection properly
  - ngtcp2: Enlarge H3_SEND_SIZE
  - ngtcp2: Fix HTTP/3 upload stall and avoid busy loop
  - ngtcp2: Fix memory leak
  - ngtcp2: Fix QUIC_IDLE_TIMEOUT
  - ngtcp2: Make curl 1ms faster
  - ngtcp2: Remove remote_addr, which is not used in a meaningful way
  - ngtcp2: Update to work after recent ngtcp2 updates
  - ngtcp2: Use token when detecting :status header field
  - nonblock: Restore setsockopt method to curlx_nonblock
  - openssl: Check SSL_get_peer_cert_chain return value
  - openssl: Enable CURLOPT_SSL_EC_CURVES with BoringSSL
  - openssl: Fix CN check error code
  - options: Remove mistaken space before paren in prototype
  - perl: Removed a double semicolon at end of line
  - pop3/smtp: return *WEIRD_SERVER_REPLY when not understood
  - projects/README: Converted to markdown
  - projects: Update VC version names for VS2017, VS2022
  - rtsp: Don't let CSeq error override earlier errors
  - runtests: Add 'bearssl' as testable feature
  - runtests: Make 'oldlibssh' be before 0.9.4
  - schannel: Remove dead code that will never run
  - scripts/copyright.pl: Ignore the new mlc_config.json file
  - scripts: Move three scripts from lib/ to scripts/
  - test1135: Sync with recent API updates
  - test1459: Disable for oldlibssh
  - test375: Fix line endings on Windows
  - test386: Fix an incorrect test markup tag
  - test718: Edited slightly to return better HTTP
  - tests/server/util.h: Align WIN32 condition with util.c
  - tests: Refactor server/socksd.c to support --unix-socket
  - timediff.[ch]: Add curlx helper functions for timeval conversions
  - tls: Make mbedtls and NSS check for h2, not nghttp2
  - tool and tests: Force flush of all buffers at end of program
  - tool_cb_hdr: Turn the Location: into a terminal hyperlink
  - tool_getparam: Error out on missing -K file
  - tool_listhelp.c: Uppercase URL
  - tool_operate: Fix a scan-build warning
  - tool_paramhlp: Use feof(3) to identify EOF correctly when using fread(3)
  - transfer: Redirects to other protocols or ports clear auth (CVE-2022-27774)
  - unit1620: Call global_init before calling Curl_open
  - url: Check sasl additional parameters for connection reuse (CVE-2022-22576)
  - vtls: Provide a unified ALPN-disagree string for all backends
  - vtls: Use a backend standard message for "ALPN: offers %%s"
  - vtls: Use a generic "ALPN, server accepted" message
  - winbuild/README.md: Fix up dead link
  - winbuild: Add a Visual Studio example to the README
  - wolfssl: Fix compiler error without IPv6

* Tue Mar 15 2022 Paul Howarth <paul@city-fan.org> - 7.82.0-2.0.cf
- openssl: Fix incorrect CURLE_OUT_OF_MEMORY error on CN check failure

* Sat Mar  5 2022 Paul Howarth <paul@city-fan.org> - 7.82.0-1.0.cf
- Update to 7.82.0
  - curl: Add --json
  - mesalink: Remove support
  - appveyor: Update images from VS 2019 to 2022
  - appveyor: Use VS 2017 image for the autotools builds
  - azure-pipelines: Add a build on Windows with libssh
  - bearssl: Fix connect error on expired cert and no verify
  - bearssl: Fix EXC_BAD_ACCESS on incomplete CA cert
  - bearssl: Fix session resumption (session id)
  - build: Enable -Warith-conversion
  - build: Fix -Wenum-conversion handling
  - build: Fix ngtcp2 crypto library detection
  - checkprefix: Remove strlen calls
  - checksrc: Fix typo in comment
  - CI: Move 'distcheck' job from Zuul to Azure pipelines
  - CI: Move scan-build job from Zuul to Azure Pipelines
  - CI: Move the NSS job from Zuul to GHA
  - ci: Move the OpenSSL + c-ares job from Zuul to Circle CI
  - CI: Move the rustls CI job to GHA from Zuul
  - CI: Move two jobs from Zuul to Circle CI
  - CI: Test building wolfssl with --enable-opensslextra
  - CI: workflows/wolfssl: Install impacket
  - circleci: Add a job using libssh
  - cirlceci: Also run a c-ares job on arm with debug enabled
  - cmake: Fix iOS CMake project generation error
  - cmdline-opts/gen.pl: Fix option matching to improve references
  - config.d: Clarify _curlrc filename is still valid on Windows
  - configure.ac: Use user-specified gssapi dir when using pkg-config
  - configure: Change output for cross-compiled alt-svc support
  - configure: Fix '--enable-code-coverage' typo
  - configure: Remove support for "embedded ares"
  - configure: Requires --with-nss-deprecated to build with NSS
  - configure: Set CURL_LIBRARY_PATH for nghttp2
  - configure: Support specification of a nghttp2 library path
  - configure: Use correct CFLAGS for threaded resolver with xlC on AIX
  - curl tool: Erase some more sensitive command line arguments
  - curl-functions.m4: Fix LIBRARY_PATH adjustment to avoid eval
  - curl-functions.m4: Revert DYLD_LIBRARY_PATH tricks in CURL_RUN_IFELSE
  - curl-openssl: Fix SRP check for OpenSSL 3.0
  - curl-openssl: Remove the OpenSSL headers and library versions check
  - curl.h: Fix typo
  - curl: Remove "separators" (when using globbed URLs)
  - curl_getdate.3: Remove pointless .PP line
  - curl_multi_socket.3: Remove callback and typical usage descriptions
  - curl_url_set.3: Mention when CURLU_ALLOW_SPACE was added
  - CURLMOPT_TIMERFUNCTION/DATA.3: Fix the examples
  - CURLOPT_PROGRESSFUNCTION.3: Fix example struct assignment
  - CURLOPT_RESOLVE.3: Change example port to 443
  - CURLOPT_XFERINFOFUNCTION.3: Fix example struct assignment
  - CURLOPT_XFERINFOFUNCTION.3: Fix typo in example
  - CURLSHOPT_LOCKFUNC.3: Fix typo "relased" ⇒ "released"
  - DES: Fix compile break for OpenSSL without DES
  - docs/cmdline-opts: Add "mutexed" options for more http versions
  - docs/DEPRECATE: Remove NPN support in August 2022
  - docs: Capitalize the name 'Netscape'
  - docs: Document HTTP/2 not insisting on TLS 1.2
  - docs: Fix mandoc -T lint formatting complaints
  - docs: Update IETF links to use datatracker
  - examples/curlx: Support building with OpenSSL 1.1.0+
  - examples/multi-app.c: Call curl_multi_remove_handle as well
  - formdata: Avoid size_t → long typecast overflows
  - ftp: Provide error message for control bytes in path
  - gen.pl: Terminate "example" sections better
  - gha: Add a macOS CI job with libssh
  - gskit: Convert to using Curl_poll
  - gskit: Fix errors from Curl_strerror refactor
  - gskit: Fix initialization of Curl_ssl_gskit struct
  - h2/h3: Allow CURLOPT_HTTPHEADER change ":scheme"
  - hostcheck: Fixed to not touch used input strings
  - hostcheck: Reduce strlen calls on chained certificates
  - hostip: Avoid unused parameter error in Curl_resolv_check
  - http2: Move two infof calls to debug-h2-only
  - http: Make Curl_compareheader() take string length arguments too
  - if2ip: Make Curl_ipv6_scope a blank macro when IPv6-disabled
  - KNOWN_BUGS: Fix typo "libpsl"
  - ldap: Return CURLE_URL_MALFORMAT for bad URL
  - lib: Remove support for CURL_DOES_CONVERSIONS
  - libssh2: Don't typecast socket to int for libssh2_session_handshake
  - libssh: Fix include files and defines use for Windows builds
  - Makefile.am: Generate VS 2022 projects
  - maketgz: Return error if 'make dist' fails
  - mbedtls: Enable use of mbedtls without CRL support
  - mbedtls: Enable use of mbedtls without filesystem functions support
  - mbedtls: Fix CURLOPT_SSLCERT_BLOB (again)
  - mbedtls: Fix ssl_init error with mbedTLS 3.1.0+
  - mbedtls: Remove #include <mbedtls/certs.h>
  - mbedtls: Return CURLcode result instead of a mbedtls error code
  - md5: Check md5_init_func return value
  - mime: Use a define instead of the magic number 24
  - misc: Allow curl to build with wolfssl --enable-opensslextra
  - misc: Remove BeOS code and references
  - misc: Remove the final watcom references
  - misc: Remove unused data when IPv6 is not supported
  - mqtt: Free 'sendleftovers' in disconnect
  - mqtt: Free any send leftover data when done
  - multi: Allow user callbacks to call curl_multi_assign
  - multi: Grammar fix in comment
  - multi: Remember connection_id before returning connection to pool
  - multi: Set in_callback for multi interface callbacks
  - netware: Remove support
  - next.d: Remove .fi/.nf as they are handled by gen.pl
  - ngtcp2: Adapt to changed end of headers callback proto
  - ngtcp2: Fix declaration of ‘result’ shadows a previous local
  - ngtcp2: Reset dynbuf when it is fully drained
  - nss: Handshake callback during shutdown has no conn->bundle
  - ntlm: Remove unused feature defines
  - openldap: Fix compiler warning when built without SSL support
  - openldap: Implement SASL authentication
  - openldap: Pass string length arguments to client_write()
  - openssl.h: Avoid including OpenSSL headers here
  - openssl: Check if sessionid flag is enabled before retrieving session
  - openssl: Check SSL_get_ex_data to prevent potential NULL dereference
  - openssl: Check the return value of BIO_new_mem_buf()
  - openssl: Fix 'ctx_option_t' for OpenSSL v3+
  - openssl: Fix build for version < 1.1.0
  - openssl: Return error if TLS 1.3 is requested when not supported
  - os400: Add function wrapper for system command
  - os400: Add link to QADRT devkit to README.OS400
  - os400: Default build to target current release
  - OS400: Fix typos in rpg include file
  - projects: Add support for Visual Studio 17 (2022)
  - projects: Fix Visual Studio wolfSSL configurations
  - projects: Remove support for MSVC before VC10 (Visual Studio 2010)
  - quiche: After leaving h3_recving state, poll again
  - quiche: Change qlog file extension to '.sqlog'
  - quiche: Fix upload for bigger content-length
  - quiche: Handle stream reset
  - quiche: Remove two leftover debug infof() outputs
  - quiche: Verify the server cert on connect
  - quiche: When *recv_body() returns data, drain it before polling again
  - README.md: Fix links
  - remote-header-name.d: Clarify
  - runtests.pl: Disable debuginfod
  - runtests.pl: Properly print the test if it contains binary zeros
  - runtests.pl: Support the nonewline attribute for the data part
  - runtests.pl: Tolerate test directories without Makefile.inc
  - runtests: Allow client/file to specify multiple directories
  - runtests: Make 'rustls' a testable feature
  - runtests: Make 'wolfssl' a testable feature
  - runtests: Set 'oldlibssh' for libssh versions before 0.9.5
  - rustls: Add CURLOPT_CAINFO_BLOB support
  - schannel: Move the algIds array out of schannel.h
  - scripts/cijobs.pl: Output data about all current CI jobs
  - scripts/completion.pl: Improve zsh completion
  - scripts/copyright.pl: Support many provided file names on the cmdline
  - scripts/delta: Check the file delta for current branch
  - sectransp: Mark a 3DES cipher as weak
  - setopt: Do bounds-check before strdup
  - setopt: Fix the TLSAUTH #ifdefs for proxy-disabled builds
  - sha256: Fix minimum OpenSSL version
  - smb: Pass socket for writing and reading data instead of FIRSTSOCKET
  - ssl: Reduce allocated space for ssl backend when FTP is disabled
  - test3021: Disable all msys2 path transformation
  - test374: GIF data without newline at the end
  - tests/disable-scan.pl: Properly detect multiple symbols per line
  - tests/unit/Makefile.am: Add NSS_LIBS to build with NSS fine
  - tool_findfile: Check ~/.config/curlrc too
  - tool_getparam: DNS options that need c-ares now fail without it
  - TPF: Drop support
  - unit1610: Init SSL library before calling SHA256 functions
  - url: Exclude zonefrom_url when no ipv6 is available
  - url: Given a user in the URL, find pwd for that user in netrc
  - url: Keep trailing dot in host name
  - url: Make Curl_disconnect return void
  - urlapi: Handle "redirects" smarter
  - urldata: CONN_IS_PROXIED replaces bits.proxy when proxy can be disabled
  - urldata: Remove conn->bits.user_passwd
  - version_win32: Fix warning for 'CURL_WINDOWS_APP'
  - vtls: Fix socket check conditions
  - vtls: Pass on the right SNI name
  - vxworks: Drop support
  - winbuild: Add parameter WITH_SSH
  - wolfssl: Return CURLE_AGAIN for the SSL_ERROR_NONE case
  - wolfssl: When SSL_read() returns zero, check the error
  - write-out.d: Fix num_headers formatting
  - x509asn1: Toggle off functions not needed for different tls backends
- Drop hacks for running tests with python3
- Drop support for running tests with python2 (support dropped upstream)
- Add --with-nss-deprecated flag to configure with NSS support
- Add fix for failing test1459 on EL-8 with libssh 0.9.4 (GH#8548)

* Thu Feb 24 2022 Paul Howarth <paul@city-fan.org> - 7.81.0-4.0.cf
- Enable IDN support also in libcurl-minimal

* Fri Feb 11 2022 Paul Howarth <paul@city-fan.org> - 7.81.0-3.0.cf
- Suggest libcurl-minimal in curl-minimal

* Fri Jan 21 2022 Paul Howarth <paul@city-fan.org> - 7.81.0-2.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Wed Jan  5 2022 Paul Howarth <paul@city-fan.org> - 7.81.0-1.0.cf
- Update to 7.81.0
  - mime: Use percent-escaping for multipart form field and file names
  - asyn-ares: ares_getaddrinfo needs no happy eyeballs timer
  - azure: Make the "w/o HTTP/SMTP/IMAP" build disable SSL proper
  - BINDINGS: Add cURL client for PostgreSQL
  - BINDINGS: Add one from Everything curl and update a link
  - checksrc: Detect more kinds of NULL comparisons we avoid
  - CI: Build examples for additional code verification
  - CI: Bump job to use mbedtls 3.1.0
  - cmake: Don't set _USRDLL on a static Windows build
  - cmake: Prevent dev warning due to mismatched arg
  - cmake: Private identifiers use CURL_ instead of CMAKE_ prefix
  - config.d: Update documentation to match the path search
  - configure: Add -lm to configure for rustls build
  - configure: Better diagnostics if hyper is built wrong
  - configure: Don't enable TLS when --without-* flags are used
  - configure: Fix runtime-lib detection on macOS
  - curl.1: Require "see also" for every documented option
  - curl: Improve error message for --head with -J
  - curl_easy_cleanup.3: Remove from multi handle first
  - curl_easy_escape.3: Call curl_easy_cleanup in example
  - curl_easy_unescape.3: Call curl_easy_cleanup in example
  - curl_multi_init.3: Fix EXAMPLE formatting
  - curl_multi_perform/socket_action.3: Clarify what errors mean
  - curl_share_setopt.3: Split out options into their own manpages
  - CURLOPT_STDERR.3: Does not work with libcurl as a win32 DLL
  - digest: Compute user:realm:pass digest w/o userhash
  - docs/checksrc: Add documentation for STRERROR
  - docs/cmdline-opts: Do not say "protocols: all"
  - docs/examples: Work around broken -Wno-pedantic-ms-format
  - docs/HTTP3: Describe how to setup a h3 reverse-proxy for testing
  - docs/INSTALL.md: Typo fix: added missing "get" verb
  - docs/URL-SYNTAX.md: Space is not fine in a given URL
  - docs: Add known bugs list to HTTP3.md
  - docs: Address proselint nits
  - docs: Consistent manpage SYNOPSIS
  - docs: Fix dead links, remove ECH.md
  - docs: Fix typo in OpenSSL 3 build instructions
  - docs: Update the Reducing Size section
  - example/progressfunc: Remove code for old libcurls
  - examples/multi-single.c: Remove WAITMS()
  - FAQ: Typo fix: "yout" → "your"
  - ftp: Disable warning 4706 in MSVC
  - gen.pl: Improve example output format
  - github workflow: Add wolfssl (removed from zuul)
  - github/workflows: Add mbedtls and mbedtls-clang (removed from zuul)
  - gtls: Check return code for gnutls_alpn_set_protocols
  - hash: lazy-alloc the table in Curl_hash_add()
  - http2: set_transfer_url() return early on OOM
  - HTTP3: Update quiche build instructions
  - http: Enable haproxy support for hyper backend
  - http: Fix CURLOPT_HTTP200ALIASES
  - http_proxy: Don't close the socket (too early)
  - insecure.d: Detail its use for SFTP and SCP as well
  - insecure.d: Expand and clarify
  - libcurl-multi.3: "SOCKS proxy handshakes" are not blocking
  - libcurl-security.3: Mention address and URL mitigations
  - libssh2: Fix error message for sha256 mismatch
  - libtest: Avoid "assignment within conditional expression"
  - lift: ignore is a deprecated config option, use ignoreRules
  - linkcheck.yml: Add CI job that checks markdown links
  - m4/curl-compilers: Tell clang -Wno-pointer-bool-conversion
  - Makefile.m32: Rename -winssl option to -schannel and tidy up
  - mbedTLS: Add support for CURLOPT_CAINFO_BLOB
  - mbedtls: Fix CURLOPT_SSLCERT_BLOB
  - mbedtls: Fix private member designations for v3.1.0
  - misc: Remove unused doh flags when CURL_DISABLE_DOH is defined
  - misc: s/e-mail/email
  - multi: Clean up the socket hash when destroying it
  - multi: Handle errors returned from socket/timer callbacks
  - multi: Shut down CONNECT in Curl_detach_connnection
  - netrc.d: Edit the .netrc example to look nicer
  - ngtcp2: Verify the server cert on connect (quictls)
  - ngtcp2: Verify the server certificate for the gnutls case
  - nss: set_cipher: don't clobber the cipher list
  - openldap: Implement STARTTLS
  - openldap: Process search query response messages one by one
  - openldap: Several minor improvements
  - openldap: Simplify ldif generation code
  - openssl: Check the return value of BIO_new()
  - openssl: define HAVE_OPENSSL_VERSION for OpenSSL 1.1.0+
  - openssl: Remove 'RSA_METHOD_FLAG_NO_CHECK' handling if unavailable
  - openssl: Remove usage of deprecated 'SSL_get_peer_certificate'
  - openssl: Use non-deprecated API to read key parameters
  - page-footer: Add a mention of how to report bugs to the man page
  - page-footer: Document more environment variables
  - request.d: Refer to 'method' rather than 'command'
  - retry-all-errors.d: Make the example complete
  - runtests: Make the SSH library a testable feature
  - rustls: Read of zero bytes might be okay
  - rustls: Remove comment about checking handshaking
  - rustls: Remove incorrect EOF check
  - sha256/md5: Return errors when init fails
  - socks5: Use appropriate ATYP for numerical IP address host names
  - test1156: Enable for hyper
  - test1156: Fix up the stdout check for Windows
  - test1525: Tweaked for hyper
  - test1526: Enable for hyper
  - test1527: Enable for hyper
  - test1528: Enable for hyper
  - test1554: Adjust for hyper
  - test1556: Adjust for hyper
  - test302[12]: Run only with the libssh2 backend
  - test661: Enable for hyper
  - tests/CI.md: Add more information on CI environments
  - tests/data/test302[12]: Fix MSYS2 path conversion of hostpubsha256
  - tftp: Mark protocol as not possible to do over CONNECT
  - tool_findfile: Updated search for a file in the homedir
  - tool_operate: Only set SSH related libcurl options for SSH URLs
  - tool_operate: Warn if too many output arguments were found
  - url.c: Fix the SIGPIPE comment for Curl_close
  - url: Check ssl_config when re-use proxy connection
  - url: Reduce ssl backend count for CURL_DISABLE_PROXY builds
  - urlapi: Accept port number zero
  - urlapi: If possible, shorten given numerical IPv6 addresses
  - urlapi: Provide more detailed return codes
  - urlapi: Reject short file URLs
  - version_win32: Check build number and platform id
  - vtls/rustls: Adapt to the updated rustls_version proto
  - writeout: Fix %%{http_version} for HTTP/3
  - x509asn1: Return early on errors
  - zuul.d: Update rustls-ffi to version 0.8.2
  - zuul: Fix quiche build pointing to wrong Cargo

* Sun Nov 14 2021 Paul Howarth <paul@city-fan.org> - 7.80.0-2.0.cf
- sshserver.pl (used in test suite) now requires the Digest::SHA perl module

* Wed Nov 10 2021 Paul Howarth <paul@city-fan.org> - 7.80.0-1.0.cf
- Update to 7.80.0
  - CURLOPT_MAXLIFETIME_CONN: Maximum allowed lifetime for conn reuse
  - CURLOPT_PREREQFUNCTION: Add new callback
  - libssh2: Add SHA256 fingerprint support
  - urlapi: Add curl_url_strerror()
  - urlapi: Support UNC paths in file: URLs on Windows
  - wolfssl: Allow setting of groups/curves
  - .github: Retry macos "brew install" command on failure
  - aws-sigv4: Make signature work when post data is binary
  - BINDINGS: URL updates
  - build: Remove checks for WinSock 1
  - c-hyper: Don't abort CONNECT responses early when auth-in-progress
  - c-hyper: Make Curl_http propagate errors better
  - c-hyper: Make CURLOPT_SUPPRESS_CONNECT_HEADERS work
  - c-hyper: Make test 217 run
  - c-hyper: Use hyper_request_set_uri_parts to make h2 better
  - checksrc: Ignore preprocessor lines
  - CI/makefiles: Introduce dedicated test target
  - ci: Update Lift config to match requirements of curl build
  - cirrus: Remove FreeBSD 11.4 from the matrix
  - cirrus: Switch to openldap24-client
  - cleanup: constify unmodified static structs
  - cmake: Add CURL_ENABLE_SSL option
  - cmake: Fix error getting LOCATION property on non-imported target
  - cmake: Restore support for SecureTransport on iOS
  - cmake: With OpenSSL, define OPENSSL_SUPPRESS_DEPRECATED
  - cmdline-opts: Made the 'Added:' field mandatory
  - configure.ac: Replace krb5-config with pkg-config
  - configure: When hyper is selected, deselect nghttp2
  - connect: Use sysaddr_un from sys/un.h or custom-defined for Windows
  - curl-confopts.m4: Remove --enable/disable-hidden-symbols
  - curl-openssl.m4: Modify library order for openssl linking
  - curl-openssl: Pass argument to sed single-quoted
  - curl.1: Remove mentions of really old version changes
  - curl: Actually append "-" to --range without number only
  - curl: Correct grammar in generated libcurl code
  - curl: Print help descriptions in an aligned right column
  - curl_gssapi: Fix link error on macOS Monterey
  - curl_multi_socket_action.3: Add a "RETURN VALUE" section
  - curl_ntlm_core: Use OpenSSL only if DES is available
  - Curl_updateconninfo: Store addresses for QUIC connections too
  - CURLOPT_ALTSVC_CTRL.3: Mention conn reuse is preferred
  - CURLOPT_HSTSWRITEFUNCTION.3: Using CURLOPT_HSTS_CTRL is required
  - CURLOPT_HTTPHEADER.3: Add description for specific headers
  - docs/HTTP3: Improve build instructions
  - docs/Makefile.am: Repair 'make html'
  - docs: Fix typo in CURLOPT_TRAILERFUNCTION example
  - docs: Provide "RETURN VALUE" section for more func manpages
  - docs: Reduce use of "very"
  - doh: Remove experimental code for DoH with GET
  - examples/htmltidy: Correct wrong printf() use
  - examples/imap-append: Fix end-of-data check
  - ftp: Make the MKD retry to retry once per directory
  - gen.pl: Insert the current date and version in generated man page
  - gen.pl: Replace leading single quotes with \(aq
  - http2: Make getsock not wait for write if there's no remote window
  - HTTP3: Fix the HTTP/3 Explained book link
  - http: Fix Basic auth with empty name field in URL
  - http: Reject HTTP response codes < 100
  - http: Remove assert that breaks hyper
  - http: Set content length earlier
  - http_proxy: Make hyper CONNECT() return the correct error code
  - http_proxy: Multiple CONNECT with hyper done better
  - hyper: Disable test 1294 since hyper doesn't allow such crazy headers
  - hyper: Does not support disabling CURLOPT_HTTP_TRANSFER_DECODING
  - hyper: Pass the CONNECT line to the debug callback
  - imap: Display quota information
  - INSTALL: Update symbol hiding option
  - lib/mk-ca-bundle.pl: Skip certs passed Not Valid After date
  - lib: Avoid fallthrough cases in switch statements
  - libcurl.rc: Switch out the copyright symbol for plain ASCII
  - libssh2: Get the version at runtime if possible
  - limit-rate.d: This is average over several seconds
  - llist: Remove redundant code, branch will not be executed
  - Makefile.m32: Fix to not require OpenSSL with -libssh2 or -rtmp options
  - maketgz: Redirect updatemanpages.pl output to /dev/null
  - man pages: Require all to use the same section header order
  - manpage: Adjust the asterisk in some SYNOPSIS sections
  - md5: Fix compilation with OpenSSL 3.0 API
  - misc: Fix a few issues on MidnightBSD
  - misc: Fix typos in docs and comments
  - ngtcp2: Advertise h3 as well as h3-29
  - ngtcp2: Compile with the latest nghttp3
  - ngtcp2: Specify the missing required callback functions
  - ngtcp2: Use latest QUIC TLS RFC9001
  - NTLM: Use DES_set_key_unchecked with OpenSSL
  - openssl: If verifypeer is not requested, skip the CA loading
  - openssl: With OpenSSL 1.1.0+ a failed RAND_status means goaway
  - Revert "src/tool_filetime: Disable -Wformat on mingw for this file"
  - sasl: Binary messages
  - schannel: Fix memory leak due to failed SSL connection
  - scripts/delta: Count command line options in the new file
  - sendf: Accept zero-length data in Curl_client_write()
  - sha256: Use high-level EVP interface for OpenSSL
  - smooth-gtk-thread.c: Enhance the mutex lock use
  - sws: Fix memory leak on exit
  - test1160: Edited to work with hyper
  - test1173: Make manpage-syntax.pl spot \n errors in examples
  - test1185: Verify checksrc
  - test1266/1267: Disabled on hyper: no HTTP/0.9 support
  - test1287: Make work on hyper
  - test207: Accept a different error code for hyper
  - test262: Don't attempt with hyper
  - test552: Updated to work with hyper
  - test559: Add 'HTTP' in keywords
  - tests/smbserver.py: Fix compatibility with impacket 0.9.23+
  - tests: Add Schannel-specific tests and disable unsupported ones
  - tests: Disable test 2043
  - tests: Kill some test servers afterwards to avoid locked logfiles
  - tests: Use python3 in test 1451
  - tls: Remove newline from three infof() calls
  - tool_cb_prg: Make resumed upload progress bar show better
  - tool_listhelp: Easier generated with gen.pl
  - tool_main: Fix typo in comment
  - tool_operate: A failed etag save now only fails that transfer
  - URL-SYNTAX: Add IMAP UID SEARCH example
  - url: Check the return value of curl_url()
  - url: Set "k->size" -1 at start of request
  - urlapi: Skip a strlen(), pass in zero
  - urlapi: URL decode percent-encoded host names
  - version_win32: Use actual version instead of manifested version
  - vtls: Fix a memory leak if an SSL session cannot be added to the cache
  - wolfssl: Use for SHA256, MD4, MD5, and setting DES odd parity
  - zuul: Pin the quiche build to use an older cmake-rs
- Add workaround for GSSAPI detection in Fedora 19 and Fedora 20

* Wed Oct 27 2021 Paul Howarth <paul@city-fan.org> - 7.79.1-3.0.cf
- Re-enable HSTS in libcurl-minimal as a security feature (#2005874)

* Tue Oct  5 2021 Paul Howarth <paul@city-fan.org> - 7.79.1-2.0.cf
- Disable more protocols and features in libcurl-minimal (#2005874)
- Run upstream tests for both curl-minimal and curl-full
- Explicitly disable zstd while configuring curl
- Don't bother looking for Kerberos in /usr/kerberos anymore

* Wed Sep 22 2021 Paul Howarth <paul@city-fan.org> - 7.79.1-1.0.cf
- Update to 7.79.1
  - Curl_http2_setup: Don't change connection data on repeat invokes
  - curl_multi_fdset: Make FD_SET() not operate on sockets out of range
  - dist: Provide lib/.checksrc in the tarball
  - FAQ: Add GOPHERS + curl works on data, not files
  - hsts: CURLSTS_FAIL from hsts read callback should fail transfer
  - hsts: Handle unlimited expiry
  - http: Fix the broken >3 digit response code detection
  - strerror: Use sys_errlist instead of strerror on Windows
  - test1184: Disable
  - tests/sshserver.pl: Make it work with openssh-8.7p1

* Thu Sep 16 2021 Paul Howarth <paul@city-fan.org> - 7.79.0-4.0.cf
- Fix regression in http2 implementation introduced in the last release
- Make SCP/SFTP tests work with openssh-8.7p1

* Wed Sep 15 2021 Paul Howarth <paul@city-fan.org> - 7.79.0-1.0.cf
- Update to 7.79.0
  - bearssl: Support CURLOPT_CAINFO_BLOB
  - http: Consider cookies over localhost to be secure
  - secure transport: Support CURLINFO_CERTINFO
  - CVE-2021-22945: Clear the leftovers pointer when sending succeeds
  - CVE-2021-22946: Do not ignore --ssl-reqd
  - CVE-2021-22947: Reject STARTTLS server response pipelining
  - ares: Use ares_getaddrinfo()
  - asyn-ares.c: Move all version number checks to the top
  - auth: Do not append zero-terminator to authorisation id in kerberos
  - auth: Properly handle byte order in kerberos security message
  - auth: Use sasl authzid option in kerberos
  - auth: We do not support a security layer after kerberos authentication
  - BINDINGS.md: Update links to use https where available
  - build: Fix compiler warnings
  - c-hyper: Deal with Expect: 100-continue combined with POSTFIELDS
  - c-hyper: Fix header value passed to debug callback
  - c-hyper: Handle HTTP/1.1 ⇒ HTTP/1.0 downgrade on reused connection
  - c-hyper: Initial step for 100-continue support
  - c-hyper: Initial support for "dumping" 1xx HTTP responses
  - c-hyper: Remove the hyper_executor_poll() loop from Curl_http
  - CI/cirrus: Reduce compile time with increased parallelism
  - CI: Use GitHub Container Registry instead of Docker Hub
  - cirrus: Add FreeBSD 13.0 job and disable sanitizer build
  - cmake: Avoid poll() on macOS
  - cmake: Sync CURL_DISABLE options
  - codeql: Fix error "Resource not accessible by integration"
  - compressed.d: It's a request, not an order
  - config.d: Escape the backslash properly
  - config.d: Note that curlrc is used even when --config
  - config: Get rid of the unused HAVE_SIG_ATOMIC_T et. al.
  - configure.ac: Revert bad nghttp2 library detection improvements
  - configure: Error out if both ngtcp2 and quiche are specified
  - configure: Make --disable-hsts work
  - configure: Set classic mingw minimum OS version to XP
  - configure: Tweak nghttp2 library name fix
  - connect: Get local port + ip also when reusing connections
  - connect: Remove superfluous conditional
  - curl-openssl.m4: Check lib64 for the pkg-config file
  - curl-openssl.m4: Show correct output for OpenSSL v3
  - curl.1: Mention "global" flags
  - curl.1: Provide examples for each option
  - curl: Add warning for ignored data after quoted form parameter
  - curl: Add warning for incompatible parameters usage
  - curl: Better error message when -O fails to get a good name
  - curl: Stop retry if Retry-After: is longer than allowed
  - curl_easy_setopt.3: Improve the string copy wording
  - Curl_hsts_loadcb: Don't attempt to load if hsts wasn't inited
  - curl_setup.h: Sync values for HTTP_ONLY
  - curl_url_get.3: Clarify about path and query
  - CURLMOPT_TIMERFUNCTION.3: Remove misplaced "time"
  - CURLOPT_DOH_URL.3: CURLOPT_OPENSOCKETFUNCTION is not inherited
  - CURLOPT_SSL_CTX_*.3: Tidy up the example
  - CURLOPT_UNIX_SOCKET_PATH.3: Remove nginx reference, add see also
  - docs/MQTT: Update state of username/password support
  - docs: Remove experimental mentions from HSTS and MQTT
  - docs: The security list is reached at security at curl.se now
  - easy: Use a custom implementation of wcsdup on Windows
  - examples/*hiperfifo.c: Fix calloc arguments to match function proto
  - examples/cookie_interface: Avoid printfing time_t directly
  - examples/cookie_interface: Fix scan-build printf warning
  - examples/ephiperfifo.c: Simplify signal handler
  - FAQ: Add two dev related questions
  - getparameter: Fix the --local-port number parser
  - happy-eyeballs-timeout-ms.d: Polish the wording
  - hostip: Make Curl_ipv6works function independent of getaddrinfo
  - http2: Curl_http2_setup needs to init stream data in all invokes
  - http2: Revert a change that broke upgrade to h2c
  - http2: Revert call the handle-closed function correctly on closed stream
  - http: Disallow >3-digit response codes
  - http: Ignore content-length if any transfer-encoding is used
  - http_proxy: Clear 'sending' when the outgoing request is sent
  - http_proxy: Fix the User-Agent inclusion in CONNECT
  - http_proxy: Fix user-agent and custom headers for CONNECT with hyper
  - http_proxy: Only wait for writeable socket while sending request
  - INTERNALS: Bump c-ares requirement to 1.16.0
  - INTERNALS: c-ares has a new home: c-ares.org
  - lib: Don't use strerror()
  - libcurl-errors.3: Clarify two CURLUcode errors
  - limit-rate.d: Clarify base unit
  - mailing lists: Move from cool.haxx.se to lists.haxx.se
  - mbedtls: Avoid using a large buffer on the stack
  - mbedTLS: Initial 3.0.0 support
  - mbedtls_threadlock: Fix unused variable warning
  - mksymbolsmanpage.pl: Fix showing symbol's last used version
  - mksymbolsmanpage.pl: Match symbols case insensitively
  - multi: Fix compiler warning with 'CURL_DISABLE_WAKEUP'
  - ngtcp2: Compile with the latest ngtcp2 and nghttp3
  - ngtcp2: Fix build with ngtcp2 and nghttp3
  - ngtcp2: Remove the acked_crypto_offset struct field init
  - ngtcp2: Replace deprecated functions with nghttp3_conn_shutdown_stream_read
  - ngtcp2: Reset the outstanding send buffer again when drained
  - ngtcp2: Rework the return value handling of ngtcp2_conn_writev_stream
  - ngtcp2: Stop buffering crypto data
  - ngtcp2: Utilize crypto API functions to simplify
  - openssl: Annotate SSL3_MT_SUPPLEMENTAL_DATA
  - openssl: When creating a new context, there cannot be an old one
  - opt-docs: Make sure all man pages have examples
  - opt-docs: Verify man page sections + order
  - opts docs: Unify phrasing in NAME header
  - output.d: Add method to suppress response bodies
  - page-header: Add GOPHERS, simplify wording in the 1st paragraph
  - progress: Fix a compile warning on some systems
  - progress: Make trspeed avoid floats
  - runtests: Add option -u to error on server unexpectedly alive
  - schannel: Work around typo in classic mingw macro
  - scripts: Invoke interpreters through /usr/bin/env
  - setopt: Enable CURLOPT_IGNORE_CONTENT_LENGTH for hyper
  - strerror.h: Remove the #include from files not using it
  - symbols-in-versions: Fix CURLSSLBACKEND_QSOSSL last used version
  - test1138: Remove trailing space to make work with hyper
  - test1173: Check references to libcurl options
  - test1280: CRLFify the response to please hyper
  - test1565: Fix Windows build errors
  - test365: Verify response with chunked AND Content-Length headers
  - tests/*server.pl: Flush output before executing subprocess
  - tests/*server.py: Remove pidfile on server termination
  - tests/runtests.pl: Cleanup copy&paste mistakes and unused code
  - tests/server/*.c: Align handling of portfile argument and file
  - tests: Adjust the tftpd output to work with hyper mode
  - tests: Be explicit about using 'python3' instead of 'python'
  - tests: Enable test 1129 for hyper builds
  - tests: Make three tests pass until 2037
  - tool/tests: Fix potential year 2038 issues
  - tool_operate: Fix --fail-early with parallel transfers
  - url: Fix compiler warning in no-verbose builds
  - urlapi.c:seturl: Assert URL instead of using if-check
  - vtls: Fix typo in schannel_verify.c
  - winbuild/README.md: Clarify GEN_PDB option
  - wolfssl: clean up wolfcrypt error queue
  - write-out.d: Clarify size_download/upload
  - x509asn1: Fix heap over-read when parsing x509 certificates

* Sat Jul 24 2021 Paul Howarth <paul@city-fan.org> - 7.78.0-3.0.cf
- Make explicit dependency on openssl work with alpha/beta builds of openssl

* Thu Jul 22 2021 Paul Howarth <paul@city-fan.org> - 7.78.0-2.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Wed Jul 21 2021 Paul Howarth <paul@city-fan.org> - 7.78.0-1.0.cf
- Update to 7.78.0
  - curl_url_set: Reject spaces in URLs w/o CURLU_ALLOW_SPACE
  - CURLE_SETOPT_OPTION_SYNTAX: New error name for wrong setopt syntax
  - hostip: Make 'localhost' return fixed values
  - mbedtls: Add support for cert and key blob options
  - metalink: Remove all support for it (CVE-2021-22922, CVE-2021-22923)
  - mqtt: Add support for username and password
  - --socks4[a]: Clarify where the host name is resolved
  - ares: Always store IPv6 addresses first
  - asyn-ares: Remove check for 'data' in Curl_resolver_cancel
  - bearssl: Explicitly initialize all fields of Curl_ssl
  - bearssl: Remove incorrect const on variable that is modified
  - build: Fix compiler warnings when CURL_DISABLE_VERBOSE_STRINGS
  - c-hyper: Abort CONNECT response reading early on non 2xx responses
  - c-hyper: Add support for transfer-encoding in the request
  - c-hyper: Bail on too long response headers
  - c-hyper: Clear NTLM auth buffer when request is issued
  - c-hyper: Convert HYPERE_INVALID_PEER_MESSAGE to CURLE_UNSUPPORTED_PROTOCOL
  - c-hyper: Fix NTLM on closed connection tested with test159
  - c-hyper: Fix the uploaded field in progress callbacks
  - c-hyper: Handle NULL from hyper_buf_copy()
  - c-hyper: Support CURLINFO_STARTTRANSFER_TIME
  - c-hyper: Support CURLOPT_HEADER
  - ccsidcurl: Fix the compile errors
  - CI/cirrus: Install impacket from PyPI instead of FreeBSD packages
  - CI: Add bearssl build
  - CI: Add Circle CI
  - CI: Add jobs using Zuul
  - CI: Delete --enable-hsts option (it is the default now)
  - CI: Remove travis details
  - cleanup: Spell DoH with a lowercase o
  - cmake: Add CURL_DISABLE_NTLM option
  - cmake: Avoid leaking absolute paths into exported config
  - cmake: Fix IoctlSocket FIONBIO check
  - cmake: Fix support for UnixSockets feature on Win32
  - cmake: Remove libssh2 feature checks
  - cmake: Try well-known send/recv signature for Apple
  - configure.ac: Make non-executable
  - configure/cmake: Remove checks for many unused functions
  - configure: Add --disable-ntlm option
  - configure: Disable RTSP when hyper is selected
  - configure: Do not strip out debug flags
  - configure: Fix nghttp2 library name for static builds
  - configure: Inhibit the implicit-fallthrough warning on gcc-12
  - configure: Rename get-easy-option configure option to get-easy-options
  - conn_shutdown: If closed during CONNECT, clean up properly
  - conncache: Lowercase the hash key for better match
  - cookies: Track expiration in jar to optimize removals
  - copyright: Add boiler-plate headers to CI config files
  - crustls: Bump crustls version and use new URL
  - curl.h: <sys/select.h> is supported by VxWorks7
  - curl.h: include sys/select.h for NuttX RTOS
  - curl: Ignore blank --output-dir
  - curl_endian: Remove the unused Curl_write64_le function
  - curl_multibyte: Remove local encoding fallbacks
  - Curl_ntlm_core_mk_nt_hash: Fix OOM in error path
  - Curl_ssl_getsessionid: Fail if no session cache exists
  - CURLOPT_WRITEFUNCTION.3: Minor update of the example
  - docs/BINDINGS: Fix outdated links
  - docs/examples: Use curl_multi_poll() in multi examples
  - docs/INSTALL: Remove mentions of configure --with-darwin-ssl
  - docs: Document missing arguments to commands
  - docs: Fix inconsistencies in EGDSOCKET documentation
  - docs: Fix incorrect argument name reference
  - docs: Fix typos
  - docs: Make docs for --etag-save match the program behaviour
  - docs: Use --max-redirs instead of --max-redir
  - doh: (void)-prefix call to curl_easy_setopt
  - doh: Fix wrong DEBUGASSERT for doh private_data
  - easy: During upkeep, attach Curl_easy to connections in the cache
  - examples/multi-single: Fix scan-build warning
  - examples: length-limit two sscanf() uses of %%s
  - examples: Safer and more proper read callback logic
  - filecheck: Quietly remove test-place/*~
  - formdata: Avoid "Argument cannot be negative" warning
  - formdata: Correct typecast in curl_mime_data call
  - GHA: Add a linux-hyper job
  - GHA: Add several libcurl tests to the hyper job
  - GHA: Run the newly fixed tests with hyper
  - github: Timeout jobs on macOS after 90 minutes
  - glob: Pass an 'int' as len when using printf's %%*s
  - gnutls: Set the preferred TLS versions in correct order
  - GOVERNANCE: Add 'user', 'committer' and 'contributor'
  - hostip: (macOS) free returned memory of SCDynamicStoreCopyProxies
  - hostip: Bad CURLOPT_RESOLVE syntax now returns error
  - hsts: Ignore numerical IP address hosts
  - HSTS: Not experimental anymore
  - http2: Clarify 'Using HTTP2' verbose message
  - http2: init recvbuf struct for pushed streams
  - http2_connisdead: Handle trailing GOAWAY better
  - http: Fix crash in rate-limited upload
  - http: Make the haproxy support work with unix domain sockets
  - http_proxy: Deal with non-200 CONNECT response with Hyper
  - hyper: Propagate errors back up from read callbacks
  - HYPER: Remove mentions of deprecated development branch
  - idn: Fix libidn2 with windows unicode builds
  - infof: Remove newline from format strings, always append it
  - lib: Don't compare fd to FD_SETSIZE when using poll
  - lib: Fix compiler warnings with CURL_DISABLE_NETRC
  - lib: Fix type of len passed to *printf's %%*s
  - lib: More %%u for port and int for %%*s fixes
  - lib: Use %%u instead of %%ld for port number printf
  - libcurl-security.3: Mention file descriptors and forks
  - libssh2: Limit time a disconnect can take to 1 second
  - mbedtls: Make mbedtls_strerror always work
  - mbedtls: Remove unnecessary include
  - mqtt: Detect illegal and too large file size
  - mqtt: Extend the error message for no topic
  - msnprintf: Return number of printed characters excluding null byte
  - multi: Add scan-build-6 work-around in curl_multi_fdset
  - multi: Alter transfer timeout ordering
  - multi: Do not switch off connect_only flag when closing
  - multi: Fix crash in curl_multi_wait / curl_multi_poll
  - netrc: Skip 'macdef' definitions
  - ngtcp2: Disable TLSv1.3 compatible mode when using GnuTLS
  - openssl: Avoid static variable for seed flag
  - openssl: Don't remove session id entry in disassociate
  - pinnedpubkey.d: Fix formatting for version support lists
  - proto.d: Fix formatting for paragraphs after margin changes
  - quiche: Use send() instead of sendto() to avoid macOS issue
  - Revert "c-hyper: handle body on HYPER_TASK_EMPTY"
  - Revert "ftp: Expression 'ftpc->wait_data_conn' is always false"
  - runtests: Also find the last test in Makefile.inc
  - runtests: Enable 'hyper mode' only for HTTP tests
  - runtests: init $VERSION to avoid warnings when using -l
  - runtests: Parse data/Makefile.inc instead of using make
  - runtests: Skip disabled tests unless -f is used
  - rustls: Remove native_roots fallback
  - schannel: Set ALPN length correctly for HTTP/2
  - SChannel: Use '_tcsncmp()' instead
  - sectransp: Check for client certs by name first, then file (CVE-2021-22926)
  - setopt: Fix incorrect comments
  - socketpair: Fix potential hangs
  - socks4: Scan for the IPv4 address in resolve results
  - ssl: Read pending close notify alert before closing the connection
  - sws: malloc request struct instead of using stack
  - telnet: Fix option parser to not send uninitialized contents
    (CVE-2021-22925)
  - test1116: hyper doesn't pass through "surprise-trailers"
  - test1147: hyper doesn't allow "crazy" request headers like built-in
  - test1151: Added missing CRLF to work with hyper
  - test1216: Adjusted for hyper mode
  - test1218: Adjusted for hyper mode
  - test1230: Adjust to work in hyper mode
  - test1340/1341: Adjusted for hyper mode
  - test1438/1457: Add HTTP keyword to make hyper mode work
  - test1514: Add a CRLF to the response to make it correct
  - test1518: Adjusted to work with hyper
  - test1519: Adjusted to work with hyper
  - test1594/1595/1596: Fix to work in hyper mode
  - test269: Disable for hyper
  - test3010: Work with hyper mode
  - test328: Avoid a header-looking body to make hyper mode work
  - test339: CRLFify better to work in hyper mode
  - test347: CRLFify to work in hyper mode
  - test393: Make Content-Length fit within 64 bit for hyper
  - test394: hyper returns a different error
  - test395: hyper cannot work around > 64 bit content-lengths like built-in
  - test433: Adjust for hyper mode
  - test434: Add HTTP keyword
  - test500: Adjust to work with hyper mode
  - test566: Adjust to work with hyper mode
  - test599: Adjusted to work in hyper mode
  - test644: Remove as duplicate of test 587
  - tests: Fix Accept-Encoding strips to work with Hyper builds
  - TLS: Prevent shutdown loops to get stuck
  - tool: Make _lseeki64() macro work with the PellesC compiler
  - tool_help: Document that --tlspassword takes a password
  - tool_help: Remove unused define
  - url.c: Remove two variable assigns that are never read
  - url: (void)-prefix a curl_url_get() call
  - url: Bad CURLOPT_CONNECT_TO syntax now returns error
  - version: Turn version number functions into returning void
  - vtls: exit addsessionid if no cache is inited
  - vtls: Fix connection reuse checks for issuer cert and case sensitivity
    (CVE-2021-22924)
  - vtls: Only store TIMER_APPCONNECT for non-proxy connect
  - vtls: Use free() not curl_free()
  - warnless: Simplify type size handling
  - Win32: Fix build with Watt-32
  - winbuild/README: VC should be set to 6 'or larger'
  - winbuild: Support alternate nghttp2 static lib name
  - wolfssl: Failing to set a session id is not reason to error out
  - write-out.d: Clarify urlnum is not unique for de-globbed URLs
  - zuul: Use the new rustls directory name
- Fix dist tags for Alma and Rocky Linux

* Thu Jun  3 2021 Paul Howarth <paul@city-fan.org> - 7.77.0-2.0.cf
- Build the curl tool without metalink support (#1967213)
  https://curl.se/mail/archive-2021-06/0006.html
  https://github.com/curl/curl/pull/7176

* Wed May 26 2021 Paul Howarth <paul@city-fan.org> - 7.77.0-1.0.cf
- Update to 7.77.0
  - CVE-2021-22297: schannel cipher selection surprise
  - CVE-2021-22298: TELNET stack contents disclosure
  - CVE-2021-22901: TLS session caching disaster
  - configure: Make the TLS library choice(s) explicit
  - curl: Ignore options asking for SSLv2 or SSLv3
  - hsts: Enable by default
  - SSL: Support in-memory CA certs for some backends
  - vtls: Refuse setting any SSL version
  - AmigaOS: Add functions definitions for SHA256
  - build: Fix compilation for Windows UWP platform
  - c-hyper: Don't write to set.writeheader if null
  - c-hyper: Fix handling of zero-byte chunk from hyper
  - c-hyper: Handle body on HYPER_TASK_EMPTY
  - checksrc: Complain on == NULL or != 0 checks in conditions
  - CI/cirrus: Add shared and static Windows release builds
  - cmake: Add CURL_ENABLE_EXPORT_TARGET option
  - cmake: Check for getppid and utimes
  - cmake: Detect CURL_SA_FAMILY_T
  - cmake: Fix two invokes result in different curl_config.h
  - cmake: Make libcurl output filename configurable
  - cmake: Use multithreaded compilation on VS 2008+
  - config: Remove now-unused macros
  - configure: If asked for, fail if ldap is not found
  - configure: Provide --with-openssl, deprecate --with-ssl
  - conn: Add 'attach' to protocol handler, make libssh2 use it
  - connect: Use CURL_SA_FAMILY_T for portability
  - ConnectionExists: Respect requests for h1 connections better
  - cookie: CURLOPT_COOKIEFILE set to NULL switches off cookies
  - curl-wolfssl.m4: Without custom include path, assume /usr/include
  - curl: Include libmetalink version in --version output
  - Curl_http_header: Check for colon when matching Persistent-Auth
  - Curl_http_input_auth: Require valid separator after negotiation type
  - Curl_input_digest: Require space after Digest
  - curl_mprintf.3: Add description
  - curl_setup: Provide the shutdown flags wider
  - curl_url_set.3: Add memory management information
  - CURLcode: Add CURLE_SSL_CLIENTCERT
  - CURLOPT_CAPATH.3: Defaults to a path, not NULL
  - CURLOPT_IPRESOLVE: Preventing wrong IP version from being used
  - CURLOPT_POSTFIELDS.3: Clarify how it gets the size of the data
  - data_pending: Check only SECONDARY socket for FTP(S) transfers
  - docs/TheArtOfHttpScripting: Fix markdown links
  - docs: CamelCase it like GitHub everywhere
  - docs: Cookies from HTTP headers need domain set
  - docs: Fix typo in fail-with-body doc
  - docs: Improve INTERNALS.md regarding getsock cb
  - docs: Replace dots with dashes in markdown enums
  - easy: Ignore sigpipe in curl_easy_send
  - FILEFORMAT: Mention sectransp as a feature
  - GIT-INFO: Suggest using autoreconf instead of buildconf
  - GitHub: Add a workflow with libssh2 on macOS using cmake
  - GitHub: Inhibit deprecated declarations for clang on macOS
  - GnuTLS: Don't allow TLS 1.3 for versions that don't support it
  - gnutls: Make setting only the MAX TLS allowed version work
  - gskit: Fix CURL_DISABLE_PROXY build
  - gskit: Fix undefined reference to 'conn'
  - hostip.h: Remove declaration of unimplemented function
  - hostip: Remove the debug code for LocalHost
  - http2: Call the handle-closed function correctly on closed stream
  - http2: Fix a resource leak in push_promise()
  - http2: Fix resource leaks in set_transfer_url()
  - http2: Make sure pause is done on HTTP
  - http2: Move the stream error field to the per-transfer storage
  - http2: Skip immediate parsing of payload following protocol switch
  - http2: Use nghttp2_session_upgrade2 instead of nghttp2_session_upgrade
  - HTTP3.md: Fix nghttp2's HTTP/3 server port
  - HTTP3.md: Make the ngtcp2 build use the quictls fork
  - http: Deal with partial CONNECT sends
  - http: Fix the check for 'Authorization' with Bearer
  - http: Limit the initial send amount to used upload buffer size
  - http: Reset the header buffer when sending the request
  - http: Use offsets inst of integer literals for header parsing
  - INSTALL: Add IBM i specific quirks
  - krb5/name_to_level: Replace checkprefix with curl_strequal
  - krb5: Don't use 'static' to store PBSZ size response
  - krb5: Remove the unused 'overhead' function
  - lib/hostip6.c: Make NAT64 address synthesis on macOS work
  - lib1564.c: Enable last wakeup test part on Windows
  - lib: Fix 0-length Curl_client_write calls
  - lib: Fix some misuse of curlx_convert_UTF8_to_tchar
  - libcurl-security.3: Be careful of setuid
  - libcurl-security.3: Don't try to filter IPv4 hosts based on the URL
  - libcurl.3: Mention the URL API
  - libssh2: Fix Value stored to 'sshp' is never read
  - libssh2: Ignore timeout during disconnect
  - libssh: Fix "empty expression statement has no effect" warnings
  - libtest: Remove lib530.c
  - m4: Add security frameworks on Mac when compiling rustls
  - multi: Don't close connection HTTP_1_1_REQUIRED
  - multi: Fix slow write/upload performance on Windows
  - multi: Reduce Win32 API calls to improve performance
  - ngtcp2: Fix the cb_acked_stream_data_offset proto
  - NSS: Add ciphers to map
  - NSS: Make colons, commas and spaces valid separators in cipher list
  - nss_set_blocking: Avoid static for sock_opt
  - ntlm: Precaution against super huge type2 offsets
  - openldap: Protect SSL-specific code with proper #ifdef
  - openldap: Replace ldap_ prefix on private functions
  - openssl: fix build error with OpenSSL < 1.0.2
  - openssl: Remove unneeded cast for CertOpenSystemStore()
  - os400: Additional support for options metadata
  - progress: Fix scan-build-11 warnings
  - progress: Reset limit_size variables at transfer start
  - progress: When possible, calculate transfer speeds with microseconds
  - README.md: Delete Codacy UTM parameters
  - Revert "Revert 'multi: implement wait using winsock events'"
  - rustls: Only return CURLE_AGAIN when TLS session is fully drained
  - rustls: Use ALPN
  - sasl: Use 'unsigned short' to store mechanism
  - schannel: Disable auto credentials; add an option to enable it
  - schannel: Support strong crypto option
  - sectransp: Allow cipher name to be specified
  - sectransp: Fix EXC_BAD_ACCESS caused by uninitialized buffer
  - sigpipe: Ignore SIGPIPE when using wolfSSL as well
  - sockfilt: Avoid getting stuck waiting for writable socket
  - sockfilt: Fix invalid increment of handles index variable nfd
  - sws: #ifdef S_IFSOCK use
  - sws: Allow HTTP requests up to 2MB in size
  - test server: Take care of siginterrupt() deprecation
  - test2100: Make it run with and require IPv6
  - tests/disable-scan.pl: Also scan all m4 files
  - tests/getpart: Generate output URL encoded for better diffs
  - tests: Ignore case of chunked hex numbers in tests
  - tls: Add USE_HTTP2 define
  - tool_getparam: Handle failure of curlx_convert_tchar_to_UTF8()
  - tool_getparam: Replace (in-place) '%20' by '+' according to RFC1866
  - tool_operate: Don't discard failed parallel transfer result
  - tool_writeout: Fix the HTTP_CODE json output
  - travis: Disable the failing libssh build
  - URL-SYNTAX: Update IDNA section for WHATWG spec changes
  - urlapi: "normalize" numerical IPv4 host names
  - vauth: Factor base64 conversions out of authentication procedures
  - version: Add gsasl_version to curl_version_info_data
  - version: Add OpenLDAP version in the output
  - vtls: Deduplicate some DISABLE_PROXY ifdefs
  - vtls: Reset ssl use flag upon negotiation failure
  - wolfssl: Handle SSL_write() returns 0 for error
  - wolfssl: Remove SSLv3 support leftovers
- Add patch to kill the gophers server after testing that protocol, so that
  the port it uses can be re-used by later tests

* Tue May  4 2021 Paul Howarth <paul@city-fan.org> - 7.76.1-2.0.cf
- http2: Fix resource leaks detected by Coverity

* Wed Apr 14 2021 Paul Howarth <paul@city-fan.org> - 7.76.1-1.0.cf
- Update to 7.76.1
  - configure: Disable min version set for Darwin
  - configure: include <time.h> unconditionally
  - configure: Remove use of RETSIGTYPE
  - docs/HTTP3.md: Update the build instruction using gnutls
  - examples/hiperfifo.c: Check event_initialized before delete
  - file: Support GETing directories again
  - github/workflow: Add "security-extended" to codeql-analysis.yml
  - h2: Allow 100 streams by default
  - hostip: Fix builds that disable all asynchronous DNS
  - http_proxy: Only loop on 407 + close if we have credentials
  - install: Add instructions for Apple Darwin platforms
  - lib: Remove unused HAVE_INET_NTOA_R* defines
  - libssh: Get rid of PATH_MAX
  - ngtcp2+gnutls: Clear credentials when freed
  - ngtcp2: Use ALPN h3-29 for now
  - ntlm: Fix negotiated flags usage
  - ntlm: Support version 2 on 32-bit platforms
  - openssl: Fix CURLOPT_SSLCERT_BLOB without CURLOPT_SSLCERT_KEY
  - TLS: Fix HTTP/2 selection
  - tool_progress: Fix progress meter final update in parallel mode
  - typecheck-gcc: Make the ssl-ctx-cb check use SSL_CTX pointers

* Wed Mar 31 2021 Paul Howarth <paul@city-fan.org> - 7.76.0-1.0.cf
- Update to 7.76.0
  - cookies: Support multiple -b parameters
  - curl: Add --fail-with-body
  - doh: Add options to disable ssl verification
  - http: Add support to read and store the referrer header
  - sasl: Support SCRAM-SHA-1 and SCRAM-SHA-256 via libgsasl
  - vtls: Initial implementation of rustls backend
  - CVE-2021-22876: Strip credentials from the auto-referer header field
  - CVE-2021-22890: Add 'isproxy' argument to Curl_ssl_get/addsessionid()
  - asyn-ares: Use consistent resolve error message
  - BUG-BOUNTY: Removed the cooperation mention
  - build: Delete unused feature guards
  - build: Fix --disable-dateparse
  - build: Fix --disable-http-auth
  - build: Remove all traces of USE_BLOCKING_SOCKETS
  - c-hyper: Remove superfluous pointer check
  - c-hyper: Support automatic content-encoding
  - CI/azure: Disable test 433 on azure-ubuntu
  - CI/azure: Replace python-impacket with python3-impacket
  - ci: Stop building on freebsd-12-1
  - cmake: Fix import library name for non-MS compiler on Windows
  - cmake: Use CMAKE_INSTALL_INCLUDEDIR indirection
  - cmake: Support WinIDN
  - config: Fix building SMB with configure using Win32 Crypto
  - config: Fix detection of restricted Windows App environment
  - configure: Fail if --with-quiche is used and quiche isn't found
  - configure: Make AC_TRY_* into AC_*_IFELSE
  - configure: Make hyper opt-in, and fail if missing
  - configure: Only add OpenSSL paths if they are defined
  - configure: Provide Largefile feature for curl-config
  - configure: Remove use of deprecated macros
  - configure: s/AC_HELP_STRING/AS_HELP_STRING/
  - cookies: Fix potential NULL pointer deref with PSL
  - curl: Set CURLOPT_NEW_FILE_PERMS if requested
  - curl_easy_setopt.3: Add curl_easy_option* functions to SEE ALSO
  - curl_multibyte: Always return a heap-allocated copy of string
  - curl_multibyte: Fall back to local code page stat/access on Windows
  - Curl_timeleft: Check both timeouts during connect
  - curl_url_set.3: Mention CURLU_PATH_AS_IS
  - CURLOPT_QUOTE.3: Clarify that libcurl doesn't parse what's sent
  - docs/HTTP2: Remove the outdated remark about multiplexing for the tool
  - docs/Makefile.inc: Format to be update-friendly
  - docs: Add CURLOPT_CURLU to 'See also' in curl_url_ functions
  - docs: Add missing Arg tag to --stderr
  - docs: Add SSL backend names to CURL_SSL_BACKEND
  - docs: Clarify timeouts for queued transfers in multi API
  - docs: Explain DOH transfers inherit some SSL settings
  - docs: Fix FILE example url in --metalink documentation
  - docs: Make gen.pl support *italic* and **bold**
  - doh: Fix sharing user's resolve list with DOH handles
  - doh: Inherit CURLOPT_STDERR from user's easy handle
  - dynbuf: Bump the max HTTP request to 1MB
  - examples: Remove threaded-shared-conn.c due to bug
  - file: Support unicode urls on windows
  - ftp: Add 'list_only' to the transfer state struct
  - ftp: Add 'prefer_ascii' to the transfer state struct
  - FTP: Allow SIZE to fail when doing (resumed) upload
  - ftp: Avoid SIZE when asking for a TYPE A file
  - ftp: Fix Codacy/cppcheck warning about null pointer arithmetic
  - ftp: Fix memory leak in ftp_done
  - ftp: Never set data->set.ftp_append outside setopt
  - gen.pl: Quote "bare" minuses in the nroff curl.1
  - github: Add torture-ftp for FTP-only torture testing
  - gnutls: Assume nettle crypto support
  - gskit: Correct the gskit_send() prototype
  - hostip: Fix build with sync resolver
  - hostip: Fix crash in sync resolver builds that use DOH
  - hsts: Remove unused defines
  - http2: Don't set KEEP_SEND when there's no more data to be sent
  - http2: Fail if connection terminated without END_STREAM
  - http: Cap body data amount during send speed limiting
  - http: Do not add a referrer header with empty value
  - http: Make 416 not fail with resume + CURLOPT_FAILONERRROR
  - http: Remove superfluous NULL assign
  - http: Strip default port from URL sent to proxy
  - http: Use credentials from transfer, not connection
  - ldap: Use correct memory free function
  - lib1536: Check ptr against NULL before dereferencing it
  - lib1537: Check ptr against NULL before dereferencing it
  - lib: Remove 'conn->data' completely
  - libssh2: kdb_callback: Get the right struct pointer
  - libssh2:ssh_connect: Clear session pointer after free
  - memdebug: Close debug logfile explicitly on exit
  - mingw: Enable using strcasecmp()
  - multi: Close the connection when h2=>h1 downgrading
  - multi: Do once-per-transfer inits in before_perform in DID state
  - multi: Rename the multi transfer states
  - multi: Update pending list when removing handle
  - ngtcp2: Adapt to the new recv_datagram callback
  - ngtcp2: Clarify calculation precedence
  - ngtcp2: Fix build error due to change in ngtcp2_addr_init
  - ngtcp2: Sync with recent API updates
  - openldap: Avoid NULL pointer dereferences
  - openssl: Adapt to v3's new const for a few API calls
  - openssl: Ensure to check SSL_CTX_set_alpn_protos return values
  - openssl: Remove get_ssl_version_txt in favour of SSL_get_version
  - openssl: Set the transfer pointer for logging early
  - OS400: Update for CURLOPT_AWS_SIGV4
  - parse_proxy: Fix a memory leak in the OOM path
  - pathhelp.pm: Fix use of pwd -L in Msys environment
  - projects: Update VS projects for OpenSSL 1.1.x
  - quiche: Fix build error: use 'int' for port number
  - quiche: Fix crash when failing to connect
  - retry-all-errors.d: Explain curl errors versus HTTP response errors
  - retry.d: Clarify transient 5xx HTTP response codes
  - runtests.pl: Add %%TESTNUMBER variable to make copying tests more convenient
  - runtests.pl: Add a -P option to specify an external proxy
  - runtests.pl: Kill processes locking test log files
  - setopt: Error on CURLOPT_HTTP09_ALLOWED set true with Hyper
  - test1188: Change error to check for: --fail HTTP status
  - test220/314: Adjust to run with Hyper
  - test304: Header CRLF cleanup to work with Hyper
  - test306: Make it not run with Hyper
  - tests: Disable .curlrc in more environments
  - tests: Use %%TESTNUMBER instead of fixed number
  - tftp: Remove the 3600 second default timeout
  - time: Enable 64-bit time_t in supported mingw environments
  - tool_help: Add missing argument for --create-file-mode
  - tool_help: Increase space between option and description
  - tool_operate: Bail if set CURLOPT_HTTP09_ALLOWED returns error
  - travis: Add a rustls build
  - travis: Bump wolfssl to 4.7.0
  - travis: Only build wolfssl when needed
  - travis: Split "torture" into a separate "events" build
  - travis: Switch ngtcp2 build over to quictls
  - travis: Use ubuntu nghttp2 package instead of build our own
  - url.c: Use consistent error message for failed resolve
  - url: Fix memory leak if OOM in the HSTS handling
  - url: Fix possible use-after-free in default protocol
  - urldata: Don't touch data->set.httpversion at run-time
  - urldata: Fix build without HTTP and MQTT
  - urldata: Make 'actions[]' use unsigned char instead of int
  - urldata: Merge "struct DynamicStatic" into "struct UrlState"
  - urldata: Remove the 'rtspversion' field
  - urldata: Remove the _ORIG suffix from string names
  - version.d: Add missing features to the features list
  - wolfssl: Don't store a NULL sessionid

* Wed Mar 24 2021 Paul Howarth <paul@city-fan.org> - 7.75.0-3.0.cf
- Fix SIGSEGV upon disconnect of a ldaps:// transfer (#1941925)

* Wed Feb 24 2021 Paul Howarth <paul@city-fan.org> - 7.75.0-2.0.cf
- Don't anticipate python3-impacket being available for EL-9 builds

* Fri Feb 12 2021 Paul Howarth <paul@city-fan.org> - 7.75.0-1.1.cf
- Use unstripped library from the build dir for %%check: it results in more
  detailed backtraces in valgrind's output
- Re-enable tests that had previously been disabled

* Wed Feb  3 2021 Paul Howarth <paul@city-fan.org> - 7.75.0-1.0.cf
- Update to 7.75.0
  - curl: Add --create-file-mode [mode]
  - curl: Add new variables to --write-out
  - dns: Extend CURLOPT_RESOLVE syntax for adding non-permanent entries
  - gopher: Implement secure gopher protocol
  - http: Add Hyper as new optional HTTP backend
  - http: Introduce AWS HTTP v4 Signature support
  - badsymbols.pl: Add verbose mode -v
  - badsymbols.pl: Ignore stand-alone single hash lines
  - BUG-BOUNTY: Minor language updates
  - build: Fix djgpp builds
  - cleanup: Fix empty expression statement has no effect
  - cmake: Add an option to disable libidn2
  - cmake: Enable gophers correctly in curl-config
  - cmake: Expose CURL_DISABLE_OPENSSL_AUTO_LOAD_CONFIG
  - cmdline-opts/gen.pl: Return hard on errors
  - cmdline-opts/retry.d: Mention response code 429 as well
  - configure: Set -Wextra-semi-stmt for clang with --enable-debug
  - connect: Defer port selection until connect() time
  - connect: Mark intentional ignores of setsockopt return values
  - connect: On linux, enable reporting of all ICMP errors on UDP sockets
  - connect: Zero variable on stack to silence valgrind complaint
  - cookie: Avoid the C1001 internal compiler error with MSVC 14
  - curl.1: Fix typo microsft → microsoft
  - curl: Fix handling of -q option
  - curl: Include the file name in --xattr/--remote-time error msgs
  - curl: Move fprintf outputs to warnf
  - Curl_chunker: Shrink the struct
  - curl_easy_pause.3: Add multiplexed pause effects
  - CURLINFO_PRETRANSFER_TIME.3: Clarify
  - CURLOPT_URL.3: Remove scheme specific details
  - digest_sspi: Show InitializeSecurityContext errors in verbose mode
  - docs/examples: Adjust prototypes for CURLOPT_READFUNCTION
  - docs/URL-SYNTAX: The URL syntax curl accepts and works with
  - docs: Enable syntax highlighting in several docs files
  - docs: Fix line length bug in gen.pl
  - docs: Fix typos in NEW-PROTOCOL.md
  - docs: Fix wrong documentation in help.d
  - docs: Remove redundant "better" in --fail help
  - doh: Allocate state struct on demand
  - examples/libtest: Add .checksrc to dist
  - examples: Remove superfluous asterisk uses
  - failf: Remove newline from formatting strings
  - file: Don't provide content-length for directories
  - getinfo: Build with disabled HTTP support
  - gitattributes: Set batch files to CRLF line endings on checkout
  - h2: Do not wait for RECV on paused transfers
  - HISTORY: Added dates to early history
  - http: Empty reply connection are not left intact
  - http: Get CURLOPT_REQUEST_TARGET working with a HTTP proxy
  - http: Have CURLOPT_FAILONERROR fail after all headers
  - http: Make providing Proxy-Connection header not cause duplicated headers
  - http: Show the request as headers even when split-sending
  - http_chunks: Correct and clarify a comment on hexnumber length
  - http_proxy: Fix CONNECT chunked encoding race condition
  - httpauth: Make multi-request auth work with custom port
  - INSTALL: Now at 85 operating systems
  - INSTALL: Update the list known OSes and CPU archs curl has run on
  - lib/unit tests: Add missing curl_global_cleanup() calls
  - lib1564/5: Verify that curl_multi_wakeup returns OK
  - lib: Pass in 'struct Curl_easy *' to most functions
  - lib: Remove Curl_ prefix from many static functions
  - lib: Save a bit of space with some structure packing
  - libssh2: Fix "Value stored to 'readdir_len' is never read"
  - libssh2: Move data from connection object to transfer object
  - libssh: Avoid plain free() of libssh-memory
  - mime: Make sure setting MIMEPOST to NULL resets properly
  - misc: Assorted typo fixes
  - misc: Fix "warning: empty expression statement has no effect"
  - misc: Fix typos
  - mk-ca-bundle.pl: Deterministic output when using -t
  - mqtt: Deal with 0 byte reads correctly
  - mqtt: Handle POST/PUBLISH without a set POSTFIELDSIZE
  - multi: Set the PRETRANSFER time-stamp when we switch to PERFORM
  - multi: Skip DONE state if there's no connection left for ftp wildcard
  - multi: When erroring in TOOFAST state, act as for PERFORM
  - multi_runsingle: Bail out early on data->conn == NULL
  - ngtcp2: Fix http3 upload stall
  - ngtcp2: Fix stack buffer overflow
  - ngtcp2: Make it build it current master again
  - nss: Get the run-time version instead of build-time
  - openssl: Lowercase the hostname before using it for SNI
  - OS400: Update ccsidcurl.c
  - pretransfer: Set up the User-Agent header here
  - quiche: Remove fprintf() leftover
  - Revert "CI/github: work-around for brew breakage on macOS"
  - runtests: Add 'wakeup' as a feature
  - runtests: Add support for %%if [feature] conditions
  - runtests: Pre-process DISABLED to allow conditionals
  - schannel: Plug a memory leak
  - schannel_verify: Fix safefree call typo
  - select: Convert Curl_select() to private static function
  - socks: Use the download buffer instead
  - speedcheck: Exclude paused transfers
  - strerror: Skip errnum >= 0 assertion on Windows
  - test1522: Add debug tracing
  - test1633: Set appropriate name
  - test179: Use consistent header line endings
  - test410: Verify HTTPS GET with a 49K request header
  - tests/mqttd: Extract the client id from the correct offset
  - tests: Make --libcurl tests only test FTP options if ftp enabled
  - tool_doswin: Restore original console settings on CTRL signal
  - tool_operate: Fix the suppression logic of some error messages
  - tool_operate: Spellfix a comment
  - tooĺ_writeout: Fix the -w time output units
  - transfer: Fix GCC 10 warning with flag '-Wint-in-bool-context'
  - travis: Build ngtcp2 --with-gnutls
  - travis: Limit the tests with quiche builds to HTTPS and FTPS only
  - travis: Restrict the openssl3 job to only run https and ftps tests
  - url: If IDNA conversion fails, fallback to Transitional
  - urldata: Make magic be the first struct field
  - urldata: Remove 'local_ip' from the connectdata struct
  - urldata: Remove duplicate 'upkeep_interval_ms' from connectdata
  - urldata: Remove duplicate port number storage
  - urldata: Remove the duplicate 'ip_addr_str' field
  - urldata: Store ip version in a single byte
  - vtls: Remove md5sum
  - warnless: Remove curlx_ultosi
  - wolfssl: Add SECURE_RENEGOTIATION support
  - wolfssl: Support wolfSSL builds missing TLS 1.1
- Disable failing test 1592 for now

* Tue Jan 26 2021 Paul Howarth <paul@city-fan.org> - 7.74.0-4.0.cf
- Do not use stunnel for tests on s390x builds to avoid spurious failures
- Drop support for EOL distributions prior to F-19
  - Always build with Posix threaded DNS lookups rather than using c-ares
  - Always build with libpsl
  - %%{_datadir}/aclocal is always included in the filesystem package
  - Drop workarounds for failing SSH tests on old Fedora releases
  - Use %%license unconditionally

* Thu Dec 10 2020 Paul Howarth <paul@city-fan.org> - 7.74.0-2.0.cf
- Do not rewrite shebangs in test suite to use python3 explicitly

* Wed Dec  9 2020 Paul Howarth <paul@city-fan.org> - 7.74.0-1.0.cf
- Update to 7.74.0
  - hsts: Add experimental support for Strict-Transport-Security
  - CVE-2020-8286: Inferior OCSP verification
  - CVE-2020-8285: FTP wildcard stack overflow
  - CVE-2020-8284: Trusting FTP PASV responses
  - acinclude: Detect manually set minimum macos/ipod version
  - alt-svc: Enable (in the build) by default
  - alt-svc: Minimize variable scope and avoid "DEAD_STORE"
  - asyn: Use 'struct thread_data *' instead of 'void *'
  - checksrc: Warn on empty line before open brace
  - CI/appveyor: Disable test 571 in two cmake builds
  - CI/azure: Improve on flakiness by avoiding libtool wrappers
  - CI/tests: Enable test target on TravisCI for CMake builds
  - CI/travis: Add brotli and zstd to the libssh2 build
  - cirrus: Build with FreeBSD 12.2 in CirrusCI
  - cmake: Call the feature unixsockets without dash
  - cmake: Check for linux/tcp.h
  - cmake: Correctly handle linker flags for static libs
  - cmake: Don't pass -fvisibility=hidden to clang-cl on Windows
  - cmake: Don't use reserved target name 'test'
  - cmake: Make BUILD_TESTING dependent option
  - cmake: Make CURL_ZLIB a tri-state variable
  - cmake: Set the unicode feature in curl-config on Windows
  - cmake: Store IDN2 information in curl_config.h
  - cmake: Use libcurl.rc in all Windows builds
  - configure: Pass -pthread to Libs.private for pkg-config
  - configure: Use pkgconfig to find openSSL when cross-compiling
  - connect: Repair build without ipv6 availability
  - curl.1: Add an "OUTPUT" section at the top of the manpage
  - curl.se: New home
  - curl: Add compatibility for Amiga and GCC 6.5
  - curl: Only warn not fail, if not finding the home dir
  - curl_easy_escape: Limit output string length to 3 * max input
  - Curl_pgrsStartNow: Init speed limit time stamps at start
  - curl_setup: USE_RESOLVE_ON_IPS is for Apple native resolver use
  - curl_url_set.3: Fix typo in the RETURN VALUE section
  - CURLOPT_DNS_USE_GLOBAL_CACHE.3: Fix typo
  - CURLOPT_HSTS.3: Document the file format
  - CURLOPT_NOBODY.3: Fix typo
  - CURLOPT_TCP_NODELAY.3: Fix comment in example code
  - CURLOPT_URL.3: Clarify SCP/SFTP URLs are for uploads as well
  - docs: Document the 8MB input string limit
  - docs: Fix typos and markup in ETag manpage sections
  - docs: Fix various typos in documentation
  - examples/httpput: Remove use of CURLOPT_PUT
  - FAQ: Refreshed
  - file: Avoid duplicated code sequence
  - ftp: Retry getpeername for FTP with TCP_FASTOPEN
  - gnutls: Fix memory leaks (certfields memory wasn't released)
  - header.d: Mention the "Transfer-Encoding: chunked" handling
  - HISTORY: The new domain
  - http3: Fix two build errors, silence warnings
  - http3: Use the master branch of GnuTLS for testing
  - http: Pass correct header size to debug callback for chunked post
  - http_proxy: Use enum with state names for 'keepon'
  - httpput-postfields.c: New example doing PUT with POSTFIELDS
  - infof/failf calls: Fix format specifiers
  - libssh2: Fix build with disabled proxy support
  - libssh2: Fix transport over HTTPS proxy
  - libssh2: Require version 1.0 or later
  - Makefile.m32: Add support for HTTP/3 via ngtcp2+nghttp3
  - Makefile.m32: Add support for UNICODE builds
  - mqttd: fclose test file when done
  - NEW-PROTOCOL: Document what needs to be done to add one
  - ngtcp2: Adapt to recent nghttp3 updates
  - ngtcp2: Advertise h3 ALPN unconditionally
  - ngtcp2: Fix build error due to symbol name change
  - ngtcp2: Use the minimal version of QUIC supported by ngtcp2
  - ntlm: Avoid malloc(0) on zero length user and domain
  - openssl: Acknowledge SRP disabling in configure properly
  - openssl: Free mem_buf in error path
  - openssl: Guard against OOM on context creation
  - openssl: Use OPENSSL_init_ssl() with ≥ 1.1.0
  - os400: Sync libcurl API options
  - packages/OS400: Make the source code-style compliant
  - quiche: Close the connection
  - quiche: Remove 'static' from local buffer
  - range.d: Clarify that curl will not parse multipart responses
  - range.d: Fix typo
  - Revert "multi: implement wait using winsock events"
  - rtsp: Error out on empty Session ID, unified the code
  - rtsp: Fixed Session ID comparison to refuse prefix
  - rtsp: Fixed the RTST Session ID mismatch in test 570
  - runtests: Return error if no tests ran
  - runtests: Revert the mistaken edit of $CURL
  - runtests: Show keywords when no tests ran
  - scripts/completion.pl: Parse all opts
  - socks: Check for DNS entries with the right port number
  - src/tool_filetime: Disable -Wformat on mingw for this file
  - strerror: Use 'const' as the string should never be modified
  - test122[12]: Remove these two tests
  - test506: Make it not run in c-ares builds
  - tests/*server.py: Close log file after each log line
  - tests/server/tftpd.c: Close upload file right after transfer
  - tests/util.py: Fix compatibility with Python 2
  - tests: Add missing global_init/cleanup calls
  - tests: Fix some http/2 tests for older versions of nghttpx
  - tool_debug_cb: Do not assume zero-terminated data
  - tool_help: Make "output" description less confusing
  - tool_operate: --retry for HTTP 408 responses too
  - tool_operate: Bail out properly on errors during parallel transfers
  - tool_operate: Fix compiler warning when --libcurl is disabled
  - tool_writeout: Use off_t getinfo-types instead of doubles
  - travis: Use ninja-build for CMake builds
  - travis: Use valgrind when running tests for debug builds
  - urlapi: Don't accept blank port number field without scheme
  - urlapi: URL encode a '+' in the query part
  - urldata: Remove 'void *protop' and create the union 'p'
  - vquic/ngtcp2.h: Define local_addr as sockaddr_storage
- Upstream URLs moved from curl.haxx.se to curl.se

* Wed Oct 14 2020 Paul Howarth <paul@city-fan.org> - 7.73.0-2.0.cf
- Prevent upstream test 1451 from being skipped

* Wed Oct 14 2020 Paul Howarth <paul@city-fan.org> - 7.73.0-1.0.cf
- Update to 7.73.0
  - curl: Add --output-dir
  - curl: Support XDG_CONFIG_HOME to find .curlrc
  - curl: Update --help with categories
  - curl_easy_option_*: New API for meta-data about easy options
  - CURLE_PROXY: New error code
  - mqtt: Enable by default
  - sftp: Add new quote commands 'atime' and 'mtime'
  - ssh: Add the option CURLKHSTAT_FINE_REPLACE
  - tls: Add CURLOPT_SSL_EC_CURVES and --curves
  - altsvc: Clone setting in curl_easy_duphandle
  - base64: Also build for smtp, pop3 and imap
  - BUGS: Convert document to markdown
  - build-wolfssl: Fix build with Visual Studio 2019
  - buildconf: Invoke 'autoreconf -fi' instead
  - checksrc: Detect // comments on column 0
  - checksrc: Verify do-while and spaces between the braces
  - checksrc: Warn on space after exclamation mark
  - CI/azure: Disable test 571 in the msys2 builds
  - CI/azure: MQTT is now enabled by default
  - CI/azure: No longer ignore results of test 1013
  - CI/tests: Fix invocation of tests for CMake builds
  - CI/travis: Add a CI job with openssl3 (from git master)
  - Clean-ups: Avoid curl_ on local variables
  - CMake: Add option to enable Unicode on Windows
  - CMake: Make HTTP_ONLY also disable MQTT
  - CMake: Remove explicit 'CMAKE_ANSI_CFLAGS'
  - CMake: Remove scary warning
  - cmdline-opts/gen.pl: Generate nicer "See Also" in curl.1
  - configure: Don't say HTTPS-proxy is enabled when disabled
  - configure: Fix pkg-config detecting wolfssl
  - configure: Let --enable-debug set -Wenum-conversion with gcc ≥ 10
  - conn: Check for connection being dead before reuse
  - connect.c: Remove superfluous 'else' in Curl_getconnectinfo
  - curl.1: Add see also no-progress-meter on two spots
  - curl.1: Fix typo invokved → invoked
  - curl: In retry output don't call all problems "transient"
  - curl: Make --libcurl show binary posts correctly
  - curl: Make checkpasswd use dynbuf
  - curl: Make file2memory use dynbuf
  - curl: Make file2string use dynbuf
  - curl: Make glob_match_url use dynbuf
  - curl: Make sure setopt CURLOPT_IPRESOLVE passes on a long
  - curl: Retry delays in parallel mode no longer sleeps blocking
  - curl: Use curlx_dynbuf for realloc when loading config files
  - curl: parallel_transfers: Make sure retry readds the transfer
  - curl_get_line: Build only if cookies or alt-svc are enabled
  - curl_mime_headers.3: Fix the example's use of curl_slist_append
  - Curl_pgrsTime: Return new time to avoid timeout integer overflow
  - Curl_send: Return error when pre_receive_plain can't malloc
  - dist: Add missing CMake Find modules to the distribution
  - docs/LICENSE-MIXING: Remove
  - docs/opts: Fix typos in two manual pages
  - docs/RESOURCES: Remove
  - docs/TheArtOfHttpScripting: Convert to markdown
  - docs: Add description about CI platforms to CONTRIBUTE.md
  - docs: Correct non-existing macros in man pages
  - doh: Add error message for DOH_DNS_NAME_TOO_LONG
  - dynbuf: Make sure Curl_dyn_tail() zero terminates
  - easy_reset: Clear retry counter
  - easygetopt: Pass a valid enum to avoid compiler warning
  - etag: Save and use the full received contents
  - ftp: A 550 response to SIZE returns CURLE_REMOTE_FILE_NOT_FOUND
  - ftp: Avoid risk of reading uninitialized integers
  - ftp: Get rid of the PPSENDF macro
  - ftp: Make a 552 response return CURLE_REMOTE_DISK_FULL
  - ftp: Separate FTPS from FTP over "HTTPS proxy"
  - git: Ignore libtests in 3XXX area
  - github: Use new issue template feature
  - HISTORY: Mention alt-svc added in 2019
  - HTTP/3: Update to OpenSSL_1_1_1g-quic-draft-29
  - http: Consolidate nghttp2_session_mem_recv() call paths
  - http_proxy: Do not count proxy headers in the header bytecount
  - http_proxy: Do not crash with HTTPS_PROXY and NO_PROXY set
  - imap: Make imap_send use dynbuf for the send buffer management
  - imap: Set cselect_bits to CURL_CSELECT_IN initially
  - ldap: Reduce the amount of #ifdefs needed
  - lib/Makefile.am: Bump VERSIONINFO due to new functions
  - lib1560: Verify "redirect" to double-slash leading URL
  - lib583: Fix enum mixup
  - lib: Fix -Wassign-enum warnings
  - lib: Make Curl_gethostname accept a const pointer
  - libssh2: Handle the SSH protocols done over HTTPS proxy
  - libssh2: Pass on the error from ssh_force_knownhost_key_type
  - Makefile.m32: Add ability to override zstd libs
  - man pages: Switch to https://example.com URLs
  - MANUAL: Update examples to resolve without redirects
  - mbedtls: Add missing header when defining MBEDTLS_DEBUG
  - memdebug: Remove 9 year old unused debug function
  - multi: Expand pre-check for socket readiness
  - multi: Handle connection state winsock events
  - multi: Implement wait using winsock events
  - ngtcp2: Adapt to new NGTCP2_PROTO_VER_MAX define
  - ngtcp2: Adapt to the new pkt_info arguments
  - ntlm: Fix condition for curl_ntlm_core usage
  - openssl: Avoid error conditions when importing native CA
  - openssl: Consider ALERT_CERTIFICATE_EXPIRED a failed verification
  - openssl: Fix wincrypt symbols conflict with BoringSSL
  - parsedate: Tune the date to epoch conversion
  - pause: Only trigger a reread if the unpause sticks
  - pingpong: Use a dynbuf for the *_pp_sendf() function
  - READMEs: Convert several to markdown
  - runtests: Add %%repeat[]%% for test files
  - runtests: Allow creating files without newlines
  - runtests: Allow generating a binary sequence from hex
  - runtests: Clear pid variables when failing to start a server
  - runtests: Make cleardir() erase dot files too
  - runtests: Provide curl's version string as %%VERSION for tests
  - schannel: Fix memory leak when using get_cert_location
  - schannel: Return CURLE_PEER_FAILED_VERIFICATION for untrusted root
  - scripts: Improve the "get latest curl release tag" logic
  - sectransp: Make it build with --disable-proxy
  - select.h: Make socket validation macros test for INVALID_SOCKET
  - select: Align poll emulation to return all relevant events
  - select: Fix poll-based check not detecting connect failure
  - select: Reduce duplication of Curl_poll in Curl_socket_check
  - select: Simplify return code handling for poll and select
  - setopt: If the buffer exists, refuse the new BUFFERSIZE
  - setopt: Return CURLE_BAD_FUNCTION_ARGUMENT on bad argument
  - socketpair: Allow CURL_DISABLE_SOCKETPAIR
  - sockfilt: Handle FD_CLOSE winsock event on write socket
  - src: Spell whitespace without whitespace
  - SSLCERTS: Fix English syntax
  - strerror: Honour Unicode API choice on Windows
  - symbian: Drop support
  - telnet.c: Depend on static requirement of WinSock version 2
  - test1541: Remove since it is a known bug
  - test163[12]: Require http to be built-in to run
  - test434: Test -K use in a single line without newline
  - test971: Show test mismatches "inline"
  - tests/data: Fix some mismatched XML tags in test cases
  - tests/FILEFORMAT: Document nonewline support for <file>
  - tests/FILEFORMAT: Document type=shell for <command>
  - tests/server/util.c: Fix support for Windows Unicode builds
  - tests: Remove pipelining tests
  - tls: Fix SRP detection by using the proper #ifdefs
  - tls: Provide the CApath verbose log on its own line
  - tool_setopt: Escape binary data to hex, not octal
  - tool_writeout: Add new writeout variable, %%{num_headers}
  - travis: Add a build using libressl (from git master)
  - url: Use blank credentials when using proxy w/o username and password
  - urlapi: Use more Curl_safefree
  - vtls: Deduplicate client certificates in ssl_config_data
  - win32: Drop support for WinSock version 1, require version 2
  - winbuild: Convert the instruction text to README.md
- Disable test 320 on EL-8 build as it is hanging, plus tests 321 and 322,
  which fail (all related to TLS-SRP)

* Thu Sep 10 2020 Jinoh Kang <aurhb20@protonmail.ch> - 7.72.0-2.0.cf
- Fix multiarch conflicts in libcurl-minimal (#1877671)

* Wed Aug 19 2020 Paul Howarth <paul@city-fan.org> - 7.72.0-1.0.cf
- Update to 7.72.0
  - content_encoding: Add zstd decoding support
  - CURL_PUSH_ERROROUT: Allow the push callback to fail the parent stream
  - CURLINFO_EFFECTIVE_METHOD: Added
  - CVE-2020-8231: libcurl: Wrong connect-only connection
  - appveyor: Collect libcurl.dll variants with prefix or suffix
  - asyn-ares: Correct some bad comments
  - bearssl: Fix build with disabled proxy support
  - buildconf: Avoid array concatenation in die()
  - buildconf: Retire ares buildconf invocation
  - checksrc: Ban gmtime/localtime
  - checksrc: Invoke script with -D to find .checksrc proper
  - CI/azure: Install libssh2 for use with msys2-based builds
  - CI/azure: Unconditionally enable warnings-as-errors with autotools
  - CI/macos: Enable warnings as errors for CMake builds
  - CI/macos: Set minimum macOS version
  - CI/macos: Unconditionally enable warnings-as-errors with autotools
  - CI: Add muse CI analyzer
  - cirrus-ci: Upgrade 11-STABLE to 11.4
  - CMake: Don't complain about missing nroff
  - CMake: Fix test for warning suppressions
  - cmake: Fix Windows XP build
  - configure.ac: Sort features name in summary
  - configure: Allow disabling warnings
  - configure: Clean up wolfssl + pkg-config conflicts when cross-compiling
  - configure: Show zstd "no" in summary when built without it
  - connect: Remove redundant message about connect failure
  - curl-config: Ignore REQUIRE_LIB_DEPS in --libs output
  - curl.1: Add a few missing valid exit codes
  - curl: Add %%{method} to the -w variables
  - curl: Improve the existing file check with -J
  - curl_multi_setopt: Fix compiler warning "result is always false"
  - curl_version_info.3: CURL_VERSION_KERBEROS4 is deprecated
  - CURLINFO_CERTINFO.3: Fix typo
  - CURLOPT_NOBODY.3: Clarify what setting to 0 means
  - docs: Add date of 7.20 to CURLM_CALL_MULTI_PERFORM mentions
  - docs: Add video link to docs/CONTRIBUTE.md
  - docs: Change "web site" to "website"
  - docs: Clarify MAX_SEND/RECV_SPEED functionality
  - docs: Update a few leftover mentions of DarwinSSL
  - doh: Remove redundant cast
  - file2memory: Use a define instead of -1 unsigned value
  - ftp: Don't do ssl_shutdown instead of ssl_close
  - ftpserver: Don't verify SMTP MAIL FROM names
  - getinfo: Reset retry-after value in initinfo
  - gnutls: Repair the build with 'CURL_DISABLE_PROXY'
  - gtls: Survive not being able to get name/issuer
  - h2: Repair trailer handling
  - http2: Close the http2 connection when no more requests may be sent
  - http2: Fix nghttp2_strerror → nghttp2_http2_strerror in debug messages
  - libssh2: s/ssherr/sftperr/
  - libtest/Makefile.am: Add -no-undefined for libstubgss for Cygwin
  - md(4|5): Don't use deprecated macOS functions
  - mprintf: Fix dollar string handling
  - mprintf: Fix stack overflows
  - multi: Condition 'extrawait' is always true
  - multi: Remove 10-year old commented-out code
  - multi: Remove two checks always true
  - multi: Update comment to say easyp list is linear
  - multi_remove_handle: Close unused connect-only connections
  - ngtcp2: Adapt to error code rename
  - ngtcp2: Adjust to recent sockaddr updates
  - ngtcp2: Update to modified qlog callback prototype
  - nss: Fix build with disabled proxy support
  - ntlm: free target_info before (re-)malloc
  - openssl: Fix build with LibreSSL < 2.9.1
  - page-header: Provide protocol details in the curl.1 man page
  - quiche: Handle calling disconnect twice
  - runtests.pl: Treat LibreSSL and BoringSSL as OpenSSL
  - runtests: Move the gnutls-serv tests to a dynamic port
  - runtests: Move the smbserver to use a dynamic port number
  - runtests: Move the TELNET server to a dynamic port
  - runtests: Run the DICT server on a random port number
  - runtests: Run the http2 tests on a random port number
  - runtests: Support dynamically base64 encoded sections in tests
  - setopt: Unset NOBODY switches to GET if still HEAD
  - smtp_parse_address: Handle blank input string properly
  - socks: Use size_t for size variable
  - strdup: Remove the odd strlen check
  - test1119: Verify stdout in the test
  - test1139: Make it display the difference on test failures
  - test1140: Compare stdout
  - test1908: Treat file as text
  - tests/FILEFORMAT.md: Mention %%HTTP2PORT
  - tests/sshserver.pl: Fix compatibility with OpenSSH for Windows
  - TLS naming: Fix more Winssl and Darwinssl leftovers
  - tls-max.d: This option is only for TLS-using connections
  - tlsv1.3.d. Only for TLS-using connections
  - tool_doswin: Simplify Windows version detection
  - tool_getparam: Make --krb option work again
  - TrackMemory tests: Ignore realloc and free in getenv.c
  - transfer: Fix data_pending for builds with both h2 and h3 enabled
  - transfer: Fix memory-leak with CURLOPT_CURLU in a duped handle
  - transfer: Move retrycount from connect struct to easy handle
  - travis/script.sh: Fix use of '-n' with unquoted envvar
  - travis: Add ppc64le and s390x builds
  - travis: Update quiche builds for new boringssl layout
  - url: Fix CURLU and location following
  - url: Silence MSVC warning
  - util: Silence conversion warnings
  - win32: Add Curl_verify_windows_version() to curlx
  - WIN32: Stop forcing narrow-character API
  - Windows: Add unicode to feature list
  - Windows: Disable Unix Sockets for old mingw

* Thu Aug  6 2020 Paul Howarth <paul@city-fan.org> - 7.71.1-5.0.cf
- setopt: Unset NOBODY switches to GET if still HEAD

* Mon Jul 27 2020 Paul Howarth <paul@city-fan.org> - 7.71.1-4.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Thu Jul 23 2020 Paul Howarth <paul@city-fan.org> - 7.71.1-3.0.cf
- Modernize spec using %%{make_build} and %%{make_install}

* Fri Jul  3 2020 Paul Howarth <paul@city-fan.org> - 7.71.1-2.0.cf
- curl: Make the --krb option work again (#1833193)

* Wed Jul  1 2020 Paul Howarth <paul@city-fan.org> - 7.71.1-1.0.cf
- Update to 7.71.1
  - cirrus-ci: Disable FreeBSD 13 (again)
  - Curl_inet_ntop: Always check the return code
  - CURLOPT_READFUNCTION.3: Provide the upload data size up front
  - DYNBUF.md: Fix a typo: trail => tail
  - escape: Make the URL decode able to reject only %%00-bytes
  - escape: Zero length input should return a zero length output
  - examples/multithread.c: Call curl_global_cleanup()
  - http2: Set the correct URL in pushed transfers
  - http: Fix proxy auth with blank password
  - mbedtls: Fix build with disabled proxy support
  - ngtcp2: Sync with current master
  - openssl: Fix compilation on Windows when ngtcp2 is enabled
  - Revert "multi: implement wait using winsock events"
  - sendf: Improve the message on client write errors
  - terminology: Call them null-terminated strings
  - tool_cb_hdr: Fix etag warning output and return code
  - url: Allow user + password to contain "control codes" for HTTP(S)
  - vtls: Compare cert blob when finding a connection to reuse
- Run the test suite on Fedora 16 builds too, since builds on Fedora 13..15
  now fail the test suite (possibly a c-ares memory clean-up issue?)

* Wed Jun 24 2020 Paul Howarth <paul@city-fan.org> - 7.71.0-1.0.cf
- Update to 7.71.0
  - CURLOPT_SSL_OPTIONS: Optional use of Windows' CA store (with openssl)
  - setopt: Add CURLOPT_PROXY_ISSUERCERT(_BLOB) for coherency
  - setopt: Support certificate options in memory with struct curl_blob
  - tool: Add option --retry-all-errors to retry on any error
  - CVE-2020-8177: curl overwrite local file with -J
  - CVE-2020-8169: Partial password leak over DNS on HTTP redirect
  - *_sspi: Fix bad uses of CURLE_NOT_BUILT_IN
  - all: Fix codespell errors
  - altsvc: Bump to h3-29
  - altsvc: Fix 'dsthost' may be used uninitialized in this function
  - altsvc: Fix parser for lines ending with CRLF
  - altsvc: Remove the num field from the altsvc struct
  - appveyor: Add non-debug plain autotools-based build
  - appveyor: Disable flaky test 1501 and ignore broken 1056
  - appveyor: Disable test 1139 instead of ignoring it
  - asyn-*: Remove support for never-used NULL entry pointers
  - azure: Use matrix strategy to avoid configuration redundancy
  - build: Disable more code/data when built without proxy support
  - buildconf: Remove -print from the find command that removes files
  - checksrc: Enhance the ASTERISKSPACE and update code accordingly
  - CI/macos: Fix 'is already installed' errors by using bundle
  - cirrus: Disable SFTP and SCP tests
  - CMake: Add ENABLE_ALT_SVC option
  - CMake: Add HTTP/3 support (ngtcp2+nghttp3, quiche)
  - CMake: Add libssh build support
  - CMake: Do not build test programs by default
  - CMake: Fix runtests.pl with CMake, add new test targets
  - CMake: Ignore INTERFACE_LIBRARY targets for pkg-config file
  - CMake: Rebuild Makefile.inc.cmake when Makefile.inc changes
  - CODE_REVIEW.md: how to do code reviews in curl
  - configure: Fix pthread check with static boringssl
  - configure: For wolfSSL, check for the DES func needed for NTLM
  - configure: Only strip first -L from LDFLAGS
  - configure: Repair the check if argv can be written to
  - configure: The wolfssh backend does not provide SCP
  - connect: Improve happy eyeballs handling
  - connect: Make happy eyeballs work for QUIC (again)
  - curl.1: Quote globbed URLs
  - curl: Remove -J "informational" written on stdout
  - Curl_addrinfo: Use one malloc instead of three
  - CURLINFO_ACTIVESOCKET.3: Clarify the description
  - doc: Add missing closing parenthesis in CURLINFO_SSL_VERIFYRESULT.3
  - doc: Rename VERSIONS to VERSIONS.md as it already has Markdown syntax
  - docs/HTTP3: Add qlog to the quiche build instruction
  - docs/options-in-versions: Which version added each cmdline option
  - docs: Unify protocol lists
  - dynbuf: Introduce internal generic dynamic buffer functions
  - easy: Fix dangling pointer on easy_perform fail
  - examples/ephiperfifo: Turn off interval when setting timerfd
  - examples/http2-down/upload: Add error checks
  - examples: Remove asiohiper.cpp
  - FILEFORMAT: Add more features that tests can depend on
  - FILEFORMAT: Describe verify/stderr
  - ftp: Make domore_getsock() return the secondary socket properly
  - ftp: Mark return-ignoring calls to Curl_GetFTPResponse with (void)
  - ftp: Shut down the secondary connection properly when SSL is used
  - GnuTLS: Backend support for CURLINFO_SSL_VERIFYRESULT
  - hostip: Make Curl_printable_address not return anything
  - hostip: On macOS avoid DoH when given a numerical IP address
  - http2: Keep trying to send pending frames after req.upload_done
  - http2: Simplify and clean up trailer handling
  - HTTP3.md: Clarify cargo build directory
  - http: Move header storage to Curl_easy from connectdata
  - libcurl.pc: Merge Libs.private into Libs for static-only builds
  - libssh2: Improved error output for wrong quote syntax
  - libssh2: Keep sftp errors as 'unsigned long'
  - libssh2: Set the expected total size in SCP upload init
  - libtest/cmake: Remove commented code
  - list-only.d: This option existed already in 4.0
  - manpage: Add three missing environment variables
  - multi: Add defensive check on data->multi->num_alive
  - multi: Implement wait using winsock events
  - ngtcp2: Clean up memory when failing to connect
  - ngtcp2: Fix build with current ngtcp2 master implementing draft 28
  - ngtcp2: Fix happy eyeballs quic connect crash
  - ngtcp2: Introduce qlog support
  - ngtcp2: Never call fprintf() in lib code in release version
  - ngtcp2: Update with recent API changes
  - ntlm: Enable NTLM support with wolfSSL
  - OpenSSL: Have CURLOPT_CRLFILE imply CURLSSLOPT_NO_PARTIALCHAIN
  - openssl: Set FLAG_TRUSTED_FIRST unconditionally
  - projects: Add crypt32.lib to dependencies for all OpenSSL configs
  - quiche: Clean up memory properly when failing to connect
  - quiche: Enable qlog output
  - quiche: Update SSLKEYLOGFILE support
  - Revert "buildconf: use find -execdir"
  - Revert "ssh: ignore timeouts during disconnect"
  - runtests: Remove sleep calls
  - runtests: Show elapsed test time with higher precision (ms)
  - select: Always use Sleep in Curl_wait_ms on Win32
  - select: Fix overflow protection in Curl_socket_check
  - sendf: Make failf() use the mvsnprintf() return code
  - server/sws: Fix asan warning on use of uninitialized variable
  - server/util: Fix logmsg format using curl_off_t argument
  - sha256: Fixed potentially uninitialized variable
  - share: Don't set the share flag if something fails
  - sockfilt: Make select_ws stop waiting on exit signal event
  - socks: Detect connection close during handshake
  - socks: Fix expected length of SOCKS5 reply
  - socks: Remove unreachable breaks in socks.c and mime.c
  - source clean-up: Remove all custom typedef structs
  - test1167: Fixes in badsymbols.pl
  - test1177: Look for curl.h in source directory
  - test1238: Avoid tftpd being busy for tests shortly following
  - test613.pl: Make tests 613 and 614 work with OpenSSH for Windows
  - test75: Remove precheck test
  - tests: Add https-proxy support to the test suite
  - tests: Add support for SSH server variant specific transfer paths
  - tests: Add two simple tests for --login-options
  - tests: Make test 1248 + 1249 use %%NOLISTENPORT
  - tests: Pick a random port number for SSH
  - tests: Run stunnel for HTTPS and FTPS on dynamic ports
  - timeouts: Change millisecond timeouts to timediff_t from time_t
  - timeouts: Move ms timeouts to timediff_t from int and long
  - tool: Fix up a few --help descriptions
  - tool: Support UTF-16 command line on Windows
  - tool_cfgable: free login_options at exit
  - tool_getparam: Fix memory leak in parse_args
  - tool_operate: Fixed potentially uninitialized variables
  - tool_paramhlp: Fixed potentially uninitialized strtol() variable
  - transfer: Close connection after excess data has been read
  - travis: Add "qlog" as feature in the quiche build
  - travis: Add ngtcp2 and quiche tests for CMake
  - travis: Upgrade to bionic, clang-9, improve readability
  - typecheck-gcc.h: CURLINFO_PRIVATE does not need a 'char *'
  - unit1604.c: Fix implicit conv from 'SANITIZEcode' to 'CURLcode'
  - url: Accept "any length" credentials for proxy auth
  - url: alloc the download buffer at transfer start
  - url: Reject too long input when parsing credentials
  - url: Sort the protocol schemes in rough popularity order
  - urlapi: Accept :: as a valid IPv6 address
  - urldata: Leave the HTTP method untouched in the set.* struct
  - urlglob: Treat literal IPv6 addresses with zone IDs as a host name
  - user-agent.d: Spell out what happens given a blank argument
  - vauth/cleartext: Fix theoretical integer overflow
  - version.d: Expanded and alpha-sorted
  - vtls: Extract and simplify key log file handling from OpenSSL
  - wolfssl: Add SSLKEYLOGFILE support
  - wording: Avoid blacklist/whitelist stereotypes
  - write-out.d: Added "response_code"

* Wed Apr 29 2020 Paul Howarth <paul@city-fan.org> - 7.70.0-1.0.cf
- Update to 7.70.0
  - curl: Add --ssl-revoke-best-effort to allow a "best effort" revocation check
  - mqtt: Add new experimental protocol
  - schannel: Add "best effort" revocation check option:
    CURLSSLOPT_REVOKE_BEST_EFFORT
  - writeout: Support to generate JSON output with '%%{json}'
  - appveyor: Add Unicode winbuild jobs
  - appveyor: Completely disable tests that fail to timeout early
  - appveyor: Show failed tests in log even if test is ignored
  - appveyor: Sort builds by type and add two new variants
  - appveyor: Turn disabled tests into ignored result tests
  - appveyor: Use random test server ports based upon APPVEYOR_API_URL
  - build: Fixed build for systems with select() in unistd.h
  - buildconf: Avoid using tempfile when removing files
  - checksrc: Warn on obvious conditional blocks on the same line as if()
  - CI-fuzz: Increase fuzz time to 40 minutes
  - ci/tests: Fix Azure Pipelines not running Windows containers
  - CI: Add build with ngtcp2 + gnutls on Travis CI
  - CI: Bring GitHub Actions fuzzing job in line with macOS jobs
  - CI: Migrate macOS jobs from Azure and Travis CI to GitHub Actions
  - CI: Remove default Ubuntu build from GitHub Actions
  - cirrus: No longer ignore test 504, which is working again
  - cirrus: Re-enable the FreeBSD 13 CI builds
  - clean-up: Insert newline after if() conditions
  - cmake: Add aliases so exported target names are available in tree
  - cmake: Add CMAKE_MSVC_RUNTIME_LIBRARY
  - cmake: Add support for building with wolfSSL
  - cmake: Avoid MSVC C4273 warnings in send/recv checks
  - cmdline: Fix handling of OperationConfig linked list (--next)
  - compressed.d: Stress that the headers are not modified
  - config: Remove all defines of HAVE_DES_H
  - configure: Convert -I to -isystem as a last step
  - configure: Document 'compiler_num' for gcc
  - configure: Don't check for Security.framework when cross-compiling
  - configure: Fix -pedantic-errors for GCC 5 and later
  - configure: Remove use of -vec-report0 from CFLAGS with icc
  - connect: Happy eyeballs clean-up
  - connect: Store connection info for QUIC connections
  - copyright: Fix out-of-date copyright ranges and missing headers
  - curl-functions.m4: Remove inappropriate AC_REQUIRE
  - curl.h: Remove CURL_VERSION_ESNI, never supported nor documented
  - curl.h: Update comment typo
  - curl: Allow both --etag-compare and --etag-save with same file name
  - curl_setup: Define _WIN32_WINNT_[OS] symbols
  - CURLINFO_CONDITION_UNMET: Return true for 304 http status code
  - CURLINFO_NUM_CONNECTS: Improve accuracy
  - CURLOPT_WRITEFUNCTION.3: Add inline example and new see-also
  - dist: Add mail-rcpt-allowfails.d to the tarball
  - docs/make: Generate curl.1 from listed files only
  - docs: Add warnings about FILE: URLs on Windows
  - easy: Fix curl_easy_duphandle for builds missing IPv6 that use c-ares
  - examples/sessioninfo.c: Add include to fix compiler warning
  - GitHub Actions: Run when pushed to master or */ci + PRs
  - gnutls: Bump lowest supported version to 3.1.10
  - gnutls: Don't skip really long certificate fields
  - gnutls: Ensure TLS 1.3 when SRP isn't requested
  - gopher: Check remaining time left during write busy loop
  - gskit: Use our internal select wrapper for portability
  - http2: Fix erroneous debug message that h2 connection closed
  - http: Don't consider upload done if the request isn't completely sent off
  - http: Free memory when Alt-Used header creation fails due to OOM
  - lib/mk-ca-bundle: Skip empty certs
  - lib670: Use the same Win32 API check as all other lib tests
  - lib: Fix typos in comments and error messages
  - lib: Never define CURL_CA_BUNDLE with a getenv
  - libcurl-multi.3: Added missing full stop
  - libssh: Avoid options override by configuration files
  - libssh: Use new ECDSA key types to check known hosts
  - mailmap: Fix up a few author names/fields
  - Makefile.m32: Improve windres parameter compatibility
  - Makefile: Run the cd commands in a subshell
  - memdebug: Don't log free(NULL)
  - mime: Properly check Content-Type even if it has parameters
  - multi-ssl: Reset the SSL backend on 'Curl_global_cleanup()'
  - multi: Improve parameter check for curl_multi_remove_handle
  - nghttp2: 1.12.0 required
  - ngtcp2: Update to git master for the key installation API change
  - nss: Check for PK11_CreateDigestContext() returning NULL
  - openssl: Adapt to functions marked as deprecated since version 3
  - OS400: Update strings for ccsid-ifier (fixes the build)
  - output.d: Quote the URL when globbing
  - packages: Add OS400/chkstrings.c to the dist
  - RELEASE-PROCEDURE.md: Run the copyright.pl script!
  - Revert "file: on Windows, refuse paths that start with \\"
  - runtests: Always put test number in servercmd file
  - runtests: Provide nicer error message when protocol "dump" file is empty
  - schannel: Fix blocking timeout logic
  - schannel: support .P12 or .PFX client certificates
  - scripts/release-notes.pl: Add helper script for RELEASE-NOTES maintenance
  - select: Make Curl_socket_check take timediff_t timeout
  - select: Move duplicate select preparation code into Curl_select
  - select: Remove typecast from SOCKET_WRITABLE/READABLE macros
  - server/getpart: Make the "XML-parser" stricter
  - server/resolve: Remove AI_CANONNAME to make macos tell the truth
  - smtp: Set auth correctly
  - sockfilt: Add logmsg output to select_ws_wait_thread on Windows
  - sockfilt: Fix broken pipe on Windows to be ready in select_ws
  - sockfilt: Fix handling of ready closed sockets on Windows
  - sockfilt: Fix race-condition of waiting threads and event handling
  - socks: Fix blocking timeout logic
  - src: Remove C99 constructs to ensure C89 compliance
  - SSLCERTS.md: Fix example code for setting CA cert file
  - test1148: Tolerate progress updates better (again)
  - test1154: Set a proper name
  - test1177: Verify that all the CURL_VERSION_ bits are documented
  - test1566: Verify --etag-compare that gets a 304 back
  - test1908: Avoid using fixed port number in test data
  - test2043: Use revoked.badssl.com instead of revoked.grc.com
  - test2100: Fix static port instead of dynamic value being used
  - tests/data: Fix some XML formatting issues in test cases
  - tests/FILEFORMAT: Converted to markdown and extended
  - tests/server/util.c: Use curl_off_t instead of long for pid
  - tests: Add %%NOLISTENPORT and use it
  - tests: Add Windows compatible pidwait like pidkill and pidterm
  - tests: Fix conflict between Cygwin/msys and Windows PIDs
  - tests: Introduce preprocessed test cases
  - tests: Make Python-based servers compatible with Python 2 and 3
  - tests: Make runtests check that disabled tests exists
  - tests: Move pingpong server to dynamic listening port
  - tests: Remove python_dependencies for smbserver from our tree
  - tests: Run the RTSP test server on a dynamic port number
  - tests: Run the SOCKS test server on a dynamic port number
  - tests: Run the sws server on "any port"
  - tests: Run the TFTP test server on a dynamic port number
  - tests: Use Cygwin/msys PIDs for stunnel and sshd on Windows
  - tls: Remove the BACKEND define kludge from most backends
  - tool: Do not declare functions with Curl_ prefix
  - tool_operate: Fix add_parallel_transfers when more are in queue
  - transfer: Cap retries of "dead connections" to 5
  - transfer: Switch PUT to GET/HEAD on 303 redirect
  - travis: Bump the wolfssl CI build to use 4.4.0
  - travis: Update the ngtcp2 build to use the latest OpenSSL patch
  - url: Allow non-HTTPS altsvc-matching for debug builds
  - version: Add 'cainfo' and 'capath' to version info struct
  - version: Increase buffer space for ssl version output
  - version: Skip idn2_check_version() check and add precaution
  - vquic: Add support for GnuTLS backend of ngtcp2
  - vtls: Fix ssl_config memory-leak on out-of-memory
  - warnless: Remove code block for icc that didn't work
  - Windows: Enable UnixSockets with all build toolchains
  - Windows: Suppress UI in all CryptAcquireContext() calls
- Add patch to fix test suite when run from separate build directory
  (https://github.com/curl/curl/pull/5310)

* Mon Apr 20 2020 Paul Howarth <paul@city-fan.org> - 7.69.1-3.0.cf
- SSH: Use new ECDSA key types to check known hosts (#1824926)

* Fri Apr 17 2020 Paul Howarth <paul@city-fan.org> - 7.69.1-2.0.cf
- Prevent discarding of -g when compiling with clang

* Wed Mar 11 2020 Paul Howarth <paul@city-fan.org> - 7.69.1-1.1.cf
- Add new tests 664, 665, and 1459 to list of tests to skip for builds on
  Fedora 12-15

* Wed Mar 11 2020 Paul Howarth <paul@city-fan.org> - 7.69.1-1.0.cf
- Update to 7.69.1
  - ares: Store dns parameters for duphandle
  - cirrus-ci: Disable the FreeBSD 13 builds
  - curl_share_setopt.3: Note sharing cookies doesn't enable the engine
  - lib1564: Reduce number of mid-wait wakeup calls
  - libssh: Fix matching user-specified MD5 hex key
  - MANUAL: Update a dict-using command line
  - mime: Do not perform more than one read in a row
  - mime: Fix the binary encoder to handle large data properly
  - mime: Latch last read callback status
  - multi: Skip EINTR check on wakeup socket if it was closed
  - pause: Bail out on bad input
  - pause: Force a connection recheck after unpausing (take 2)
  - pause: Return early for calls that don't change pause state
  - runtests.1: Rephrase how to specify what tests to run
  - runtests: Fix missing use of exe_ext helper function
  - seek: Fix fall back for missing ftruncate on Windows
  - sftp: Fix segfault regression introduced by #4747 in 7.69.0
  - sha256: Added SecureTransport implementation
  - sha256: Added WinCrypt implementation
  - socks4: Fix host resolve regression
  - socks5: Host name resolv regression fix
  - tests/server: Fix missing use of exe_ext helper function
  - tests: Fix static ip:port instead of dynamic values being used
  - tests: Make sleeping portable by avoiding select
  - unit1612: Fix the inclusion and compilation of the HMAC unit test
  - urldata: Remove the 'stream_was_rewound' connectdata struct member
  - version: Make curl_version* thread-safe without using global context

* Mon Mar  9 2020 Paul Howarth <paul@city-fan.org> - 7.69.0-2.0.cf
- Make Flatpak work again (#1810989)

* Wed Mar  4 2020 Paul Howarth <paul@city-fan.org> - 7.69.0-1.0.cf
- Update to 7.69.0
  - polarssl: Removed
  - smtp: Add CURLOPT_MAIL_RCPT_ALLLOWFAILS and --mail-rcpt-allowfails
  - wolfSSH: New SSH backend
  - altsvc: Improved header parser
  - altsvc: Keep a copy of the file name to survive handle reset
  - altsvc: Make saving the cache an atomic operation
  - altsvc: Use h3-27
  - azure: Disable brotli on the macos debug-builds
  - build: Remove all HAVE_OPENSSL_ENGINE_H defines
  - checksrc.bat: Fix not being able to run script from the main curl dir
  - cleanup: Fix several comment typos
  - cleanup: Fix typos and wording in docs and comments
  - cmake: Add support for CMAKE_LTO option
  - cmake: Clean up and improve build procedures
  - cmake: Enable SMB for Windows builds
  - cmake: Improve libssh2 check on Windows
  - cmake: Show HTTPS-proxy in the features output
  - cmake: Support specifying the target Windows version
  - cmake: Use check_symbol_exists also for inet_pton
  - configure.ac: Fix comments about --with-quiche
  - configure: Disable metalink if mbedTLS is specified
  - configure: Disable metalink support for incompatible SSL/TLS
  - conn: Do not reuse connection if SOCKS proxy credentials differ
  - conncache: Removed unused Curl_conncache_bundle_size()
  - connect: Remove some spurious infof() calls
  - connection reuse: Respect the max_concurrent_streams limits
  - contributors: Also include people who contributed to curl-www
  - contrithanks: Use the most recent tag by default
  - cookie: Check __Secure- and __Host- case sensitively
  - cookies: Make saving atomic with a rename
  - create-dirs.d: Mention the mode
  - curl: Avoid using strlen for testing if a string is empty
  - curl: Error on --alt-svc use without support
  - curl: Let -D merge headers in one file again
  - curl: Make #0 not output the full URL
  - curl: Make the -# spaceship bar not wrap the line
  - curl: Remove 'config' field from OutStruct
  - curl: progressbarinit: Ignore column width from terminals < 20
  - curl_escape.3: Add a link to curl_free
  - curl_getenv.3: Fix the memory handling description
  - curl_global_init: Assume the EINTR bit by default
  - curl_global_init: Move the IPv6 works status bool to multi handle
  - CURLINFO_COOKIELIST.3: Fix example
  - CURLOPT_ALTSVC_CTRL.3: Fix the DEFAULT wording
  - CURLOPT_PROXY_SSL_OPTIONS.3: Sync with CURLOPT_SSL_OPTIONS.3
  - CURLOPT_REDIR_PROTOCOLS.3: Update the DEFAULT section
  - data.d: Remove "Multiple files can also be specified"
  - digest: Do not quote algorithm in HTTP authorisation
  - docs/HTTP3: Add --enable-alt-svc to curl's configure
  - docs/HTTP3: Update the OpenSSL branch to use for ngtcp2
  - docs: Fix typo on CURLINFO_RETRY_AFTER
  - easy: Remove dead code
  - form.d: Fix two minor typos
  - ftp: Convert 'sock_accepted' to a plain boolean
  - ftp: Remove superfluous checking for crlf in user or pwd
  - ftp: Shrink temp buffers used for PORT
  - github action: Add CIFuzz
  - github: Instructions to post "uname -a" on Unix systems in issues
  - GnuTLS: Always send client cert
  - gtls: Fixed compilation when using GnuTLS < 3.5.0
  - hostip: Move code to resolve IP address literals to 'Curl_resolv'
  - HTTP-COOKIES: Describe the cookie file format
  - HTTP-COOKIES: Mention that a trailing newline is required
  - http2: Make pausing/unpausing set/clear local stream window
  - http2: Now requires nghttp2 ≥ 1.12.0
  - http: Added 417 response treatment
  - http: Increase EXPECT_100_THRESHOLD to 1Mb
  - http: Mark POSTs with no body as "upload done" from the start
  - http: Move "oauth_bearer" from connectdata to Curl_easy
  - include: Remove non-curl prefixed defines
  - KNOWN_BUGS: Multiple methods in a single WWW-Authenticate: header
  - libssh2: Add support for forcing a hostkey type
  - libssh2: Fix variable type
  - libssh: Improve known hosts handling
  - llist: Removed unused Curl_llist_move()
  - location.d: The method change is from POST to GET only
  - md4: Fixed compilation issues when using GNU TLS gcrypt
  - md4: Use init/update/final functions in Secure Transport
  - md5: Added implementation for mbedTLS
  - mk-ca-bundle: Add support for CKA_NSS_SERVER_DISTRUST_AFTER
  - multi: Change curl_multi_wait/poll to error on negative timeout
  - multi: Fix outdated comment
  - multi: If Curl_readwrite sets 'comeback' use expire, not loop
  - multi_done: If multiplexed, make conn->data point to another transfer
  - multi_wait: Stop loop when sread() returns zero
  - ngtcp2: Add error code for QUIC connection errors
  - ngtcp2: Fixed to only use AF_INET6 when ENABLE_IPV6
  - ngtcp2: Update to git master and its draft-25 support
  - ntlm: Move the winbind data into the NTLM data structure
  - ntlm: Pass the Curl_easy structure to the private winbind functions
  - ntlm: Removed the dependency on the TLS libraries when using MD5
  - ntlm_wb: Use Curl_socketpair() for greater portability
  - oauth2-bearer.d: Works for HTTP too
  - openssl: Make CURLINFO_CERTINFO not truncate x509v3 fields
  - openssl: Remove redundant assignment
  - os400: Fixed the build
  - pause: Force-drain the transfer on unpause
  - quiche: Update to draft-25
  - README: Mention that the docs are in docs/
  - RELEASE-PROCEDURE: Feature window is closed post-release a few days
  - runtests: Make random seed fixed for a month
  - runtests: Restore the command log
  - schannel: Make CURLOPT_CAINFO work better on Windows 7
  - schannel_verify: Fix alt names manual verify for UNICODE builds
  - sha256: Use crypto implementations when available
  - singleuse.pl: Support new API functions, fix curl_dbg_ handling
  - smtp: Support the SMTPUTF8 extension
  - smtp: Support UTF-8 based host names in MAIL FROM
  - SOCKS: Make the connect phase non-blocking
  - strcase: Turn Curl_raw_tolower into static
  - strerror: Increase STRERROR_LEN 128 → 256
  - test1323: Added missing 'unit test' feature requirement
  - tests: Add a unit test for MD4 digest generation
  - tests: Add a unit test for SHA256 digest generation
  - tests: Add a unit test for the HMAC hash generation
  - tests: Deduce the tool name from the test case for unit tests
  - tests: Fix Python 3 compatibility of smbserver.py
  - tool_dirhie: Allow directory traversal during creation
  - tool_homedir: Change GetEnv() to use libcurl's curl_getenv()
  - tool_util: Improve Windows version of tvnow()
  - travis: Update non-OpenSSL Linux jobs to Bionic
  - url: Include the failure reason when curl_win32_idn_to_ascii() fails
  - urlapi: Guess scheme properly with credentials given
  - urldata: Do string enums without #ifdefs for build scripts
  - vtls: Refactor Curl_multissl_version to make the code clearer
  - win32: USE_WIN32_CRYPTO to enable Win32 based MD4, MD5 and SHA256
- Drop http2 support for EL-6, F-23 and F-24 (libnghttp2 too old)

* Tue Jan 28 2020 Paul Howarth <paul@city-fan.org> - 7.68.0-2.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Wed Jan  8 2020 Paul Howarth <paul@city-fan.org> - 7.68.0-1.0.cf
- Update to 7.68.0
  - TLS: Add BearSSL vtls implementation
  - XFERINFOFUNCTION: Support CURL_PROGRESSFUNC_CONTINUE
  - curl: Add --etag-compare and --etag-save
  - curl: Add --parallel-immediate
  - multi: Add curl_multi_wakeup()
  - openssl: CURLSSLOPT_NO_PARTIALCHAIN can disable partial cert chains
  - CVE-2019-15601: file: on Windows, refuse paths that start with \\
  - Azure Pipelines: Add several builds
  - CMake: Add support for building with the NSS vtls backend
  - CURL-DISABLE: Initial docs for the CURL_DISABLE_* defines
  - CURLOPT_HEADERFUNCTION.3: Document that size is always 1
  - CURLOPT_QUOTE.3: Fix typos
  - CURLOPT_READFUNCTION.3: Fix the example
  - CURLOPT_URL.3: "curl supports SMB version 1 (only)"
  - CURLOPT_VERBOSE.3: See also ERRORBUFFER
  - HISTORY: Added cmake, HTTP/3 and parallel downloads with curl
  - HISTORY: The SMB(S) support landed in 2014
  - INSTALL.md: Provide Android build instructions
  - KNOWN_BUGS: Connection information when using TCP Fast Open
  - KNOWN_BUGS: LDAP on Windows doesn't work correctly
  - KNOWN_BUGS: TLS session cache doesn't work with TFO
  - OPENSOCKETFUNCTION.3: Correct the purpose description
  - TrackMemory tests: Always remove CR before LF
  - altsvc: Bump to h3-24
  - altsvc: Make the save function ignore NULL filenames
  - build: Disable Visual Studio warning "conditional expression is constant"
  - build: Fix for CURL_DISABLE_DOH
  - checksrc.bat: Add a check for vquic and vssh directories
  - checksrc: Repair the copyrightyear check
  - cirrus-ci: Enable clang sanitizers on freebsd 13
  - cirrus: Drop the FreeBSD 10.4 build
  - config-win32: cpu-machine-OS for Windows on ARM
  - configure: Avoid unportable '==' test(1) operator
  - configure: Enable IPv6 support without 'getaddrinfo'
  - configure: Fix typo in help text
  - conncache: CONNECT_ONLY connections assumed always in-use
  - conncache: Fix multi-thread use of shared connection cache
  - copyrights: Fix copyright year range
  - create_conn: Prefer multiplexing to using new connections
  - curl -w: Handle a blank input file correctly
  - curl.h: Add two missing defines for "pre ISO C" compilers
  - curl/parseconfig: Fix mem-leak
  - curl/parseconfig: Use curl_free() to free memory allocated by libcurl
  - curl: Clean up multi handle on failure
  - curl: Fix --upload-file . hangs if delay in STDIN
  - curl: Fix -T globbing
  - curl: Improved clean-up in upload error path
  - curl: Make a few char pointers point to const char instead
  - curl: Properly free mimepost data
  - curl: Show better error message when no homedir is found
  - curl: Show error for --http3 if libcurl lacks support
  - curl_setup_once: Consistently use WHILE_FALSE in macros
  - define: Remove HAVE_ENGINE_LOAD_BUILTIN_ENGINES, not used anymore
  - docs: Change 'experiemental' to 'experimental'
  - docs: TLS SRP doesn't work with TLS 1.3
  - docs: Fix several typos
  - docs: Mention CURL_MAX_INPUT_LENGTH restrictions
  - doh: Improved both encoding and decoding
  - doh: Make it behave when built without proxy support
  - examples/postinmemory.c: Always call curl_global_cleanup
  - examples/url2file.c: Corrected erroneous comment
  - examples: Add multi-poll.c
  - global_init: Undo the "initialized" bump in case of failure
  - hostip: Suppress compiler warning
  - http_ntlm: Remove duplicate NSS initialization
  - lib: Move lib/ssh.h → lib/vssh/ssh.h
  - lib: Fix compiler warnings with 'CURL_DISABLE_VERBOSE_STRINGS'
  - lib: Fix warnings found when porting to NuttX
  - lib: Remove ASSIGNWITHINCONDITION exceptions, use our code style
  - lib: Remove erroneous +x file permission on some c files
  - libssh2: Add support for ECDSA and ed25519 knownhost keys
  - multi.h: Remove INITIAL_MAX_CONCURRENT_STREAMS from public header
  - multi: Free sockhash on OOM
  - multi_poll: Avoid busy-loop when called without easy handles attached
  - ngtcp2: Support the latest update key callback type
  - ngtcp2: Fix thread-safety bug in error-handling
  - ngtcp2: Free used resources on disconnect
  - ngtcp2: Handle key updates as ngtcp2 master branch tells us
  - ngtcp2: Increase QUIC window size when data is consumed
  - ngtcp2: Use overflow buffer for extra HTTP/3 data
  - ntlm: USE_WIN32_CRYPTO check removed to get USE_NTLM2SESSION set
  - ntlm_wb: Fix double-free in OOM
  - openssl: Revert to less sensitivity for SYSCALL errors
  - openssl: Improve error message for SYSCALL during connect
  - openssl: Prevent recursive function calls from ctx callbacks
  - openssl: Retrieve reported LibreSSL version at runtime
  - openssl: Set X509_V_FLAG_PARTIAL_CHAIN by default
  - parsedate: Offer a getdate_capped() alternative
  - pause: Avoid updating socket if done was already called
  - projects: Fix Visual Studio projects SSH builds
  - projects: Fix Visual Studio wolfSSL configurations
  - quiche: Reject HTTP/3 headers in the wrong order
  - remove_handle: Clear expire timers after multi_done()
  - runtests: --repeat=[num] to repeat tests
  - runtests: Introduce --shallow to reduce huge torture tests
  - schannel: Fix --tls-max for when min is --tlsv1 or default
  - setopt: Fix ALPN / NPN user option when built without HTTP2
  - strerror: Add Curl_winapi_strerror for Win API specific errors
  - strerror: Fix an error looking up some Windows error strings
  - strerror: Fix compiler warning "empty expression"
  - system.h: Fix for MCST lcc compiler
  - test/sws: Search for "Testno:" header unconditionally if no testno
  - test1175: Verify symbols-in-versions and libcurl-errors.3 in sync
  - test1270: A basic -w redirect_url test
  - test1456: Remove the use of a fixed local port number
  - test1558: Use double slash after file:
  - test1560: Require IPv6 for IPv6 aware URL parsing
  - tests/lib1557: Fix mem-leak in OOM
  - tests/lib1559: Fix mem-leak in OOM
  - tests/lib1591: Free memory properly on OOM, in the trailers callback
  - tests/unit1607: Fix mem-leak in OOM
  - tests/unit1609: Fix mem-leak in OOM
  - tests/unit1620: Fix bad free in OOM
  - tests: Change NTLM tests to require SSL
  - tests: Fix bounce requests with truncated writes
  - tests: Fix build with 'CURL_DISABLE_DOH'
  - tests: Fix permissions of ssh keys in WSL
  - tests: Make it possible to set executable extensions
  - tests: Make sure checksrc runs on header files too
  - tests: Set LC_ALL=en_US.UTF-8 instead of blank in several tests
  - tests: Use DoH feature for DoH tests
  - tests: Use \r\n for log messages in WSL
  - tool_operate: Fix mem leak when failed config parse
  - travis: Fix error detection
  - travis: Abandon coveralls, it is not reliable
  - travis: Build ngtcp2 with --enable-lib-only
  - travis: Export the CC/CXX variables when set
  - vtls: Make BearSSL possible to set with CURL_SSL_BACKEND
  - winbuild: Define CARES_STATICLIB when WITH_CARES=static
  - winbuild: Document CURL_STATICLIB requirement for static libcurl

* Thu Nov 14 2019 Paul Howarth <paul@city-fan.org> - 7.67.0-2.0.cf
- Fix infinite loop on upload using a glob (#1771025)

* Wed Nov  6 2019 Paul Howarth <paul@city-fan.org> - 7.67.0-1.0.cf
- Update to 7.67.0
  - curl: Added --no-progress-meter
  - setopt: CURLMOPT_MAX_CONCURRENT_STREAMS is new
  - urlapi: CURLU_NO_AUTHORITY allows empty authority/host part
  - BINDINGS: Five new bindings addded
  - CURLOPT_TIMEOUT.3: Clarify transfer timeout time includes queue time
  - CURLOPT_TIMEOUT.3: Remove the mention of "minutes"
  - ESNI: Initial build/setup support
  - FTP: FTPFILE_NOCWD: Avoid redundant CWDs
  - FTP: Allow "rubbish" prepended to the SIZE response
  - FTP: Remove trailing slash from path for LIST/MLSD
  - FTP: Skip CWD to entry dir when target is absolute
  - FTP: url-decode path before evaluation
  - HTTP3.md: Move -p for mkdir, remove -j for make
  - HTTP3: Fix invalid use of sendto for connected UDP socket
  - HTTP3: Fix ngtcp2 Windows build
  - HTTP3: Fix prefix parameter for ngtcp2 build
  - HTTP3: Fix typo somehere1 > somewhere1
  - HTTP3: Show an --alt-svc using example too
  - INSTALL: Add missing space for configure commands
  - INSTALL: Add vcpkg installation instructions
  - README: Minor grammar fix
  - altsvc: Accept quoted ma and persist values
  - altsvc: Both backends run h3-23 now
  - appveyor: Add MSVC ARM64 build
  - appveyor: Use two parallel compilation on appveyor with CMake
  - appveyor: Add --disable-proxy autotools build
  - appveyor: Add 32-bit MinGW-w64 build
  - appveyor: Add a winbuild
  - appveyor: Add a winbuild that uses VS2017
  - appveyor: Make winbuilds with DEBUG=no/yes and VS 2015/2017
  - appveyor: Publish artifacts on appveyor
  - appveyor: Upgrade VS2017 to VS2019
  - asyn-thread: Make use of Curl_socketpair() where available
  - asyn-thread: s/AF_LOCAL/AF_UNIX for Solaris
  - build: Remove unused HAVE_LIBSSL and HAVE_LIBCRYPTO defines
  - checksrc: Fix uninitialized variable warning
  - chunked-encoding: Stop hiding the CURLE_BAD_CONTENT_ENCODING error
  - cirrus: Increase the git clone depth
  - cirrus: Switch the FreeBSD 11.x build to 11.3 and add a 13.0 build
  - cirrus: Switch off blackhole status on the freebsd CI machines
  - cleanups: 21 various PVS-Studio warnings
  - configure: Only say ipv6 enabled when the variable is set
  - configure: Remove all cyassl references
  - conn-reuse: Requests wanting NTLM can reuse non-NTLM connections
  - connect: Return CURLE_OPERATION_TIMEDOUT for errno == ETIMEDOUT
  - connect: Silence sign-compare warning
  - cookie: Avoid harmless use after free
  - cookie: Pass in the correct cookie amount to qsort()
  - cookies: Change argument type for Curl_flush_cookies
  - cookies: Using a share with cookies shouldn't enable the cookie engine
  - copyrights: Update copyright notices to 2019
  - curl: Create easy handles on-demand and not ahead of time
  - curl: Ensure HTTP 429 triggers --retry
  - curl: Exit the create_transfers loop on errors
  - curl: Fix memory leaked by parse_metalink()
  - curl: Load large files with -d @ much faster
  - docs/HTTP3: Fix '--with-ssl' ngtcp2 configure flag
  - docs: Added multi-event.c example
  - docs: Disambiguate CURLUPART_HOST is for host name (i.e. no port)
  - docs: Note on failed handles not being counted by curl_multi_perform
  - doh: Allow only http and https in debug mode
  - doh: Avoid truncating DNS QTYPE to lower octet
  - doh: Clean up dangling DOH memory on easy close
  - doh: Fix (harmless) buffer overrun
  - doh: Fix undefined behaviour and open up for gcc and clang optimization
  - doh: Return early if there is no time left
  - examples/sslbackend: Fix -Wchar-subscripts warning
  - examples: Remove the "this exact code has not been verified"
  - git: Add tests/server/disabled to .gitignore
  - gnutls: Make gnutls_bye() not wait for response on shutdown
  - http2: Expire a timeout at end of stream
  - http2: Prevent dup'ed handles to send dummy PRIORITY frames
  - http2: Relax verification of :authority in push promise requests
  - http2_recv: A closed stream trumps pause state
  - http: Lowercase headernames for HTTP/2 and HTTP/3
  - ldap: Stop using wide char version of ldapp_err2string
  - ldap: Fix OOM error on missing query string
  - mbedtls: Add error message for cert validity starting in the future
  - mime: When disabled, avoid C99 macro
  - ngtcp2: Adapt to API change
  - ngtcp2: Compile with latest ngtcp2 + nghttp3 draft-23
  - ngtcp2: Remove fprintf() calls
  - openssl: close_notify on the FTP data connection doesn't mean closure
  - openssl: Fix compiler warning with LibreSSL
  - openssl: Use strerror on SSL_ERROR_SYSCALL
  - os400: getpeername() and getsockname() return ebcdic AF_UNIX sockaddr
  - parsedate: Fix date parsing disabled builds
  - quiche: Don't close connection at end of stream
  - quiche: Persist connection details (fixes -I with --http3)
  - quiche: Set 'drain' when returning without having drained the queues
  - quiche: Update HTTP/3 config creation to new API
  - redirect: Handle redirects to absolute URLs containing spaces
  - runtests: Get textaware info from curl instead of perl
  - schannel: Reverse the order of certinfo insertions
  - schannel_verify: Fix concurrent openings of CA file
  - security: Silence conversion warning
  - setopt: Handle ALTSVC set to NULL
  - setopt: Make it easier to add new enum values
  - setopt: Store CURLOPT_RTSP_SERVER_CSEQ correctly
  - smb: Check for full size message before reading message details
  - smbserver: Fix Python 3 compatibility
  - socks: Fix destination host shown on SOCKS5 error
  - test1162: Disable MSYS2's POSIX path conversion
  - test1591: Fix spelling of http feature
  - tests: Add 'connect to non-listen' keywords
  - tests: Fix narrowing conversion warnings
  - tests: Fix the test 3001 cert failures
  - tests: Make tests succeed when using --disable-proxy
  - tests: Use %%FILE_PWD for file:// URLs
  - tests: Use port 2 instead of 60000 for a safer non-listening port
  - tool_operate: Fix retry sleep time shown to user when Retry-After
  - travis: Add an ARM64 build
  - url: Curl_free_request_state() should also free doh handles
  - url: Don't set appconnect time for non-ssl/non-ssh connections
  - url: Fix the NULL hostname compiler warning
  - url: Normalize CURLINFO_EFFECTIVE_URL
  - url: Only reuse TLS connections with matching pinning
  - urlapi: Avoid index underflow for short ipv6 hostnames
  - urlapi: Fix URL encoding when setting a full URL
  - urlapi: Fix unused variable warning
  - urlapi: Question mark within fragment is still fragment
  - urldata: Use 'bool' for the bit type on MSVC compilers
  - vtls: Fix comment typo about macosx-version-min compiler flag
  - vtls: Fix narrowing conversion warnings
  - winbuild/MakefileBuild.vc: Add vssh
  - winbuild/MakefileBuild.vc: Fix line endings
  - winbuild: Add manifest to curl.exe for proper OS version detection
  - winbuild: Add ENABLE_UNICODE option
- Trim package changelog to include only entries from the last 5 years; older
  entries contained in new doc-file: curl-pkg-changelog.old

* Fri Sep 13 2019 Paul Howarth <paul@city-fan.org> - 7.66.0-1.1.cf
- curl: Fix memory leaked by parse_metalink()
  (https://github.com/curl/curl/pull/4326)

* Wed Sep 11 2019 Paul Howarth <paul@city-fan.org> - 7.66.0-1.0.cf
- Update to 7.66.0
  - CVE-2019-5481: FTP-KRB double-free
  - CVE-2019-5482: TFTP small blocksize heap buffer overflow
  - CURLINFO_RETRY_AFTER: Parse the Retry-After header value
  - HTTP3: Initial (experimental still not working) support
  - curl: --sasl-authzid added to support CURLOPT_SASL_AUTHZID from the tool
  - curl: Support parallel transfers with -Z
  - curl_multi_poll: A sister to curl_multi_wait() that waits more
  - sasl: Implement SASL authorisation identity via CURLOPT_SASL_AUTHZID
  - CI: Remove duplicate configure flag for LGTM.com
  - CMake: Remove needless newlines at end of gss variables
  - CMake: Use platform dependent name for dlopen() library
  - CURLINFO docs: Mention that in redirects times are added
  - CURLOPT_ALTSVC.3: Use a "" file name to not load from a file
  - CURLOPT_ALTSVC_CTRL.3: Remove CURLALTSVC_ALTUSED
  - CURLOPT_HEADERFUNCTION.3: Clarify
  - CURLOPT_HTTP_VERSION: Setting this to 3 forces HTTP/3 use directly
  - CURLOPT_READFUNCTION.3: Provide inline example
  - CURLOPT_SSL_VERIFYHOST: Treat the value 1 as 2
  - Curl_addr2string: Take an addrlen argument too
  - Curl_fillreadbuffer: Avoid double-free trailer buf on error
  - HTTP: Use chunked Transfer-Encoding for HTTP_POST if size unknown
  - alt-svc: Add protocol version selection masking
  - alt-svc: Fix removal of expired cache entry
  - alt-svc: Make it use h3-22 with ngtcp2 as well
  - alt-svc: More liberal ALPN name parsing
  - alt-svc: Send Alt-Used: in redirected requests
  - alt-svc: With quiche, use the quiche h3 alpn string
  - appveyor: Pass on -k to make
  - asyn-thread: Create a socketpair to wait on
  - build-openssl: Fix build with Visual Studio 2019
  - cleanup: Move functions out of url.c and make them static
  - cleanup: Remove the 'numsocks' argument used in many places
  - configure: Avoid undefined check_for_ca_bundle
  - curl.h: Add CURL_HTTP_VERSION_3 to the version enum
  - curl.h: Fix outdated comment
  - curl: Cap the maximum allowed values for retry time arguments
  - curl: Handle a libcurl build without netrc support
  - curl: Make use of CURLINFO_RETRY_AFTER when retrying
  - curl: Remove outdated comment
  - curl: Use .curlrc (with a dot) on Windows
  - curl: Use CURLINFO_PROTOCOL to check for HTTP(s)
  - curl_global_init_mem.3: Mention it was added in 7.12.0
  - curl_version: Bump string buffer size to 250
  - curl_version_info.3: Mentioned ALTSVC and HTTP3
  - curl_version_info: Offer quic (and h3) library info
  - curl_version_info: Provide nghttp2 details
  - defines: Avoid underscore-prefixed defines
  - docs/ALTSVC: Remove what works and the experimental explanation
  - docs/EXPERIMENTAL: Explain what it means and what's experimental now
  - docs/MANUAL.md: Converted to markdown from plain text
  - docs/examples/curlx: Fix errors
  - docs: s/curl_debug/curl_dbg_debug in comments and docs
  - easy: Resize receive buffer on easy handle reset
  - examples: Avoid reserved names in hiperfifo examples
  - examples: Add http3.c, altsvc.c and http3-present.c
  - getenv: Support up to 4K environment variable contents on Windows
  - http09: Disable HTTP/0.9 by default in both tool and library
  - http2: When marked for closure and wanted to close == OK
  - http2_recv: Trigger another read when the last data is returned
  - http: Fix use of credentials from URL when using HTTP proxy
  - http_negotiate: Improve handling of gss_init_sec_context() failures
  - md4: Use our own MD4 when no crypto libraries are available
  - multi: Call detach_connection before Curl_disconnect
  - netrc: Make the code try ".netrc" on Windows
  - nss: Use TLSv1.3 as default if supported
  - openssl: Build warning free with boringssl
  - openssl: Use SSL_CTX_set_<min|max>_proto_version() when available
  - plan9: Add support for running on Plan 9
  - progress: Reset download/uploaded counter between transfers
  - readwrite_data: Repair setting the TIMER_STARTTRANSFER stamp
  - scp: Fix directory name length used in memcpy
  - smb: Initialize *msg to NULL in smb_send_and_recv()
  - smtp: Check for and bail out on too short EHLO response
  - source: Remove names from source comments
  - spnego_sspi: Add typecast to fix build warning
  - src/makefile: Fix uncompressed hugehelp.c generation
  - ssh-libssh: Do not specify O_APPEND when not in append mode
  - ssh: Move code into vssh for SSH backends
  - sspi: Fix memory leaks
  - tests: Replace outdated test case numbering documentation
  - tftp: Return error when packet is too small for options
  - timediff: Make it 64 bit (if possible) even with 32 bit time_t
  - travis: Reduce number of torture tests in 'coverage'
  - url: Make use of new HTTP version if alt-svc has one
  - urlapi: Verify the IPv6 numerical address
  - urldata: Avoid 'generic', use dedicated pointers
  - vauth: Use CURLE_AUTH_ERROR for auth function errors

* Tue Aug 27 2019 Paul Howarth <paul@city-fan.org> - 7.65.3-4.0.cf
- Avoid reporting spurious error in the HTTP2 framing layer (#1690971)

* Thu Aug  1 2019 Paul Howarth <paul@city-fan.org> - 7.65.3-3.0.cf
- Improve handling of gss_init_sec_context() failures

* Thu Jul 25 2019 Paul Howarth <paul@city-fan.org> - 7.65.3-2.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Fri Jul 19 2019 Paul Howarth <paul@city-fan.org> - 7.65.3-1.0.cf
- Update to 7.65.3
  - progress: Make the progress meter appear again

* Wed Jul 17 2019 Paul Howarth <paul@city-fan.org> - 7.65.2-1.0.cf
- Update to 7.65.2
  - CIPHERS.md: Explain Schannel error SEC_E_ALGORITHM_MISMATCH
  - CMake: Convert errant elseif() to else()
  - CMake: Fix finding Brotli on case-sensitive file systems
  - CURLMOPT_SOCKETFUNCTION.3: Clarified
  - CURLMOPT_SOCKETFUNCTION.3: Fix typo
  - CURLOPT_CAINFO.3: Polished wording
  - CURLOPT_HEADEROPT.3: Fix example
  - CURLOPT_RANGE.3: Caution against using it for HTTP PUT
  - CURLOPT_SEEKDATA.3: Fix variable name
  - DEPRECATE: Fixup versions and spelling
  - bindlocal: Detect and avoid IP version mismatches in bind()
  - build: Fix Codacy warnings
  - buildconf.bat: Fix header filename
  - c-ares: Honour port numbers in CURLOPT_DNS_SERVERS
  - config-os400: Add getpeername and getsockname defines
  - configure: --disable-progress-meter
  - configure: Fix --disable-code-coverage
  - configure: Fix typo '--disable-http-uath'
  - configure: More --disable switches to toggle off individual features
  - configure: Remove CURL_DISABLE_TLS_SRP
  - conn_maxage: Move the check to prune_dead_connections()
  - curl: Skip CURLOPT_PROXY_CAPATH for disabled-proxy builds
  - curl_multi_wait.3: Escape backslash in example
  - docs: Explain behaviour change in --tlsv1. options since 7.54
  - docs: Fix links to OpenSSL docs
  - docs: Fix string suggesting HTTP/2 is not the default
  - examples/fopen: Fix comparison
  - examples/htmltitle: Use C++ casts between pointer types
  - headers: Remove no longer exported functions
  - http2: Call done_sending on end of upload
  - http2: Don't call stream-close on already closed streams
  - http2: Remove CURL_DISABLE_TYPECHECK define
  - http: Allow overriding timecond with custom header
  - http: Clarify header buffer size calculation
  - krb5: Fix compiler warning
  - lib: Use UTF-8 encoding in comments
  - libcurl-tutorial.3: Fix small typo (mutipart → multipart)
  - libcurl: Restrict redirect schemes to HTTP, HTTPS, FTP and FTPS
  - multi: Enable multiplexing by default (again)
  - multi: Fix the transfer hashes in the socket hash entries
  - multi: Make sure 'data' can present in several sockhash entries
  - netrc: Return the correct error code when out of memory
  - nss: Don't set unused parameter
  - nss: Inspect return value of token check
  - nss: Only cache valid CRL entries
  - nss: Support using libnss on macOS
  - openssl: define HAVE_SSL_GET_SHUTDOWN based on version number
  - openssl: Disable engine if OPENSSL_NO_UI_CONSOLE is defined
  - openssl: Fix pubkey/signature algorithm detection in certinfo
  - openssl: Remove outdated comment
  - os400: Make vsetopt() non-static as Curl_vsetopt() for os400 support
  - quote.d: Asterisk prefix works for SFTP as well
  - runtests: Keep logfiles around by default
  - runtests: Report single test time + total duration
  - smb: Use the correct error code for access denied on file open
  - sws: Remove unused variables
  - system_win32: Fix clang warning
  - system_win32: Fix typo
  - test1165: Verify that CURL_DISABLE_ symbols are in sync
  - test1521: Adapt to SLISTPOINT
  - test1523: Test CURLOPT_LOW_SPEED_LIMIT
  - test153: Fix content-length to avoid occasional hang
  - test188/189: Fix Content-Length
  - tests: Have runtests figure out disabled features
  - tests: Support non-localhost HOSTIP for dict/smb servers
  - tests: Update fixed IP for hostip/clientip split
  - tool_cb_prg: Fix integer overflow in progress bar
  - travis: Disable threaded resolver for coverage build
  - travis: Enable alt-svc for coverage build
  - travis: Enable brotli for all xenial jobs
  - travis: Enable libssh2 for coverage build
  - travis: Enable warnings-as-errors for coverage build
  - travis: Update scan-build job to xenial
  - typecheck: CURLOPT_CONNECT_TO takes an slist too
  - typecheck: Add 3 missing strings and a callback data pointer
  - unit1654: Cleanup on memory failure
  - unpause: Trigger a timeout for event-based transfers
  - url: Fix CURLOPT_MAXAGE_CONN time comparison
  - win32: Make DLL loading a no-op for UWP
  - winbuild: Change Makefile to honor ENABLE_OPENSSL_AUTO_LOAD_CONFIG
  - winbuild: Use WITH_PREFIX if given
  - wolfssl: Refer to it as wolfSSL only

* Wed Jun  5 2019 Paul Howarth <paul@city-fan.org> - 7.65.1-1.0.cf
- Update to 7.65.1
  - CURLOPT_LOW_SPEED_* repaired
  - NTLM: Reset proxy "multipass" state when CONNECT request is done
  - PolarSSL: Deprecate support step 1 - removed from configure
  - appveyor: Add Visual Studio solution build
  - cmake: Check for if_nametoindex()
  - cmake: Support CMAKE_OSX_ARCHITECTURES when detecting SIZEOF variables
  - config-win32: Add support for if_nametoindex and getsockname
  - conncache: Remove the DEBUGASSERT on length check
  - conncache: Make "bundles" per host name when doing proxy tunnels
  - curl-win32.h: Enable Unix Domain Sockets based on the Windows SDK version
  - curl_share_setopt.3: Improve wording
  - dump-header.d: Spell out that no headers == empty file
  - example/http2-download: Fix format specifier
  - examples: Clean-ups and compiler warning fixes
  - http2: Stop drain from being permanently set
  - http: Don't parse body-related headers in bodyless responses
  - md4: Build correctly with openssl without MD4
  - md4: include the mbedtls config.h to get the MD4 info
  - multi: Track users of a socket better
  - nss: Allow to specify TLS 1.3 ciphers if supported by NSS
  - parse_proxy: Make sure portptr is initialized
  - parse_proxy: Use the IPv6 zone id if given
  - sectransp: Handle errSSLPeerAuthCompleted from SSLRead()
  - singlesocket: Use separate variable for inner loop
  - ssl: Update outdated "openssl-only" comments for supported backends
  - tests: Add HAProxy keywords
  - tests: Add support to test against OpenSSH for Windows
  - tests: Make test 1420 and 1406 work with rtsp-disabled libcurl
  - tls13-docs: Mention it is only for OpenSSL ≥ 1.1.1
  - tool_parse_cfg: Avoid 2 fopen() for WIN32
  - tool_setopt: For builds with disabled-proxy, skip all proxy setopts()
  - url: Load if_nametoindex() dynamically from iphlpapi.dll on Windows
  - url: Fix bad feature-disable #ifdef
  - url: Use correct port in ConnectionExists()
  - winbuild: Use two space indentation

* Thu May 30 2019 Paul Howarth <paul@city-fan.org> - 7.65.0-2.0.cf
- Fix spurious timeout events with speed-limit (#1714893)

* Wed May 22 2019 Paul Howarth <paul@city-fan.org> - 7.65.0-1.0.cf
- Update to 7.65.0
  - CURLOPT_DNS_USE_GLOBAL_CACHE: removed
  - CURLOPT_MAXAGE_CONN: Set the maximum allowed age for conn reuse
  - pipelining: Removed
  - CVE-2019-5435: Integer overflows in curl_url_set
  - CVE-2019-5436: tftp: Use the current blksize for recvfrom()
  - --config: Clarify that initial : and = might need quoting
  - AppVeyor: Enable testing for WinSSL build
  - CURLMOPT_TIMERFUNCTION.3: Warn about the recursive risk
  - CURLOPT_ADDRESS_SCOPE: Fix range check and more
  - CURLOPT_CAINFO.3: With Schannel, you want Windows 8 or later
  - CURLOPT_CHUNK_BGN_FUNCTION.3: Document the struct and time value
  - CURLOPT_READFUNCTION.3: See also CURLOPT_UPLOAD_BUFFERSIZE
  - CURL_MAX_INPUT_LENGTH: Largest acceptable string input size
  - Curl_disconnect: Treat all CONNECT_ONLY connections as "dead"
  - INTERNALS: Add code highlighting
  - OS400/ccsidcurl: Replace use of Curl_vsetopt
  - OpenSSL: Report -fips in version if OpenSSL is built with FIPS
  - README.md: Fix no-consecutive-blank-lines Codacy warning
  - VC15 project: Remove MinimalRebuild
  - VS projects: Use Unicode for VC10+
  - WRITEFUNCTION: Add missing set_in_callback around callback
  - altsvc: Fix building with cookies disabled
  - auth: Rename the various authentication clean up functions
  - base64: Build conditionally if there are users
  - build-openssl.bat: Fixed support for OpenSSL v1.1.0+
  - build: Fix "clarify calculation precedence" warnings
  - checksrc.bat: Ignore snprintf warnings in docs/examples
  - cirrus: Customize the disabled tests per FreeBSD version
  - cleanup: Remove FIXME and TODO comments
  - cmake: Avoid linking executable for some tests with cmake 3.6+
  - cmake: Clear CMAKE_REQUIRED_LIBRARIES after each use
  - cmake: Rename CMAKE_USE_DARWINSSL to CMAKE_USE_SECTRANSP
  - cmake: Set SSL_BACKENDS
  - configure: Avoid unportable '==' test(1) operator
  - configure: Error out if OpenSSL wasn't detected when asked for
  - configure: Fix default location for fish completions
  - cookie: Guard against possible NULL ptr deref
  - curl: Make code work with protocol-disabled libcurl
  - curl: Report error for "--no-" on non-boolean options
  - curl_easy_getinfo.3: Fix minor formatting mistake
  - curlver.h: Use parenthesis in CURL_VERSION_BITS macro
  - docs/BUG-BOUNTY: Bug bounty time
  - docs/INSTALL: Fix broken link
  - docs/RELEASE-PROCEDURE: Link to live iCalendar
  - documentation: Fix several typos
  - doh: Acknowledge CURL_DISABLE_DOH
  - doh: Disable DOH for the cases it doesn't work
  - examples: Remove unused variables
  - ftplistparser: Fix LGTM alert "Empty block without comment"
  - hostip: Acknowledge CURL_DISABLE_SHUFFLE_DNS
  - http: Ignore HTTP/2 prior knowledge setting for HTTP proxies
  - http: Acknowledge CURL_DISABLE_HTTP_AUTH
  - http: Mark bundle as not for multiuse on < HTTP/2 response
  - http_digest: Don't expose functions when HTTP and Crypto Auth are disabled
  - http_negotiate: Do not treat failure of gss_init_sec_context() as fatal
  - http_ntlm: Corrected the name of the include guard
  - http_ntlm_wb: Handle auth for only a single request
  - http_ntlm_wb: Return the correct error on receiving an empty auth message
  - lib509: Add missing include for strdup
  - lib557: Initialize variables
  - makedebug: Fix ERRORLEVEL detection after running where.exe
  - mbedtls: Enable use of EC keys
  - mime: Acknowledge CURL_DISABLE_MIME
  - multi: Improved HTTP_1_1_REQUIRED handling
  - netrc: Acknowledge CURL_DISABLE_NETRC
  - nss: Allow fifos and character devices for certificates
  - nss: Provide more specific error messages on failed init
  - ntlm: Fix misaligned function comments for Curl_auth_ntlm_cleanup
  - ntlm: Support the NT response in the type-3 when OpenSSL doesn't include MD4
  - openssl: Mark connection for close on TLS close_notify
  - openvms: Remove pre-processor for SecureTransport
  - openvms: Remove pre-processors for Windows
  - parse_proxy: Use the URL parser API
  - parsedate: Disabled on CURL_DISABLE_PARSEDATE
  - pingpong: Disable more when no pingpong protocols are enabled
  - polarssl_threadlock: Remove conditionally unused code
  - progress: Acknowledge CURL_DISABLE_PROGRESS_METER
  - proxy: Acknowledge DISABLE_PROXY more
  - resolve: Apply Happy Eyeballs philosophy to parallel c-ares queries
  - revert "multi: Support verbose conncache closure handle"
  - sasl: Don't send authcid as authzid for the PLAIN mechanism as per RFC 4616
  - sasl: Only enable if there's a protocol enabled using it
  - scripts: Fix typos
  - singleipconnect: Show port in the verbose "Trying ..." message
  - smtp: Fix compiler warning
  - socks5: User name and passwords must be shorter than 256
  - socks: Fix error message
  - socksd: New SOCKS 4+5 server for tests
  - spnego_gssapi: Fix return code on gss_init_sec_context() failure
  - ssh-libssh: Remove unused variable
  - ssh: Define USE_SSH if SSH is enabled (any backend)
  - ssh: Move variable declaration to where it's used
  - test1002: Correct the name
  - test2100: Fix typos in test description
  - tests/server/util: Fix Windows Unicode build
  - tests: Run global cleanup at end of tests
  - tests: Make Impacket (SMB server) Python 3 compatible
  - tool_cb_wrt: Fix bad-function-cast warning
  - tool_formparse: Remove redundant assignment
  - tool_help: Warn if curl and libcurl versions do not match
  - tool_help: include <strings.h> for strcasecmp
  - transfer: Fix LGTM alert "Comparison is always true"
  - travis: Add an osx http-only build
  - travis: Allow builds on branches named "ci"
  - travis: Install dependencies only when needed
  - travis: Update some builds do Xenial
  - travis: Updated mesalink builds
  - url: Always clone the CUROPT_CURLU handle
  - url: Convert the zone id from a IPv6 URL to correct scope id
  - urlapi: Add CURLUPART_ZONEID to set and get
  - urlapi: Increase supported scheme length to 40 bytes
  - urlapi: Require a non-zero host name length when parsing URL
  - urlapi: Stricter CURLUPART_PORT parsing
  - urlapi: Strip off zone id from numerical IPv6 addresses
  - urlapi: urlencode characters above 0x7f correctly
  - vauth/cleartext: Update the PLAIN login to match RFC 4616
  - vauth/oauth2: Fix OAUTHBEARER token generation
  - vauth: Fix incorrect function description for Curl_auth_user_contains_domain
  - vtls: Fix potential ssl_buffer stack overflow
  - wildcard: Disable from build when FTP isn't present
  - winbuild: Support MultiSSL builds
  - xattr: Skip unittest on unsupported platforms
- Re-enable fish completions as they shouldn't conflict with fish any more

* Thu May 09 2019 Paul Howarth <paul@city-fan.org> - 7.64.1-2.0.cf
- Do not treat failure of gss_init_sec_context() with --negotiate as fatal

* Thu Apr  4 2019 Paul Howarth <paul@city-fan.org> - 7.64.1-1.1.cf
- Rebuild without fish completion support, which conflicts with fish itself

* Wed Mar 27 2019 Paul Howarth <paul@city-fan.org> - 7.64.1-1.0.cf
- Update to 7.64.1
  - alt-svc: Experimental support added
  - configure: Add --with-amissl
  - AppVeyor: Add MinGW-w64 and classic Mingw builds
  - AppVeyor: Switch VS 2015 builds to VS 2017 image
  - CURLU: Fix NULL dereference when used over proxy
  - Curl_easy: Remove req.maxfd - never used!
  - Curl_now: Figure out windows version in win32_init
  - Curl_resolv: Fix a gcc -Werror=maybe-uninitialized warning
  - DoH: Inherit some SSL options from user's easy handle
  - Secure Transport: No more "darwinssl"
  - Secure Transport: tvOS 11 is required for ALPN support
  - cirrus: Added FreeBSD builds using Cirrus CI
  - cleanup: Make local functions static
  - cli tool: Do not use mime.h private structures
  - cmdline-opts/proxytunnel.d: The option tunnels all protocols
  - configure: Add additional libraries to check for LDAP support
  - configure: Remove the unused fdopen macro
  - configure: Show features as well in the final summary
  - conncache: Use conn->data to know if a transfer owns it
  - connection: Never reuse CONNECT_ONLY connections
  - connection_check: Restore original conn->data after the check
  - connection_check: Set ->data to the transfer doing the check
  - cookie: Add support for cookie prefixes
  - cookies: Dotless names can set cookies again
  - cookies: Fix NULL dereference if flushing cookies with no CookieInfo set
  - curl.1: --user and --proxy-user are hidden from ps output
  - curl.1: Mark the argument to --cookie as <data|filename>
  - curl.h: Use __has_declspec_attribute for shared builds
  - curl: Display --version features sorted alphabetically
  - curl: Fix FreeBSD compiler warning in the --xattr code
  - curl: Remove MANUAL from -M output
  - curl_easy_duphandle.3: Clarify that a duped handle has no shares
  - curl_multi_remove_handle.3: Use at any time, just not from within callbacks
  - curl_url.3: This API is not experimental any more
  - dns: Release sharelock as soon as possible
  - docs: Update max-redirs.d phrasing
  - easy: Fix win32 init to work without CURL_GLOBAL_WIN32
  - examples/10-at-a-time.c: Improve readability and simplify
  - examples/cacertinmem.c: Use multiple certificates for loading CA-chain
  - examples/crawler: Fix the Accept-Encoding setting
  - examples/ephiperfifo.c: Various fixes
  - examples/externalsocket: Add missing close socket calls
  - examples/http2-download: Cleaned up
  - examples/http2-serverpush: Add some sensible error checks
  - examples/http2-upload: Cleaned up
  - examples/httpcustomheader: Value stored to 'res' is never read
  - examples/postinmemory: Potential leak of memory pointed to by 'chunk.memory'
  - examples/sftpuploadresume: Value stored to 'result' is never read
  - examples: Only include <curl/curl.h>
  - examples: Remove recursive calls to curl_multi_socket_action
  - examples: Remove superfluous null-pointer checks
  - file: Fix "Checking if unsigned variable 'readcount' is less than zero"
  - fnmatch: Disable if FTP is disabled
  - gnutls: Remove call to deprecated gnutls_compression_get_name
  - gopher: Remove check for path == NULL
  - gssapi: Fix deprecated header warnings
  - hostip: Make create_hostcache_id avoid alloc + free
  - http2: multi_connchanged() moved from multi.c, only used for h2
  - http2: Verify :authority in push promise requests
  - http: Make adding a blank header thread-safe
  - http: Send payload when (proxy) authentication is done
  - http: Set state.infilesize when sending multipart formposts
  - makefile: Make checksrc and hugefile commands "silent"
  - mbedtls: Make it build even if MBEDTLS_VERSION_C isn't set
  - mbedtls: Release sessionid resources on error
  - memdebug: Log pointer before freeing its data
  - memdebug: Make debug-specific functions use curl_dbg_ prefix
  - mime: Put the boundary buffer into the curl_mime struct
  - multi: Call multi_done on connect timeouts, fixes CURLINFO_TOTAL_TIME
  - multi: Remove verbose "Expire in" ... messages
  - multi: Removed unused code for request retries
  - multi: Support verbose conncache closure handle
  - negotiate: Fix for HTTP POST with Negotiate
  - openssl: Add support for TLS ASYNC state
  - openssl: If cert type is ENG and no key specified, key is ENG too
  - pretransfer: Don't strlen() POSTFIELDS set for GET requests
  - rand: Fix a mismatch between comments in source and header
  - runtests: Detect "schannel" as an alias for "winssl"
  - schannel: Be quiet - remove verbose output
  - schannel: Close TLS before removing conn from cache
  - schannel: Support CALG_ECDH_EPHEM algorithm
  - scripts/completion.pl: Also generate fish completion file
  - singlesocket: Fix the 'sincebefore' placement
  - source: Fix two 'nread' may be used uninitialized warnings
  - ssh: Fix Condition '!status' is always true
  - ssh: Loop the state machine if not done and not blocking
  - strerror: Make the strerror function use local buffers
  - system_win32: Move win32_init here from easy.c
  - test578: Make it read data from the correct test
  - tests: Fixed XML validation errors in some test files
  - tests: Add stderr comparison to the test suite
  - tests: Fix multiple may be used uninitialized warnings
  - threaded-resolver: Shutdown the resolver thread without error message
  - tool_cb_wrt: Fix writing to Windows null device NUL
  - tool_getpass: termios.h is present on AmigaOS 3, but no tcgetattr/tcsetattr
  - tool_operate: Build on AmigaOS
  - tool_operate: Fix typecheck warning
  - transfer.c: Do not compute length of undefined hex buffer
  - travis: Add build using gnutls
  - travis: Add scan-build
  - travis: Bump the used wolfSSL version to 4.0.0
  - travis: Enable valgrind for the iconv tests
  - travis: Use updated compiler versions: clang 7 and gcc 8
  - unit1307: Require FTP support
  - unit1651: Survive curl_easy_init() fails
  - url/idnconvert: Remove scan for ≤ 32 ascii values
  - url: Change conn shutdown order to ensure SOCKETFUNCTION callbacks
  - urlapi: Reduce variable scope, remove unreachable 'break'
  - urldata: Convert bools to bitfields and move to end
  - urldata: Simplify bytecounters
  - urlglob: Argument with 'nonnull' attribute passed null
  - version.c: Silent scan-build even when librtmp is not enabled
  - vtls: Rename some of the SSL functions
  - wolfssl: Stop custom-adding curves
  - x509asn1: "Dereference of null pointer"
  - x509asn1: Cleanup and unify code layout
  - zsh.pl: Escape ':' character
  - zsh.pl: Update regex to better match curl -h output

* Mon Mar 25 2019 Paul Howarth <paul@city-fan.org> - 7.64.0-6.0.cf
- Remove verbose "Expire in" ... messages (#1690971)

* Thu Mar 21 2019 Paul Howarth <paul@city-fan.org> - 7.64.0-5.0.cf
- Avoid spurious "Could not resolve host: [host name]" error messages

* Thu Feb 28 2019 Paul Howarth <paul@city-fan.org> - 7.64.0-4.0.cf
- Fix NULL dereference if flushing cookies with no CookieInfo set (#1683676)

* Mon Feb 25 2019 Paul Howarth <paul@city-fan.org> - 7.64.0-3.0.cf
- Prevent NetworkManager from leaking file descriptors (#1680198)

* Mon Feb 11 2019 Paul Howarth <paul@city-fan.org> - 7.64.0-2.0.cf
- Make zsh completion work again

* Wed Feb  6 2019 Paul Howarth <paul@city-fan.org> - 7.64.0-1.0.cf
- Update to 7.64.0
  - CVE-2018-16890: NTLM type-2 out-of-bounds buffer read
  - CVE-2019-3822: NTLMv2 type-3 header stack buffer overflow
  - CVE-2019-3823: SMTP end-of-response out-of-bounds read
  - cookies: Leave secure cookies alone
  - hostip: Support wildcard hosts
  - http: Implement trailing headers for chunked transfers
  - http: Added options for allowing HTTP/0.9 responses
  - timeval: Use high resolution timestamps on Windows
  - FAQ: Remove mention of sourceforge for github
  - OS400: Handle memory error in list conversion
  - OS400: Upgrade ILE/RPG binding
  - README: Add codacy code quality badge
  - Revert http_negotiate: do not close connection
  - THANKS: Added several missing names from year ≤ 2000
  - build: Make 'tidy' target work for metalink builds
  - cmake: Added checks for variadic macros
  - cmake: Updated check for HAVE_POLL_FINE to match autotools
  - cmake: Use lowercase for function name like the rest of the code
  - configure: Detect xlclang separately from clang
  - configure: Fix recv/send/select detection on Android
  - configure: Rewrite --enable-code-coverage
  - conncache_unlock: Avoid indirection by changing input argument type
  - cookie: Fix comment typo
  - cookies: Allow secure override when done over HTTPS
  - cookies: Extend domain checks to non psl builds
  - cookies: Skip custom cookies when redirecting cross-site
  - curl --xattr: Strip credentials from any URL that is stored
  - curl -J: Refuse to append to the destination file
  - curl/urlapi.h: include "curl.h" first
  - curl_multi_remove_handle() don't block terminating c-ares requests
  - darwinssl: Accept setting max-tls with default min-tls
  - disconnect: Separate connections and easy handles better
  - disconnect: Set conn->data for protocol disconnect
  - docs/version.d: Mention MultiSSL
  - docs: Fix the --tls-max description
  - docs: Use $(INSTALL_DATA) to install man page
  - docs: Use meaningless port number in CURLOPT_LOCALPORT example
  - gopher: Always include the entire gopher-path in request
  - http2: Clear pause stream id if it gets closed
  - if2ip: Remove unused function Curl_if_is_interface_name
  - libssh: Do not let libssh create socket
  - libssh: Enable CURLOPT_SSH_KNOWNHOSTS and CURLOPT_SSH_KEYFUNCTION for libssh
  - libssh: free sftp_canonicalize_path() data correctly
  - libtest/stub_gssapi: Use "real" snprintf
  - mbedtls: Use VERIFYHOST
  - multi: Multiplexing improvements
  - multi: Set the EXPIRE_*TIMEOUT timers at TIMER_STARTSINGLE time
  - ntlm: Fix NTMLv2 compliance
  - ntlm_sspi: Add support for channel binding
  - openssl: Adapt to 3.0.0, OpenSSL_version_num() is deprecated
  - openssl: Fix the SSL_get_tlsext_status_ocsp_resp call
  - openvms: Fix OpenSSL discovery on VAX
  - openvms: Fix typos in documentation
  - os400: Add a missing closing bracket
  - os400: Fix extra parameter syntax error
  - pingpong: Change default response timeout to 120 seconds
  - pingpong: Ignore regular timeout in disconnect phase
  - printf: Fix format specifiers
  - runtests.pl: Fix perl call to include srcdir
  - schannel: Fix compiler warning
  - schannel: Preserve original certificate path parameter
  - schannel: Stop calling it "winssl"
  - sigpipe: If mbedTLS is used, ignore SIGPIPE
  - smb: Fix incorrect path in request if connection reused
  - ssh: Log the libssh2 error message when ssh session startup fails
  - test1558: Verify CURLINFO_PROTOCOL on file:// transfer
  - test1561: Improve test name
  - test1653: Make it survive torture tests
  - tests: Allow tests to pass by 2037-02-12
  - tests: Move objnames-* from lib into tests
  - timediff: Fix math for unsigned time_t
  - timeval: Disable MSVC Analyzer GetTickCount warning
  - tool_cb_prg: Avoid integer overflow
  - travis: Added cmake build for osx
  - urlapi: Fix port parsing of eol colon
  - urlapi: Distinguish possibly empty query
  - urlapi: Fix parsing ipv6 with zone index
  - urldata: Rename easy_conn to just conn
  - winbuild: Conditionally use /DZLIB_WINAPI
  - wolfssl: Fix memory-leak in threaded use
  - spnego_sspi: Add support for channel binding

* Mon Feb  4 2019 Paul Howarth <paul@city-fan.org> - 7.63.0-7.0.cf
- Prevent valgrind from reporting false positives on x86_64

* Fri Feb  1 2019 Paul Howarth <paul@city-fan.org> - 7.63.0-6.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Mon Jan 21 2019 Paul Howarth <paul@city-fan.org> - 7.63.0-5.0.cf
- xattr: Strip credentials from any URL that is stored (CVE-2018-20483)

* Fri Jan  4 2019 Paul Howarth <paul@city-fan.org> - 7.63.0-4.0.cf
- Replace 0105-curl-7.63.0-libstubgss-ldadd.patch by upstream patch

* Wed Dec 19 2018 Paul Howarth <paul@city-fan.org> - 7.63.0-3.0.cf
- curl -J: Do not append to the destination file (#1658574)

* Fri Dec 14 2018 Paul Howarth <paul@city-fan.org> - 7.63.0-2.0.cf
- Revert an upstream commit that broke 'fedpkg new-sources' (#1659329)

* Wed Dec 12 2018 Paul Howarth <paul@city-fan.org> - 7.63.0-1.0.cf
- Update to 7.63.0
  - curl: Add %%{stderr} and %%{stdout} for --write-out
  - curl: Add undocumented option --dump-module-paths for win32
  - setopt: Add CURLOPT_CURLU
  - (lib)curl.rc: Fixup for minor bugs
  - CURLINFO_REDIRECT_URL: Extract the Location: header field unvalidated
  - CURLOPT_HEADERFUNCTION.3: Match 'nitems' name in synopsis and description
  - CURLOPT_WRITEFUNCTION.3: Spell out that it gets called many times
  - Curl_follow: Accept non-supported schemes for "fake" redirects
  - KNOWN_BUGS: Add --proxy-any connection issue
  - NTLM: Remove redundant ifdef USE_OPENSSL
  - NTLM: Force the connection to HTTP/1.1
  - OS400: Add URL API ccsid wrappers and sync ILE/RPG bindings
  - SECURITY-PROCESS: bountygraph shuts down again
  - TODO: Have the URL API offer IDN decoding
  - ares: Remove fd from multi fd set when ares is about to close the fd
  - axtls: Removed
  - checksrc: Add COPYRIGHTYEAR check
  - cmake: Fix MIT/Heimdal Kerberos detection
  - configure: Include all libraries in ssl-libs fetch
  - configure: Show CFLAGS, LDFLAGS etc. in summary
  - connect: Fix building for recent versions of Minix
  - cookies: Create the cookiejar even if no cookies to save
  - cookies: Expire "Max-Age=0" immediately
  - curl: --local-port range was not "including"
  - curl: Fix --local-port integer overflow
  - curl: Fix memory leak reading --writeout from file
  - curl: Fixed UTF-8 in current console code page (Windows)
  - curl_easy_perform: Fix timeout handling
  - curl_global_sslset(): id == -1 is not necessarily an error
  - curl_multibyte: Fix a malloc overcalculation
  - curle: Move deprecated error code to ifndef block
  - docs: curl_formadd field and file names are now escaped
  - docs: Escape "\n" codes
  - doh: Fix memory leak in OOM situation
  - doh: Make it work for h2-disabled builds too
  - examples/ephiperfifo: Report error when epoll_ctl fails
  - ftp: Avoid two unsigned int overflows in FTP listing parser
  - host names: Allow trailing dot in name resolve, then strip it
  - http2: Upon HTTP_1_1_REQUIRED, retry the request with HTTP/1.1
  - http: Don't set CURLINFO_CONDITION_UNMET for http status code 204
  - http: Fix HTTP Digest auth to include query in URI
  - http_negotiate: Do not close connection until negotiation is completed
  - impacket: Add LICENSE
  - infof: Clearly indicate truncation
  - ldap: Fix LDAP URL parsing regressions
  - libcurl: Stop reading from paused transfers
  - mprintf: Avoid unsigned integer overflow warning
  - netrc: Don't ignore the login name specified with "--user"
  - nss: Fall back to latest supported SSL version
  - nss: Fix compatibility with nss versions 3.14 to 3.15
  - nss: Fix fallthrough comment to fix picky compiler warning
  - nss: Remove version selecting dead code
  - nss: Set default max-tls to 1.3/1.2
  - openssl: Remove SSLEAY leftovers
  - openssl: Do not log excess "TLS app data" lines for TLS 1.3
  - openssl: Do not use file BIOs if not requested
  - openssl: Fix unused variable compiler warning with old openssl
  - openssl: Support session resume with TLS 1.3
  - openvms: Fix example name
  - os400: Add curl_easy_conn_upkeep() to ILE/RPG binding
  - os400: Add CURLOPT_CURLU to ILE/RPG binding
  - os400: Fix return type of curl_easy_pause() in ILE/RPG binding
  - packages: Remove old leftover files and dirs
  - pop3: Only do APOP with a valid timestamp
  - runtests: Use the local curl for verifying
  - schannel: Be consistent in Schannel capitalization
  - schannel: Better CURLOPT_CERTINFO support
  - schannel: Use Curl_ prefix for global private symbols
  - snprintf: Renamed and we now only use msnprintf()
  - ssl: Fix compilation with OpenSSL 0.9.7
  - ssl: Replace all internal uses of CURLE_SSL_CACERT
  - symbols-in-versions: Add missing CURLU_ symbols
  - test328: Verify Content-Encoding: none
  - tests: Disable SO_EXCLUSIVEADDRUSE for stunnel on Windows
  - tests: Drop http_pipe.py script, no longer used
  - tool_cb_wrt: Silence function cast compiler warning
  - tool_doswin: Fix uninitialized field warning
  - travis: Build with clang sanitizers
  - travis: Remove curl before a normal build
  - url: A short host name + port is not a scheme
  - url: Fix IPv6 numeral address parser
  - urlapi: Only skip encoding the first '=' with APPENDQUERY set
- Add workaround to avoid symbol lookup error in libstubgss.so (libtest)

* Tue Dec  4 2018 Paul Howarth <paul@city-fan.org> - 7.62.0-1.7.cf
- Work around TLS 1.3 being disabled in NSS in EL-7
  - https://github.com/curl/curl/issues/3261
  - https://github.com/curl/curl/pull/3337
- Only supported IDN library is libidn2, so don't bother trying to use
  libidn

* Wed Oct 31 2018 Paul Howarth <paul@city-fan.org> - 7.62.0-1.0.cf
- Update to 7.62.0
  - multiplex: Enable by default
  - url: Default to CURL_HTTP_VERSION_2TLS if built h2-enabled
  - setopt: Add CURLOPT_DOH_URL
  - curl: --doh-url added
  - setopt: Add CURLOPT_UPLOAD_BUFFERSIZE: set upload buffer size
  - imap: Change from "FETCH" to "UID FETCH"
  - configure: Add option to disable automatic OpenSSL config loading
  - upkeep: Add a connection upkeep API: curl_easy_upkeep()
  - URL-API: Added five new functions
  - vtls: MesaLink is a new TLS backend
  - Fix SASL password overflow via integer overflow (CVE-2018-16839)
  - Fix use-after-free in handle close (CVE-2018-16840)
  - Fix warning message out-of-buffer read (CVE-2018-16842)
  - CURLOPT_DNS_USE_GLOBAL_CACHE: deprecated
  - Curl_dedotdotify(): Always nul terminate returned string
  - Curl_follow: Always free the passed new URL
  - Curl_http2_done: Fix memleak in error path
  - Curl_retry_request: Fix memory leak
  - Curl_saferealloc: Fixed typo in docblock
  - FILE: Fix CURLOPT_NOBODY and CURLOPT_HEADER output
  - GnutTLS: TLS 1.3 support
  - SECURITY-PROCESS: Mention the bountygraph program
  - VS projects: Add USE_IPV6:
  - Windows: Fixes for MinGW targeting Windows Vista
  - anyauthput: Fix compiler warning on 64-bit Windows
  - appveyor: Add WinSSL builds
  - appveyor: Run test suite (on Windows!)
  - certs: Generate tests certs with sha256 digest algorithm
  - checksrc: Enable strict mode and warnings
  - checksrc: Handle zero scoped ignore commands
  - cmake: Backport to work with CMake 3.0 again
  - cmake: Improve config installation
  - cmake: Add support for transitive ZLIB target
  - cmake: Disable -Wpedantic-ms-format
  - cmake: Don't require OpenSSL if USE_OPENSSL=OFF
  - cmake: Fixed path used in generation of docs/tests
  - cmake: Remove unused *SOCKLEN_T variables
  - cmake: Suppress MSVC warning C4127 for libtest
  - cmake: Test and set missed defines during configuration
  - comment: Fix multiple typos in function parameters
  - config: Remove unused SIZEOF_VOIDP
  - config_win32: Enable LDAPS
  - configure: Force-use -lpthreads on HPUX
  - configure: Remove CURL_CONFIGURE_CURL_SOCKLEN_T
  - configure: s/AC_RUN_IFELSE/CURL_RUN_IFELSE/
  - cookies: Remove redundant expired check
  - cookies: Fix leak when writing cookies to file
  - curl-config.in: Remove dependency on bc
  - curl.1: --ipv6 mutexes ipv4 (fixed typo)
  - curl: Enabled Windows VT Support and UTF-8 output
  - curl: Update the documentation of --tlsv1.0
  - curl_multi_wait: Call getsock before figuring out timeout
  - curl_ntlm_wb: Check aprintf() return codes
  - curl_threads: Fix classic MinGW compile break
  - darwinssl: Fix realloc memleak
  - darwinssl: More specific and unified error codes
  - data-binary.d: Clarify default content-type is x-www-form-urlencoded
  - docs/BUG-BOUNTY: Explain the bounty program
  - docs/CIPHERS: Mention the options used to set TLS 1.3 ciphers
  - docs/CIPHERS: Fix the TLS 1.3 cipher names
  - docs/CIPHERS: Mention the colon separation for OpenSSL
  - docs/examples: URL updates
  - docs: Add "see also" links for SSL options
  - example/asiohiper: Insert warning comment about its status
  - example/htmltidy: Fix include paths of tidy libraries
  - examples/Makefile.m32: Sync with core
  - examples/http2-pushinmemory: Receive HTTP/2 pushed files in memory
  - examples/parseurl.c: Show off the URL API
  - examples: Fix memory leaks from realloc errors
  - examples: Do not wait when no transfers are running
  - ftp: Include command in Curl_ftpsend sendbuffer
  - gskit: Make sure to terminate version string
  - gtls: Values stored to but never read
  - hostip: Fix check on Curl_shuffle_addr return value
  - http2: Fix memory leaks on error-path
  - http: Fix memleak in rewind error path
  - krb5: Fix memory leak in krb_auth
  - ldap: Show precise LDAP call in error message on Windows
  - lib: Fix gcc8 warning on Windows
  - memory: Add missing curl_printf header
  - memory: Ensure to check allocation results
  - multi: Fix error handling in the SENDPROTOCONNECT state
  - multi: Fix memory leak in content encoding related error path
  - multi: Make the closure handle "inherit" CURLOPT_NOSIGNAL
  - netrc: Free temporary strings if memory allocation fails
  - nss: Fix nssckbi module loading on Windows
  - nss: Try to connect even if libnssckbi.so fails to load
  - ntlm_wb: Fix memory leaks in ntlm_wb_response
  - ntlm_wb: Bail out if the response gets overly large
  - openssl: Assume engine support in 0.9.8 or later
  - openssl: Enable TLS 1.3 post-handshake auth
  - openssl: Fix gcc8 warning
  - openssl: Load built-in engines too
  - openssl: Make 'done' a proper boolean
  - openssl: Output the correct cipher list on TLS 1.3 error
  - openssl: Return CURLE_PEER_FAILED_VERIFICATION on failure to parse issuer
  - openssl: Show "proper" version number for libressl builds
  - pipelining: Deprecated
  - rand: Add comment to skip a clang-tidy false positive
  - rtmp: Fix for compiling with lwIP
  - runtests: Ignore disabled even when ranges are given
  - runtests: Skip ld_preload tests on macOS
  - runtests: Use Windows paths for Windows curl
  - schannel: Unified error code handling
  - sendf: Fix whitespace in infof/failf concatenation
  - ssh: free the session on init failures
  - ssl: Deprecate CURLE_SSL_CACERT in favour of a unified error code
  - system.h: Use proper setting with Sun C++ as well
  - test1299: Use single quotes around asterisk
  - test1452: Mark as flaky
  - test1651: Unit test Curl_extract_certinfo()
  - test320: Strip out more HTML when comparing
  - tests/negtelnetserver.py: Fix Python2-ism in neg TELNET server
  - tests: Add unit tests for url.c
  - timeval: Fix use of weak symbol clock_gettime() on Apple platforms
  - tool_cb_hdr: Handle failure of rename()
  - travis: Add a "make tidy" build that runs clang-tidy
  - travis: Add build for "configure --disable-verbose"
  - travis: Bump the Secure Transport build to use xcode
  - travis: Make distcheck scan for BOM markers
  - unit1300: Fix stack-use-after-scope AddressSanitizer warning
  - urldata: Fix "connecting" comment
  - urlglob: Improve error message on bad globs
  - vtls: Fix ssl version "or later" behaviour change for many backends
  - x509asn1: Fix SAN IP address verification
  - x509asn1: Always check return code from getASN1Element()
  - x509asn1: Return CURLE_PEER_FAILED_VERIFICATION on failure to parse cert
  - x509asn1: Suppress left shift on signed value
- Test 656 segfaults on Fedora 13 to 15 inclusive, so disable it there

* Fri Oct 12 2018 Paul Howarth <paul@city-fan.org> - 7.61.1-3.0.cf
- Enable TLS 1.3 post-handshake auth in OpenSSL
- Update the documentation of --tlsv1.0 in curl(1) man page

* Fri Oct  5 2018 Paul Howarth <paul@city-fan.org> - 7.61.1-2.0.cf
- Enforce versioned libpsl dependency for libcurl (#1631804)
- test320: Update expected output for gnutls-3.6.4
- Drop 0105-curl-7.61.0-tests-ssh-keygen.patch, no longer needed (#1622594)
- test1456: Seems to be flaky so disable it

* Wed Sep  5 2018 Paul Howarth <paul@city-fan.org> - 7.61.1-1.0.cf
- Update to 7.61.1
  - Fix NTLM password overflow via integer overflow (CVE-2018-14618)
  - CURLINFO_SIZE_UPLOAD: Fix missing counter update
  - CURLOPT_ACCEPT_ENCODING.3: List them comma-separated
  - CURLOPT_SSL_CTX_FUNCTION.3: Might cause accidental connection reuse
  - Curl_getoff_all_pipelines: Improved for multiplexed
  - DEPRECATE: Remove release date from 7.62.0
  - HTTP: Don't attempt to needlessly decompress redirect body
  - INTERNALS: Require GnuTLS ≥ 2.11.3
  - README.md: Add LGTM.com code quality grade for C/C++
  - SSLCERTS: Improve the openssl command line
  - Silence GCC 8 cast-function-type warnings
  - ares: Check for NULL in completed-callback
  - asyn-thread: Remove unused macro
  - auth: Only pick CURLAUTH_BEARER if we *have* a Bearer token
  - auth: Pick Bearer authentication whenever a token is available
  - cmake: CMake config files are defining CURL_STATICLIB for static builds
  - cmake: Respect BUILD_SHARED_LIBS
  - cmake: Update scripts to use consistent style
  - cmake: Bumped minimum version to 3.4
  - cmake: Link curl to the OpenSSL targets instead of lib absolute paths
  - configure: Conditionally enable pedantic-errors
  - configure: Fix for -lpthread detection with OpenSSL and pkg-config
  - conn: Remove the boolean 'inuse' field
  - content_encoding: Accept up to 4 unknown trailer bytes after raw deflate data
  - cookie tests: Treat files as text
  - cookies: Support creation-time attribute for cookies
  - curl: Fix segfault when -H @headerfile is empty
  - curl: Add http code 408 to transient list for --retry
  - curl: Fix time-of-check, time-of-use race in dir creation
  - curl: Use Content-Disposition before the "URL end" for -OJ
  - curl: Warn the user if a given file name looks like an option
  - curl_threads: Silence bad-function-cast warning
  - darwinssl: Add support for ALPN negotiation
  - docs/CURLOPT_URL: Fix indentation
  - docs/CURLOPT_WRITEFUNCTION: Size is always 1
  - docs/SECURITY-PROCESS: Mention bounty, drop pre-notify
  - docs/examples: Add hiperfifo example using linux epoll/timerfd
  - docs: Add disallow-username-in-url.d and haproxy-protocol.d to dist
  - docs: Clarify NO_PROXY env variable functionality
  - docs: Improved the manual pages of some callbacks
  - docs: Mention NULL is fine input to several functions
  - formdata: Remove unused macro HTTPPOST_CONTENTTYPE_DEFAULT
  - gopher: Do not translate '?' to '%%09'
  - header output: Switch off all styles, not just unbold
  - hostip: Fix unused variable warning
  - http2: Use correct format identifier for stream_id
  - http2: Abort the send_callback if not setup yet
  - http2: Avoid set_stream_user_data() before stream is assigned
  - http2: Check nghttp2_session_set_stream_user_data return code
  - http2: Clear the drain counter in Curl_http2_done
  - http2: Make sure to send after RST_STREAM
  - http2: Separate easy handle from connections better
  - http: Fix for tiny "HTTP/0.9" response
  - http_proxy: Remove unused macro SELECT_TIMEOUT
  - lib/Makefile: Only do symbol hiding if told to
  - lib1502: Fix memory leak in torture test
  - lib1522: Fix curl_easy_setopt argument type
  - libcurl-thread.3: Expand somewhat on the NO_SIGNAL motivation
  - mime: Check Curl_rand_hex's return code
  - multi: Always do the COMPLETED procedure/state
  - openssl: Assume engine support in 1.0.0 or later
  - openssl: Fix debug messages
  - projects: Improve Windows perl detection in batch scripts
  - retry: Return error if rewind was necessary but didn't happen
  - reuse_conn(): Memory leak - free old_conn->options
  - schannel: Client certificate store opening fix
  - schannel: Enable CALG_TLS1PRF for w32api ≥ 5.1
  - schannel: Fix MinGW compile break
  - sftp: Don't send post-quote sequence when retrying a connection
  - smb: Fix memory leak on early failure
  - smb: Fix memory-leak in URL parse error path
  - smb_getsock: Always wait for write socket too
  - ssh-libssh: Fix infinite connect loop on invalid private key
  - ssh-libssh: Reduce excessive verbose output about pubkey auth
  - ssh-libssh: Use FALLTHROUGH to silence gcc8
  - ssl: Set engine implicitly when a PKCS#11 URI is provided
  - sws: Handle EINTR when calling select()
  - system_win32: Fix version checking
  - telnet: Remove unused macros TELOPTS and TELCMDS
  - test1143: Disable MSYS2's POSIX path conversion
  - test1148: Disable if decimal separator is not point
  - test1307: (fnmatch testing) disabled
  - test1422: Add required file feature
  - test1531: Add timeout
  - test1540: Remove unused macro TEST_HANG_TIMEOUT
  - test214: Disable MSYS2's POSIX path conversion for URL
  - test320: Treat curl320.out file as binary
  - tests/http_pipe.py: Use /usr/bin/env to find python
  - tests: Don't use Windows path %%PWD for SSH tests
  - tests: Fixes for Windows line endings
  - tool_operate: Fix setting proxy TLS 1.3 ciphers
  - travis: Build darwinssl on macos 10.12 to fix linker errors
  - travis: Execute "set -eo pipefail" for coverage build
  - travis: Run a 'make checksrc' too
  - travis: Update to GCC-8
  - travis: Verify that man pages can be regenerated
  - upload: Allocate upload buffer on-demand
  - upload: Change default UPLOAD_BUFSIZE to 64KB
  - urldata: Remove unused pipe_broke struct field
  - vtls: Re-instantiate engine on duplicated handles
  - windows: Implement send buffer tuning
  - wolfSSL/CyaSSL: Fix memory leak in Curl_cyassl_random

* Tue Sep  4 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-8.0.cf
- Make the --tls13-ciphers option work

* Tue Aug 28 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-7.0.cf
- tests: Make ssh-keygen always produce PEM format (#1622594)

* Wed Aug 15 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-6.0.cf
- scp/sftp: Fix infinite connect loop on invalid private key (#1595135)

* Mon Aug 13 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-5.0.cf
- ssl: Set engine implicitly when a PKCS#11 URI is provided (#1219544)
- Relax crypto policy for the test-suite to make it pass again (#1610888)

* Tue Jul 31 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-3.0.cf
- Adapt test 323 for updated OpenSSL

* Fri Jul 13 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-2.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Wed Jul 11 2018 Paul Howarth <paul@city-fan.org> - 7.61.0-1.0.cf
- Update to 7.61.0
  - CVE-2018-0500: smtp: Fix SMTP send buffer overflow
  - getinfo: Add microsecond precise timers for seven intervals
  - curl: Show headers in bold, switch off with --no-styled-output
  - httpauth: Add support for Bearer tokens
  - Add CURLOPT_TLS13_CIPHERS and CURLOPT_PROXY_TLS13_CIPHERS
  - curl: --tls13-ciphers and --proxy-tls13-ciphers
  - Add CURLOPT_DISALLOW_USERNAME_IN_URL
  - curl: --disallow-username-in-url
  - schannel: Disable client cert option if APIs not available
  - schannel: Disable manual verify if APIs not available
  - tests/libtest/Makefile: Do not unconditionally add gcc-specific flags
  - openssl: Acknowledge --tls-max for default version too
  - stub_gssapi: Fix 'unused parameter' warnings
  - examples/progressfunc: Make it build on both new and old libcurls
  - docs: Mention it is HA Proxy protocol "version 1"
  - curl_fnmatch: Only allow two asterisks for matching
  - docs: Clarify CURLOPT_HTTPGET
  - configure: Replace a AC_TRY_RUN with CURL_RUN_IFELSE
  - configure: Do compile-time SIZEOF checks instead of run-time
  - checksrc: Make sure sizeof() is used *with* parentheses
  - CURLOPT_ACCEPT_ENCODING.3: Add brotli and clarify a bit
  - schannel: Make CAinfo parsing resilient to CR/LF
  - tftp: Make sure error is zero terminated before printfing it
  - http resume: Skip body if http code 416 (range error) is ignored
  - configure: Add basic test of --with-ssl prefix
  - cmake: Set -d postfix for debug builds
  - multi: Provide a socket to wait for in Curl_protocol_getsock
  - content_encoding: Handle zlib versions too old for Z_BLOCK
  - winbuild: Only delete OUTFILE if it exists
  - winbuild: In MakefileBuild.vc fix typo DISTDIR->DIRDIST
  - schannel: Add failf calls for client certificate failures
  - cmake: Fix the test for fsetxattr and strerror_r
  - curl.1: Fix cmdline-opts reference errors
  - cmdline-opts/gen.pl: Warn if mutexes: or see-also: list non-existing options
  - cmake: Check for getpwuid_r
  - configure: Fix ssh2 linking when built with a static mbedtls
  - psl: Use latest psl and refresh it periodically
  - fnmatch: Insist on escaped bracket to match
  - KNOWN_BUGS: Restore text regarding #2101
  - INSTALL: LDFLAGS=-Wl,-R/usr/local/ssl/lib
  - configure: Override AR_FLAGS to silence warning
  - os400: Implement mime api EBCDIC wrappers
  - curl.rc: Embed manifest for correct Windows version detection
  - strictness: Correct {infof, failf} format specifiers
  - tests: Update .gitignore for libtests
  - configure: Check for declaration of getpwuid_r
  - fnmatch: Use the system one if available
  - CURLOPT_RESOLVE: Always purge old entry first
  - multi: Remove a potentially bad DEBUGF()
  - curl_addrinfo: Use same #ifdef conditions in source as header
  - build: Remove the Borland specific makefiles
  - axTLS: Not considered fit for use
  - cmdline-opts/cert-type.d: Mention "p12" as a recognized type
  - system.h: Add support for IBM xlc C compiler
  - tests/libtest: Add lib1521 to nodist_SOURCES
  - mk-ca-bundle.pl: Leave certificate name untouched
  - boringssl + schannel: undef X509_NAME in lib/schannel.h
  - openssl: Assume engine support in 1.0.1 or later
  - cppcheck: Fix warnings
  - test 46: Make test pass after year 2025
  - schannel: Support selecting ciphers
  - Curl_debug: Remove dead printhost code
  - test 1455: Unflakified
  - Curl_init_do: Handle NULL connection pointer passed in
  - progress: Remove a set of unused defines
  - mk-ca-bundle.pl: Make -u delete certdata.txt if found not changed
  - GOVERNANCE.md: Explains how this project is run
  - configure: Use pkg-config for c-ares detection
  - configure: Enhance ability to build with static openssl
  - maketgz: Fix sed issues on OSX
  - multi: Fix memory leak when stopped during name resolve
  - CURLOPT_INTERFACE.3: Interface names not supported on Windows
  - url: Fix dangling conn->data pointer
  - cmake: Allow multiple SSL backends
  - system.h: Fix for gcc on 32 bit OpenServer
  - ConnectionExists: Make sure conn->data is set when "taking" a connection
  - multi: Fix crash due to dangling entry in connect-pending list
  - CURLOPT_SSL_VERIFYPEER.3: Add performance note
  - netrc: Use a larger buffer to support longer passwords 
  - url: Check Curl_conncache_add_conn return code
  - configure: Add dependent libraries after crypto
  - easy_perform: Faster local name resolves by using *multi_timeout()
  - getnameinfo: Not used, removed all configure checks
  - travis: Add a build using the synchronous name resolver
  - CURLINFO_TLS_SSL_PTR.3: Improve the example
  - openssl: Allow TLS 1.3 by default
  - openssl: Make the requested TLS version the *minimum* wanted
  - openssl: Remove some dead code
  - telnet: Fix clang warnings
  - DEPRECATE: New doc describing planned item removals
  - example/crawler.c: Simple crawler based on libxml2
  - libssh: Goto DISCONNECT state on error, not SESSION_FREE
  - CMake: Remove unused functions
  - darwinssl: Allow High Sierra users to build the code using GCC
  - scripts: Include _curl as part of CLEANFILES
  - examples: Fix -Wformat warnings
  - curl_setup: Include <winerror.h> before <windows.h>
  - schannel: Make more cipher options conditional
  - CMake: Remove redundant and old end-of-block syntax
  - post303.d: Clarify that this is an RFC violation
- Add patch to fix builds with openssl < 1.0.1

* Tue Jul 10 2018 Paul Howarth <paul@city-fan.org> - 7.60.0-3.0.cf
- Disable flaky test 1455
- Enable support for brotli compression in libcurl-full from F-29 onwards

* Wed Jul  4 2018 Paul Howarth <paul@city-fan.org> - 7.60.0-2.0.cf
- Do not hard-wire path of the Python 3 interpreter

* Wed May 16 2018 Paul Howarth <paul@city-fan.org> - 7.60.0-1.0.cf
- Update to 7.60.0
  - Add CURLOPT_HAPROXYPROTOCOL, support for the HAProxy PROXY protocol
  - Add --haproxy-protocol for the command line tool
  - Add CURLOPT_DNS_SHUFFLE_ADDRESSES, shuffle returned IP addresses
  - FTP: Shutdown response buffer overflow CVE-2018-1000300
  - RTSP: Bad headers buffer over-read CVE-2018-1000301
  - FTP: Fix typo in recursive callback detection for seeking
  - test1208: Marked flaky
  - HTTP: Make header-less responses still count correct body size
  - user-agent.d: Mention --proxy-header as well
  - http2: fixes typo
  - cleanup: Misc typos in strings and comments
  - rate-limit: Use three second window to better handle high speeds
  - examples/hiperfifo.c: Improved
  - pause: When changing pause state, update socket state
  - multi: Improved pending transfers handling ⇒ improved performance
  - curl_version_info.3: Fix ssl_version description
  - add_handle/easy_perform: Clear errorbuffer on start if set
  - darwinssl: Fix iOS build
  - cmake: Add support for brotli
  - parsedate: Support UT timezone
  - vauth/ntlm.h: Fix the #ifdef header guard
  - lib/curl_path.h: Added #ifdef header guard
  - vauth/cleartext: Fix integer overflow check
  - CURLINFO_COOKIELIST.3: Made the example not leak memory
  - cookie.d: Mention that "-" as filename means stdin
  - CURLINFO_SSL_VERIFYRESULT.3: Fixed the example
  - http2: Read pending frames (including GOAWAY) in connection-check
  - timeval: Remove compilation warning by casting
  - cmake: Avoid warn-as-error during config checks
  - travis-ci: Enable -Werror for CMake builds
  - openldap: Fix for NULL return from ldap_get_attribute_ber()
  - threaded resolver: Track resolver time and set suitable timeout values
  - cmake: Add advapi32 as explicit link library for win32
  - docs: Fix CURLINFO_*_T examples use of CURL_FORMAT_CURL_OFF_T
  - test1148: Set a fixed locale for the test
  - cookies: When reading from a file, only remove_expired once
  - cookie: Store cookies per top-level-domain-specific hash table
  - openssl: Fix build with LibreSSL 2.7
  - tls: Fix mbedTLS 2.7.0 build + handle sha256 failures
  - openssl: RESTORED verify locations when verifypeer==0
  - file: Restore old behaviour for file:////foo/bar URLs
  - FTP: Allow PASV on IPv6 connections when a proxy is being used
  - build-openssl.bat: Allow custom paths for VS and perl
  - winbuild: Make the clean target work without build-type
  - build-openssl.bat: Refer to VS2017 as VC14.1 instead of VC15
  - curl: Retry on FTP 4xx, ignore other protocols
  - configure: Detect (and use) sa_family_t
  - examples/sftpuploadresume: Fix Windows large file seek
  - build: Clean up to fix clang warnings/errors
  - winbuild: Updated the documentation
  - lib: Silence null-dereference warnings
  - travis: Bump to clang 6 and gcc 7
  - travis: Build libpsl and make builds use it
  - proxy: Show getenv proxy use in verbose output
  - duphandle: Make sure CURLOPT_RESOLVE is duplicated
  - all: Refactor malloc+memset to use calloc
  - checksrc: Fix typo
  - system.h: Add sparcv8plus to oracle/sunpro 32-bit detection
  - vauth: Fix typo
  - ssh: Show libSSH2 error code when closing fails
  - test1148: Tolerate progress updates better
  - urldata: Make service names unconditional
  - configure: Keep LD_LIBRARY_PATH changes local
  - ntlm_sspi: Fix authentication using Credential Manager
  - schannel: Add client certificate authentication
  - winbuild: Support custom devel paths for each dependency
  - schannel: Add support for CURLOPT_CAINFO
  - http2: Handle on_begin_headers() called more than once
  - openssl: Support OpenSSL 1.1.1 verbose-mode trace messages
  - openssl: Fix subjectAltName check on non-ASCII platforms
  - http2: Avoid strstr() on data not zero terminated
  - http2: Clear the "drain counter" when a stream is closed
  - http2: Handle GOAWAY properly
  - tool_help: Clarify --max-time unit of time is seconds
  - curl.1: Clarify that options and URLs can be mixed
  - http2: Convert an assert to run-time check
  - curl_global_sslset: Always provide available backends
  - ftplistparser: Keep state between invokes
  - Curl_memchr: Zero length input can't match
  - examples/sftpuploadresume: typecast fseek argument to long
  - examples/http2-upload: Expand buffer to avoid silly warning
  - ctype: Restore character classification for non-ASCII platforms
  - mime: Avoid NULL pointer dereference risk
  - cookies: Ensure that we have cookies before writing jar
  - os400.c: Fix checksrc warnings
  - configure: Provide --with-wolfssl as an alias for --with-cyassl
  - cyassl: Adapt to libraries without TLS 1.0 support built-in
  - http2: Get rid of another strstr
  - checksrc: Force indentation of lines after an else
  - cookies: Remove unused macro
  - CURLINFO_PROTOCOL.3: Mention the existing defined names
  - tests: Provide 'manual' as a feature to optionally require
  - travis: Enable libssh2 on both macos and Linux
  - CURLOPT_URL.3: Added ENCODING section
  - wolfssl: Fix non-blocking connect
  - vtls: Don't define MD5_DIGEST_LENGTH for wolfssl
  - docs: Remove extraneous commas in man pages
  - URL: Fix ASCII dependency in strcpy_url and strlen_url
  - ssh-libssh.c: Fix left shift compiler warning
  - configure: Only check for CA bundle for file-using SSL backends
  - travis: Add an mbedtls build
  - http: Don't set the "rewind" flag when not uploading anything
  - configure: Put CURLDEBUG and DEBUGBUILD in lib/curl_config.h
  - transfer: Don't unset writesockfd on setup of multiplexed conns
  - vtls: Use unified "supports" bitfield member in backends
  - URLs: Fix one more http url
  - travis: Add a build using WolfSSL
  - openssl: Change FILE ops to BIO ops
  - travis: Add build using NSS
  - smb: Reject negative file sizes
  - cookies: Accept parameter names as cookie name
  - http2: getsock fix for uploads
  - All over: Fixed format specifiers
  - http2: Use the correct function pointer typedef

* Thu Mar 15 2018 Paul Howarth <paul@city-fan.org> - 7.59.0-3.0.cf
- Run the test suite using Python 3 from Fedora 28 onwards

* Wed Mar 14 2018 Paul Howarth <paul@city-fan.org> - 7.59.0-2.0.cf
- ftp: Fix typo in recursive callback detection for seeking

* Wed Mar 14 2018 Paul Howarth <paul@city-fan.org> - 7.59.0-1.0.cf
- Update to 7.59.0
  - curl: Add --proxy-pinnedpubkey
  - Added: CURLOPT_TIMEVALUE_LARGE and CURLINFO_FILETIME_T
  - CURLOPT_RESOLVE: Add support for multiple IP addresses per entry
  - Add option CURLOPT_HAPPY_EYEBALLS_TIMEOUT_MS
  - Add new tool option --happy-eyeballs-timeout-ms
  - Add CURLOPT_RESOLVER_START_FUNCTION and CURLOPT_RESOLVER_START_DATA
  - openldap: Check ldap_get_attribute_ber() results for NULL before using
    (fixes CVE-2018-1000121)
  - FTP: Reject path components with control codes (fixes CVE-2018-1000120)
  - readwrite: Make sure excess reads don't go beyond buffer end (fixes
    CVE-2018-1000122)
  - lib555: Drop text conversion and encode data as ASCII codes
  - lib517: Make variable static to avoid compiler warning
  - lib544: Sync ASCII code data with textual data
  - GSKit: Restore pinnedpubkey functionality
  - darwinssl: Don't import client certificates into Keychain on macOS
  - parsedate: Fix date parsing for systems with 32 bit long
  - openssl: Fix pinned public key build error in FIPS mode
  - SChannel/WinSSL: Implement public key pinning
  - cookies: Remove verbose "cookie size:" output
  - progress-bar: Don't use stderr explicitly, use bar->out
  - Fixes for MSDOS
  - build: Open VC15 projects with VS 2017
  - curl_ctype: Private is*() type macros and functions
  - configure: Set PATH_SEPARATOR to colon for PATH w/o separator
  - winbuild: Make linker generate proper PDB
  - curl_easy_reset: Clear digest auth state
  - curl/curl.h: Fix comment typo for CURLOPT_DNS_LOCAL_IP6
  - range: Commonize FTP and FILE range handling
  - progress-bar docs: Update to match implementation
  - fnmatch: Do not match the empty string with a character set
  - fnmatch: Accept an alphanum to be followed by a non-alphanum in char set
  - build: Fix termios issue on android cross-compile
  - getdate: Return -1 for out of range
  - formdata: Use the mime-content type function
  - time-cond: Fix reading the file modification time on Windows
  - build-openssl.bat: Extend VC15 support to include Enterprise and Professional
  - build-wolfssl.bat: Extend VC15 support to include Enterprise and Professional
  - openssl: Don't add verify locations when verifypeer==0
  - fnmatch: Optimize processing of consecutive *s and ?s pattern characters
  - schannel: Fix compiler warnings
  - content_encoding: Add "none" alias to "identity"
  - get_posix_time: Only check for overflows if they can happen
  - http_chunks: Don't write chunks twice with CURLOPT_HTTP_TRANSFER_DECODING
  - README: Language fix
  - sha256: Build with OpenSSL < 0.9.8
  - smtp: Fix processing of initial dot in data
  - --tlsauthtype: Works only if libcurl is built with TLS-SRP support
  - tests: New tests for http raw mode
  - libcurl-security.3: man page discussion security concerns when using libcurl
  - curl_gssapi: Make sure this file too uses our *printf()
  - BINDINGS: Fix curb link (and remove ruby-curl-multi)
  - nss: Use PK11_CreateManagedGenericObject() if available
  - travis: Add build with iconv enabled
  - ssh: Add two missing state names
  - CURLOPT_HEADERFUNCTION.3: Mention folded headers
  - http: Fix the max header length detection logic
  - header callback: Don't chop headers into smaller pieces
  - CURLOPT_HEADER.3: Clarify problems with different data sizes
  - curl --version: Show PSL if the run-time lib has it enabled
  - examples/sftpuploadresume: Resume upload via CURLOPT_APPEND
  - Return error if called recursively from within callbacks
  - sasl: Prefer PLAIN mechanism over LOGIN
  - winbuild: Use CALL to run batch scripts
  - curl_share_setopt.3: Connection cache is shared within multi handles
  - winbuild: Use macros for the names of some build utilities
  - projects/README: Remove reference to dead IDN link/package
  - lib655: Silence compiler warning
  - configure: Fix version check for OpenSSL 1.1.1
  - docs/MANUAL: formfind.pl is not accessible on the site anymore
  - unit1309: Fix warning on Windows x64
  - unit1307: Proper cleanup on OOM to fix torture tests
  - curl_ctype: Fix macro redefinition warnings
  - build: Get CFLAGS (including -werror) used for examples and tests
  - NO_PROXY: Fix for IPv6 numericals in the URL
  - krb5: Use nondeprecated functions
  - winbuild: Prefer documented zlib library names
  - http2: Mark the connection for close on GOAWAY
  - limit-rate: Kick in even before "limit" data has been received
  - HTTP: Allow "header;" to replace an internal header with a blank one
  - http2: Verbose output new MAX_CONCURRENT_STREAMS values
  - SECURITY: Distros' max embargo time is 14 days
  - curl tool: Accept --compressed also if Brotli is enabled and zlib is not
  - WolfSSL: Adding TLSv1.3
  - checksrc.pl: Add -i and -m options
  - CURLOPT_COOKIEFILE.3: "-" as file name means stdin

* Mon Mar 12 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-8.0.cf
- http2: mark the connection for close on GOAWAY

* Mon Feb 19 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-7.0.cf
- Add explicitly-used build requirements
- Fix libcurl soname version number in %%files list to avoid accidental soname
  bumps

* Thu Feb 15 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-6.0.cf
- Drop ldconfig scriptlets from Fedora 28 onwards

* Tue Feb 13 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-5.0.cf
- Drop temporary work around for ICE on x86_64 (#1540549)

* Fri Feb  9 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-4.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Jan 31 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-3.0.cf
- Temporarily work around internal compiler error on x86_64 (#1540549)
- Disable brp-ldconfig to make RemovePathPostfixes work with shared libs again

* Thu Jan 25 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-2.0.cf
- Use libssh (instead of libssh2) to implement SCP/SFTP in libcurl from
  Fedora 28 onwards (#1531483)

* Wed Jan 24 2018 Paul Howarth <paul@city-fan.org> - 7.58.0-1.0.cf
- Update to 7.58.0
  - New libssh-powered SSH SCP/SFTP back-end
  - curl-config: Add --ssl-backends
  - http2: Fix incorrect trailer buffer size (CVE-2018-1000005)
  - http: Prevent custom Authorization headers in redirects (CVE-2018-1000007)
  - travis: Add boringssl build
  - examples/xmlstream.c: Don't switch off CURL_GLOBAL_SSL
  - SSL: Avoid magic allocation of SSL backend specific data
  - lib: Don't export all symbols, just everything curl_*
  - libssh2: Send the correct CURLE error code on scp file not found
  - libssh2: Return CURLE_UPLOAD_FAILED on failure to upload
  - openssl: Enable pkcs12 in boringssl builds
  - libssh2: Remove dead code from SSH_SFTP_QUOTE
  - sasl_getmessage: Make sure we have a long enough string to pass
  - conncache: Fix several lock issues
  - threaded-shared-conn.c: New example
  - conncache: Only allow multiplexing within same multi handle
  - configure: Check for netinet/in6.h
  - URL: Tolerate backslash after drive letter for FILE:
  - openldap: Add commented out debug possibilities
  - include: Get netinet/in.h before linux/tcp.h
  - CONNECT: Keep close connection flag in http_connect_state struct
  - BINDINGS: Another PostgreSQL client
  - curl: Limit -# update frequency for unknown total size
  - configure: Add AX_CODE_COVERAGE only if using gcc
  - curl.h: Remove incorrect comment about ERRORBUFFER
  - openssl: Improve data-pending check for https proxy
  - curl: Remove __EMX__ #ifdefs
  - CURLOPT_PRIVATE.3: Fix grammar
  - sftp: Allow quoted commands to use relative paths
  - CURLOPT_DNS_CACHE_TIMEOUT.3: See also CURLOPT_RESOLVE
  - RESOLVE: Output verbose text when trying to set a duplicate name
  - openssl: Disable file buffering for Win32 SSLKEYLOGFILE
  - multi_done: Prune DNS cache
  - tests: Update .gitignore for libtests
  - tests: Mark data files as non-executable in git
  - CURLOPT_DNS_LOCAL_IP4.3: Fixed the "SEE ALSO" to not self-reference
  - curl.1: Documented two missing valid exit codes
  - curl.1: Mention http:// and https:// as valid proxy prefixes
  - vtls: Replaced getenv() with curl_getenv()
  - setopt: Less *or equal* than INT_MAX/1000 should be fine
  - examples/smtp-mail.c: Use separate defines for options and mail
  - curl: Support >256 bytes warning messages
  - conncache: Fix a return code
  - krb5: Fix a potential access of uninitialized memory
  - rand: Add a clang-analyzer work-around
  - CURLOPT_READFUNCTION.3: Refer to argument with correct name
  - brotli: Allow compiling with version 0.6.0
  - content_encoding: Rework zlib_inflate
  - curl_easy_reset: Release mime-related data
  - examples/rtsp: Fix error handling macros
  - build-openssl.bat: Added support for VC15
  - build-wolfssl.bat: Added support for VC15
  - build: Added Visual Studio 2017 project files
  - winbuild: Added support for VC15
  - curl: Support size modifiers for --max-filesize
  - examples/cacertinmem: Ignore cert-already-exists error
  - brotli: Data at the end of content can be lost
  - curl_version_info.3: Call the argument 'age'
  - openssl: Fix memory leak of SSLKEYLOGFILE filename
  - build: Remove HAVE_LIMITS_H check
  - --mail-rcpt: Fix short-text description
  - scripts: Allow all perl scripts to be run directly
  - progress: Calculate transfer speed on milliseconds if possible
  - system.h: Check __LONG_MAX__ for defining curl_off_t
  - easy: Fix connection ownership in curl_easy_pause
  - setopt: Reintroduce non-static Curl_vsetopt() for OS400 support
  - setopt: Fix SSLVERSION to allow CURL_SSLVERSION_MAX_ values
  - configure.ac: Append extra linker flags instead of prepending them
  - HTTP: Bail out on negative Content-Length: values
  - docs: Comment about CURLE_READ_ERROR returned by curl_mime_filedata
  - mime: Clone mime tree upon easy handle duplication
  - openssl: Enable SSLKEYLOGFILE support by default
  - smtp/pop3/imap_get_message: Decrease the data length too...
  - CURLOPT_TCP_NODELAY.3: Fix typo
  - SMB: Fix numeric constant suffix and variable types
  - ftp-wildcard: Fix matching an empty string with "*[^a]"
  - curl_fnmatch: only allow 5 '*' sections in a single pattern
  - openssl: Fix potential memory leak in SSLKEYLOGFILE logic
  - SSH: Fix state machine for ssh-agent authentication
  - examples/url2file.c: Add missing curl_global_cleanup() call
  - http2: Don't close connection when single transfer is stopped
  - libcurl-env.3: First version
  - curl: Progress bar refresh, get width using ioctl()
  - CONNECT_TO: Fail attempt to set an IPv6 numerical without IPv6 support

* Wed Nov 29 2017 Paul Howarth <paul@city-fan.org> - 7.57.0-1.0.cf
- Update to 7.57.0
  - auth: Add support for RFC7616 - HTTP Digest access authentication
  - share: Add support for sharing the connection cache
  - HTTP: Implement Brotli content encoding
  - Fix CVE-2017-8816: NTLM buffer overflow via integer overflow
  - Fix CVE-2017-8817: FTP wildcard out of bounds read
  - Fix CVE-2017-8818: SSL out of buffer access
  - curl_mime_filedata.3: Fix typos
  - libtest: Add required test libraries for lib1552 and lib1553
  - Fix time diffs for systems using unsigned time_t
  - ftplistparser: Memory leak fix: always free temporary memory
  - multi: Allow table handle sizes to be overridden
  - wildcards: Don't use with non-supported protocols
  - curl_fnmatch: Return error on illegal wildcard pattern
  - transfer: Fix chunked-encoding upload too early exit
  - curl_setup: Improve detection of CURL_WINDOWS_APP
  - resolvers: Only include anything if needed
  - setopt: Fix CURLOPT_SSH_AUTH_TYPES option read
  - appveyor: Add a win32 build
  - Curl_timeleft: Change return type to timediff_t
  - cmake: Export libcurl and curl targets to use by other cmake projects
  - curl: In -F option arg, comma is a delimiter for files only
  - curl: Improved ";type=" handling in -F option arguments
  - timeval: Use mach_absolute_time() on MacOS
  - curlx: The timeval functions are no longer provided as curlx_*
  - mkhelp.pl: Do not generate comment with current date
  - memdebug: Use send/recv signature for curl_dosend/curl_dorecv
  - cookie: Avoid NULL dereference
  - url: Fix CURLOPT_POSTFIELDSIZE arg value check to allow -1
  - include: Remove conncache.h inclusion from where it's not needed
  - CURLOPT_MAXREDIRS: Allow -1 as a value
  - tests: Fixed torture tests on tests 556 and 650
  - http2: Fixed OOM handling in upgrade request
  - url: Fix CURLOPT_DNS_CACHE_TIMEOUT arg value check to allow -1
  - CURLOPT_INFILESIZE: Accept -1
  - curl: Pass through [] in URLs instead of calling globbing error
  - curl: Speed up handling of many URLs
  - ntlm: Avoid malloc(0) for zero length passwords
  - url: Remove faulty arg value check from CURLOPT_SSH_AUTH_TYPES
  - HTTP: Support multiple Content-Encodings
  - travis: Add a job with brotli enabled
  - url: Remove unnecessary NULL-check
  - fnmatch: Remove dead code
  - connect: Store IPv6 connection status after valid connection
  - imap: Deal with commands case insensitively
  - --interface: Add support for Linux VRF
  - content_encoding: Fix inflate_stream for no bytes available
  - cmake: Correctly include curl.rc in Windows builds
  - cmake: Add missing setmode check
  - connect.c: Remove executable bit on file
  - SMB: Fix uninitialized local variable
  - zlib/brotli: Only include header files in modules needing them
  - URL: Return error on malformed URLs with junk after IPv6 bracket
  - openssl: Fix too broad use of HAVE_OPAQUE_EVP_PKEY
  - macOS: Fix missing connectx function with Xcode version older than 9.0
  - --resolve: Allow IP address within [] brackets
  - examples/curlx: Fix code style
  - ntlm: Remove unnecessary NULL-check to please scan-build
  - Curl_llist_remove: Fix potential NULL pointer deref
  - mime: Fix "Value stored to 'sz' is never read" scan-build error
  - openssl: Fix "Value stored to 'rc' is never read" scan-build error
  - http2: Fix "Value stored to 'hdbuf' is never read" scan-build error
  - http2: Fix "Value stored to 'end' is never read" scan-build error
  - Curl_open: Fix OOM return error correctly
  - url: Reject ASCII control characters and space in host names
  - examples/rtsp: Clear RANGE again after use
  - connect: Improve the bind error message
  - make: Fix "make distclean"
  - connect: Add support for new TCP Fast Open API on Linux
  - metalink: Fix memory leak and NULL pointer dereference
  - URL: Update "file:" URL handling
  - ssh: Remove check for a NULL pointer
  - global_init: Ignore CURL_GLOBAL_SSL's absence

* Mon Oct 23 2017 Paul Howarth <paul@city-fan.org> - 7.56.1-1.0.cf
- Update to 7.56.1
  - imap: If a FETCH response has no size, don't call write callback
    (CVE-2017-1000257)
  - ftp: UBsan fixup 'pointer index expression overflowed
  - failf: Skip the sprintf() if there are no consumers
  - fuzzer: Move to using external curl-fuzzer
  - lib/Makefile.m32: Allow customizing dll suffixes
  - docs: Fix typo in curl_mime_data_cb man page
  - darwinssl: Add support for TLSv1.3
  - build: Fix --disable-crypto-auth
  - lib/config-win32.h: Let SMB/SMBS be enabled with OpenSSL/NSS
  - openssl: Fix build without HAVE_OPAQUE_EVP_PKEY
  - strtoofft: Remove extraneous null check
  - multi_cleanup: Call DONE on handles that never got that
  - tests: Added flaky keyword to tests 587 and 644
  - pingpong: Return error when trying to send without connection
  - remove_handle: Call multi_done() first, then clear dns cache pointer
  - mime: Be tolerant about setting twice the same header list in a part
  - mime: Improve unbinding top multipart from easy handle.
  - mime: Avoid resetting a part's encoder when part's contents change
  - mime: Refuse to add subparts to one of their own descendants
  - RTSP: Avoid integer overflow on funny RTSP responses
  - curl: Don't pass semicolons when parsing Content-Disposition
  - openssl: Enable PKCS12 support for !BoringSSL
  - FAQ: s/CURLOPT_PROGRESSFUNCTION/CURLOPT_XFERINFOFUNCTION
  - CURLOPT_NOPROGRESS.3: Also refer to xferinfofunction
  - CURLOPT_XFERINFODATA.3: Fix duplicate see also
  - test298: Verify --ftp-method nowcwd with URL encoded path
  - FTP: URL decode path for dir listing in nocwd mode
  - smtp_done: Fix memory leak on send failure
  - ftpserver: Support case insensitive commands
  - test950: Verify SMTP with custom request
  - openssl: Don't use old BORINGSSL_YYYYMM macros
  - setopt: Update current connection SSL verify params
  - winbuild/BUILD.WINDOWS.txt: Mention WITH_NGHTTP2
  - curl: Reimplement stdin buffering in -F option
  - mime: Keep "text/plain" content type if user-specified
  - mime: Fix the content reader to handle >16K data properly
  - configure: Remove the C++ compiler check
  - memdebug: Trace send, recv and socket
  - runtests: Use valgrind for torture as well
  - ldap: Silence clang warning
  - makefile.m32: Allow to override gcc, ar and ranlib
  - setopt: Avoid integer overflows when setting millsecond values
  - setopt: Range check most long options
  - ftp: Reject illegal IP/port in PASV 227 response
  - mime: Do not reuse previously computed multipart size
  - vtls: Change struct Curl_ssl 'close' field name to 'close_one'
  - os400: Add missing symbols in config file
  - mime: Limit bas64-encoded lines length to 76 characters
  - mk-ca-bundle: Remove URL for aurora
  - mk-ca-bundle: Fix URL for NSS

* Wed Oct  4 2017 Paul Howarth <paul@city-fan.org> - 7.56.0-1.0.cf
- Update to 7.56.0
  - curl: Enable compression for SCP/SFTP with --compressed-ssh
  - libcurl: Enable compression for SCP/SFTP with CURLOPT_SSH_COMPRESSION
  - vtls: Added dynamic changing SSL backend with curl_global_sslset()
  - New MIME API, curl_mime_init() and friends
  - openssl: Initial SSLKEYLOGFILE implementation
  - FTP: zero terminate the entry path even on bad input (CVE-2017-1000254)
  - examples/ftpuploadresume.c: Use portable code
  - runtests: Match keywords case insensitively
  - travis: Build the examples too
  - strtoofft: Reduce integer overflow risks globally
  - zsh.pl: Produce a working completion script again
  - cmake: Remove dead code for CURL_DISABLE_RTMP
  - progress: Track total times following redirects
  - configure: Fix --disable-threaded-resolver
  - cmake: Remove dead code for DISABLED_THREADSAFE
  - configure: Fix clang version detection
  - darwinssl: Fix error: variable length array used
  - travis: Add metalink to some osx builds
  - configure: Check for __builtin_available() availability
  - http_proxy: Fix build error for CURL_DOES_CONVERSIONS
  - examples/ftpuploadresume: checksrc compliance
  - ftp: Fix CWD when doing multicwd then nocwd on same connection
  - system.h: Remove all CURL_SIZEOF_* defines
  - http: Don't wait on CONNECT when there is no proxy
  - system.h: Check for __ppc__ as well
  - http2_recv: Return error better on fatal h2 errors
  - scripts/contri*sh: Use "git log --use-mailmap"
  - tftp: Fix memory leak on too long filename
  - system.h: Fix build for hppa
  - cmake: Enable picky compiler options with clang and gcc
  - makefile.m32: Add support for libidn2
  - curl: Turn off MinGW CRT's globbing
  - request-target.d: Mention added in 7.55.0
  - curl: Shorten and clean up CA cert verification error message
  - imap: Support PREAUTH
  - CURLOPT_USERPWD.3: See also CURLOPT_PROXYUSERPWD
  - examples/threaded-ssl: Mention that this is for openssl before 1.1
  - winbuild: Fix embedded manifest option
  - tests: Make sure libtests and unittests call curl_global_cleanup()
  - system.h: include sys/poll.h for AIX
  - darwinssl: Handle long strings in TLS certs
  - strtooff: Fix build for systems with long long but no strtoll
  - asyn-thread: Improved cleanup after OOM situations
  - HELP-US.md: "How to get started helping out in the curl project"
  - curl.h: CURLSSLBACKEND_WOLFSSL used wrong value
  - unit1301: Fix error message on first test
  - ossfuzz: Moving towards the ideal integration
  - http: Fix a memory leakage in checkrtspprefix()
  - examples/post-callback: Stop returning one byte at a time
  - schannel: return CURLE_SSL_CACERT on failed verification
  - MAIL-ETIQUETTE: Added "1.9 Your emails are public"
  - http-proxy: Treat all 2xx as CONNECT success
  - openssl: Use OpenSSL's default ciphers by default
  - runtests.pl: Support attribute "nonewline" in part verify/upload
  - configure: Remove --enable-soname-bump and SONAME_BUMP
  - travis: Add c-ares enabled builds linux + osx
  - vtls: Fix WolfSSL 3.12 build problems
  - http-proxy: When not doing CONNECT, that phase is done immediately
  - configure: Fix curl_off_t check's include order
  - configure: Use -Wno-varargs on clang 3.9[.X] debug builds
  - rtsp: Do not call fwrite() with NULL pointer FILE *
  - mbedtls: Enable CA path processing
  - travis: Add build without HTTP/SMTP/IMAP
  - checksrc: Verify more code style rules
  - HTTP proxy: On connection re-use, still use the new remote port
  - tests: Add initial gssapi test using stub implementation
  - rtsp: Segfault when using WRITEDATA
  - docs: Clarify the CURLOPT_INTERLEAVE* options behavior
  - non-ascii: Use iconv() with 'char **' argument
  - server/getpart: Provide dummy function to build conversion enabled
  - conversions: Fix several compiler warnings
  - openssl: Add missing includes
  - schannel: Support partial send for when data is too large
  - socks: Fix incorrect port number in SOCKS4 error message
  - curl: Fix integer overflow in timeout options
- Re-enable temporarily disabled IDN2 test-cases

* Tue Aug 29 2017 Paul Howarth <paul@city-fan.org> - 7.55.1-5.0.cf
- Fix NetworkManager connectivity check not working (#1485702)

* Wed Aug 23 2017 Paul Howarth <paul@city-fan.org> - 7.55.1-3.0.cf
- Utilize system wide crypto policies for TLS (#1483972)

* Tue Aug 15 2017 Paul Howarth <paul@city-fan.org> - 7.55.1-2.0.cf
- Make zsh completion work again

* Mon Aug 14 2017 Paul Howarth <paul@city-fan.org> - 7.55.1-1.0.cf
- Update to 7.55.1
  - build: Fix 'make install' with configure, install docs/libcurl/* too
  - make install: Add 8 missing man pages to the installation
  - curl: Do bounds check using a double comparison
  - dist: Add dictserver.py/negtelnetserver.py to release
  - digest_sspi: Don't reuse context if the user/passwd has changed
  - gitignore: Ignore top-level .vs folder
  - build: Check out *.sln files with Windows line endings
  - travis: Verify "make install"
  - dist: Fix the cmake build by shipping cmake_uninstall.cmake.in too
  - metalink: Fix error: ‘*’ in boolean context, suggest ‘&&’ instead
  - configure: Use the threaded resolver backend by default if possible
  - mkhelp.pl: Allow executing this script directly
  - maketgz: Remove old *.dist files before making the tarball
  - openssl: Remove CONST_ASN1_BIT_STRING
  - openssl: Fix "error: this statement may fall through"
  - proxy: Fix memory leak in case of invalid proxy server name
  - curl/system.h: Support more architectures (OpenRISC, ARC)
  - docs: Fix typos
  - curl/system.h: Add Oracle Solaris Studio
  - CURLINFO_TOTAL_TIME: Could wrongly return 4200 seconds
  - docs: --connect-to clarified
  - cmake: Allow user to override CMAKE_DEBUG_POSTFIX
  - travis: Test cmake build on tarball too
  - redirect: Make it handle absolute redirects to IDN names
  - curl/system.h: Fix for gcc on PowerPC
  - curl --interface: Fixed for IPV6 unique local addresses
  - cmake: threads detection improvements

* Wed Aug  9 2017 Paul Howarth <paul@city-fan.org> - 7.55.0-1.1.cf
- Address some test suite issues

* Wed Aug  9 2017 Paul Howarth <paul@city-fan.org> - 7.55.0-1.0.cf
- Update to 7.55.0
  New Features:
  - curl: Allow --header and --proxy-header read from file
  - getinfo: Provide sizes as curl_off_t
  - curl: Prevent binary output spewed to terminal
  - curl: Added --request-target
  - libcurl: Added CURLOPT_REQUEST_TARGET
  - curl: Added --socks5-{basic,gssapi}: control socks5 auth
  - libcurl: Added CURLOPT_SOCKS5_AUTH
   Bug Fixes:
  - glob: Do not parse after a strtoul() overflow range (CVE-2017-1000101)
  - tftp: Reject file name lengths that don't fit (CVE-2017-1000100)
  - file: Output the correct buffer to the user (CVE-2017-1000099)
  - includes: Remove curl/curlbuild.h and curl/curlrules.h
  - dist: Make the hugehelp.c not get regenerated unnecessarily
  - timers: Store internal time stamps as time_t instead of doubles
  - progress: Let "current speed" be UL + DL speeds combined
  - http-proxy: Do the HTTP CONNECT process entirely non-blocking
  - lib/curl_setup.h: Remove CURL_WANTS_CA_BUNDLE_ENV
  - fuzz: Bring oss-fuzz initial code converted to C89
  - configure: Disable nghttp2 too if HTTP has been disabled
  - mk-ca-bundle.pl: Check curl's exit code after certdata download
  - test1148: Verify the -# progressbar
  - tests: Stabilize test 2032 and 2033
  - HTTPS-Proxy: Don't offer h2 for https proxy connections
  - http-proxy: Only attempt FTP over HTTP proxy
  - curl-compilers.m4: Enable vla warning for clang
  - curl-compilers.m4: Enable double-promotion warning
  - curl-compilers.m4: Enable missing-variable-declarations clang warning
  - curl-compilers.m4: Enable comma clang warning
  - Makefile.m32: Enable -W for MinGW32 build
  - CURLOPT_PREQUOTE: Not supported for SFTP
  - http2: Fix OOM crash
  - PIPELINING_SERVER_BL: Clean up the internal list use
  - mkhelp.pl: Fix script name in usage text
  - lib1521: Add curl_easy_getinfo calls to the test set
  - travis: Do the distcheck test build out-of-tree as well
  - if2ip: Fix compiler warning in ISO C90 mode
  - lib: Fix the djgpp build
  - typecheck-gcc: Add support for CURLINFO_OFF_T
  - travis: Enable typecheck-gcc warnings
  - maketgz: Switch to xz instead of lzma
  - CURLINFO_REDIRECT_URL.3: Mention the CURLOPT_MAXREDIRS case
  - curl-compilers.m4: Fix unknown-warning-option on Apple clang
  - winbuild: Fix boringssl build
  - curl/system.h: Add check for XTENSA for 32bit gcc
  - test1537: Fixed memory leak on OOM
  - test1521: Fix compiler warnings
  - curl: Fix memory leak on test 1147 OOM
  - libtest/make: Generate lib1521.c dynamically at build-time
  - curl_strequal.3: Fix typo in SYNOPSIS
  - progress: Prevent resetting t_starttransfer
  - openssl: Improve fallback seed of PRNG with a time based hash
  - http2: Improved PING frame handling
  - test1450: Add simple testing for DICT
  - make: Build the docs subdir only from within src
  - cmake: Added compatibility options for older Windows versions
  - gtls: Fix build when sizeof(long) < sizeof(void *)
  - url: Make the original string get used on subsequent transfers
  - timeval.c: Use long long constant type for timeval assignment
  - tool_sleep: Typecast to avoid macos compiler warning
  - travis.yml: Use --enable-werror on debug builds
  - test1451: Add SMB support to the testbed
  - configure: Remove checks for 5 functions never used
  - configure: Try ldap/lber in reversed order first
  - smb: Fix build for djgpp/MSDOS
  - travis: Install nghttp2 on linux builds
  - smb: Add support for CURLOPT_FILETIME
  - cmake: Fix send/recv argument scanner for windows
  - inet_pton: Fix include on windows to get prototype
  - select.h: Avoid macro redefinition harder
  - cmake: If inet_pton is used, bump _WIN32_WINNT
  - asyn-thread.c: Fix unused variable warnings on macOS
  - runtests: Support "threaded-resolver" as a feature
  - test506: Skip if threaded-resolver
  - cmake: Remove spurious "-l" from linker flags
  - cmake: Add CURL_WERROR for enabling "warning as errors"
  - memdebug: Don't setbuf() if the file open failed
  - curl_easy_escape.3: Mention the (lack of) encoding
  - test1452: Add telnet negotiation
  - CURLOPT_POSTFIELDS.3: Explain the 100-continue magic better
  - cmake: Offer CMAKE_DEBUG_POSTFIX when building with MSVC
  - tests/valgrind.supp: Suppress OpenSSL false positive seen on travis
  - curl_setup_once: Remove ERRNO/SET_ERRNO macros
  - curl-compilers.m4: Disable warning spam with Cygwin's clang
  - ldap: Fix MinGW compiler warning
  - make: Fix docs build on OpenBSD
  - curl_setup: Always define WIN32_LEAN_AND_MEAN on Windows
  - system.h: include winsock2.h before windows.h
  - winbuild: Build with warning level 4
  - rtspd: Fix MSVC level 4 warning
  - sockfilt: Suppress conversion warning with explicit cast
  - libtest: Fix MSVC warning C4706
  - darwinssl: Fix pinnedpubkey build error
  - tests/server/resolve.c: Fix deprecation warning
  - nss: Fix a possible use-after-free in SelectClientCert()
  - checksrc: Escape open brace in regex
  - multi: Mention integer overflow risk if using > 500 million sockets
  - darwinssl: Fix --tlsv1.2 regression
  - timeval: struct curltime is a struct timeval replacement
  - curl_rtmp: Fix a compiler warning
  - include.d: Clarify that it concerns the response headers
  - cmake: Support make uninstall
  - include.d: Clarify --include is only for response headers
  - libcurl: Stop using error codes defined under CURL_NO_OLDIES
  - http: Fix response code parser to avoid integer overflow
  - configure: Fix the check for IdnToUnicode
  - multi: Fix request timer management
  - curl_threads: Fix MSVC compiler warning
  - travis: Build on osx with openssl
  - travis: Build on osx with libressl
  - CURLOPT_NETRC.3: Mention the file name on Windows
  - cmake: Set MSVC warning level to 4
  - netrc: Skip lines starting with '#'
  - darwinssl: Fix curlssl_sha256sum() compiler warnings on first argument
  - BUILD.WINDOWS: Mention buildconf.bat for builds off git
  - darwinssl: Silence compiler warnings
  - travis: Build on osx with darwinssl
  - FTP: Skip unnecessary CWD when in nocwd mode
  - gssapi: Fix memory leak of output token in multi round context
  - getparameter: Avoid returning uninitialized 'usedarg'
  - curl (debug build) easy_events: Make event data static
  - curl: Detect and bail out early on parameter integer overflows
  - configure: Fix recv/send/select detection on Android
- Drop curlbuild.h multilib hacks
- Re-enable now-stabilized test 2033
- Disable test 1427 on i686 (failing just-added test)
- Manually install the libcurl manpages since upstream has accidentally stopped
  doing so

* Thu Aug  3 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-8.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Mon Jul 31 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-7.0.cf
- Enable separate debuginfo back

* Thu Jul 27 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-5.0.cf
- Avoid build failure caused by broken RPM code that produces debuginfo
  packages (https://github.com/rpm-software-management/rpm/issues/280)

* Wed Jul 26 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-3.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jun 19 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-2.0.cf
- Enforce versioned openssl-libs dependency for libcurl (#1462184)

* Wed Jun 14 2017 Paul Howarth <paul@city-fan.org> - 7.54.1-1.0.cf
- Update to 7.54.1
  - CVE-2017-9502: file: URL buffer overflow
  - curl: Show the libcurl release date in --version output
  - openssl: Fix memory leak in servercert
  - tests: Remove the html and PDF versions from the tarball
  - mbedtls: Enable NTLM (and SMB) even if MD4 support is unavailable
  - typecheck-gcc: Handle function pointers properly
  - llist: No longer uses malloc
  - gnutls: Removed some code when --disable-verbose is configured
  - lib: Fix maybe-uninitialized warnings
  - multi: Clarify condition in curl_multi_wait
  - schannel: Don't treat encrypted partial record as pending data
  - configure: Fix the -ldl check for openssl, add -lpthread check
  - configure: Accept -Og and -Ofast GCC flags
  - Makefile: Avoid use of GNU-specific form of $<
  - if2ip: Fix -Wcast-align warning
  - configure: Stop prepending to LDFLAGS, CPPFLAGS
  - curl: Set a 100K buffer size by default
  - typecheck-gcc: Fix _curl_is_slist_info
  - nss: Do not leak PKCS #11 slot while loading a key
  - nss: Load libnssckbi.so if no other trust is specified
  - examples: ftpuploadfrommem.c
  - url: Declare get_protocol_family() static
  - examples/cookie_interface.c: Changed to example.com
  - test1443: Test --remote-time
  - curl: Use utimes instead of obsolescent utime when available
  - url: Fixed a memory leak on OOM while setting CURLOPT_BUFFERSIZE
  - curl_rtmp: Fix missing-variable-declarations warnings
  - tests: Fixed OOM handling of unit tests to abort test
  - curl_setup: Ensure no more than one IDN lib is enabled
  - tool: Fix missing prototype warnings for CURL_DOES_CONVERSIONS
  - CURLOPT_BUFFERSIZE: 1024 bytes is now the minimum size
  - curl: Non-boolean command line args reject --no- prefixes
  - telnet: Write full buffer instead of byte-by-byte
  - typecheck-gcc: Add missing string options
  - typecheck-gcc: Add support for CURLINFO_SOCKET
  - opt man pages: They all have examples now
  - curl_setup_once: Use SEND_QUAL_ARG2 for swrite
  - test557: Set a known good numeric locale
  - schannel: Return a more specific error code for SEC_E_UNTRUSTED_ROOT
  - tests/server: Make string literals const
  - runtests: Use -R for random order
  - unit1305: Fix compiler warning
  - curl_slist_append.3: Clarify a NULL input creates a new list
  - tests/server: Run checksrc by default in debug-builds
  - tests: Fix -Wcast-qual warnings
  - runtests.pl: Simplify the datacheck read section
  - curl: Remove --environment and tool_writeenv.c
  - buildconf: Fix hang on IRIX
  - tftp: Silence bad-function-cast warning
  - asyn-thread: Fix unused macro warnings
  - tool_parsecfg: Fix -Wcast-qual warning
  - sendrecv: Fix MinGW-w64 warning
  - test537: Use correct variable type
  - rand: Treat fake entropy the same regardless of endianness
  - curl: Generate the --help output
  - tests: Removed redundant --trace-ascii arguments
  - multi: Assign IDs to all timers and make each timer singleton
  - multi: Use a fixed array of timers instead of malloc
  - mbedtls: Support server renegotiation request
  - pipeline: Fix mistakenly trying to pipeline POSTs
  - lib510: Don't write past the end of the buffer if it's too small
  - CURLOPT_HTTPPROXYTUNNEL.3: Clarify, add example
  - SecureTransport/DarwinSSL: Implement public key pinning
  - curl.1: Clarify --config
  - curl_sasl: Fix build error with CURL_DISABLE_CRYPTO_AUTH + USE_NTLM
  - darwinssl: Fix exception when processing a client-side certificate
  - curl.1: Mention --oauth2-bearer's <token> argument
  - mkhelp.pl: Do not add current time into curl binary
  - asiohiper.cpp / evhiperfifo.c: Deal with negative timerfunction input
  - ssh: Fix memory leak in disconnect due to timeout
  - tests: Stabilize test 1034
  - cmake: Auto detection of CURL_CA_BUNDLE/CURL_CA_PATH
  - assert: Avoid, use DEBUGASSERT instead
  - LDAP: Using ldap_bind_s on Windows with methods
  - redirect: Store the "would redirect to" URL when max redirs is reached
  - winbuild: Fix the nghttp2 build
  - examples: Fix -Wimplicit-fallthrough warnings
  - time: Fix type conversions and compiler warnings
  - mbedtls: Fix variable shadow warning
  - test557: Fix ubsan runtime error due to int left shift
  - transfer: Init the infilesize from the postfields
  - docs: Clarify NO_PROXY further
  - build-wolfssl: Sync config with wolfSSL 3.11
  - curl-compilers.m4: Enable -Wshift-sign-overflow for clang
  - example/externalsocket.c: Make it use CLOSESOCKETFUNCTION too
  - lib574.c: Use correct callback proto
  - lib583: Fix compiler warning
  - curl-compilers.m4: Fix compiler_num for clang
  - typecheck-gcc.h: Separate getinfo slist checks from other pointers
  - typecheck-gcc.h: Check CURLINFO_TLS_SSL_PTR and CURLINFO_TLS_SESSION
  - typecheck-gcc.h: Check CURLINFO_CERTINFO
  - build: Provide easy code coverage measuring
  - test1537: Dedicated tests of the URL (un)escape API calls
  - curl_endian: Remove unused functions
  - test1538: Verify the libcurl strerror API calls
  - MD(4|5): Silence cast-align clang warning
  - dedotdot: Fixed output for ".." and "." only input
  - cyassl: Define build macros before including ssl.h
  - updatemanpages.pl: Error out on too old git version
  - curl_sasl: Fix unused-variable warning
  - x509asn1: Fix implicit-fallthrough warning with GCC 7
  - libtest: Fix implicit-fallthrough warnings with GCC 7
  - BINDINGS: Add Ring binding
  - curl_ntlm_core: Pass unsigned char to toupper
  - test1262: Verify ftp download with -z for "if older than this"
  - test1521: Test all curl_easy_setopt options
  - typecheck-gcc: Allow CURLOPT_STDERR to be NULL too
  - metalink: Remove unused printf() argument
  - file: Make speedcheck use current time for checks
  - configure: Fix link with librtmp when specifying path
  - examples/multi-uv.c: Fix deprecated symbol
  - cmake: Fix inconsistency regarding mbed TLS include directory
  - setopt: Check CURLOPT_ADDRESS_SCOPE option range
  - gitignore: Ignore all vim swap files
  - urlglob: Fix division by zero
  - libressl: OCSP and intermediate certs workaround no longer needed
- New test 1446 segfaulting on builds for older distributions, so disable for
  now
- Update patches as needed

* Thu May  4 2017 Paul Howarth <paul@city-fan.org> - 7.54.0-4.0.cf
- Make curl-minimal require a new enough version of libcurl

* Sat Apr 29 2017 Paul Howarth <paul@city-fan.org> - 7.54.0-3.1.cf
- Don't require nss-pem for OpenSSL builds

* Thu Apr 27 2017 Paul Howarth <paul@city-fan.org> - 7.54.0-3.0.cf
- Switch the TLS backend back to OpenSSL for Fedora 27 onwards (#1445153)

* Tue Apr 25 2017 Paul Howarth <paul@city-fan.org> - 7.54.0-2.0.cf
- nss: use libnssckbi.so as the default source of trust
- nss: do not leak PKCS #11 slot while loading a key (#1444860)

* Wed Apr 19 2017 Paul Howarth <paul@city-fan.org> - 7.54.0-1.0.cf
- Update to 7.54.0
  - Add CURL_SSLVERSION_MAX_* constants to CURLOPT_SSLVERSION
  - Add --max-tls
  - Add CURLOPT_SUPPRESS_CONNECT_HEADERS
  - Add --suppress-connect-headers
  - CVE-2017-7468: switch off SSL session id when client cert is used
  - cmake: Replace invalid UTF-8 byte sequence
  - tests: Use consistent environment variables for setting charset
  - proxy: Fixed a memory leak on OOM
  - ftp: Removed an erroneous free in an OOM path
  - docs: De-duplicate file lists in the Makefiles
  - ftp: Fixed a NULL pointer dereference on OOM
  - gopher: Fixed detection of an error condition from Curl_urldecode
  - url: Fix unix-socket support for proxy-disabled builds
  - test1139: Allow for the possibility that the man page is not rebuilt
  - cyassl: Get library version string at runtime
  - digest_sspi: Fix compilation warning
  - tests: Enable HTTP/2 tests to run with non-default port numbers
  - warnless: Suppress compiler warning
  - darwinssl: Warn that disabling host verify also disables SNI
  - configure: Fix for --enable-pthreads
  - checksrc.bat: Ignore curl_config.h.in, curl_config.h
  - no-keepalive.d: Fix typo
  - configure: Fix --with-zlib when a path is specified
  - build: Fix gcc7 implicit fallthrough warnings
  - Fix potential use of uninitialized variables
  - CURLOPT_SSL_CTX_FUNCTION.3: Fix EXAMPLE formatting errors
  - CMake: Reorganize SSL support, separate WinSSL and SSPI
  - CMake: Add DarwinSSL support
  - CMake: Add mbedTLS support
  - ares: Return error at once if timed out before name resolve starts
  - BINDINGS: Added C++, perl, go and Scilab bindings
  - URL: Return error on malformed URLs with junk after port number
  - KNOWN_BUGS: Add DarwinSSL won't import PKCS#12 without a password
  - http2: Fix assertion error on redirect with CL=0
  - updatemanpages.pl: Update man pages to use current date and versions
  - --insecure: Clarify that this option is for server connections
  - mkhelp: Simplified the gzip code
  - build: Fixed making man page in out-of-tree tarball builds
  - tests: Disabled 1903 due to flakiness
  - openssl: Add two /* FALLTHROUGH */ to satisfy coverity
  - cmdline-opts: Fixed a few typos
  - authneg: Clear auth.multi flag at http_done
  - curl_easy_reset: Also reset the authentication state
  - proxy: Skip SSL initialization for closed connections
  - http_proxy: Ignore TE and CL in CONNECT 2xx responses
  - tool_writeout: Fixed a buffer read overrun on --write-out
  - make: Regenerate docs/curl.1 by running make in docs
  - winbuild: Add basic support for OpenSSL 1.1.x
  - build: Removed redundant DEPENDENCIES from makefiles
  - CURLINFO_LOCAL_PORT.3: Added example
  - curl: Show HTTPS-Proxy options on CURLE_SSL_CACERT
  - tests: Strip more options from non-HTTP --libcurl tests
  - tests: Fixed the documented test server port numbers
  - runtests.pl: Fixed display of the Gopher IPv6 port number
  - multi: Fix streamclose() crash in debug mode
  - cmake: Build manual pages
  - cmake: Add support for building HTML and PDF docs
  - mbedtls: Add support for CURLOPT_SSL_CTX_FUNCTION
  - make: Introduce 'test-nonflaky' target
  - CURLINFO_PRIMARY_IP.3: Add example
  - tests/README: Mention nroff for --manual tests
  - mkhelp: Disable compression if the perl gzip module is unavailable
  - openssl: Fall back on SSL_ERROR_* string when no error detail
  - asiohiper: Make sure socket is open in event_cb
  - tests/README: Make "Run" section foolproof
  - curl: Check for end of input in writeout backslash handling
  - .gitattributes: Turn off CRLF for *.am
  - multi: Fix MinGW-w64 compiler warnings
  - schannel: Fix variable shadowing warning
  - openssl: Exclude DSA code when OPENSSL_NO_DSA is defined
  - http: Fix proxy connection reuse with basic-auth
  - pause: Handle mixed types of data when paused
  - http: Do not treat FTPS over CONNECT as HTTPS
  - conncache: Make hashkey avoid malloc
  - make: Use the variable MAKE for recursive calls
  - curl: Fix callback argument inconsistency
  - NTLM: Check for features with #ifdef instead of #if
  - cmake: Add several missing files to the dist
  - select: Use correct SIZEOF_ constant
  - connect: Fix unreferenced parameter warning
  - schannel: Fix unused variable warning
  - gcc7: Fix ‘*’ in boolean context
  - http2: Silence unused parameter warnings
  - ssh: Fix narrowing conversion warning
  - telnet: (win32) Fix read callback return variable
  - docs: Explain --fail-early does not imply --fail
  - docs: Added examples for CURLINFO_FILETIME.3 and CURLOPT_FILETIME.3
  - tests/server/util: Remove in6addr_any for recent MinGW
  - multi: Make curl_multi_wait avoid malloc in the typical case
  - include: curl/system.h is a run-time version of curlbuild.h
  - easy: Silence compiler warning
  - llist: Replace Curl_llist_alloc with Curl_llist_init
  - hash: Move key into hash struct to reduce mallocs
  - url: Don't free postponed data on connection reuse
  - curl_sasl: Declare mechtable static
  - curl: Fix Windows Unicode build
  - multi: Fix queueing of pending easy handles
  - tool_operate: Fix MinGW compiler warning
  - low_speed_limit: Improved function for longer time periods
  - gtls: Fix compiler warning
  - sspi: Print out InitializeSecurityContext() error message
  - schannel: Fix compiler warnings
  - vtls: fix unreferenced variable warnings
  - INSTALL.md: Fix secure transport configure arguments
  - CURLINFO_SCHEME.3: Fix variable type
  - libcurl-thread.3: Also mention threaded-resolver
  - nss: Load CA certificates even with --insecure
  - openssl: Fix this statement may fall through
  - poll: Prefer <poll.h> over <sys/poll.h>
  - polarssl: Unbreak build with versions < 1.3.8
  - Curl_expire_latest: Ignore already expired timers
  - configure: Turn implicit function declarations into errors
  - mbedtls: Fix memory leak in error path
  - http2: Fix handle leak in error path
  - .gitattributes: Force shell scripts to LF
  - configure.ac: Ignore CR after version numbers
  - extern-scan.pl: Strip trailing CR
  - openssl: Make SSL_ERROR_to_str more future-proof
  - openssl: Fix thread-safety bugs in error-handling
  - openssl: Don't try to print nonexistant peer private keys
  - nss: Fix MinGW compiler warnings
- Switch to lzma-compressed upstream tarball

* Thu Apr 13 2017 Paul Howarth <paul@city-fan.org> - 7.53.1-7.0.cf
- Provide (lib)curl-minimal subpackages with lightweight build of (lib)curl
  (Fedora 27 onwards)

* Mon Apr 10 2017 Paul Howarth <paul@city-fan.org> - 7.53.1-5.0.cf
- Disable upstream test 2033 (flaky test for HTTP/1 pipelining)

* Fri Apr  7 2017 Paul Howarth <paul@city-fan.org> - 7.53.1-4.0.cf
- Fix out of bounds read in curl --write-out (CVE-2017-7407)
- Make the dependency on nss-pem arch-specific from F-25 onwards (#1428550)
- Drop support for EOL distributions prior to F-13
  - Drop BuildRoot: and Group: tags
  - Drop buildroot cleaning in %%install
  - Drop explicit %%clean section
  - Drop explicit dependency on pkgconfig

* Thu Mar  2 2017 Paul Howarth <paul@city-fan.org> - 7.53.1-2.0.cf
- Rebuild to sync with Rawhide

* Fri Feb 24 2017 Paul Howarth <paul@city-fan.org> - 7.53.1-1.0.cf
- Update to 7.53.1
  - cyassl: Fix typo
  - url: Improve CURLOPT_PROXY_CAPATH error handling
  - urldata: Include curl_sspi.h when Windows SSPI is enabled
  - formdata: check for EOF when reading from stdin
  - tests: Set CHARSET and LANG to UTF-8 in 1035, 2046 and 2047
  - url: Default the proxy CA bundle location to CURL_CA_BUNDLE
  - rand: Added missing #ifdef HAVE_FCNTL_H around fcntl.h header

* Wed Feb 22 2017 Paul Howarth <paul@city-fan.org> - 7.53.0-1.0.cf
- Update to 7.53.0
  - CVE-2017-2629: Make SSL_VERIFYSTATUS work again
  - unix_socket: Added --abstract-unix-socket and CURLOPT_ABSTRACT_UNIX_SOCKET
  - CURLOPT_BUFFERSIZE: Support enlarging receive buffer
  - gnutls-random: Check return code for failed random
  - openssl-random: Check return code when asking for random
  - http: Remove "Curl_http_done: called premature" message
  - cyassl: Use time_t instead of long for timeout
  - build-wolfssl: Sync config with wolfSSL 3.10
  - ftp-gss: Check for init before use
  - configure: Accept --with-libidn2 instead
  - ftp: Failure to resolve proxy should return that error code
  - curl.1: Add three more exit codes
  - docs/ciphers: Link to our own new page about ciphers
  - vtls: s/SSLEAY/OPENSSL - fixes multi_socket timeouts with openssl
  - darwinssl: Fix iOS build
  - darwinssl: Fix CFArrayRef leak
  - cmake: Use crypt32.lib when building with OpenSSL on windows
  - curl_formadd.3: CURLFORM_CONTENTSLENGTH not needed when chunked
  - digest_sspi: Copy terminating NUL as well
  - curl: Fix --remote-time incorrect times on Windows
  - curl.1: Several updates and corrections
  - content_encoding: Change return code on a failure
  - curl.h: CURLE_FUNCTION_NOT_FOUND is no longer in use
  - docs: TCP_KEEPALIVE start and interval default to 60
  - darwinssl: --insecure overrides --cacert if both settings are in use
  - TheArtOfHttpScripting: Grammar
  - CIPHERS.md: Document GSKit ciphers
  - wolfssl: Support setting cipher list
  - wolfssl: Display negotiated SSL version and cipher
  - lib506: Fix build for Open Watcom
  - asiohiper: Improved socket handling
  - examples: Make the C++ examples follow our code style too
  - tests/sws: Retry send() on EWOULDBLOCK
  - cmake: Fix passing _WINSOCKAPI_ macro to compiler
  - smtp: Fix STARTTLS denied error message
  - imap/pop3: Don't print response character in STARTTLS denied messages
  - rand: Make it work without TLS backing
  - url: Fix parsing for when 'file' is the default protocol
  - url: Allow file://X:/path URLs on windows again
  - gnutls: Check for alpn and ocsp in configure
  - IDN: Use TR46 'non-transitional' for toASCII translations
  - url: Fix NO_PROXY env var to work properly with --proxy option
  - CURLOPT_PREQUOTE.3: Takes a struct curl_slist*, not a char*
  - docs: Add note about libcurl copying strings to CURLOPT_* manpages
  - curl: Reset the easy handle at --next
  - --next docs: --trace and --trace-ascii are also global
  - --write-out docs: 'time_total' is not always shown with ms precision
  - http: Print correct HTTP string in verbose output when using HTTP/2
  - docs: Improved language in README.md HISTORY.md CONTRIBUTE.md
  - http2: Disable server push if not requested
  - nss: Use the correct lock in nss_find_slot_by_name()
  - usercertinmem.c: Improve the short description
  - CURLOPT_CONNECT_TO: Fix compile warnings
  - docs: Non-blocking SSL handshake is now supported with NSS
  - *.rc: Escape non-ASCII/non-UTF-8 character for clarity
  - mbedTLS: Fix multi interface non-blocking handshake
  - PolarSSL: Fix multi interface non-blocking handshake
  - VC: Remove the makefile.vc6 build infra
  - telnet: Fix windows compiler warnings
  - cookies: Do not assume a valid domain has a dot
  - polarssl: Fix hangs
  - gnutls: Disable TLS session tickets
  - mbedtls: Disable TLS session tickets
  - mbedtls: Implement CTR-DRBG and HAVEGE random generators
  - openssl: Don't use certificate after transferring ownership
  - cmake: Support curl --xattr when built with cmake
  - OS400: Fix symbols
  - docs: Add more HTTPS proxy documentation
  - docs: Use more HTTPS links
  - cmdline-opts: Fixed build and test in out of source tree builds
  - CHANGES.0: Removed
  - schannel: Remove incorrect SNI disabled message
  - darwinssl: Avoid parsing certificates when not in verbose mode
  - test552: Fix typos
  - telnet: Fix typos
  - transfer: Only retry nobody-requests for HTTP
  - http2: Reset push header counter fixes crash
  - nss: Make FTPS work with --proxytunnel
  - test1139: Added the --manual keyword since the manual is required
  - polarssl, mbedtls: Fix detection of pending data
  - http_proxy: Fix tiny memory leak upon edge case connecting to proxy
  - URL: Only accept ";options" in SMTP/POP3/IMAP URL schemes
  - curl.1: ftp.sunet.se is no longer an FTP mirror
  - tool_operate: Show HTTPS-Proxy options on CURLE_SSL_CACERT
  - http2: Fix memory-leak when denying push streams
  - configure: Allow disabling pthreads, fall back on Win32 threads
  - curl: Fix typo in time condition warning message
  - axtls: Adapt to API changes
  - tool_urlglob: Allow a glob range with the same start and stop
  - winbuild: Add note on auto-detection of MACHINE in Makefile.vc
  - http: Fix missing 'Content-Length: 0' while negotiating auth
  - proxy: Fix hostname resolution and IDN conversion
  - docs: Fix timeout handling in multi-uv example
  - digest_sspi: Fix nonce-count generation in HTTP digest
  - sftp: Improved checks for create dir failures
  - smb: Use getpid replacement for windows UWP builds
  - digest_sspi: Handle 'stale=TRUE' directive in HTTP digest

* Fri Feb 10 2017 Paul Howarth <paul@city-fan.org> - 7.52.1-2.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Dec 23 2016 Paul Howarth <paul@city-fan.org> - 7.52.1-1.0.cf
- Update to 7.52.1
  - CVE-2016-9594: Uninitialized random
  - lib557: Fix checksrc warnings
  - lib: Fix MSVC compiler warnings
  - lib557.c: Use a shorter MAXIMIZE representation
  - tests: Run checksrc on debug builds

* Wed Dec 21 2016 Paul Howarth <paul@city-fan.org> - 7.52.0-1.0.cf
- Update to 7.52.0
  - nss: Map CURL_SSLVERSION_DEFAULT to NSS default
  - vtls: Support TLS 1.3 via CURL_SSLVERSION_TLSv1_3
  - curl: Introduce the --tlsv1.3 option to force TLS 1.3
  - curl: Add --retry-connrefused
  - proxy: Support HTTPS proxy and SOCKS+HTTP(s)
  - Add CURLINFO_SCHEME, CURLINFO_PROTOCOL, and %%{scheme}
  - curl: Add --fail-early
  - CVE-2016-9586: printf floating point buffer overflow
  - CVE-2016-9952: Win CE schannel cert wildcard matches too much
  - CVE-2016-9953: Win CE schannel cert name out of buffer read
  - msvc: Removed a straggling reference to strequal.c
  - winbuild: Remove strcase.obj from curl build
  - examples: Bugfixed multi-uv.c
  - configure: Verify that compiler groks -Werror=partial-availability
  - mbedtls: Fix build with mbedtls versions < 2.4.0
  - dist: Add unit test CMakeLists.txt to the tarball
  - curl -w: Added more decimal digits to timing counters
  - easy: Initialize info variables on easy init and duphandle
  - cmake: Disable poll for macOS
  - http2: Don't send header fields prohibited by HTTP/2 spec
  - ssh: Check md5 fingerprints case insensitively (regression)
  - openssl: Initial TLS 1.3 adaptions
  - curl_formadd.3: *_FILECONTENT and *_FILE need the file to be kept
  - printf: Fix ".*f" handling
  - examples/fileupload.c: fclose the file as well
  - SPNEGO: Fix memory leak when authentication fails
  - realloc: Use Curl_saferealloc to avoid common mistakes
  - openssl: Make sure to fail in the unlikely event that PRNG seeding fails
  - URL-parser: For file://[host]/ URLs, the [host] must be localhost
  - timeval: Prefer time_t to hold seconds instead of long
  - Curl_rand: Fixed and moved to rand.c
  - glob: Fix [a-c] globbing regression
  - darwinssl: Fix SSL client certificate not found on MacOS Sierra
  - curl.1: Clarify --dump-header only writes received headers
  - http2: Fix address sanitizer memcpy warning
  - http2: Use huge HTTP/2 windows
  - connects: Don't mix unix domain sockets with regular ones
  - url: Fix conn reuse for local ports and interfaces
  - x509: Limit ASN.1 structure sizes to 256K
  - checksrc: Add more checks
  - winbuild: Add config option ENABLE_NGHTTP2
  - http2: Check nghttp2_session_set_local_window_size exists
  - http2: Fix crashes when parent stream gets aborted
  - CURLOPT_CONNECT_TO: Skip non-matching "connect-to" entries
  - URL parser: Reject non-numerical port numbers
  - CONNECT: Reject TE or CL in 2xx responses
  - CONNECT: Read responses one byte at a time
  - curl: Support zero-length argument strings in config files
  - openssl: Don't use OpenSSL's ERR_PACK
  - curl.1: Generated with the new man page system
  - curl_easy_recv: Improve documentation and example program
  - Curl_getconnectinfo: Avoid checking if the connection is closed
  - CIPHERS.md: Attempt to document TLS cipher names

* Mon Nov 21 2016 Paul Howarth <paul@city-fan.org> - 7.51.0-3.0.cf
- Map CURL_SSLVERSION_DEFAULT to NSS default, add support for TLS 1.3
  (#1396719)

* Tue Nov 15 2016 Paul Howarth <paul@city-fan.org> - 7.51.0-2.0.cf
- Stricter host name checking for file:// URLs
- ssh: Check md5 fingerprints case insensitively

* Wed Nov  2 2016 Paul Howarth <paul@city-fan.org> - 7.51.0-1.0.cf
- Update to 7.51.0
  - nss: Additional cipher suites are now accepted by CURLOPT_SSL_CIPHER_LIST
  - New option: CURLOPT_KEEP_SENDING_ON_ERROR
  - CVE-2016-8615: Cookie injection for other servers
  - CVE-2016-8616: Case insensitive password comparison
  - CVE-2016-8617: OOB write via unchecked multiplication
  - CVE-2016-8618: Double-free in curl_maprintf
  - CVE-2016-8619: Double-free in krb5 code
  - CVE-2016-8620: glob parser write/read out of bounds
  - CVE-2016-8621: curl_getdate read out of bounds
  - CVE-2016-8622: URL unescape heap overflow via integer truncation
  - CVE-2016-8623: Use-after-free via shared cookies
  - CVE-2016-8624: Invalid URL parsing with '#'
  - CVE-2016-8625: IDNA 2003 makes curl use wrong host
  - openssl: Fix per-thread memory leak using 1.0.1 or 1.0.2
  - http: Accept "Transfer-Encoding: chunked" for HTTP/2 as well
  - LICENSE-MIXING.md: Update with mbedTLS dual licensing
  - examples/imap-append: Set size of data to be uploaded
  - test2048: Fix url
  - darwinssl: Disable RC4 cipher-suite support
  - CURLOPT_PINNEDPUBLICKEY.3: Fix the AVAILABILITY formatting
  - openssl: Don’t call CRYTPO_cleanup_all_ex_data
  - libressl: Fix version output
  - easy: Reset all statistical session info in curl_easy_reset
  - curl_global_cleanup.3: Don't unload the lib with sub threads running
  - dist: Add CurlSymbolHiding.cmake to the tarball
  - docs: Remove that --proto is just used for initial retrieval
  - configure: Fixed builds with libssh2 in a custom location
  - curl.1: --trace supports %% for sending to stderr!
  - cookies: Same domain handling changed to match browser behaviour
  - formpost: Trying to attach a directory no longer crashes
  - CURLOPT_DEBUGFUNCTION.3: Fixed unused argument warning
  - formpost: Avoid silent snprintf() truncation
  - ftp: Fix Curl_ftpsendf
  - mprintf: Return error on too many arguments
  - smb: Properly check incoming packet boundaries
  - GIT-INFO: Remove the Mac 10.1-specific details
  - resolve: Add error message when resolving using SIGALRM
  - cmake: Add nghttp2 support
  - dist: Remove PDF and HTML converted docs from the releases
  - configure: Disable poll() in macOS builds
  - vtls: Only re-use session-ids using the same scheme
  - pipelining: Skip to-be-closed connections when pipelining
  - win: Fix Universal Windows Platform build
  - curl: Do not set CURLOPT_SSLENGINE to DEFAULT automatically
  - maketgz: Make it support "only" generating version info
  - Curl_socket_check: Add extra check to avoid integer overflow
  - gopher: Properly return error for poll failures
  - curl: Set INTERLEAVEDATA too
  - polarssl: Clear thread array at init
  - polarssl: Fix unaligned SSL session-id lock
  - polarssl: Reduce #ifdef madness with a macro
  - curl_multi_add_handle: Set timeouts in closure handles
  - configure: Set min version flags for builds on mac
  - INSTALL: Converted to markdown => INSTALL.md
  - curl_multi_remove_handle: Fix a double-free
  - multi: Fix infinite loop in curl_multi_cleanup()
  - nss: Fix tight loop in non-blocking TLS handshake over proxy
  - mk-ca-bundle: Change URL retrieval to HTTPS-only by default
  - mbedtls: Stop using deprecated include file
  - docs: Fix req->data in multi-uv example
  - configure: Fix test syntax for monotonic clock_gettime
  - CURLMOPT_MAX_PIPELINE_LENGTH.3: Clarify it's not for HTTP/2
- Use libidn2 from Fedora 25 onwards

* Fri Oct  7 2016 Paul Howarth <paul@city-fan.org> - 7.50.3-2.0.cf
- Use the just-built version of libcurl while generating zsh completion

* Wed Sep 14 2016 Paul Howarth <paul@city-fan.org> - 7.50.3-1.0.cf
- Update to 7.50.3
  - CVE-2016-7167: Escape and unescape integer overflows
  - mk-ca-bundle.pl: Use SHA256 instead of SHA1
  - checksrc: Detect strtok() use
  - errors: New alias CURLE_WEIRD_SERVER_REPLY
  - http2: Support > 64bit sized uploads
  - openssl: Fix bad memory free (regression)
  - CMake: Hide private library symbols
  - http: Refuse to pass on response body when NO_NODY was set
  - cmake: Fix curl-config --static-libs
  - mbedtls: Switch off NTLM in build if md4 isn't available
  - curl: --create-dirs on Windows groks both forward and backward slashes

* Wed Sep  7 2016 Paul Howarth <paul@city-fan.org> - 7.50.2-1.0.cf
- Update to 7.50.2
  - nss: Fix incorrect use of a previously loaded certificate from file
    (CVE-2016-7141)
  - nss: Work around race condition in PK11_FindSlotByName()
  - mbedtls: Added support for NTLM
  - SSH: Fixed SFTP/SCP transfer problems
  - multi: Make Curl_expire() work with 0 ms timeouts
  - mk-ca-bundle.pl: -m keeps ca cert meta data in output
  - TFTP: Fix upload problem with piped input
  - CURLOPT_TCP_NODELAY: now enabled by default
  - mbedtls: Set verbose TLS debug when MBEDTLS_DEBUG is defined
  - http2: Always wait for readable socket
  - cmake: Enable win32 large file support by default
  - cmake: Enable win32 threaded resolver by default
  - winbuild: Avoid setting redundant CFLAGS to compile commands
  - curl.h: Make CURL_NO_OLDIES define CURL_STRICTER
  - docs: Make more markdown files use .md extension
  - docs: CONTRIBUTE and LICENSE-MIXING were converted to markdown
  - winbuild: Allow changing C compiler via environment variable CC
  - rtsp: Accept any RTSP session id
  - HTTP: Retry failed HEAD requests on reused connections too
  - configure: Add zlib search with pkg-config
  - openssl: Accept subjectAltName iPAddress if no dNSName match
  - MANUAL: Remove invalid link to LDAP documentation
  - socks: Improved connection procedure
  - proxy: Reject attempts to use unsupported proxy schemes
  - proxy: Bring back use of "Proxy-Connection:"
  - curl: Allow "pkcs11:" prefix for client certificates
  - spnego_sspi: Fix memory leak in case *outlen is zero
  - SOCKS: Improve verbose output of SOCKS5 connection sequence
  - SOCKS: Display the hostname returned by the SOCKS5 proxy server
  - http/sasl: Query authentication mechanism supported by SSPI before using
  - sasl: Don't use GSSAPI authentication when domain name not specified
  - win: Basic support for Universal Windows Platform apps
  - ftp: Fix wrong poll on the secondary socket
  - openssl: Build warning-free with 1.1.0 (again)
  - HTTP: Stop parsing headers when switching to unknown protocols
  - test219: Add http as a required feature
  - TLS: random file/egd doesn't have to match for conn reuse
  - schannel: Disable ALPN for Wine since it is causing problems
  - http2: Make sure stream errors don't needlessly close the connection
  - http2: Return CURLE_HTTP2_STREAM for unexpected stream close
  - darwinssl: --cainfo is intended for backward compatibility only
  - Speed caps: Not based on average speeds anymore
  - configure: Make the cpp -P detection not clobber CPPFLAGS
  - http2: Use named define instead of magic constant in read callback
  - http2: Skip the content-length parsing, detect unknown size
  - http2: Return EOF when done uploading without known size
  - darwinssl: Test for errSecSuccess in PKCS12 import rather than noErr
  - openssl: Fix CURLINFO_SSL_VERIFYRESULT
- Disable various ssh tests for F12..F15, which are failing for reasons unknown
- Build with c-ares rather than POSIX threaded DNS resolver for F12..F15,
  which resolves some other test failures, and allows dropping of workaround
  patch for old applications on F12 and F13
- Update patches as needed

* Fri Aug 26 2016 Paul Howarth <paul@city-fan.org> - 7.50.1-2.0.cf
- Work around race condition in PK11_FindSlotByName()
- Fix incorrect use of a previously loaded certificate from file
  (related to CVE-2016-5420)

* Wed Aug  3 2016 Paul Howarth <paul@city-fan.org> - 7.50.1-1.0.cf
- Update to 7.50.1
  - TLS: Switch off SSL session id when client cert is used (CVE-2016-5419)
  - TLS: Only reuse connections with the same client cert (CVE-2016-5420)
  - curl_multi_cleanup: Clear connection pointer for easy handles
    (CVE-2016-5421)
  - Include the CURLINFO_HTTP_VERSION(3) man page into the release tarball
  - Include the http2-server.pl script in the release tarball
  - test558: Fix test by stripping file paths from FD lines
  - spnego: Corrected misplaced * in Curl_auth_spnego_cleanup() declaration
  - tests: Fix for http/2 feature
  - cmake: Fix for schannel support
  - curl.h: Make public types void * again
  - win32: Fix a potential memory leak in Curl_load_library
  - travis: Fix OSX build by re-installing libtool
  - mbedtls: Fix debug function name

* Wed Jul 27 2016 Paul Howarth <paul@city-fan.org> - 7.50.0-2.0.cf
- Use upstream fix for HTTP2 test confusion

* Fri Jul 22 2016 Paul Howarth <paul@city-fan.org> - 7.50.0-1.1.cf
- Fix confusion in test suite about whether or not HTTP2 support is available
- Use the default ports for the test suite; it's not robust enough to support
  running under different ports

* Thu Jul 21 2016 Paul Howarth <paul@city-fan.org> - 7.50.0-1.0.cf
- Update to 7.50.0
  - http: Add CURLINFO_HTTP_VERSION and %%{http_version}
  - memdebug: Fix MSVC crash with -DMEMDEBUG_LOG_SYNC
  - openssl: Fix build with OPENSSL_NO_COMP
  - mbedtls: Removed unused variables
  - cmake: Added missing mbedTLS support
  - URL parser: Allow URLs to use one, two or three slashes
  - curl: Fix -q [regression]
  - openssl: Use correct buffer sizes for error messages
  - curl: Fix SIGSEGV while parsing URL with too many globs
  - schannel: Add CURLOPT_CERTINFO support
  - vtls: Fix ssl session cache race condition
  - http: Fix HTTP/2 connection reuse [regression]
  - checksrc: Add LoadLibrary to the banned functions list
  - schannel: Disable ALPN on Windows < 8.1
  - configure: Occasional ignorance of --enable-symbol-hiding with GCC
  - http2: test17xx are the first real HTTP/2 tests
  - resolve: Add support for IPv6 DNS64/NAT64 Networks on OS X + iOS
  - curl_multi_socket_action.3: Rewording
  - CURLOPT_POSTFIELDS.3: Clarify what happens when set empty
  - cmake: Fix build with winldap
  - openssl: Fix cert check with non-DNS name fields present
  - curl.1: Mention the units for the progress meter
  - openssl: Use more 'const' to fix build warnings with 1.1.0 branch
  - cmake: Now using BUILD_TESTING=ON/OFF
  - vtls: Only call add/getsession if session id is enabled
  - headers: Forward declare CURL, CURLM and CURLSH as structs
  - configure: Improve detection of CA bundle path on FreeBSD
  - SFTP: Set a generic error when no SFTP one exists
  - curl_global_init.3: Expand on the SSL and WIN32 bits purpose
  - conn: Don't free easy handle data in handler->disconnect
  - cookie.c: Fix misleading indentation
  - library: Fix memory leaks found during static analysis
  - CURLMOPT_SOCKETFUNCTION.3: Fix typo
  - curl_global_init: Moved the "IPv6 works" check here
  - connect: Disable TFO on Linux when using SSL
  - vauth: Fixed memory leak due to function returning without free
  - winbuild: Fix embedded manifest option
- Fix HTTPS and FTPS tests (work around stunnel bug #1358810)
- Require nss-pem because it is no longer included in the nss package
  (#1347336)

* Wed Jun 22 2016 Paul Howarth <paul@city-fan.org> - 7.49.1-3.1.cf
- Add HTTP/2 protocol support for EL-6 and EL-7 builds too

* Sun Jun 19 2016 Paul Howarth <paul@city-fan.org> - 7.49.1-3.0.cf
- Use multilib-rpm-config to install arch-dependent header files

* Fri Jun  3 2016 Paul Howarth <paul@city-fan.org> - 7.49.1-2.0.cf
- Fix SIGSEGV of the curl tool while parsing URL with too many globs (#1340757)

* Mon May 30 2016 Paul Howarth <paul@city-fan.org> - 7.49.1-1.0.cf
- Update to 7.49.1
  - Windows: prevent DLL hijacking, CVE-2016-4802
  - dist: Include manpage-scan.pl, nroff-scan.pl and CHECKSRC.md
  - schannel: Fix compile break with MSVC XP toolset
  - curlbuild.h.dist: Check __LP64__ as well to fix MIPS build
  - dist: Include curl_multi_socket_all.3
  - http2: Use HTTP/2 in the HTTP/1.1-alike response
  - openssl: ERR_remove_thread_state() is deprecated in latest 1.1.0
  - CURLOPT_CONNECT_TO.3: User must not free the list prematurely
  - libcurl.m4: Avoid obsolete warning
  - winbuild/Makefile.vc: Fix check on SSL, MBEDTLS, WINSSL exclusivity
  - curl_multibyte: Fix compiler error
  - openssl: Cleanup must free compression methods (memory leak)
  - mbedtls: Fix includes so snprintf() works
  - checksrc.pl: Added variants of strcat()/strncat() to banned function list
  - contributors.sh: Better grep pattern and show GitHub username
  - ssh: Fix build for libssh2 before 1.2.6
  - curl_share_setopt.3: Add min ver needed for ssl session lock

* Fri May 20 2016 Paul Howarth <paul@city-fan.org> - 7.49.0-1.1.cf
- Manually install (and package) zsh completion
- Bundle upstream files needed so we can run tests 1139 and 1140

* Wed May 18 2016 Paul Howarth <paul@city-fan.org> - 7.49.0-1.0.cf
- Update to 7.49.0
  - schannel: Add ALPN support
  - SSH: Support CURLINFO_FILETIME
  - SSH: New CURLOPT_QUOTE command "statvfs"
  - wolfssl: Add ALPN support
  - http2: Added --http2-prior-knowledge
  - http2: Added CURL_HTTP_VERSION_2_PRIOR_KNOWLEDGE
  - libcurl: Added CURLOPT_CONNECT_TO
  - curl: Added --connect-to
  - libcurl: Added CURLOPT_TCP_FASTOPEN
  - curl: Added --tcp-fastopen
  - curl: Remove support for --ftpport, -http-request and --socks
    (deprecated versions since around 10 years)
  - CVE-2016-3739: TLS certificate check bypass with mbedTLS/PolarSSL
  - checksrc.bat: Updated the help to be consistent with generate.bat
  - checksrc.bat: Added support for scanning the tests and examples
  - openssl: Fix ERR_remove_thread_state() for boringssl/libressl
  - openssl: boringssl provides the same numbering as openssl
  - multi: Fix "Operation timed out after" timer
  - url: Don't use bad offset in tld_check_name to show error
  - sshserver.pl: Use quotes for given options
  - Makefile.am: Skip the scripts dir
  - curl: Warn for --capath use if not supported by libcurl
  - http2: Fix connection reuse
  - GSS: Make Curl_gss_log_error more verbose
  - build-wolfssl: Allow a broader range of ciphers (Visual Studio)
  - wolfssl: Use ECC supported curves extension
  - openssl: Fix compilation warnings
  - Curl_add_buffer_send: Avoid possible NULL dereference
  - SOCKS5_gssapi_negotiate: Don't assume little-endian ints
  - strerror: Don't bit shift a signed integer
  - url: Corrected get protocol family for FTP and LDAP
  - curl/mprintf.h: Remove support for _MPRINTF_REPLACE
  - upload: Missing rewind call could make libcurl hang
  - IMAP: Check pointer before dereferencing it
  - build: Changed the Visual Studio projects warning level from 3 to 4
  - checksrc: Now stricter, wider checks, code cleaned up
  - checksrc: Added docs/CHECKSRC.md
  - curl_sasl: Fixed potential null pointer utilisation
  - krb5: Fixed missing client response when mutual authentication enabled
  - krb5: Only process challenge when present
  - krb5: Only generate a SPN when its not known
  - formdata: Use appropriate fopen() macros
  - curl.1: -w filename_effective was introduced in 7.26.0
  - http2: Make use of the nghttp2 error callback
  - http2: Fix connection reuse when PING comes after last DATA
  - curl.1: Change example for -F
  - HTTP2: Add a space character after the status code
  - curl.1: Use example.com more
  - mbedtls.c: Changed private prefix to mbed_
  - mbedtls: Implement and provide *_data_pending() to avoid hang
  - mbedtls: Fix MBEDTLS_DEBUG builds
  - ftp/imap/pop3/smtp: Allow the service name to be overridden
  - CURLOPT_SOCKS5_GSSAPI_SERVICE: Merged with CURLOPT_PROXY_SERVICE_NAME
  - build: Include scripts/ in the dist
  - http2: Add handling stream level error
  - http2: Improve header parsing
  - makefile.vc6: Use d suffix on debug object
  - configure: Remove check for libresolve
  - scripts/make: Use $(EXEEXT) for executables
  - checksrc: Got rid of the whitelist files
  - sendf: Added ability to call recv() before send() as workaround
  - NTLM: Check for NULL pointer before dereferencing
  - openssl: Builds with OpenSSL 1.1.0-pre5
  - configure: ac_cv_ -> curl_cv_ for all cached vars
  - winbuild: Add mbedtls support
  - curl: Make --ftp-create-dirs retry on failure
  - PolarSSL: Implement public key pinning
  - multi: Accidentally used resolved host name instead of proxy
  - CURLINFO_TLS_SESSION.3: clarify TLS library support before 7.48.0
  - CONNECT_ONLY: Don't close connection on GSS 401/407 reponses
  - opts: Fix some syntax errors in example code fragments
  - mbedtls: Fix session resume
  - test1139: Verifies libcurl option man page presence
  - CURLINFO_TLS_SSL_PTR.3: Clarify SSL pointer availability
  - curl: Make --disable work as long form of -q
  - curl: Use --telnet-option as documented
  - curl.1: Document --ftp-ssl-reqd, --krb4 and --ntlm-wb
  - curl: -h output lacked --proxy-header and --ntlm-wb
  - curl -J: Make it work even without http:// scheme on URL
  - lib: Include curl_printf.h as one of the last headers
  - tests: Handle path properly on Msys/Cygwin
  - curl.1: --mail-rcpt can be used multiple times
  - CURLOPT_ACCEPT_ENCODING.3: Clarified
  - docs: Fixed lots of broken man page references
  - tls: Make setting pinnedkey option fail if not supported
  - test1140: Run nroff-scan to verify man pages
  - http: Make sure a blank header overrides accept_decoding
  - connections: Do not reuse non-HTTP proxies on different ports
  - connect: Fix invalid "Network is unreachable" errors
  - TLS: Move the ALPN/NPN enable bits to the connection
  - TLS: SSL_peek is not a const operation
  - http2: Add space between colon and header value
  - darwinssl: Fix certificate verification disable on OS X 10.8
  - mprintf: Fix processing of width and prec args
  - ftp wildcard: segfault due to init only in multi_perform
- Update zsh completion patch
- Disable tests 1139 and 1140, which fail due to files missing from tarball
- Upstream not building/installing zsh completion script any longer

* Wed Mar 23 2016 Paul Howarth <paul@city-fan.org> - 7.48.0-1.0.cf
- Update to 7.48.0
  - configure: --with-ca-fallback: Use built-in TLS CA fallback
  - TFTP: Add --tftp-no-options to expose CURLOPT_TFTP_NO_OPTIONS
  - getinfo: CURLINFO_TLS_SSL_PTR supersedes CURLINFO_TLS_SESSION
  - Added CODE_STYLE.md
  - Proxy-Connection: Stop sending this header by default
  - os400: Sync ILE/RPG definitions with latest public header files
  - cookies: Allow spaces in cookie names, cut off trailing spaces
  - tool_urlglob: Allow reserved dos device names (Windows)
  - openssl: Remove most BoringSSL #ifdefs
  - tool_doswin: Support for literal path prefix \\?\
  - mbedtls: Fix ALPN usage segfault
  - mbedtls: Fix memory leak when destroying SSL connection data
  - nss: Do not count enabled cipher-suites
  - examples/cookie_interface.c: Add cleanup call
  - examples: Adhere to curl code style
  - curlx_tvdiff: Handle 32bit time_t overflows
  - dist: Ship buildconf.bat too
  - curl.1: --disable-{eprt,epsv} are ignored for IPv6 hosts
  - generate.bat: Fix comment bug by removing old comments
  - test1604: Add to Makefile.inc so it gets run
  - gtls: Fix for builds lacking encrypted key file support
  - SCP: Use libssh2_scp_recv2 to support > 2GB files on windows
  - CURLOPT_CONNECTTIMEOUT_MS.3: Fix example to use milliseconds option
  - cookie: Do not refuse cookies to localhost
  - openssl: Avoid direct PKEY access with OpenSSL 1.1.0
  - http: Don't break the header into chunks if HTTP/2
  - http2: Don't decompress gzip decoding automatically
  - curlx.c: i2s_ASN1_IA5STRING() clashes with an openssl function
  - curl.1: Add a missing dash
  - curl.1: HTTP headers for --cookie must be Set-Cookie style
  - CURLOPT_COOKIEFILE.3: HTTP headers must be Set-Cookie style
  - curl_sasl: Fix memory leak in digest parser
  - src/Makefile.m32: Add CURL_{LD,C}FLAGS_EXTRAS support
  - CURLOPT_DEBUGFUNCTION.3: Fix example
  - runtests: Fixed usage of %%PWD on MinGW64
  - tests/sshserver.pl: Use RSA instead of DSA for host auth
  - multi_remove_handle: Keep the timeout list until after disconnect
  - Curl_read: Check for activated HTTP/1 pipelining, not only requested
  - configure: Warn on invalid ca bundle or path
  - file: Try reading from files with no size
  - getinfo: Add support for mbedTLS TLS session info
  - formpost: Fix memory leaks in AddFormData error branches
  - makefile.m32: Allow to pass .dll/.exe-specific LDFLAGS
  - url: If Curl_done is premature then pipeline not in use
  - cookie: Remove redundant check
  - cookie: Don't expire session cookies in remove_expired
  - makefile.m32: Fix to allow -ssh2-winssl combination
  - checksrc.bat: Fixed cannot find perl if installed but not in path
  - build-openssl.bat: Fixed cannot find perl if installed but not in path
  - mbedtls: Fix user-specified SSL protocol version
  - makefile.m32: Add missing libs for static -winssl-ssh2 builds
  - test46: Change cookie expiry date
  - pipeline: Sanity check pipeline pointer before accessing it
  - openssl: Use the correct OpenSSL/BoringSSL/LibreSSL in messages
  - ftp_done: Clear tunnel_state when secondary socket closes
  - opt-docs: Fix heading macros
  - imap/pop3/smtp: Fixed connections upgraded with TLS are not reused
  - curl_multi_wait: Never return -1 in 'numfds'
  - url.c: Fix clang warning: no newline at end of file
  - krb5: Improved type handling to avoid clang compiler warnings
  - cookies: First n/v pair in Set-Cookie: is the cookie, then parameters
  - multi: Avoid blocking during CURLM_STATE_WAITPROXYCONNECT
  - multi hash: Ensure modulo performed on curl_socket_t
  - curl: glob_range: No need to check unsigned variable for negative
  - easy: Add check to malloc() when running event-based
  - CURLOPT_SSLENGINE.3: Only for OpenSSL built with engine support
  - version: Thread safety
  - openssl: verbose: Show matching SAN pattern
  - openssl: Adapt to OpenSSL 1.1.0 API breakage in ERR_remove_thread_state()
  - formdata.c: Fixed compilation warning
  - configure: Use cpp -P when needed
  - imap.c: Fixed compilation warning with /Wall enabled
  - config-w32.h: Fixed compilation warning when /Wall enabled
  - ftp/imap/pop3/smtp: Fixed compilation warning when /Wall enabled
  - build: Added missing Visual Studio filter files for VC10 onwards
  - easy: Remove poll failure check in easy_transfer
  - mbedtls: Fix compiler warning
  - build-wolfssl: Update VS properties for wolfSSL v3.9.0
  - Fixed various compilation warnings when verbose strings disabled
- Update patches as needed

* Thu Mar  3 2016 Paul Howarth <paul@city-fan.org> - 7.47.1-4.0.cf
- Do not refuse cookies for localhost (#1308791)

* Wed Feb 17 2016 Paul Howarth <paul@city-fan.org> - 7.47.1-3.0.cf
- Make SCP and SFTP test-cases work with recent OpenSSH versions that don't
  support DSA keys

* Thu Feb 11 2016 Paul Howarth <paul@city-fan.org> - 7.47.1-2.0.cf
- Enable support for Public Suffix List where possible (#1305701)

* Mon Feb  8 2016 Paul Howarth <paul@city-fan.org> - 7.47.1-1.0.cf
- Update to 7.47.1
  - getredirect.c: Fix variable name
  - tool_doswin: Silence unused function warning
  - cmake: Fixed when OpenSSL enabled on Windows and schannel detected
  - curl.1: Explain remote-name behavior if file already exists
  - tool_operate: Don't sanitize --output path (Windows)
  - URLs: Change all http:// URLs to https:// in documentation & comments
  - sasl_sspi: Fix memory leak in domain populate
  - COPYING: Clarify that Daniel is not the sole author
  - examples/htmltitle: Use _stricmp on Windows
  - examples/asiohiper: Avoid function name collision on Windows
  - idn_win32: Better error checking
  - openssl: Fix signed/unsigned mismatch warning in X509V3_ext
  - curl save files: Check for backslashes on cygwin
- Update patches as needed

* Thu Feb  4 2016 Paul Howarth <paul@city-fan.org> - 7.47.0-2.0.cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Jan 27 2016 Paul Howarth <paul@city-fan.org> - 7.47.0-1.0.cf
- Update to 7.47.0
  - version: Add flag CURL_VERSION_PSL for libpsl
  - http: Added CURL_HTTP_VERSION_2TLS to do HTTP/2 for HTTPS only
  - curl: Use 2TLS by default
  - curl --expect100-timeout: added
  - Add .dir-locals and set c-basic-offset to 2 (for emacs)
  - curl: Avoid local drive traversal when saving file on Windows
    (CVE-2016-0754)
  - NTLM: Do not resuse proxy connections without diff proxy credentials
    (CVE-2016-0755)
  - tests: Disable the OAUTHBEARER tests when using a non-default port number
  - curl: Remove keepalive #ifdef checks done on libcurl's behalf
  - formdata: Check if length is too large for memory
  - lwip: Fix compatibility issues with later versions
  - openssl: BoringSSL doesn't have CONF_modules_free
  - config-win32: Fix warning HAVE_WINSOCK2_H undefined
  - build: Fix compilation error with CURL_DISABLE_VERBOSE_STRINGS
  - http2: Fix hanging paused stream
  - scripts/Makefile: Fix GNUism and survive no perl
  - openssl: Adapt to 1.1.0+ name changes
  - openssl: Adapt to openssl ≥ 1.1.0 X509 opaque structs
  - HTTP2.md: Spell fix and remove TODO now implemented
  - setstropt: const-correctness
  - cyassl: Fix compiler warning on type conversion
  - gskit: Fix host subject altname verification
  - http2: Support trailer fields
  - wolfssl: Handle builds without SSLv3 support
  - cyassl: Deal with lack of *get_peer_certificate
  - sockfilt: Do not wait on unreliable file or pipe handle
  - make: Build zsh script even in an out-of-tree build
  - test 1326: Fix getting stuck on Windows
  - test 87: Fix file check on Windows
  - configure: Allow static builds on mingw
  - configure: Detect IPv6 support on Windows
  - ConnectionExists: With *PIPEWAIT, wait for connections
  - Makefile.inc: s/curl_SOURCES/CURL_FILES
  - test 16: Fixed for Windows
  - test 252-255: Use datacheck mode text for ASCII-mode LISTings
  - tftpd server: Add Windows support by writing files in binary mode
  - ftplistparser: Fix handling of file LISTings using Windows EOL
  - tests first.c: Fix calculation of sleep timeout on Windows
  - tests (several): Use datacheck mode text for ASCII-mode LISTings
  - CURLOPT_RANGE.3: For HTTP servers, range support is optional
  - test 1515: Add MSYS support by passing a relative path
  - curl_global_init.3: Add Windows-specific info for init via DLL
  - http2: Fix client write for trailers on stream close
  - mbedtls: Fix ALPN support
  - connection reuse: IDN host names fixed
  - http2: Fix PUSH_PROMISE headers being treated as trailers
  - http2: Handle the received SETTINGS frame
  - http2: Ensure that http2_handle_stream_close is called
  - mbedtls: Implement CURLOPT_PINNEDPUBLICKEY
  - runtests: Add mbedTLS to the SSL backends
  - IDN host names: Remove the port number before converting to ACE
  - zsh.pl: Fail if no curl is found
  - scripts: Fix zsh completion generation
  - scripts: Don't generate and install zsh completion when cross-compiling
  - lib: Prefix URLs with lower-case protocol names/schemes
  - ConnectionExists: Only do pipelining/multiplexing when asked
  - configure: Assume IPv6 works when cross-compiled
  - openssl: For 1.1.0+ they now provide a SSLeay() macro of their own
  - openssl: Improved error detection/reporting
  - ssh: CURLOPT_SSH_PUBLIC_KEYFILE now treats "" as NULL again
  - mbedtls: Fix pinned key return value on fail
  - maketgz: Generate date stamp with LC_TIME=C
- Re-enable previously-disabled tests
- Fix FTBFS when building curl dynamically with no libcurl.so.4 in system

* Fri Dec  4 2015 Paul Howarth <paul@city-fan.org> - 7.46.0-2.0.cf
- Rebuild for #1288529

* Wed Dec  2 2015 Paul Howarth <paul@city-fan.org> - 7.46.0-1.0.cf
- Update to 7.46.0
  - configure: build silently by default
  - cookies: Add support for Public Suffix List with libpsl
  - vtls: Added support for mbedTLS
  - Added CURLOPT_STREAM_DEPENDS
  - Added CURLOPT_STREAM_DEPENDS_E
  - Added CURLOPT_STREAM_WEIGHT
  - Added CURLFORM_CONTENTLEN
  - oauth2: Added support for OAUTHBEARER SASL mechanism to IMAP, POP3 and SNMP
  - des: Fix header conditional for Curl_des_set_odd_parity
  - ntlm: Get rid of unconditional use of long long
  - CURLOPT_CERTINFO.3: Fix reference to CURLINFO_CERTINFO
  - docs: CURLINFO_LASTSOCKET => CURLINFO_ACTIVESOCKET
  - http2: Fix http2_recv to return -1 if recv returned -1
  - curl_global_init_mem: Set function pointers before doing init
  - ntlm: Error out without 64bit support as the code needs it
  - openssl: Fix set up of pkcs12 certificate verification chain
  - acinclude: Remove PKGCONFIG override
  - test1531: case the size to fix the test on non-largefile builds
  - fread_func: Move callback pointer from set to state struct
  - test1601: Fix compilation with --enable-debug and --disable-crypto-auth
  - http2: Don't pass uninitialized name+len pairs to nghttp2_submit_request
  - curlbuild.h: Fix non-configure compiling to mips and sh4 targets
  - tool: Generate easysrc with last cache linked-list
  - cmake: Fix for add_subdirectory(curl) use-case
  - vtls: Fix compiler warning for TLS backends without sha256
  - build: Fix for MSDOS/djgpp
  - checksrc: Add crude // detection
  - http2: on_frame_recv: Trust the conn/data input
  - ftp: Allow CURLOPT_IGNORE_CONTENT_LENGTH to ignore size
  - polarssl/mbedtls: Fix name space pollution
  - build: Fix mingw ssl gdi32 order
  - build: Fix support for PKG_CONFIG
  - MacOSX-Framework: sdk regex fix for sdk 10.10 and later
  - socks: Fix incorrect port numbers in failed connect messages
  - curl.1: -E: s/private certificate/client certificate/
  - curl.h: s/HTTPPOST_/CURL_HTTPOST_/
  - curl_formadd: Support >2GB files on windows
  - http redirects: %%-encode bytes outside of ascii range
  - rawstr: Speed up Curl_raw_toupper by 40%%
  - curl_ntlm_core: Fix 2 curl_off_t constant overflows
  - getinfo: CURLINFO_ACTIVESOCKET: Fix bad socket value
  - tftp tests: Verify sent options too
  - imap: Don't call imap_atom() when no mailbox specified in LIST command
  - imap: Fixed double quote in LIST command when mailbox contains spaces
  - imap: Don't check for continuation when executing a CUSTOMREQUEST
  - acinclude: Remove check for 16-bit curl_off_t
  - BoringSSL: Work with stricter BIO_get_mem_data()
  - cmake: Add missing feature macros in config header
  - sasl_sspi: Fixed unicode build for digest authentication
  - sasl_sspi: Fix identity memory leak in digest authentication
  - unit1602: Fixed failure in torture test
  - unit1603: Added unit tests for hash functions
  - vtls/openssl: Remove unused traces of yassl ifdefs
  - openssl: Remove #ifdefs for < 0.9.7 support
  - typecheck-gcc.h: Add some missing options
  - curl: Mark two more options strings for --libcurl output
  - openssl: Free modules on cleanup
  - CURLMOPT_PUSHFUNCTION.3: *_byname() returns only the first header
  - getconnectinfo: Don't call recv(2) if socket == -1
  - http2: http_done: Don't free already-freed push headers
  - zsh completion: Preserve single quotes in output
  - os400: Provide options for libssh2 use in compile scripts
  - build: Fix theoretical infinite loops
  - pop3: Differentiate between success and continuation responses
  - examples: Fixed compilation warnings
  - schannel: Use GetVersionEx() when VerifyVersionInfo() isn't available
  - CURLOPT_HEADERFUNCTION.3: fix typo
  - curl: Expanded the -XHEAD warning text
  - done: Make sure the final progress update is made
  - build: Install zsh completion
  - RTSP: Do not add if-modified-since without timecondition
  - curl: Fixed display of URL index in password prompt for --next
  - nonblock: Fix setting non-blocking mode for Amiga
  - http2 push: Add missing inits of new stream
  - http2: Convert some verbose output into debug-only output
  - Curl_read_plain: clean up ifdefs that break statements
- Explicitly turn off silent building so we can see the compiler flags used
- Disable OAUTHBEARER tests since they don't work with custom test ports

* Wed Oct  7 2015 Paul Howarth <paul@city-fan.org> - 7.45.0-1.0.cf
- Update to 7.45.0
  - Added CURLOPT_DEFAULT_PROTOCOL
  - Added new tool option --proto-default
  - getinfo: Added CURLINFO_ACTIVESOCKET
  - Turned CURLINFO_* option docs as stand-alone man pages
  - curl: Point out unnecessary uses of -X in verbose mode
  - curl_global_init_mem.3: Stronger thread safety warning
  - buildconf.bat: Fixed issues when ran in directories with special chars
  - cmake: Fix CurlTests check for gethostbyname_r with 5 arguments
  - generate.bat: Fixed issues when ran in directories with special chars
  - generate.bat: Only call buildconf.bat if it exists
  - generate.bat: Added support for generating only the prerequisite files
  - curl.1: Document weaknesses in SSLv2 and SSLv3
  - CURLOPT_HTTP_VERSION.3: Connection re-use goes before version
  - docs: Update the redirect protocols disabled by default
  - inet_pton.c: Fix MSVC run-time check failure
  - CURLMOPT_PUSHFUNCTION.3: Fix argument types
  - rtsp: Support basic/digest authentication
  - rtsp: Stop reading empty DESCRIBE responses
  - travis: Upgrading to container based build
  - travis.yml: Add OS X testbot
  - FTP: Make state machine not get stuck in state
  - openssl: Handle lack of server cert when strict checking disabled
  - configure: Change functions to detect openssl (clones)
  - configure: Detect latest boringssl
  - runtests: Allow for spaces in server-verify curl custom path
  - http2: on_frame_recv: Get a proper 'conn' for the debug logging
  - ntlm: Mark deliberate switch case fall-through
  - http2: Remove dead code
  - curl_easy_{escape,unescape}.3: "char *" vs. "const char *"
  - curl: Point out the conflicting HTTP methods if used
  - cmake: Added Windows SSL support
  - curl_easy_{escape,setopt}.3: Fix example
  - curl_easy_escape.3: Escape '\n'
  - libcurl.m4: Put braces around empty if body
  - buildconf.bat: Fixed double blank line in 'curl manual' warning output
  - sasl: Only define Curl_sasl_digest_get_pair() when CRYPTO_AUTH enabled
  - inet_pton.c: Fix MSVC run-time check failure
  - CURLOPT_FOLLOWLOCATION.3: Mention methods for redirects
  - http2: Don't pass on Connection: headers
  - nss: Do not directly access SSL_ImplementedCiphers
  - docs: Numerous cleanups and spelling fixes
  - FTP: do_more: Add check for wait_data_conn in upload case
  - parse_proxy: Reject illegal port numbers
  - cmake: IPv6 : Disable Unix header check on Windows platform
  - winbuild: Run buildconf.bat if necessary
  - buildconf.bat: Fix syntax error
  - curl_sspi: Fix possibly undefined CRYPT_E_REVOKED
  - nss: Prevent NSS from incorrectly re-using a session
  - libcurl-errors.3: Add two missing error codes
  - openssl: Fix build with < 0.9.8
  - openssl: Refactor certificate parsing to use OpenSSL memory BIO
  - openldap: Only part of LDAP query results received
  - ssl: Add server cert's "sha256//" hash to verbose
  - NTLM: Reset auth-done when using a fresh connection
  - curl: Generate easysrc only on --libcurl
  - tests: Disable 1801 until fixed
  - CURLINFO_TLS_SESSION: Always return backend info
  - gnutls: Support CURLOPT_KEYPASSWD
  - gnutls: Report actual GnuTLS error message for certificate errors
  - tests: Disable 1510 due to CI-problems on github
  - cmake: Put "winsock2.h" before "windows.h" during configure checks
  - cmake: Ensure discovered include dirs are considered
  - configure: Add missing ')' for CURL_CHECK_OPTION_RT
  - build: Fix failures with -Wcast-align and -Werror
  - FTP: Fix uploading ASCII with unknown size
  - readwrite_data: Set a max number of loops
  - http2: Avoid superfluous Curl_expire() calls
  - http2: Set TCP_NODELAY unconditionally
  - docs: Fix unescaped '\n' in man pages
  - openssl: Fix algorithm init to make (gost) engines work
  - win32: Make recent Borland compilers use long long
  - runtests: Fix pid check in checkdied
  - gopher: Don't send NUL byte
  - tool_setopt: Fix c_escape truncated octal
  - hiperfifo: Fix the pointer passed to WRITEDATA
  - getinfo: Fix return code for unknown CURLINFO options

* Fri Sep 18 2015 Paul Howarth <paul@city-fan.org> - 7.44.0-2.0.cf
- Prevent NSS from incorrectly re-using a session (#1104597)

* Wed Aug 12 2015 Paul Howarth <paul@city-fan.org> - 7.44.0-1.0.cf
- Update to 7.44.0
  - http2: Added CURLMOPT_PUSHFUNCTION and CURLMOPT_PUSHDATA
  - examples: Added http2-serverpush.c
  - http2: Added curl_pushheader_byname() and curl_pushheader_bynum()
  - docs: Added CODE_OF_CONDUCT.md
  - curl: Add --ssl-no-revoke to disable certificate revocation checks
  - libcurl: New value CURLSSLOPT_NO_REVOKE for CURLOPT_SSL_OPTIONS
  - makefile: Added support for VC14
  - build: Added Visual Studio 2015 (VC14) project files
  - build: Added wolfSSL configurations to VC10+ project files
  - FTP: Fix HTTP CONNECT logic regression
  - openssl: Fix build with openssl < ~ 0.9.8f
  - openssl: Fix build with BoringSSL
  - curl_easy_setopt.3: Option order doesn't matter
  - openssl: Fix use of uninitialized buffer
  - RTSP: Removed dead code
  - Makefile.m32: Add support for CURL_LDFLAG_EXTRAS
  - curl: Always provide negotiate/kerberos options
  - cookie: Fix bug in export if any-domain cookie is present
  - curl_easy_setopt.3: Mention CURLOPT_PIPEWAIT
  - INSTALL: Advise use of non-native SSL for Windows <= XP
  - tool_help: Fix --tlsv1 help text to use >= for TLSv1
  - HTTP: POSTFIELDSIZE set after added to multi handle
  - SSL-PROBLEMS: Mention WinSSL problems in WinXP
  - setup-vms.h: Symbol case fixups
  - SSL: Pinned public key hash support
  - libtest: Call PR_Cleanup() on exit if NSPR is used
  - ntlm_wb: Fix theoretical memory leak
  - runtests: Allow for spaces in curl custom path
  - http2: Add stream != NULL checks for reliability
  - schannel: Replace deprecated GetVersion with VerifyVersionInfo
  - http2: Verify success of strchr() in http2_send()
  - configure: Add --disable-rt option
  - openssl: Work around MSVC warning
  - HTTP: Ignore "Content-Encoding: compress"
  - configure: Check if OpenSSL linking wants -ldl
  - build-openssl.bat: Show syntax if required args are missing
  - test1902: Attempt to make the test more reliable
  - libcurl-thread.3: Consolidate thread safety info
  - maketgz: Fixed some VC makefiles missing from the release tarball
  - libcurl-multi.3: Mention curl_multi_wait
  - ABI doc: Use secure URL
  - http: Move HTTP/2 cleanup code off http_disconnect()
  - libcurl-thread.3: Warn memory functions must be thread safe
  - curl_global_init_mem.3: Warn threaded resolver needs thread safe funcs
  - docs: formpost needs the full size at start of upload
  - curl_gssapi: Remove 'const' to fix compiler warnings
  - SSH: Three state machine fixups
  - libcurl.3: Fix a single typo
  - generate.bat: Only clean prerequisite files when in ALL mode
  - curl_slist_append.3: Add error checking to the example
  - buildconf.bat: Added support for file clean-up via -clean
  - generate.bat: Use buildconf.bat for prerequisite file clean-up
  - NTLM: Handle auth for only a single request
  - curl_multi_remove_handle.3: Fix formatting
  - checksrc.bat: Fixed error when [directory] isn't a curl source directory
  - checksrc.bat: Fixed error when missing *.c and *.h files
  - CURLOPT_RESOLVE.3: Note removal support was added in 7.42
  - test46: Update cookie expire time
  - SFTP: Fix range request off-by-one in size check
  - CMake: Fix GSSAPI builds
  - build: Refer to fixed libidn versions
  - http2: Discard frames with no SessionHandle
  - curl_easy_recv.3: Fix formatting
  - libcurl-tutorial.3: Fix formatting
  - curl_formget.3: Correct return code

* Thu Jul 30 2015 Paul Howarth <paul@city-fan.org> - 7.43.0-3.0.cf
- Prevent dnf from crashing when using both FTP and HTTP (#1248389)
- Add HTTP/2 protocol support for Fedora 23 too

* Sat Jul 18 2015 Paul Howarth <paul@city-fan.org> - 7.43.0-2.0.cf
- Build support for the HTTP/2 protocol (Fedora 24 onwards)

* Wed Jun 17 2015 Paul Howarth <paul@city-fan.org> - 7.43.0-1.0.cf
- Update to 7.43.0
  - CVE-2015-3236: Lingering HTTP credentials in connection re-use
  - CVE-2015-3237: SMB send off unrelated memory contents
  - Added CURLOPT_PROXY_SERVICE_NAME
  - Added CURLOPT_SERVICE_NAME
  - New curl option: --proxy-service-name
  - New curl option: --service-name
  - New curl option: --data-raw
  - Added CURLOPT_PIPEWAIT
  - Added support for multiplexing transfers using HTTP/2, enable this
    with the new CURLPIPE_MULTIPLEX bit for CURLMOPT_PIPELINING
  - HTTP/2: Requires nghttp2 1.0.0 or later
  - scripts: Add zsh.pl for generating zsh completion
  - curl.h: Add CURL_HTTP_VERSION_2
  - nss: Fix compilation failure with old versions of NSS
  - curl_easy_getinfo.3: Document 'internals' in CURLINFO_TLS_SESSION
  - schannel.c: Fix possible SEC_E_BUFFER_TOO_SMALL error
  - Curl_ossl_init: Load built-in modules
  - configure: Follow-up fix for krb5-config
  - sasl_sspi: Populate domain from the realm in the challenge
  - netrc: Support 'default' token
  - README: Convert to UTF-8
  - cyassl: Implement public key pinning
  - nss: Implement public key pinning for NSS backend
  - mingw build: Add arch -m32/-m64 to LDFLAGS
  - schannel: Fix out of bounds array
  - configure: Remove autogenerated files by autoconf
  - configure: Remove --automake from libtoolize call
  - acinclude.m4: Fix shell test for default CA cert bundle/path
  - schannel: Fix regression in schannel_recv
  - openssl: Skip trace outputs for ssl_ver == 0
  - gnutls: Properly retrieve certificate status
  - netrc: Read in text mode when cygwin
  - winbuild: Document the option used to statically link the CRT
  - FTP: Make EPSV use the control IP address rather than the original host
  - FTP: fIx dangling conn->ip_addr dereference on verbose EPSV
  - conncache: Keep bundles on host+port bases, not only host names
  - runtests.pl: Use 'h2c' now, no -14 anymore
  - curlver: Introducing new version number (checking) macros
  - openssl: boringssl build breakage, use SSL_CTX_set_msg_callback
  - CURLOPT_POSTFIELDS.3: Correct variable names
  - curl_easy_unescape.3: Update RFC reference
  - gnutls: Don't fail on non-fatal alerts during handshake
  - testcurl.pl: Allow source to be in an arbitrary directory
  - CURLOPT_HTTPPROXYTUNNEL.3: Only works with a HTTP proxy
  - SSPI-error: Change SEC_E_ILLEGAL_MESSAGE description
  - parse_proxy: Switch off tunneling if non-HTTP proxy
  - share_init: Fix OOM crash
  - perl: Remove subdir, not touched in 9 years
  - CURLOPT_COOKIELIST.3: Add example
  - CURLOPT_COOKIE.3: Explain that the cookies won't be modified
  - CURLOPT_COOKIELIST.3: Explain Set-Cookie without a domain
  - FAQ: How do I port libcurl to my OS?
  - openssl: Use TLS_client_method for OpenSSL 1.1.0+
  - HTTP-NTLM: Fail auth on connection close instead of looping
  - curl_setup: Add macros for FOPEN_READTEXT, FOPEN_WRITETEXT
  - curl_getdate.3: Update RFC reference
  - curl_multi_info_read.3: Added example
  - curl_multi_perform.3: Added example
  - curl_multi_timeout.3: Added example
  - cookie: Stop exporting any-domain cookies
  - openssl: Remove dummy callback use from SSL_CTX_set_verify()
  - openssl: Remove SSL_get_session()-using code
  - openssl: Removed USERDATA_IN_PWD_CALLBACK kludge
  - openssl: Removed error string #ifdef
  - openssl: Fix verification of server-sent legacy intermediates
  - docs: man page indentation and syntax fixes
  - docs: Spelling fixes
  - fopen.c: Fix a few compiler warnings
  - CURLOPT_OPENSOCKETFUNCTION: Return error at once
  - schannel: Add support for optional client certificates
  - build: Properly detect OpenSSL 1.0.2 when using configure
  - urldata: Store POST size in state.infilesize too
  - security: choose_mech: Remove dead code
  - rtsp_do: Remove dead code
  - docs: Many HTTP URIs changed to HTTPS
  - schannel: schannel_recv overhaul
- Fix build for old openssl versions without SSL3_MT_NEWSESSION_TICKET

* Sat Jun  6 2015 Paul Howarth <paul@city-fan.org> - 7.42.1-2.0.cf
- curl-config --libs now works on x86_64 without libcurl-devel.x86_64
  (#1228363)

* Wed Apr 29 2015 Paul Howarth <paul@city-fan.org> - 7.42.1-1.0.cf
- Update to 7.42.1
  - CURLOPT_HEADEROPT: default to separate (CVE-2015-3153)
  - dist: include {src,lib}/checksrc.whitelist
  - connectionexists: fix build without NTLM
  - docs: distribute the CURLOPT_PINNEDPUBLICKEY(3) man page, too
  - curl -z: do not write empty file on unmet condition
  - openssl: fix serial number output
  - curl_easy_getinfo.3: document 'internals' in CURLINFO_TLS_SESSION
  - sws: init http2 state properly
  - curl.1: fix typo

* Wed Apr 22 2015 Paul Howarth <paul@city-fan.org> - 7.42.0-1.1.cf
- Implement public key pinning for NSS backend (#1195771)
- Do not run flaky test-cases in %%check

* Wed Apr 22 2015 Paul Howarth <paul@city-fan.org> - 7.42.0-1.0.cf
- Update to 7.42.0
  - openssl: Show the cipher selection to use in verbose text
  - gtls: Implement CURLOPT_CERTINFO
  - Add CURLOPT_SSL_FALSESTART option (darwinssl and NSS)
  - curl: Add --false-start option
  - Add CURLOPT_PATH_AS_IS
  - curl: Add --path-as-is option
  - curl: Create output file on successful download of an empty file
  - ConnectionExists: For NTLM re-use, require credentials to match
    (CVE-2015-3143)
  - Cookie: Cookie parser out of boundary memory access (CVE-2015-3145)
  - fix_hostname: Zero length host name caused -1 index offset (CVE-2015-3144)
  - http_done: Close Negotiate connections when done (CVE-2015-3148)
  - sws: Timeout idle CONNECT connections
  - nss: Improve error handling in Curl_nss_random()
  - nss: Do not skip Curl_nss_seed() if data is NULL
  - curl-config.in: Eliminate double quotes around CURL_CA_BUNDLE
  - http2: Move lots of verbose output to be debug-only
  - dist: Add extern-scan.pl to the tarball
  - http2: Return recv error on unexpected EOF
  - build: Use default RandomizedBaseAddress directive in VC9+ project files
  - build: Removed DataExecutionPrevention directive from VC9+ project files
  - tool: Updated the warnf() function to use the GlobalConfig structure
  - http2: Return error if stream was closed with other than NO_ERROR
  - mprintf.h: Remove #ifdef CURLDEBUG
  - libtest: Fixed linker errors on msvc
  - tool: Use ENABLE_CURLX_PRINTF instead of _MPRINTF_REPLACE
  - curl.1: Fix "The the" typo
  - cmake: Handle build definitions CURLDEBUG/DEBUGBUILD
  - openssl: Remove all uses of USE_SSLEAY
  - multi: Fix memory-leak on timeout (regression)
  - curl_easy_setopt.3: Added CURLOPT_SSL_VERIFYSTATUS
  - metalink: Add some error checks
  - TLS: Make it possible to enable ALPN/NPN without HTTP/2
  - http2: Use CURL_HTTP_VERSION_* symbols instead of NPN_*
  - conncontrol: Only log changes to the connection bit
  - multi: Fix *getsock() with CONNECT
  - symbols.pl: Handle '-' in the deprecated field
  - MacOSX-Framework: Use @rpath instead of @executable_path
  - GnuTLS: Add support for CURLOPT_CAPATH
  - GnuTLS: Print negotiated TLS version and full cipher suite name
  - GnuTLS: Don't print double newline after certificate dates
  - memanalyze.pl: Handle free(NULL)
  - proxy: Re-use proxy connections (regression)
  - mk-ca-bundle: Don't report SHA1 numbers with "-q"
  - http: Always send Host: header as first header
  - openssl: Sort ciphers to use based on strength
  - openssl: Use colons properly in the ciphers list
  - http2: Detect premature close without data transferred
  - hostip: Fix signal race in Curl_resolv_timeout
  - closesocket: Call multi socket cb on close even with custom close
  - mksymbolsmanpage.pl: Use std header and generate better nroff header
  - connect: Fix happy eyeballs logic for IPv4-only builds
  - curl_easy_perform.3: Remove superfluous close brace from example
  - HTTP: Don't use Expect: headers when on HTTP/2
  - Curl_sh_entry: Remove unused 'timestamp'
  - docs/libcurl: Makefile portability fix
  - mkhelp: Remove trailing carriage return from every line of input
  - nss: Explicitly tell NSS to disable NPN/ALPN when libcurl disables it
  - curl_easy_setopt.3: Added a few missing options
  - metalink: Fix resource leak in OOM
  - axtls: Version 1.5.2 now requires that config.h be manually included
  - HTTP: Don't switch to HTTP/2 from 1.1 until we get the 101
  - cyassl: Detect the library as renamed wolfssl
  - CURLOPT_HTTPHEADER.3: Add a "SECURITY CONCERNS" section
  - CURLOPT_URL.3: Added "SECURITY CONCERNS"
  - openssl: Try to avoid accessing OCSP structs when possible
  - test938: Added missing closing tags
  - testcurl: Allow '=' in values given on command line
  - tests/certs: Added make target to rebuild certificates
  - tests/certs: Rebuild certificates with modified key usage bits
  - gtls: Avoid uninitialized variable
  - gtls: Dereferencing NULL pointer
  - gtls: Add check of return code
  - test1513: Eliminated race condition in test run
  - dict: Rename byte to avoid compiler shadowed declaration warning
  - curl_easy_recv/send: Make them work with the multi interface
  - vtls: Fix compile with --disable-crypto-auth but with SSL
  - openssl: Adapt to ASN1/X509 things gone opaque in 1.1
  - openssl: verifystatus: Only use the OCSP work-around <= 1.0.2a
  - curl_memory: Make curl_memory.h the second-last header file loaded
  - testcurl.pl: Add the --notes option to supply more info about a build
  - cyassl: If wolfSSL then identify as such in version string
  - cyassl: Check for invalid length parameter in Curl_cyassl_random
  - cyassl: Default to highest possible TLS version
  - Curl_ssl_md5sum: Return CURLcode (fixes OOM)
  - polarssl: Remove dead code
  - polarssl: Called mbedTLS in 1.3.10 and later
  - globbing: Fix step parsing for character globbing ranges
  - globbing: Fix url number calculation when using range with step
  - multi: On a request completion, check all CONNECT_PEND transfers
  - build: Link curl to openssl libraries when openssl support is enabled
  - url: Don't accept CURLOPT_SSLVERSION unless USE_SSL is defined
  - vtls: Don't accept unknown CURLOPT_SSLVERSION values
  - build: Fix libcurl.sln erroneous mixed configurations
  - cyassl: Remove undefined reference to CyaSSL_no_filesystem_verify
  - cyassl: Add SSL context callback support for CyaSSL
  - tool: Only set SSL options if SSL is enabled
  - multi: Remove_handle: move pending connections
  - configure: Use KRB5CONFIG for krb5-config
  - axtls: Add timeout within Curl_axtls_connect
  - CURLOPT_HTTP200ALIASES.3: Mainly SHOUTcast servers use "ICY 200"
  - cyassl: Fix library initialization return value
  - cookie: Handle spaces after the name in Set-Cookie
  - http2: Fix missing nghttp2_session_send call in Curl_http2_switched
  - cyassl: Fix certificate load check
  - build-openssl.bat: Fix mixed line endings
  - checksrc.bat: Check lib\vtls source
  - DNS: Fix refreshing of obsolete dns cache entries
  - CURLOPT_RESOLVE: Actually implement removals
  - checksrc.bat: Quotes to support an SRC_DIR with spaces
  - cyassl: Remove 'Connecting to' message from cyassl_connect_step2
  - cyassl: Use CYASSL_MAX_ERROR_SZ for error buffer size
  - lib/transfer.c: Remove factor of 8 from sleep time calculation
  - lib/makefile.m32: Add missing libs to build libcurl.dll
  - build: Generate source prerequisites for Visual Studio in generate.bat
  - cyassl: Include the CyaSSL build config
  - firefox-db2pem: Fix wildcard to find Firefox default profile
  - BUGS: Refer to the github issue tracker now as primary
  - vtls_openssl: Improve several certificate error messages
  - cyassl: Add support for TLS extension SNI
  - parsecfg: Do not continue past a zero termination
  - configure --with-nss=PATH: Query pkg-config if available
  - configure --with-nss: Drop redundant if statement
  - cyassl: Fix include order
  - HTTP: Fix PUT regression with Negotiate
  - curl_version_info.3: Fixed the 'protocols' variable type
- Add patch to disabled unsupported TLS False Start support in NSS builds
  with NSS < 3.15.4

* Wed Feb 25 2015 Paul Howarth <paul@city-fan.org> - 7.41.0-1.0.cf
- Update to 7.41.0
  - NetWare build: added TLS-SRP enabled build
  - winbuild: Added option to build with c-ares
  - Added --cert-status
  - Added CURLOPT_SSL_VERIFYSTATUS
  - sasl: Implement EXTERNAL authentication mechanism
  - sasl_gssapi: Fixed build on NetBSD with built-in GSS-API
  - FTP: Fix IPv6 host using link-local address
  - FTP: If EPSV fails on IPV6 connections, bail out
  - gssapi: Remove need for duplicated GSS_C_NT_HOSTBASED_SERVICE definitions
  - NSS: Fix compiler error when built http2-enabled
  - mingw build: allow to pass custom CFLAGS
  - Add -m64 CFLAGS when targeting mingw64, add -m32/-m64 to LDFLAGS
  - curl_schannel.c: Mark session as removed from cache if not freed
  - Curl_pretransfer: Reset expected transfer sizes
  - curl.h: Remove extra space
  - curl_endian: Fixed build when 64-bit integers are not supported
  - checksrc.bat: Better detection of Perl installation
  - build-openssl.bat: Added check for Perl installation
  - http_negotiate: Return CURLcode in Curl_input_negotiate() instead of int
  - http_negotiate: Added empty decoded challenge message info text
  - vtls: Removed unimplemented overrides of curlssl_close_all()
  - sasl_gssapi: Fixed memory leak with local SPN variable
  - http_negotiate: Use dynamic buffer for SPN generation
  - ldap: Renamed the CURL_LDAP_WIN definition to USE_WIN32_LDAP
  - openssl: Do public key pinning check independently
  - timeval: Typecast for better type (on Amiga)
  - ipv6: Enclose AF_INET6 uses with proper #ifdefs for ipv6
  - SASL: Common URL option and auth capabilities decoders for all protocols
  - BoringSSL: Fix build
  - BoringSSL: Detected by configure, switches off NTLM
  - openvms: Handle openssl/0.8.9zb version parsing
  - configure: Detect libresssl
  - configure: Remove detection of the old yassl emulation API
  - curl_setup: Disable SMB/CIFS support when HTTP only
  - imap: Remove automatic password setting: it breaks external sasl authentication
  - sasl: Remove XOAUTH2 from default enabled authentication mechanism
  - runtests: Identify BoringSSL and libressl
  - Security: Avoid compiler warning
  - ldap: Build with BoringSSL
  - des: Added Curl_des_set_odd_parity()
  - CURLOPT_SEEKFUNCTION.3: also when server closes a connection
  - CURLOPT_HTTP_VERSION.3: CURL_HTTP_VERSION_2_0 added in 7.33.0
  - build: Removed unused Visual Studio bscmake settings
  - build: Enabled DEBUGBUILD in Visual Studio debug builds
  - build: Renamed top level Visual Studio solution files
  - build: Removed Visual Studio SuppressStartupBanner directive for VC8+
  - libcurl-symbols: First basic shot for autogenerated docs
  - Makefile.am: fix 'make distcheck'
  . getpass_r: Read from stdin, not stdout!
  - getpass: Protect include with proper #ifdef
  - opts: CURLOPT_CAINFO availability depends on SSL engine
  - More cleanup of 'CURLcode result' return code
  - MD4: Replace implementation
  - MD5: Replace implementation
  - openssl: SSL_SESSION->ssl_version no longer exist
  - md5: use axTLS's own MD5 functions when available
  - schannel: Removed curl_ prefix from source files
  - curl.1: Add warning when using -H and redirects
  - curl.1: Clarify that -X is used for all requests
  - gskit: Fix exclusive SSLv3 option
  - polarssl: Fix exclusive SSL protocol version options
  - http2: Fix bug that associated stream canceled on PUSH_PROMISE
  - ftp: Accept all 2xx responses to the PORT command
  - configure: Allow both --with-ca-bundle and --with-ca-path
  - cmake: Install the dll file to the correct directory
  - nss: Fix NPN/ALPN protocol negotiation
  - polarssl: Fix ALPN protocol negotiation
  - cmake: Fix generation of tool_hugehelp.c on windows
  - cmake: Fix winsock2 detection on windows
  - gnutls: Fix build with HTTP2
  - connect: Fix a spurious connect failure on dual-stacked hosts
  - test: Test 530 is now less timing dependent
  - telnet: Invalid use of custom read function if not set
- Include extern-scan.pl to make test1135 succeed (upstream commit 1514b718)

* Mon Feb 23 2015 Paul Howarth <paul@city-fan.org> - 7.40.0-3.0.cf
- Fix a spurious connect failure on dual-stacked hosts (#1187531)

* Sun Feb 22 2015 Paul Howarth <paul@city-fan.org> - 7.40.0-2.0.cf
- Rebuilt for Fedora 23 Change
  https://fedoraproject.org/wiki/Changes/Harden_all_packages_with_position-independent_code

* Thu Jan  8 2015 Paul Howarth <paul@city-fan.org> - 7.40.0-1.0.cf
- Update to 7.40.0 (addresses CVE-2014-8150 and CVE-2014-8151)
  - http_digest: added support for Windows SSPI based authentication
  - version info: added Kerberos V5 to the supported features
  - Makefile: added VC targets for WinIDN
  - config-win32: introduce build targets for VS2012+
  - SSL: add PEM format support for public key pinning
  - smtp: added support for the conversion of Unix newlines during mail send
  - smb: added initial support for the SMB/CIFS protocol
  - added support for HTTP over unix domain sockets, via
    CURLOPT_UNIX_SOCKET_PATH and --unix-socket
  - sasl: added support for GSS-API based Kerberos V5 authentication
  - darwinssl: fix session ID keys to only reuse identical sessions
  - url-parsing: reject CRLFs within URLs
  - OS400: adjust specific support to last release
  - THANKS: remove duplicate names
  - url.c: fixed compilation warning
  - ssh: fixed build on platforms where R_OK is not defined
  - tool_strdup.c: include the tool strdup.h
  - build: fixed Visual Studio project file generation of strdup.[c|h]
  - curl_easy_setopt.3: add CURLOPT_PINNEDPUBLICKEY
  - curl.1: show zone index use in a URL
  - mk-ca-bundle.vbs: switch to new certdata.txt url
  - Makefile.dist: added some missing SSPI configurations
  - build: fixed no NTLM support for email when CURL_DISABLE_HTTP is defined
  - SSH: use the port number as well for known_known checks
  - libssh2: detect features based on version, not configure checks
  - http2: deal with HTTP/2 data inside Upgrade response header buffer
  - multi: removed Curl_multi_set_easy_connection
  - symbol-scan.pl: do not require autotools
  - cmake: add ENABLE_THREADED_RESOLVER, rename ARES
  - cmake: build libhostname for test suite
  - cmake: fix HAVE_GETHOSTNAME definition
  - tests: fix libhostname visibility
  - tests: fix memleak in server/resolve.c
  - vtls.h: fixed compiler warning when compiled without SSL
  - CMake: restore order-dependent header checks
  - CMake: restore order-dependent library checks
  - tool: removed krb4 from the supported features
  - http2: don't send Upgrade headers when we already do HTTP/2
  - examples: don't call select() to sleep on windows
  - win32: updated some legacy APIs to use the newer extended versions
  - easy.c: fixed compilation warning when no verbose string support
  - connect.c: fixed compilation warning when no verbose string support
  - build: in Makefile.m32 pass -F flag to windres
  - build: in Makefile.m32 add -m32 flag for 32bit
  - multi: when leaving for timeout, close accordingly
  - CMake: simplify if() conditions on check result variables
  - build: in Makefile.m32 try to detect 64bit target
  - multi: inform about closed sockets before they are closed
  - multi-uv.c: close the file handle after download
  - examples: wait recommended 100ms when no file descriptors are ready
  - ntlm: split the SSPI based messaging code from the native messaging code
  - cmake: fix NTLM detection when CURL_DISABLE_HTTP defined
  - cmake: add Kerberos to the supported feature
  - CURLOPT_POSTFIELDS.3: mention the COPYPOSTFIELDS option
  - http: disable pipelining for HTTP/2 and upgraded connections
  - ntlm: fixed static'ness of local decode function
  - sasl: reduced the need for two sets of NTLM messaging functions
  - multi.c: fixed compilation warnings when no verbose string support
  - select.c: fix compilation for VxWorks
  - multi-single.c: switch to use curl_multi_wait
  - curl_multi_wait.3: clarify numfds being used if not NULL
  - http.c: fixed compilation warnings from features being disabled
  - NSS: enable the CAPATH option
  - docs: fix FAILONERROR typos
  - HTTP: don't abort connections with pending Negotiate authentication
  - HTTP: free (proxy)userpwd for NTLM/Negotiate after sending a request
  - http_perhapsrewind: don't abort CONNECT requests
  - build: updated dependencies in makefiles
  - multi.c: fixed compilation warning
  - ftp.c: fixed compilation warnings when proxy support disabled
  - get_url_file_name: fixed crash on OOM on debug build
  - cookie.c: refactored cleanup code to simplify
  - OS400: enable NTLM authentication
  - ntlm: use Windows Crypt API
  - http2: avoid logging neg "failure" if h2 was not requested
  - schannel_recv: return the correct code
  - VC build: added sspi define for winssl-zlib builds
  - Curl_client_write(): chop long data, convert data only once
  - openldap: do not ignore Curl_client_write() return code
  - ldap: check Curl_client_write() return codes
  - parsedate.c: fixed compilation warning
  - url.c: fixed compilation warning when USE_NTLM is not defined
  - ntlm_wb_response: fix "statement not reached"
  - telnet: fix "cast increases required alignment of target type"
  - smtp: fixed dot stuffing when EOL characters at end of input buffers
  - ntlm: allow NTLM2Session messages when USE_NTRESPONSES manually defined
  - ntlm: disable NTLM v2 when 64-bit integers are not supported
  - ntlm: use short integer when decoding 16-bit values
  - ftp.c: fixed compilation warning when no verbose string support
  - synctime.c: fixed timeserver URLs
  - mk-ca-bundle.pl: restored forced run again
  - ntlm: fixed return code for bad type-2 Target Info
  - curl_schannel.c: data may be available before connection shutdown
  - curl_schannel: improvements to memory re-allocation strategy
  - darwinssl: aprintf() to allocate the session key
  - tool_util.c: use GetTickCount64 if it is available
  - lib: fixed multiple code analysis warnings if SAL are available
  - tool_binmode.c: explicitly ignore the return code of setmode
  - tool_urlglob.c: silence warning C6293: Ill-defined for-loop
  - opts: warn CURLOPT_TIMEOUT overrides when set after CURLOPT_TIMEOUT_MS
  - SFTP: work-around servers that return zero size on STAT
  - connect: singleipconnect(): properly try other address families after failure
  - IPV6: address scope != scope id
  - parseurlandfillconn(): fix improper non-numeric scope_id stripping
  - secureserver.pl: make OpenSSL CApath and cert absolute path values
  - secureserver.pl: update Windows detection and fix path conversion
  - secureserver.pl: clean up formatting of config and fix verbose output
  - tests: added Windows support using Cygwin-based OpenSSH
  - sockfilt.c: use non-Ex functions that are available before WinXP
  - VMS: updates for 0740-0D1220
  - openssl: warn for SRP set if SSLv3 is used, not for TLS version
  - openssl: make it compile against openssl 1.1.0-DEV master branch
  - openssl: fix SSL/TLS versions in verbose output
  - curl: show size of inhibited data when using -v
  - build: removed WIN32 definition from the Visual Studio projects
  - build: removed WIN64 definition from the libcurl Visual Studio projects
  - vtls: use bool for Curl_ssl_getsessionid() return type
  - sockfilt.c: replace 100ms sleep with thread throttle
  - sockfilt.c: reduce the number of individual memory allocations
  - vtls: don't set cert info count until memory allocation is successful
  - nss: don't ignore Curl_ssl_init_certinfo() OOM failure
  - nss: don't ignore Curl_extract_certinfo() OOM failure
  - vtls: fixed compilation warning and an ignored return code
  - sockfilt.c: fixed compilation warnings
  - darwinssl: fixed compilation warning
  - vtls: use '(void) arg' for unused parameters
  - sepheaders.c: fixed resource leak on failure
  - lib1900.c: fixed cppcheck error
  - ldap: fixed Unicode connection details in Win32 initialsation / bind calls
  - ldap: fixed Unicode DN, attributes and filter in Win32 search calls
- re-enable test 2034 (https with certificate pinning) as it seems to be
  working again on EL
- update patches as needed
- replace metalink patch with an openssl-specific version, since nss is fixed
  upstream
- BR: python for http-pipe testing
