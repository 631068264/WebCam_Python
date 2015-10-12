CREATE TABLE `role` (
	`id` BIGINT (20) NOT NULL COMMENT '��ɫʶ���� 0:����Ա,1:��ͨ�û�',
	`name` VARCHAR (32) NOT NULL COMMENT '��ɫ����',
	PRIMARY KEY (`id`)
) ENGINE = INNODB DEFAULT CHARSET = utf8 COMMENT = '��ɫ��';
INSERT INTO `role` VALUES ('0', '����Ա');
INSERT INTO `role` VALUES ('1', '��ͨ�û�');

CREATE TABLE `account` (
	`id` BIGINT (20) NOT NULL,
	`username` VARCHAR (64) NOT NULL UNIQUE COMMENT '�ǳ�',
	`password` VARCHAR (64) NOT NULL COMMENT '����',
	`name` VARCHAR (32) DEFAULT NULL COMMENT '����',
	`device` VARCHAR (128) NOT NULL DEFAULT '0' COMMENT '�豸ʶ����',
	`role_id` BIGINT (20) NOT NULL DEFAULT '1' COMMENT '��ɫ',
	`status` TINYINT (4) NOT NULL DEFAULT '0' COMMENT '0: normal, 1: deleted',
	PRIMARY KEY (`id`),
	FOREIGN KEY (`role_id`) REFERENCES `role` (`id`)
) ENGINE = INNODB AUTO_INCREMENT = 1 DEFAULT CHARSET = utf8 COMMENT = '�˺ű�';
INSERT INTO `account` VALUES ('150328239', 'admin', 'c3e01e2715dd95ee3e97475276b2f74b', null, 'd1cc4dfcd4145a0a2ecd44cb3', '1', '0');

CREATE TABLE `task` (
	`id` BIGINT (20) NOT NULL,
	`name` VARCHAR (64) NOT NULL DEFAULT 'Default' COMMENT '�û��Զ���������',
	`src` VARCHAR (200) DEFAULT NULL COMMENT '��Դ����url',
	`thumbnail` VARCHAR (200) DEFAULT NULL COMMENT '����ͼ����url',
	`create_time` datetime DEFAULT NULL COMMENT '���񴴽�ʱ�� ��������',
	`duration` BIGINT (20) DEFAULT NULL COMMENT '����ʱ��',
	`interval` BIGINT (20) DEFAULT NULL COMMENT 'ʱ����',
	`size` BIGINT (20) DEFAULT NULL COMMENT '��Դ��С',
	`account_id` BIGINT (20) NOT NULL COMMENT '�û�id',
	`status` TINYINT (4) NOT NULL DEFAULT '0' COMMENT '0: normal, 1: deleted',
	PRIMARY KEY (`id`),
	FOREIGN KEY (`account_id`) REFERENCES `account` (`id`)
) ENGINE = INNODB AUTO_INCREMENT = 1 DEFAULT CHARSET = utf8 COMMENT = '�����';

INSERT INTO `task` VALUES ('1', 'Default', null, null, '2015-10-12 22:21:29', '3', '2', null, '150328239', '0');