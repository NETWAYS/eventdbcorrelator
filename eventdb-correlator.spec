Name:		eventdb-correlator
Version:	0.2.0
Release:	1%{?dist}
Summary:	EDBC (EventDB Correlator) is an agent for EventDB

Group:		Applications/System
License:	GPL v2 or later
URL:		https://www.netways.org/projects/edbc
Source0:	https://www.netways.org/attachments/download/980/eventdbcorrelator-0.2.0.tar.gz

#BuildRequires:	
#Requires:	

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


%build
%configure \
  --sysconfdir="%{_sysconfdir}/%{name}" \
  --libdir="%{_libdir}/%{name}" \
  --libexecdir="%{_libexecdir}/%{name}"
#make %{?_smp_mflags}


%install
make install DESTDIR=%{buildroot} \
  INSTALL_OPTS="" 


%files
%defattr(-,root,root)
%doc
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
%{_bindir}/edbc



%changelog

