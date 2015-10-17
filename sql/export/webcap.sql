/*
Navicat MySQL Data Transfer

Source Server         : mysql
Source Server Version : 50521
Source Host           : localhost:3306
Source Database       : webcap

Target Server Type    : MYSQL
Target Server Version : 50521
File Encoding         : 65001

Date: 2015-10-17 16:40:08
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for account
-- ----------------------------
DROP TABLE IF EXISTS `account`;
CREATE TABLE `account` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `username` varchar(64) NOT NULL COMMENT '昵称',
  `password` varchar(64) NOT NULL COMMENT '密码',
  `name` varchar(32) DEFAULT NULL COMMENT '姓名',
  `size` bigint(20) NOT NULL DEFAULT '0' COMMENT '用户资源总大小',
  `device_num` bigint(3) NOT NULL DEFAULT '0' COMMENT '设备个数',
  `role_id` bigint(20) NOT NULL DEFAULT '1' COMMENT '角色',
  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0: normal, 1: deleted',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `account_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `role` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18620749655 DEFAULT CHARSET=utf8 COMMENT='账号表';

-- ----------------------------
-- Records of account
-- ----------------------------
INSERT INTO `account` VALUES ('18620749654', 'admin', '20966d46a6446a610bce72e00eccd954', null, '0', '1', '1', '0');

-- ----------------------------
-- Table structure for device
-- ----------------------------
DROP TABLE IF EXISTS `device`;
CREATE TABLE `device` (
  `id` varchar(50) NOT NULL COMMENT '设备ID',
  `name` varchar(64) NOT NULL COMMENT '设备名',
  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0: normal, 1: deleted',
  `account_id` bigint(20) NOT NULL COMMENT '账号ID',
  UNIQUE KEY `id` (`id`),
  KEY `account_id` (`account_id`),
  CONSTRAINT `device_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `account` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='设备表';

-- ----------------------------
-- Records of device
-- ----------------------------
INSERT INTO `device` VALUES ('0d0b0e608af645a0590d0c425', '1234', '0', '18620749654');

-- ----------------------------
-- Table structure for role
-- ----------------------------
DROP TABLE IF EXISTS `role`;
CREATE TABLE `role` (
  `id` bigint(20) NOT NULL COMMENT '角色识别码 0:管理员,1:普通用户',
  `name` varchar(32) NOT NULL COMMENT '角色名称',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='角色表';

-- ----------------------------
-- Records of role
-- ----------------------------
INSERT INTO `role` VALUES ('0', '管理员');
INSERT INTO `role` VALUES ('1', '普通用户');

-- ----------------------------
-- Table structure for src
-- ----------------------------
DROP TABLE IF EXISTS `src`;
CREATE TABLE `src` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '资源ID',
  `create_time` datetime DEFAULT NULL COMMENT '资源创建时间,即任务完成时间',
  `src_path` varchar(200) DEFAULT NULL COMMENT '资源——url',
  `thumbnail` varchar(200) DEFAULT NULL COMMENT '缩略图——url',
  `size` bigint(20) DEFAULT NULL COMMENT '资源大小',
  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0: normal, 1: deleted',
  `device_id` bigint(20) NOT NULL COMMENT '设备ID',
  `account_id` bigint(20) NOT NULL COMMENT '账号ID',
  PRIMARY KEY (`id`),
  KEY `account_id` (`account_id`),
  CONSTRAINT `src_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `account` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='资源表';

-- ----------------------------
-- Records of src
-- ----------------------------

-- ----------------------------
-- Table structure for task
-- ----------------------------
DROP TABLE IF EXISTS `task`;
CREATE TABLE `task` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  `create_time` datetime DEFAULT NULL COMMENT '任务创建时间',
  `duration` bigint(20) DEFAULT NULL COMMENT '持续时间',
  `interval` bigint(20) DEFAULT NULL COMMENT '时间间隔',
  `now` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0: 非即时, 1: 即时',
  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0: normal, 1: deleted',
  `device_id` varchar(50) NOT NULL COMMENT '设备ID',
  `account_id` bigint(20) NOT NULL COMMENT '账号ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `device_id` (`device_id`),
  KEY `account_id` (`account_id`),
  CONSTRAINT `task_ibfk_1` FOREIGN KEY (`account_id`) REFERENCES `account` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COMMENT='任务表';

-- ----------------------------
-- Records of task
-- ----------------------------
INSERT INTO `task` VALUES ('1', '2015-10-17 15:14:59', '5', '5', '0', '0', '0d0b0e608af645a0590d0c425', '18620749654');
