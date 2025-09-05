#
# Regular cron jobs for the sql-tool package.
#
0 4	* * *	root	[ -x /usr/bin/sql-tool_maintenance ] && /usr/bin/sql-tool_maintenance
