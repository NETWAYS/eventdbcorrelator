#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.59)
AC_INIT("EDBC", 0.2.2, "info@netways.de")
AC_PREFIX_DEFAULT(/usr/local/edbc)


if test "x$prefix" = "xNONE" ; then
    installDir="/usr/local/edbc"
    prefix=$installDir
else
    installDir=$prefix 
fi


# Checks for programs.
AC_PROG_INSTALL
AC_PROG_MAKE_SET

# Checks for libraries.

# Checks for header files.

# Checks for typedefs, structures, and compiler characteristics.

# Checks for library functions.


AC_ARG_WITH([bin_user],
    AS_HELP_STRING([--with-bin-user=USER], [user for all other files (default root)]),
    bin_user=$withval,
    bin_user=root
)

AC_ARG_WITH([bin_group],
    AS_HELP_STRING([--with-bin-group=GROUP], [group for all other files (default bin)]),
    bin_group=$withval,
    bin_group=bin
)

AC_ARG_WITH([db_host],
    AS_HELP_STRING([--with-db-host=HOST], [Host of dbms (default localhost)]),
    db_host=$withval,
    db_host=localhost
)

AC_ARG_WITH([db_port],
    AS_HELP_STRING([--with-db-port=PORT], [Port of the dbms (default 3306)]),
    db_port=$withval,
    db_port=3306
)

AC_ARG_WITH([db_name],
    AS_HELP_STRING([--with-db-name=DBNAME], [DB name for eventdb (default eventdb)]),
    db_name=$withval,
    db_name=eventdb
)

AC_ARG_WITH([db_user],
    AS_HELP_STRING([--with-db-user=USER], [DB user for eventdb (default eventdb)]),
    db_user=$withval,
    db_user=eventdb
)

AC_ARG_WITH([db_pass],
    AS_HELP_STRING([--with-db-pass=PASS], [DB pass for eventdb (default eventdb)]),
    db_pass=$withval,
    db_pass=eventdb
)

AC_ARG_WITH([lock_dir],
    AS_HELP_STRING([--with-lock-dir=DIR], [Directory to use for storing the lockfile when using as a system daemon (default: $prefix/var)]),
    lock_dir=$withval,
    lock_dir=`readlink -m $prefix/var/`
)

AC_ARG_WITH([pid_dir],
    AS_HELP_STRING([--with-pid-dir=DIR], [Directory to use for storing the pidfile when using as a system daemon (default: /var/run/)]),
    pid_dir=$withval,
    pid_dir=/var/run
)

AC_ARG_WITH([log_file],
    AS_HELP_STRING([--with-log-file=FILE], [Filename to use for logging when running as a system daemon (default: $prefix/var/edbc.log)]),
    log_file=$withval,
    log_file=`readlink -m $prefix/var/edbc.log`
)

AC_SUBST(db_host)
AC_SUBST(db_port)
AC_SUBST(db_name)
AC_SUBST(db_user)
AC_SUBST(db_pass)
AC_SUBST(bin_user)
AC_SUBST(bin_group)
AC_SUBST(lock_dir)
AC_SUBST(pid_dir)
AC_SUBST(log_file)





AC_CONFIG_FILES([
    Makefile
    src/Makefile
    src/doc/Makefile
    src/config/config.py
    src/receptors/snmp_receptor.py
    src/receptors/pipe_receptor.py
    etc/conf.d/database.cfg
    etc/conf.d/mail.cfg
    etc/conf.d/snmp.cfg
    etc/conf.d/syslog.cfg
    etc/edbc.cfg
    bin/edbc
    bin/edbc.rc
    bin/edbc.rc.suse
])

AC_OUTPUT
