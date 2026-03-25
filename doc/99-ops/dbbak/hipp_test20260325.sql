-- MySQL dump 10.13  Distrib 8.0.30, for macos12 (arm64)
--
-- Host: 8.137.33.38    Database: hipp_test
-- ------------------------------------------------------
-- Server version	8.0.45-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `apscheduler_jobs`
--

DROP TABLE IF EXISTS `apscheduler_jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `apscheduler_jobs` (
  `id` varchar(191) NOT NULL,
  `next_run_time` double DEFAULT NULL,
  `job_state` longblob NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `scheduler_task_record`
--

DROP TABLE IF EXISTS `scheduler_task_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `scheduler_task_record` (
  `job_id` varchar(191) NOT NULL COMMENT '任务编号',
  `job_class` varchar(512) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `group` varchar(255) DEFAULT NULL,
  `exec_strategy` varchar(32) DEFAULT NULL,
  `expression` varchar(512) DEFAULT NULL,
  `start_time` varchar(32) DEFAULT NULL,
  `end_time` varchar(32) DEFAULT NULL,
  `process_time` float DEFAULT NULL,
  `retval` text,
  `exception` text,
  `traceback` text,
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `ix_scheduler_task_record_job_id` (`job_id`),
  KEY `ix_scheduler_task_record_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='定时任务执行记录（MySQL）';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_agent`
--

DROP TABLE IF EXISTS `vadmin_agent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_agent` (
  `api_server` varchar(500) NOT NULL COMMENT 'Dify API 服务器地址',
  `app_key` varchar(500) NOT NULL COMMENT 'Dify APP_KEY',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `name` varchar(255) DEFAULT NULL COMMENT '智能体名称',
  `description` text COMMENT '智能体描述',
  `tags` text COMMENT '标签 JSON 数组',
  `mode` varchar(50) DEFAULT NULL COMMENT '应用模式',
  `icon_type` varchar(20) DEFAULT NULL COMMENT '图标类型',
  `icon` varchar(255) DEFAULT NULL COMMENT '图标内容',
  `icon_background` varchar(20) DEFAULT NULL COMMENT '图标背景色',
  `icon_url` varchar(500) DEFAULT NULL COMMENT '图标图片URL',
  `webapp_config` text COMMENT 'Dify WebApp配置JSON',
  `status` varchar(20) NOT NULL COMMENT '上架状态: draft/published',
  `is_tested` tinyint(1) NOT NULL COMMENT '是否通过连通性测试',
  `create_user_id` int NOT NULL COMMENT '创建人',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `create_user_id` (`create_user_id`),
  KEY `ix_vadmin_agent_name` (`name`),
  CONSTRAINT `vadmin_agent_ibfk_1` FOREIGN KEY (`create_user_id`) REFERENCES `vadmin_auth_user` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能客服表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_auth_dept`
--

DROP TABLE IF EXISTS `vadmin_auth_dept`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_auth_dept` (
  `name` varchar(50) NOT NULL COMMENT '部门名称',
  `dept_key` varchar(50) NOT NULL COMMENT '部门标识',
  `disabled` tinyint(1) NOT NULL COMMENT '是否禁用',
  `order` int DEFAULT NULL COMMENT '显示排序',
  `desc` varchar(255) DEFAULT NULL COMMENT '描述',
  `owner` varchar(255) DEFAULT NULL COMMENT '负责人',
  `phone` varchar(255) DEFAULT NULL COMMENT '联系电话',
  `email` varchar(255) DEFAULT NULL COMMENT '邮箱',
  `parent_id` int DEFAULT NULL COMMENT '上级部门',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `parent_id` (`parent_id`),
  KEY `ix_vadmin_auth_dept_dept_key` (`dept_key`),
  KEY `ix_vadmin_auth_dept_name` (`name`),
  CONSTRAINT `vadmin_auth_dept_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `vadmin_auth_dept` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='部门表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_auth_menu`
--

DROP TABLE IF EXISTS `vadmin_auth_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_auth_menu` (
  `title` varchar(50) NOT NULL COMMENT '名称',
  `icon` varchar(50) DEFAULT NULL COMMENT '菜单图标',
  `redirect` varchar(100) DEFAULT NULL COMMENT '重定向地址',
  `component` varchar(255) DEFAULT NULL COMMENT '前端组件地址',
  `path` varchar(50) DEFAULT NULL COMMENT '前端路由地址',
  `disabled` tinyint(1) NOT NULL COMMENT '是否禁用',
  `hidden` tinyint(1) NOT NULL COMMENT '是否隐藏',
  `order` int NOT NULL COMMENT '排序',
  `menu_type` varchar(8) NOT NULL COMMENT '菜单类型',
  `parent_id` int DEFAULT NULL COMMENT '父菜单',
  `perms` varchar(50) DEFAULT NULL COMMENT '权限标识',
  `noCache` tinyint(1) NOT NULL COMMENT '如果设置为true，则不会被 <keep-alive> 缓存(默认 false)',
  `breadcrumb` tinyint(1) NOT NULL COMMENT '如果设置为false，则不会在breadcrumb面包屑中显示(默认 true)',
  `affix` tinyint(1) NOT NULL COMMENT '如果设置为true，则会一直固定在tag项中(默认 false)',
  `noTagsView` tinyint(1) NOT NULL COMMENT '如果设置为true，则不会出现在tag中(默认 false)',
  `canTo` tinyint(1) NOT NULL COMMENT '设置为true即使hidden为true，也依然可以进行路由跳转(默认 false)',
  `alwaysShow` tinyint(1) NOT NULL COMMENT '当你一个路由下面的 children 声明的路由大于1个时，自动会变成嵌套的模式，\n    只有一个时，会将那个子路由当做根路由显示在侧边栏，若你想不管路由下面的 children 声明的个数都显示你的根路由，\n    你可以设置 alwaysShow: true，这样它就会忽略之前定义的规则，一直显示根路由(默认 true)',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `parent_id` (`parent_id`),
  KEY `ix_vadmin_auth_menu_perms` (`perms`),
  CONSTRAINT `vadmin_auth_menu_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `vadmin_auth_menu` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=84 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='菜单表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_auth_role`
--

DROP TABLE IF EXISTS `vadmin_auth_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_auth_role` (
  `name` varchar(50) NOT NULL COMMENT '名称',
  `role_key` varchar(50) NOT NULL COMMENT '权限字符',
  `data_range` int NOT NULL COMMENT '数据权限范围',
  `disabled` tinyint(1) NOT NULL COMMENT '是否禁用',
  `order` int DEFAULT NULL COMMENT '排序',
  `desc` varchar(255) DEFAULT NULL COMMENT '描述',
  `is_admin` tinyint(1) NOT NULL COMMENT '是否为超级角色',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `ix_vadmin_auth_role_name` (`name`),
  KEY `ix_vadmin_auth_role_role_key` (`role_key`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='角色表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_auth_role_depts`
--

DROP TABLE IF EXISTS `vadmin_auth_role_depts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_auth_role_depts` (
  `role_id` int DEFAULT NULL,
  `dept_id` int DEFAULT NULL,
  KEY `dept_id` (`dept_id`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `vadmin_auth_role_depts_ibfk_1` FOREIGN KEY (`dept_id`) REFERENCES `vadmin_auth_dept` (`id`) ON DELETE CASCADE,
  CONSTRAINT `vadmin_auth_role_depts_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `vadmin_auth_role` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_auth_role_menus`
--

DROP TABLE IF EXISTS `vadmin_auth_role_menus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_auth_role_menus` (
  `role_id` int DEFAULT NULL,
  `menu_id` int DEFAULT NULL,
  KEY `menu_id` (`menu_id`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `vadmin_auth_role_menus_ibfk_1` FOREIGN KEY (`menu_id`) REFERENCES `vadmin_auth_menu` (`id`) ON DELETE CASCADE,
  CONSTRAINT `vadmin_auth_role_menus_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `vadmin_auth_role` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_auth_user`
--

DROP TABLE IF EXISTS `vadmin_auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_auth_user` (
  `avatar` varchar(500) DEFAULT NULL COMMENT '头像',
  `telephone` varchar(11) NOT NULL COMMENT '手机号',
  `email` varchar(50) DEFAULT NULL COMMENT '邮箱地址',
  `name` varchar(50) NOT NULL COMMENT '姓名',
  `nickname` varchar(50) DEFAULT NULL COMMENT '昵称',
  `password` varchar(255) DEFAULT NULL COMMENT '密码',
  `gender` varchar(8) DEFAULT NULL COMMENT '性别',
  `is_active` tinyint(1) NOT NULL COMMENT '是否可用',
  `is_reset_password` tinyint(1) NOT NULL COMMENT '是否已经重置密码，没有重置的，登陆系统后必须重置密码',
  `last_ip` varchar(50) DEFAULT NULL COMMENT '最后一次登录IP',
  `last_login` datetime DEFAULT NULL COMMENT '最近一次登录时间',
  `is_staff` tinyint(1) NOT NULL COMMENT '是否为工作人员',
  `wx_server_openid` varchar(255) DEFAULT NULL COMMENT '服务端微信平台openid',
  `is_wx_server_openid` tinyint(1) NOT NULL COMMENT '是否已有服务端微信平台openid',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `ix_vadmin_auth_user_name` (`name`),
  KEY `ix_vadmin_auth_user_telephone` (`telephone`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_auth_user_depts`
--

DROP TABLE IF EXISTS `vadmin_auth_user_depts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_auth_user_depts` (
  `user_id` int DEFAULT NULL,
  `dept_id` int DEFAULT NULL,
  KEY `dept_id` (`dept_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `vadmin_auth_user_depts_ibfk_1` FOREIGN KEY (`dept_id`) REFERENCES `vadmin_auth_dept` (`id`) ON DELETE CASCADE,
  CONSTRAINT `vadmin_auth_user_depts_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `vadmin_auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_auth_user_roles`
--

DROP TABLE IF EXISTS `vadmin_auth_user_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_auth_user_roles` (
  `user_id` int DEFAULT NULL,
  `role_id` int DEFAULT NULL,
  KEY `role_id` (`role_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `vadmin_auth_user_roles_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `vadmin_auth_role` (`id`) ON DELETE CASCADE,
  CONSTRAINT `vadmin_auth_user_roles_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `vadmin_auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_chat_message`
--

DROP TABLE IF EXISTS `vadmin_chat_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_chat_message` (
  `session_id` int NOT NULL COMMENT '会话 vadmin_chat_session.id',
  `role` varchar(20) NOT NULL COMMENT 'user / assistant / system',
  `content` text NOT NULL COMMENT '消息内容',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `ix_vadmin_chat_message_session_id` (`session_id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='小程序会话消息';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_chat_session`
--

DROP TABLE IF EXISTS `vadmin_chat_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_chat_session` (
  `user_id` int NOT NULL COMMENT '用户 vadmin_auth_user.id',
  `agent_id` int DEFAULT NULL COMMENT '智能体 vadmin_agent.id',
  `title` varchar(255) NOT NULL COMMENT '展示标题',
  `last_message_preview` varchar(500) DEFAULT NULL COMMENT '最近消息摘要',
  `is_pinned` tinyint(1) NOT NULL COMMENT '是否置顶',
  `dify_conversation_id` varchar(255) DEFAULT NULL COMMENT 'Dify conversation_id',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  `agent_name_snapshot` varchar(255) DEFAULT NULL COMMENT '智能体名称快照',
  `agent_avatar_snapshot` varchar(500) DEFAULT NULL COMMENT '智能体头像快照',
  `is_topic_closed` tinyint(1) NOT NULL COMMENT '话题是否已结束（归档）',
  `session_kind` varchar(32) NOT NULL COMMENT 'dify=智能体对话 human_support=人工客服',
  `assigned_human_user_id` int DEFAULT NULL COMMENT '分配的人工客服 vadmin_auth_user.id',
  `source_archive_session_id` int DEFAULT NULL COMMENT '触发人工会话的归档会话 id',
  PRIMARY KEY (`id`),
  KEY `ix_vadmin_chat_session_user_id` (`user_id`),
  KEY `ix_vadmin_chat_session_agent_id` (`agent_id`),
  KEY `ix_vadmin_chat_session_session_kind` (`session_kind`),
  KEY `ix_vadmin_chat_session_assigned_human_user_id` (`assigned_human_user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='小程序用户与智能体会话';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_help_issue`
--

DROP TABLE IF EXISTS `vadmin_help_issue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_help_issue` (
  `category_id` int NOT NULL COMMENT '类别',
  `title` varchar(255) NOT NULL COMMENT '标题',
  `content` text NOT NULL COMMENT '内容',
  `view_number` int NOT NULL COMMENT '查看次数',
  `is_active` tinyint(1) NOT NULL COMMENT '是否可见',
  `create_user_id` int NOT NULL COMMENT '创建人',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `category_id` (`category_id`),
  KEY `create_user_id` (`create_user_id`),
  KEY `ix_vadmin_help_issue_title` (`title`),
  CONSTRAINT `vadmin_help_issue_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `vadmin_help_issue_category` (`id`) ON DELETE CASCADE,
  CONSTRAINT `vadmin_help_issue_ibfk_2` FOREIGN KEY (`create_user_id`) REFERENCES `vadmin_auth_user` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='常见问题记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_help_issue_category`
--

DROP TABLE IF EXISTS `vadmin_help_issue_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_help_issue_category` (
  `name` varchar(50) NOT NULL COMMENT '类别名称',
  `platform` varchar(8) NOT NULL COMMENT '展示平台',
  `is_active` tinyint(1) NOT NULL COMMENT '是否可见',
  `create_user_id` int NOT NULL COMMENT '创建人',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `create_user_id` (`create_user_id`),
  KEY `ix_vadmin_help_issue_category_name` (`name`),
  KEY `ix_vadmin_help_issue_category_platform` (`platform`),
  CONSTRAINT `vadmin_help_issue_category_ibfk_1` FOREIGN KEY (`create_user_id`) REFERENCES `vadmin_auth_user` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='常见问题类别表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_record_login`
--

DROP TABLE IF EXISTS `vadmin_record_login`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_record_login` (
  `telephone` varchar(255) NOT NULL COMMENT '手机号',
  `status` tinyint(1) NOT NULL COMMENT '是否登录成功',
  `platform` varchar(8) NOT NULL COMMENT '登陆平台',
  `login_method` varchar(8) NOT NULL COMMENT '认证方式',
  `ip` varchar(50) DEFAULT NULL COMMENT '登陆地址',
  `address` varchar(255) DEFAULT NULL COMMENT '登陆地点',
  `country` varchar(255) DEFAULT NULL COMMENT '国家',
  `province` varchar(255) DEFAULT NULL COMMENT '县',
  `city` varchar(255) DEFAULT NULL COMMENT '城市',
  `county` varchar(255) DEFAULT NULL COMMENT '区/县',
  `operator` varchar(255) DEFAULT NULL COMMENT '运营商',
  `postal_code` varchar(255) DEFAULT NULL COMMENT '邮政编码',
  `area_code` varchar(255) DEFAULT NULL COMMENT '地区区号',
  `browser` varchar(50) DEFAULT NULL COMMENT '浏览器',
  `system` varchar(50) DEFAULT NULL COMMENT '操作系统',
  `response` text COMMENT '响应信息',
  `request` text COMMENT '请求信息',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `ix_vadmin_record_login_telephone` (`telephone`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='登录记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_record_operation`
--

DROP TABLE IF EXISTS `vadmin_record_operation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_record_operation` (
  `telephone` varchar(32) DEFAULT NULL COMMENT '手机号',
  `user_id` int DEFAULT NULL COMMENT '用户ID',
  `user_name` varchar(255) DEFAULT NULL COMMENT '用户名',
  `status_code` int DEFAULT NULL COMMENT 'HTTP 状态码',
  `client_ip` varchar(64) DEFAULT NULL COMMENT '客户端 IP',
  `request_method` varchar(16) DEFAULT NULL COMMENT 'HTTP 方法',
  `api_path` varchar(512) DEFAULT NULL COMMENT '路由 path',
  `system` varchar(128) DEFAULT NULL COMMENT '操作系统',
  `browser` varchar(128) DEFAULT NULL COMMENT '浏览器',
  `summary` varchar(255) DEFAULT NULL COMMENT '接口摘要',
  `route_name` varchar(128) DEFAULT NULL COMMENT '路由 name',
  `description` text COMMENT '接口描述',
  `tags` text COMMENT '标签 JSON 数组',
  `process_time` float DEFAULT NULL COMMENT '处理耗时(秒)',
  `params` text COMMENT '请求参数 JSON',
  `request_api` text COMMENT '完整请求 URL',
  `content_length` varchar(32) DEFAULT NULL COMMENT 'Content-Length',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `ix_vadmin_record_operation_request_method` (`request_method`),
  KEY `ix_vadmin_record_operation_summary` (`summary`),
  KEY `ix_vadmin_record_operation_telephone` (`telephone`)
) ENGINE=InnoDB AUTO_INCREMENT=98 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='操作审计（Mongo 关闭时）';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_record_sms_send`
--

DROP TABLE IF EXISTS `vadmin_record_sms_send`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_record_sms_send` (
  `user_id` int NOT NULL COMMENT '操作人',
  `status` tinyint(1) NOT NULL COMMENT '发送状态',
  `content` varchar(255) NOT NULL COMMENT '发送内容',
  `telephone` varchar(11) NOT NULL COMMENT '目标手机号',
  `desc` varchar(255) DEFAULT NULL COMMENT '失败描述',
  `scene` varchar(50) DEFAULT NULL COMMENT '发送场景',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `vadmin_record_sms_send_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `vadmin_auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='短信发送记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_resource_images`
--

DROP TABLE IF EXISTS `vadmin_resource_images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_resource_images` (
  `filename` varchar(255) NOT NULL COMMENT '原图片名称',
  `image_url` varchar(500) NOT NULL COMMENT '图片链接',
  `create_user_id` int NOT NULL COMMENT '创建人',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `create_user_id` (`create_user_id`),
  CONSTRAINT `vadmin_resource_images_ibfk_1` FOREIGN KEY (`create_user_id`) REFERENCES `vadmin_auth_user` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='图片素材表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_system_dict_details`
--

DROP TABLE IF EXISTS `vadmin_system_dict_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_system_dict_details` (
  `label` varchar(50) NOT NULL COMMENT '字典标签',
  `value` varchar(50) NOT NULL COMMENT '字典键值',
  `disabled` tinyint(1) NOT NULL COMMENT '字典状态，是否禁用',
  `is_default` tinyint(1) NOT NULL COMMENT '是否默认',
  `order` int NOT NULL COMMENT '字典排序',
  `dict_type_id` int NOT NULL COMMENT '关联字典类型',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `dict_type_id` (`dict_type_id`),
  KEY `ix_vadmin_system_dict_details_label` (`label`),
  KEY `ix_vadmin_system_dict_details_value` (`value`),
  CONSTRAINT `vadmin_system_dict_details_ibfk_1` FOREIGN KEY (`dict_type_id`) REFERENCES `vadmin_system_dict_type` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='字典详情表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_system_dict_type`
--

DROP TABLE IF EXISTS `vadmin_system_dict_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_system_dict_type` (
  `dict_name` varchar(50) NOT NULL COMMENT '字典名称',
  `dict_type` varchar(50) NOT NULL COMMENT '字典类型',
  `disabled` tinyint(1) NOT NULL COMMENT '字典状态，是否禁用',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  KEY `ix_vadmin_system_dict_type_dict_name` (`dict_name`),
  KEY `ix_vadmin_system_dict_type_dict_type` (`dict_type`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='字典类型表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_system_settings`
--

DROP TABLE IF EXISTS `vadmin_system_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_system_settings` (
  `config_label` varchar(255) NOT NULL COMMENT '配置表标签',
  `config_key` varchar(255) NOT NULL COMMENT '配置表键',
  `config_value` text COMMENT '配置表内容',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注信息',
  `disabled` tinyint(1) NOT NULL COMMENT '是否禁用',
  `tab_id` int NOT NULL COMMENT '关联tab标签',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_vadmin_system_settings_config_key` (`config_key`),
  KEY `tab_id` (`tab_id`),
  CONSTRAINT `vadmin_system_settings_ibfk_1` FOREIGN KEY (`tab_id`) REFERENCES `vadmin_system_settings_tab` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_system_settings_tab`
--

DROP TABLE IF EXISTS `vadmin_system_settings_tab`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_system_settings_tab` (
  `title` varchar(255) NOT NULL COMMENT '标题',
  `classify` varchar(255) NOT NULL COMMENT '分类键',
  `tab_label` varchar(255) NOT NULL COMMENT 'tab标题',
  `tab_name` varchar(255) NOT NULL COMMENT 'tab标识符',
  `hidden` tinyint(1) NOT NULL COMMENT '是否隐藏',
  `disabled` tinyint(1) NOT NULL COMMENT '是否禁用',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_vadmin_system_settings_tab_tab_name` (`tab_name`),
  KEY `ix_vadmin_system_settings_tab_classify` (`classify`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统配置分类表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_system_task`
--

DROP TABLE IF EXISTS `vadmin_system_task`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_system_task` (
  `task_id` varchar(24) NOT NULL COMMENT '任务编号',
  `name` varchar(255) NOT NULL COMMENT '任务名称',
  `group` varchar(255) DEFAULT NULL COMMENT '分组',
  `job_class` text NOT NULL COMMENT '任务类路径',
  `exec_strategy` varchar(32) NOT NULL COMMENT '执行策略',
  `expression` varchar(512) NOT NULL COMMENT '表达式',
  `remark` varchar(512) DEFAULT NULL COMMENT '备注',
  `start_date` varchar(32) DEFAULT NULL COMMENT '开始时间',
  `end_date` varchar(32) DEFAULT NULL COMMENT '结束时间',
  `task_disabled` tinyint(1) NOT NULL COMMENT '调度失败等标记',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`task_id`),
  KEY `ix_vadmin_system_task_group` (`group`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='定时任务定义（MySQL）';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vadmin_system_task_group`
--

DROP TABLE IF EXISTS `vadmin_system_task_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vadmin_system_task_group` (
  `value` varchar(255) NOT NULL COMMENT '分组值',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_datetime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `delete_datetime` datetime DEFAULT NULL COMMENT '删除时间',
  `is_delete` tinyint(1) NOT NULL COMMENT '是否软删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `value` (`value`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='定时任务分组（MySQL）';
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-03-25 15:22:39
