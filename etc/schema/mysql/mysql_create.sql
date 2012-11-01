CREATE TABLE event (
  `id`                  bigint(20) unsigned NOT NULL auto_increment,
  `host_name`           varchar(255) NOT NULL,
  `host_address`        binary(16) DEFAULT '',
  `type`                int(11) NOT NULL,
  `facility`            int(11),
  `priority`            int(11) NOT NULL,
  `program`             varchar(50) character set ascii NOT NULL,
  `message`             varchar(4096) default NULL,
  `alternative_message`          varchar(4096) default NULL,
  `ack`                 tinyint(1) default '0',
  `created`             datetime default NULL,
  `modified`            datetime default NULL,
  `active`              tinyint(1) default '1',
  `group_active`        tinyint(1) default '0',
  `group_id`            binary(16) default NULL, 
  `group_count`         int(16) default NULL, 
  `group_leader`        bigint(20) default NULL,
  `group_autoclear`     tinyint(1) default '0',
  `flags`               int(11) default '0',
  
  PRIMARY KEY (`id`),
  KEY `host_address` (`host_address`),
  KEY `host_name` (`host_name`),
  KEY `ack` (`ack`),
  KEY `group_id` (`group_id`),
  KEY `type` (`type`),
  KEY `active` (`active`),
  KEY `group_active` (`group_active`),
  KEY `idx_groups` (`group_id`,`group_active`,`group_leader`),
  KEY `flags` (`flags`)
) ENGINE=InnoDB;


CREATE TABLE comment (
  `id`          int(10) unsigned NOT NULL auto_increment,
  `event_id`    bigint(20) unsigned NOT NULL,
  `type`        int(10) unsigned default '0',
  `message`     varchar(1024) default NULL,
  `created`     datetime default NULL,
  `modified`    datetime default NULL,
  `user`        varchar(64) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `fk_event_id` (`event_id`),
  KEY `idx_all` (`id`,`event_id`,`user`),	
  CONSTRAINT `db_comments_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `event` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;
