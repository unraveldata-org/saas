SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema clm
-- -----------------------------------------------------


CREATE SCHEMA IF NOT EXISTS `clm` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci ;
USE `clm` ;

-- -----------------------------------------------------
-- Table `trial_request`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `trial_request` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(128) NOT NULL,
  `last_name` VARCHAR(128) NOT NULL,
  `email` VARCHAR(256) NOT NULL,
  `title` VARCHAR(256) DEFAULT NULL,
  `company` VARCHAR(256) DEFAULT NULL,
  `ip` VARCHAR(32) DEFAULT NULL,
  `state` VARCHAR(32) NOT NULL,
  `start_date` DATETIME NOT NULL,
  `cloud_provider` VARCHAR(128) NOT NULL,
  `create_cluster` BOOLEAN NOT NULL,
  `notify_customer` VARCHAR(32) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- -----------------------------------------------------
-- Table `node_spec`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `node_spec` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `cloud_provider` VARCHAR(128) NOT NULL,
  `state` VARCHAR(32) NOT NULL,
  `user` VARCHAR(64) NOT NULL,
  `node_type` VARCHAR(256) NOT NULL,
  `storage_config` TEXT NULL,
  `unravel_version` VARCHAR(64) NOT NULL,
  `unravel_tar` VARCHAR(256) NULL,
  `mysql_version` VARCHAR(256) NULL,
  `install_ondemand` BOOLEAN NOT NULL,
  `extra` TEXT NULL,
  `date_requested` DATETIME NOT NULL,
  `ttl_hours` SMALLINT UNSIGNED NOT NULL,
  `trial_request_id` INT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_node_spec_trial_request_id`
    FOREIGN KEY (`trial_request_id`)
    REFERENCES `trial_request` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- TODO, add region
-- -----------------------------------------------------
-- Table `cluster_spec`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cluster_spec` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `cloud_provider` VARCHAR(128) NOT NULL,
  `state` VARCHAR(32) NOT NULL,
  `user` VARCHAR(64) NOT NULL,
  `num_head_nodes` INT UNSIGNED NOT NULL,
  `head_node_type` VARCHAR(256) NOT NULL,
  `num_worker_nodes` INT UNSIGNED NOT NULL,
  `worker_node_type` VARCHAR(256) NOT NULL,
  `os_family` VARCHAR(128) NULL,
  `stack_version` VARCHAR(128) NULL,
  `cluster_type` VARCHAR(128) NULL,
  `jdk` VARCHAR(32) NULL,
  `storage` VARCHAR(1024) NULL,
  `services` TEXT NULL,
  `is_hdfs_ha` BOOLEAN NULL,
  `is_rm_ha` BOOLEAN NULL,
  `is_ssl` BOOLEAN NULL,
  `is_kerberized` BOOLEAN NULL,
  `extra` TEXT NULL,
  `date_requested` DATETIME NOT NULL,
  `ttl_hours` SMALLINT UNSIGNED NOT NULL,
  `trial_request_id` INT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_cluster_spec_trial_request_id`
    FOREIGN KEY (`trial_request_id`)
    REFERENCES `trial_request` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- -----------------------------------------------------
-- Table `node`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `node` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `cloud_provider` VARCHAR(128) NOT NULL,
  `state` VARCHAR(32) NOT NULL,
  `node_type` VARCHAR(256) NOT NULL,
  `node_ip` VARCHAR(32) NULL,
  `ttl_hours` SMALLINT UNSIGNED NOT NULL,
  `date_launched` DATETIME NOT NULL,
  `date_ready` DATETIME NULL,
  `date_expired` DATETIME NULL,
  `date_deleted` DATETIME NULL,
  `node_spec_id` INT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_node_node_spec_id`
    FOREIGN KEY (`node_spec_id`)
    REFERENCES `node_spec` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- -----------------------------------------------------
-- Table `cluster`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cluster` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `cloud_provider` VARCHAR(128) NOT NULL,
  `cluster_name` VARCHAR(128) NOT NULL,
  `state` VARCHAR(32) NOT NULL,
  `config` TEXT,
  `ttl_hours` SMALLINT UNSIGNED NOT NULL,
  `date_launched` DATETIME NOT NULL,
  `date_ready` DATETIME NULL,
  `date_expired` DATETIME NULL,
  `date_deleted` DATETIME NULL,
  `cluster_spec_id` INT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_cluster_cluster_spec_id`
    FOREIGN KEY (`cluster_spec_id`)
    REFERENCES `cluster_spec` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;