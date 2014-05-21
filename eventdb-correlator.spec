Name:		eventdb-correlator
Version:	0.2.0
Release:	1%{?dist}
Summary:	EDBC (EventDB Correlator) is an agent for EventDB

Group:		Applications/System
License:	GPL v2 or later
URL:		https://www.netways.org/projects/edbc
Source0:	https://www.netways.org/attachments/download/980/eventdbcorrelator-0.2.0.tar.gz
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}

%if "%{_vendor}" == "redhat"
Requires:	MySQL-python
Requires(pre):	shadow-utils
Requires(post):	chkconfig
Requires(preun):	chkconfig
%endif
%if "%{_vendor}" == "suse"
Requires:	python-mysql
%endif

%define	progname edbc

%description
EDBC (EventDB Correlator) is an agent for EventDB, our tool for integrating passive monitoring 
(like snmp, syslog or mail events) into icinga (or similar) monitoring enviromnents. 
EDBC offers a lot of features that are required to cover advanced monitoring use cases:
* Pipe based event collection with the possibility to define your own input formats
* Basic support for acting as a snmp_agent by parsing and using SNMPTT mib files
* Aggregation of events based on advanced matcher patterns
* Clearance of aggregations via clear matchers or by timeout
* Extensible and easy to understand event processor mechanismn for writing your own processors


%prep
%setup -qn eventdbcorrelator-%{version}

%clean
rm -rf %{buildroot}

%build
%configure \
  --sysconfdir="%{_sysconfdir}/%{name}" \
  --libdir="%{_libdir}/%{name}" \
  --libexecdir="%{_libexecdir}/%{name}" \
  --localstatedir="%{_localstatedir}/cache/%{name}" \
  --with-log-file="%{_localstatedir}/log/%{name}/%{progname}.log" \
  --with-lock-dir="%{_localstatedir}/lock/subsys"

%if 0%{?el5} || 0%{?rhel} == 5 || "%{?dist}" == ".el5"
# disable email modules because of missing support in older python version
sed -i 'sX^from mail_X#\0X' src/receptors/__init__.py
sed -i 'sX^from mail_X#\0X' src/event/__init__.py
%endif

%install
make install DESTDIR=%{buildroot} \
  INSTALL_OPTS="" 
%{__mkdir_p} %{buildroot}%{_defaultdocdir}/%{name}-%{version}
%{__mv} %{buildroot}/%{_libdir}/%{name}/doc/* %{buildroot}%{_defaultdocdir}/%{name}-%{version}
%{__mkdir_p} %{buildroot}%{_sysconfdir}/init.d
%if "%{_vendor}" == "redhat"
%{__install} -m 755 ./bin/edbc.rc %{buildroot}%{_sysconfdir}/init.d/%{progname}
%endif
%if "%{_vendor}" == "suse"
%{__install} -m 755 ./bin/edbc.rc.suse %{buildroot}%{_sysconfdir}/init.d/%{progname}
%endif
%{__mkdir_p} %{buildroot}%{_localstatedir}/log/%{name}
%{__mkdir_p} %{buildroot}%{_sbindir}
echo '#!/bin/bash
%{__rm} %{_localstatedir}/cache/%{name}/*' >  %{buildroot}%{_sbindir}/%{progname}-clearcache

%pre
getent group %{progname} >/dev/null || groupadd -r %{progname}
getent passwd %{progname} >/dev/null || \
    useradd -r -g %{progname} -d %{_libexecdir}/%{name} -s /sbin/nologin \
    -c "Eventdb Correlator" %{progname}
exit 0

%post
/sbin/chkconfig --add %{progname}

%preun
if [ $1 -eq 0 ] ; then
/sbin/service %{progname} stop >/dev/null 2>&1
%{_sbindir}/%{progname}-clearcache || :
/sbin/chkconfig --del %{progname}
fi

%files
%defattr(-,root,root)
%doc %{_defaultdocdir}/%{name}-%{version}
%dir %{_sysconfdir}/%{name}
%dir %{_sysconfdir}/%{name}/chains
%dir %{_sysconfdir}/%{name}/conf.d
%dir %{_sysconfdir}/%{name}/conf.d/base
%dir %{_sysconfdir}/%{name}/mail
%dir %{_sysconfdir}/%{name}/rules
%config(noreplace) %{_sysconfdir}/%{name}/edbc.cfg
%config(noreplace) %{_sysconfdir}/%{name}/chains/*.chain
%config(noreplace) %{_sysconfdir}/%{name}/conf.d/*.cfg
%config(noreplace) %{_sysconfdir}/%{name}/conf.d/base/*.cfg
%config(noreplace) %{_sysconfdir}/%{name}/mail/*.filter
%config(noreplace) %{_sysconfdir}/%{name}/rules/*.rules
%{_libdir}/%{name}
%{_libexecdir}/%{name}
%{_bindir}/%{progname}
%attr(0750,root,root) %{_sbindir}/%{progname}-clearcache
%{_sysconfdir}/init.d/%{progname}
%defattr(-,%{progname},%{progname})
%{_localstatedir}/log/%{name}
%{_localstatedir}/cache/%{name}



%changelog
* Mon Feb 03 2014 Dirk Goetz <dirk.goetz@netways.de> - 0.2.0-1
- initial creation

