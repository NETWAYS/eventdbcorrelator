#
# Update from plain eventdb
#
ALTER TABLE event ADD  `group_active`        tinyint(1) default '0';
ALTER TABLE event ADD  `group_id`            binary(16) default NULL; 
ALTER TABLE event ADD  `group_count`         int(16) default NULL; 
ALTER TABLE event ADD  `group_leader`        bigint(20) default NULL;
ALTER TABLE event ADD  `group_autoclear`     tinyint(1) default '0';
ALTER TABLE event ADD  `flags`               int(11) default '0';
ALTER TABLE event ADD KEY `group_active` (`group_active`);
ALTER TABLE event ADD KEY `idx_groups` (`group_id`,`group_active`,`group_leader`);
